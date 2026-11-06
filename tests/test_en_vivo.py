from datetime import datetime, timedelta, timezone

import pandas as pd
import pytest
from fastapi.testclient import TestClient

from tradingbots.almacen import Almacen
from tradingbots.config import BotConfig, Config
from tradingbots.mercado import BrokerBinance
from tradingbots.modelos import Cartera, Intencion
from tradingbots.motor import Motor
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

    def precios(self, pares): return {p: self.p for p in pares}

    def velas(self, par, temporalidad, limite=300):
        fin = self.reloj().replace(minute=0, second=0)
        idx = pd.date_range(end=fin - timedelta(hours=1), periods=limite, freq="h", tz="UTC")
        return pd.DataFrame({"open": self.p, "high": self.p, "low": self.p, "close": self.p, "volume": 1.0}, index=idx)

    def ejecutar(self, intencion, cartera, ahora):
        return self.sim.ejecutar(intencion, cartera, self.p, ahora)


def config(**riesgo):
    return Config("t", 0.1, 0, LimitesRiesgo(pares_permitidos=["BTC/USDT"], orden_maxima_usdt=1000, **riesgo), [
        BotConfig("dca_btc", "dca", "BTC/USDT", "1h", 1000, {"monto_usdt": 10, "cada_horas": 24}),
    ])


@pytest.fixture
def entorno(tmp_path):
    reloj = Reloj(T0)
    db = Almacen(tmp_path / "bots.sqlite")
    broker = BrokerFalso(reloj)
    return reloj, db, broker, Motor(config(), broker, db, reloj=reloj)


def test_ciclo_compra_y_guarda_foto_para_el_panel(entorno):
    reloj, db, broker, m = entorno
    m.paso()
    ops = db.ejecuciones()
    assert len(ops) == 1 and ops[0]["lado"] == "compra" and ops[0]["monto_usdt"] == 10
    bot = db.obtener("en_vivo")["bots"][0]
    assert bot["efectivo"] == pytest.approx(990)
    assert bot["master"]["estado"] == "activo" and bot["analisis"]["texto"]
    assert len(bot["grafica"]) > 0
    reloj.t += timedelta(minutes=1)
    m.paso()  # misma vela: no vuelve a comprar
    assert len(db.ejecuciones()) == 1


def test_estado_sobrevive_a_un_reinicio(entorno):
    reloj, db, broker, m = entorno
    m.paso()
    m.master.fichas["dca_btc"].tamano = 0.5
    m.paso()
    reloj.t += timedelta(hours=2)
    m2 = Motor(config(), broker, db, reloj=reloj)
    assert m2.bots["dca_btc"].cartera.efectivo == pytest.approx(990)
    assert m2.bots["dca_btc"].estrategia.ultima_compra_t is not None
    assert m2.master.fichas["dca_btc"].tamano == 0.5
    m2.paso()  # no han pasado 24 h: no compra otra vez tras reiniciar
    assert len(db.ejecuciones()) == 1


def test_comandos_del_panel(entorno):
    reloj, db, broker, m = entorno
    db.agregar_comando("pausar")
    m.paso()
    assert m.sup.estado == "pausado"
    assert db.ejecuciones() == []
    assert any(e["tipo"] == "rechazo" for e in db.eventos())
    db.agregar_comando("reanudar")
    reloj.t += timedelta(hours=25)
    m.paso()
    assert m.sup.estado == "activo" and len(db.ejecuciones()) == 1
    db.agregar_comando("pausar", "dca_btc")
    m.paso()
    assert "dca_btc" in m.sup.bots_pausados


def test_master_cierra_posicion_que_pierde_demasiado(entorno):
    reloj, db, broker, m = entorno
    m.paso()  # compra a 100
    broker.p = 96.0  # -4 %: más que el límite del Master (2.5 %)
    reloj.t += timedelta(minutes=1)
    m.paso()
    ops = db.ejecuciones()
    assert ops[0]["lado"] == "venta" and "Master" in ops[0]["motivo"]
    assert any(e["tipo"] == "master_alerta" for e in db.eventos())


def test_supervisor_detiene_y_se_reanuda_solo(entorno):
    reloj, db, broker, m = entorno
    m.sup.limites.reanudar_auto_horas = 1
    m.master.reglas_base.perdida_max_posicion_pct = 99
    m.master.reglas_base.caida_cuarentena_pct = 99
    m.paso()
    m.sup.limites.caida_maxima_pct = 0.5
    broker.p = 10.0
    reloj.t += timedelta(minutes=1)
    m.paso()
    assert m.sup.estado == "detenido"
    reloj.t += timedelta(hours=1, minutes=1)
    m.paso()
    assert m.sup.estado == "activo"
    assert any("automática" in e["mensaje"] for e in db.eventos())


def test_error_del_broker_no_detiene_el_motor(entorno):
    reloj, db, broker, m = entorno

    def falla(*a): raise RuntimeError("Binance caído")
    broker.ejecutar = falla
    m.paso()
    assert any(e["tipo"] == "error" and "Binance caído" in e["mensaje"] for e in db.eventos())


def test_panel_api(entorno):
    reloj, db, broker, m = entorno
    m.paso()
    cli = TestClient(crear_app(db))
    assert "Centro de Control" in cli.get("/").text
    assert cli.get("/static/chart.umd.min.js").status_code == 200
    d = cli.get("/api/estado").json()
    assert d["en_vivo"]["modo"] == "papel" and len(d["ejecuciones"]) == 1
    assert d["metricas"]["dca_btc"]["compras"] == 1 and d["global"]["operaciones"] == 1
    assert cli.post("/api/comando", json={"accion": "detener_todo"}).status_code == 200
    assert cli.post("/api/comando", json={"accion": "borrar_todo"}).status_code == 400
    m.paso()
    assert m.sup.estado == "detenido"


def test_tendencia_vigila_stop_con_precio_en_vivo():
    from tradingbots.estrategias import Tendencia
    e = Tendencia("t", "ETH/USDT")
    c = Cartera("t", "ETH/USDT", 1000)
    e.en_ejecucion(Simulador(0, 0).ejecutar(Intencion("t", "ETH/USDT", "compra", monto_usdt=900), c, 100, T0))
    assert e.en_precio(99, c) == []
    assert e.en_precio(104, c) == []  # sube el máximo, activa trailing
    [v] = e.en_precio(101.5, c)
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
