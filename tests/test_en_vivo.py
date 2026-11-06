from datetime import datetime, timedelta, timezone

import pandas as pd
import pytest
from fastapi.testclient import TestClient

from tradingbots.almacen import Almacen
from tradingbots.config import BotConfig, Config
from tradingbots.mercado import BrokerBinance
from tradingbots.modelos import Cartera, Intencion
from tradingbots.motor import Motor
from tradingbots.notificador import Notificador
from tradingbots.panel import crear_app
from tradingbots.simulador import Simulador
from tradingbots.supervisor import LimitesRiesgo

T0 = datetime(2026, 3, 2, 10, 0, 30, tzinfo=timezone.utc)


class Reloj:
    def __init__(self, t): self.t = t
    def __call__(self): return self.t


class BrokerFalso:
    modo = "papel"

    def __init__(self, reloj, precio=100.0):
        self.reloj, self.p, self.sim = reloj, precio, Simulador(0.1, 0)

    def precio(self, par): return self.p

    def velas(self, par, temporalidad, limite=300):
        fin = self.reloj().replace(minute=0, second=0)
        idx = pd.date_range(end=fin - timedelta(hours=1), periods=limite, freq="h", tz="UTC")
        return pd.DataFrame({"open": self.p, "high": self.p, "low": self.p, "close": self.p, "volume": 1.0}, index=idx)

    def ejecutar(self, intencion, cartera, ahora):
        return self.sim.ejecutar(intencion, cartera, self.p, ahora)


class TelegramFalso(Notificador):
    def __init__(self):
        super().__init__()
        self.enviados, self.entrantes = [], []

    def enviar(self, texto): self.enviados.append(texto)

    def leer_comandos(self):
        c, self.entrantes = self.entrantes, []
        return c


def config(**riesgo):
    return Config("t", 0.1, 0, LimitesRiesgo(pares_permitidos=["BTC/USDT"], orden_maxima_usdt=1000, **riesgo), [
        BotConfig("dca_btc", "dca", "BTC/USDT", "1h", 1000, {"monto_usdt": 10, "cada_horas": 24}),
    ])


@pytest.fixture
def entorno(tmp_path):
    reloj = Reloj(T0)
    db = Almacen(tmp_path / "bots.sqlite")
    broker, tg = BrokerFalso(reloj), TelegramFalso()
    return reloj, db, broker, tg, Motor(config(), broker, db, tg, reloj=reloj, hora_reporte=99)


def test_ciclo_compra_guarda_y_avisa(entorno):
    reloj, db, broker, tg, m = entorno
    m.paso()
    ops = db.ejecuciones()
    assert len(ops) == 1 and ops[0]["lado"] == "compra" and ops[0]["monto_usdt"] == 10
    assert any("compró" in t for t in tg.enviados)
    assert db.obtener("en_vivo")["bots"][0]["efectivo"] == pytest.approx(990)
    reloj.t += timedelta(minutes=1)
    m.paso()  # misma vela: no vuelve a comprar
    assert len(db.ejecuciones()) == 1


def test_estado_sobrevive_a_un_reinicio(entorno, tmp_path):
    reloj, db, broker, tg, m = entorno
    m.paso()
    reloj.t += timedelta(hours=2)
    m2 = Motor(config(), broker, db, TelegramFalso(), reloj=reloj, hora_reporte=99)
    assert m2.bots["dca_btc"].cartera.efectivo == pytest.approx(990)
    assert m2.bots["dca_btc"].estrategia.ultima_compra_t is not None
    m2.paso()  # no han pasado 24 h: no compra otra vez tras reiniciar
    assert len(db.ejecuciones()) == 1


def test_comandos_de_telegram_y_panel(entorno):
    reloj, db, broker, tg, m = entorno
    tg.entrantes = ["/pausar"]
    m.paso()
    assert m.sup.estado == "pausado"
    assert db.ejecuciones() == []  # la compra fue rechazada
    assert any(e["tipo"] == "rechazo" for e in db.eventos())
    db.agregar_comando("reanudar")
    reloj.t += timedelta(hours=25)
    m.paso()
    assert m.sup.estado == "activo" and len(db.ejecuciones()) == 1
    tg.entrantes = ["/estado", "/pausar dca_btc", "/inventado"]
    m.paso()
    assert "dca_btc" in m.sup.bots_pausados
    assert any("<b>Estado</b>" in t for t in tg.enviados)
    assert any("No conozco" in t for t in tg.enviados)


def test_supervisor_detiene_por_caida_y_avisa(entorno):
    reloj, db, broker, tg, m = entorno
    m.paso()
    m.sup.limites.caida_maxima_pct = 0.5
    broker.p = 10.0  # la posición de 10 USDT pierde 90 %: ~0.9 % del total
    reloj.t += timedelta(minutes=1)
    m.paso()
    assert m.sup.estado == "detenido"
    assert any("Supervisor · detencion" in t for t in tg.enviados)


def test_error_del_broker_no_detiene_el_motor(entorno):
    reloj, db, broker, tg, m = entorno

    def falla(*a): raise RuntimeError("Binance caído")
    broker.ejecutar = falla
    m.paso()
    assert any(e["tipo"] == "error" for e in db.eventos())
    assert any("Binance caído" in t for t in tg.enviados)


def test_panel_api(entorno):
    reloj, db, broker, tg, m = entorno
    m.paso()
    cli = TestClient(crear_app(db))
    assert "Panel de Bots" in cli.get("/").text
    d = cli.get("/api/estado").json()
    assert d["en_vivo"]["modo"] == "papel" and len(d["ejecuciones"]) == 1
    assert cli.post("/api/comando", json={"accion": "detener_todo"}).status_code == 200
    assert cli.post("/api/comando", json={"accion": "borrar_todo"}).status_code == 400
    m.paso()
    assert m.sup.estado == "detenido"


def test_notificador_ignora_chats_desconocidos():
    class Resp:
        def __init__(self, d): self.d = d
        def raise_for_status(self): pass
        def json(self): return self.d

    class Sesion:
        def get(self, url, params, timeout):
            return Resp({"result": [
                {"update_id": 1, "message": {"chat": {"id": 999}, "text": "/detener_todo"}},
                {"update_id": 2, "message": {"chat": {"id": 42}, "text": "/estado"}},
            ]})

    n = Notificador("token", "42", sesion=Sesion())
    n._offset = None
    assert n.leer_comandos() == ["/estado"]


def test_tendencia_vigila_stop_con_precio_en_vivo():
    from tradingbots.estrategias import Tendencia
    e = Tendencia("t", "ETH/USDT")
    c = Cartera("t", "ETH/USDT", 1000)
    e.en_ejecucion(Simulador(0, 0).ejecutar(Intencion("t", "ETH/USDT", "compra", monto_usdt=900), c, 100, T0))
    assert e.revisar_salidas(99, c) == []
    assert e.revisar_salidas(104, c) == []  # sube el máximo, activa trailing
    [v] = e.revisar_salidas(101.5, c)
    assert "Trailing" in v.motivo
    restaurada = Tendencia("t", "ETH/USDT")
    restaurada.cargar_estado(e.exportar_estado())
    assert restaurada.precio_entrada == pytest.approx(100) and restaurada.maximo == pytest.approx(104)


class ExchangeFalso:
    """Imita las respuestas de ccxt para Binance."""

    def __init__(self): self.ordenes = []
    def load_markets(self): pass
    def fetch_ticker(self, par): return {"last": 50_000.0}
    def fetch_balance(self): return {"USDT": {"free": 100.0}, "BTC": {"free": 0.000199}}
    def cost_to_precision(self, par, x): return f"{x:.2f}"
    def amount_to_precision(self, par, x): return f"{int(x * 1e5) / 1e5:.5f}"

    def create_market_buy_order_with_cost(self, par, costo):
        self.ordenes.append(("compra", costo))
        return {"id": 1, "filled": 0.0002, "cost": 10.0, "average": 50_000.0,
                "fees": [{"cost": 0.0000002, "currency": "BTC"}]}

    def create_market_sell_order(self, par, cantidad):
        self.ordenes.append(("venta", cantidad))
        return {"id": 2, "filled": cantidad, "cost": cantidad * 55_000, "average": 55_000.0,
                "fees": [{"cost": cantidad * 55_000 * 0.001, "currency": "USDT"}]}


def test_broker_binance_contabiliza_comisiones():
    ex = ExchangeFalso()
    b = BrokerBinance("testnet", "", "", exchange=ex)
    c = Cartera("dca", "BTC/USDT", 20)
    e = b.ejecutar(Intencion("dca", "BTC/USDT", "compra", monto_usdt=10), c, T0)
    assert c.efectivo == pytest.approx(10) and c.cantidad == pytest.approx(0.0001998)
    assert e.comision_usdt == pytest.approx(0.01) and e.id_orden == "1"
    v = b.ejecutar(Intencion("dca", "BTC/USDT", "venta", cantidad=c.cantidad), c, T0)
    assert ex.ordenes[-1] == ("venta", 0.00019)  # redondeado a la precisión de Binance y al saldo libre
    assert v.ganancia_usdt == pytest.approx(0.00019 * 55_000 * 0.999 - 10 * 0.00019 / 0.0001998)


def test_broker_binance_rechaza_si_no_hay_saldo():
    b = BrokerBinance("testnet", "", "", exchange=ExchangeFalso())
    with pytest.raises(RuntimeError, match="Saldo insuficiente"):
        b.ejecutar(Intencion("dca", "BTC/USDT", "compra", monto_usdt=500), Cartera("dca", "BTC/USDT", 1000), T0)
