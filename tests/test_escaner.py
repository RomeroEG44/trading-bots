from datetime import datetime, timedelta, timezone

import pandas as pd
import pytest

from tradingbots.almacen import Almacen
from tradingbots.config import BotConfig, Config
from tradingbots.escaner import Escaner, FiltrosEscaner, calificar
from tradingbots.motor import Motor
from tradingbots.simulador import Simulador
from tradingbots.supervisor import LimitesRiesgo

T0 = datetime(2026, 3, 2, 10, 0, 30, tzinfo=timezone.utc)


def ticker(sym, precio, cambio, vol, alto=None, bajo=None, bid=None, ask=None):
    alto = alto or precio * 1.05
    bajo = bajo or precio * 0.95
    return {"symbol": sym, "lastPrice": str(precio), "highPrice": str(alto), "lowPrice": str(bajo),
            "quoteVolume": str(vol), "priceChangePercent": str(cambio),
            "bidPrice": str(bid or precio * 0.9999), "askPrice": str(ask or precio * 1.0001)}


TICKERS = [
    ticker("PEPEUSDT", 0.00001, 9.0, 300e6, alto=0.0000101, bajo=0.0000090),  # impulso fuerte
    ticker("SOLUSDT", 150, -8.0, 200e6, alto=165, bajo=149),  # caída fuerte
    ticker("USDCUSDT", 1, 0.0, 2e9, alto=1.0001, bajo=0.9999),  # estable: se descarta
    ticker("FLOJOUSDT", 2, 0.5, 1e6),  # poco volumen: no pasa
    ticker("ANCHOUSDT", 3, 1.0, 50e6, bid=3, ask=3.03),  # spread de 1 %: no pasa
    ticker("BTCEUR", 70000, 1, 1e9),  # no es USDT
]


class Sesion:
    def get(self, url, timeout):
        class R:
            def raise_for_status(self): pass
            def json(self): return TICKERS
        return R()


def test_calificar_filtros_y_puntajes():
    f = FiltrosEscaner()
    assert calificar(TICKERS[2], f) is None and calificar(TICKERS[5], f) is None
    pepe, sol = calificar(TICKERS[0], f), calificar(TICKERS[1], f)
    assert pepe.aprobado and sol.aprobado
    assert pepe.puntajes["impulso"] > sol.puntajes["impulso"]
    assert sol.puntajes["caida"] > pepe.puntajes["caida"]
    assert not calificar(TICKERS[3], f).aprobado
    ancho = calificar(TICKERS[4], f)
    assert not ancho.aprobado and not [x for x in ancho.filtros if x[0] == "spread_pct"][0][3]


def test_escaner_ordena_y_respeta_pares_disponibles():
    e = Escaner(FiltrosEscaner(), sesion=Sesion())
    e.escanear(T0)
    assert e.escaneados == 4 and set(e.aprobados) == {"PEPE/USDT", "SOL/USDT"}
    assert e.mejores("impulso", 1)[0].par == "PEPE/USDT"
    assert e.mejores("caida", 1)[0].par == "SOL/USDT"
    e.disponibles = {"SOL/USDT"}
    e.escanear(T0)
    assert e.aprobados == ["SOL/USDT"]
    assert not e.toca(T0 + timedelta(seconds=30)) and e.toca(T0 + timedelta(seconds=61))
    foto = e.foto()
    assert foto["candidatos"][0]["filtros"][0]["nombre"] == "volumen_24h_usdt"


class BrokerMulti:
    """Broker falso con varios pares: SOL da señal de ruptura, PEPE no."""
    modo = "papel"

    def __init__(self):
        self.p = {"BTC/USDT": 70000.0, "PEPE/USDT": 0.00001, "SOL/USDT": 160.0}
        self.sim = Simulador(0.1, 0)

    def mercados(self): return None
    def precios(self, pares): return {p: self.p[p] for p in pares}

    def velas(self, par, temporalidad, limite=300):
        idx = pd.date_range(end=T0.replace(minute=0, second=0) - timedelta(minutes=5), periods=60, freq="5min", tz="UTC")
        base = self.p[par]
        cierres = [base * (1 + 0.001 * (k % 3)) for k in range(59)]
        cierres.append(base * (1.05 if par == "SOL/USDT" else 1.0))  # SOL rompe su máximo
        c = pd.Series(cierres, index=idx)
        return pd.DataFrame({"open": c.shift(1).fillna(c.iloc[0]), "high": c, "low": c, "close": c, "volume": 1.0})

    def ejecutar(self, intencion, cartera, ahora):
        return self.sim.ejecutar(intencion, cartera, self.p[intencion.par], ahora)


def test_cazador_elige_el_mercado_con_senal(tmp_path, monkeypatch):
    import tradingbots.motor as motor_mod

    class EscanerFalso(Escaner):
        def __init__(self, f):
            super().__init__(f, sesion=Sesion())

    monkeypatch.setattr(motor_mod, "Escaner", EscanerFalso)
    cfg = Config("t", 0.1, 0, LimitesRiesgo(pares_permitidos=[], orden_maxima_usdt=1000), [
        BotConfig("impulso", "ruptura", "auto", "5m", 1000, {"fraccion_capital": 0.5}, mercado="impulso", candidatos=3),
    ])
    db = Almacen(tmp_path / "b.sqlite")
    m = Motor(cfg, BrokerMulti(), db, reloj=lambda: T0)
    m.paso()
    ops = db.ejecuciones()
    assert len(ops) == 1 and ops[0]["par"] == "SOL/USDT" and "Rompió" in ops[0]["motivo"]
    bot = db.obtener("en_vivo")["bots"][0]
    assert bot["par"] == "SOL/USDT" and bot["cazador"] is True
    assert {r["par"] for r in bot["revisados"]} == {"PEPE/USDT", "SOL/USDT"}
    assert db.obtener("en_vivo")["escaner"]["escaneados"] == 4
    assert any("elige SOL/USDT" in e["mensaje"] for e in db.eventos())
    m2 = Motor(cfg, BrokerMulti(), db, reloj=lambda: T0)  # tras reiniciar sigue en SOL
    assert m2.bots["impulso"].par == "SOL/USDT" and m2.bots["impulso"].estrategia.par == "SOL/USDT"


def test_venta_permitida_aunque_el_par_ya_no_este_aprobado():
    from tradingbots.modelos import Cartera, Intencion
    from tradingbots.supervisor import Supervisor
    s = Supervisor(LimitesRiesgo(pares_permitidos=[]))
    c = Cartera("b", "SOL/USDT", 100)
    c.cantidad = 1
    assert s.revisar(Intencion("b", "SOL/USDT", "venta", cantidad=1), c, 150, T0).aprobada
    assert not s.revisar(Intencion("b", "SOL/USDT", "compra", monto_usdt=10), c, 150, T0).aprobada


def test_descarta_acciones_tokenizadas_pero_no_cripto_con_b():
    from tradingbots.escaner import es_accion_tokenizada
    assert es_accion_tokenizada("NVDAB") and es_accion_tokenizada("SPYB") and es_accion_tokenizada("MUB")
    assert not es_accion_tokenizada("SHIB") and not es_accion_tokenizada("BNB") and not es_accion_tokenizada("ARB")
    assert calificar(ticker("TSLABUSDT", 300, 1, 1e9), FiltrosEscaner()) is None
    assert calificar(ticker("TSLABUSDT", 300, 1, 1e9), FiltrosEscaner(excluir_acciones=False)) is not None
