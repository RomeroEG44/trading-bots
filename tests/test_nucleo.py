from datetime import datetime, timedelta, timezone

import pandas as pd
import pytest

from tradingbots.estrategias import DCA, Tendencia
from tradingbots.indicadores import rsi
from tradingbots.modelos import Cartera, Intencion
from tradingbots.simulador import Simulador
from tradingbots.supervisor import LimitesRiesgo, Supervisor

T0 = datetime(2026, 1, 1, tzinfo=timezone.utc)


def sup(**kw):
    return Supervisor(LimitesRiesgo(pares_permitidos=["BTC/USDT"], **kw))


def compra(monto, par="BTC/USDT"):
    return Intencion("b", par, "compra", monto_usdt=monto)


# ---------- simulador ----------
def test_simulador_compra_y_venta_con_comisiones():
    c = Cartera("b", "BTC/USDT", 100)
    sim = Simulador(comision_pct=0.1, deslizamiento_pct=0)
    sim.ejecutar(compra(100), c, 50_000, T0)
    assert c.efectivo == 0
    assert c.cantidad == pytest.approx(99.9 / 50_000)
    v = sim.ejecutar(Intencion("b", "BTC/USDT", "venta", cantidad=c.cantidad), c, 55_000, T0)
    assert c.cantidad == 0
    assert c.efectivo == pytest.approx(99.9 * 1.1 * 0.999)
    assert v.ganancia_usdt == pytest.approx(c.efectivo - 100)


# ---------- supervisor ----------
def test_rechaza_par_no_permitido():
    d = sup().revisar(compra(10, "DOGE/USDT"), Cartera("b", "DOGE/USDT", 100), 1, T0)
    assert not d.aprobada


def test_ajusta_compra_al_maximo_y_al_efectivo():
    s = sup(orden_maxima_usdt=20)
    assert s.revisar(compra(50), Cartera("b", "BTC/USDT", 100), 1, T0).intencion.monto_usdt == 20
    assert s.revisar(compra(50), Cartera("b", "BTC/USDT", 8), 1, T0).intencion.monto_usdt == 8


def test_presupuesto_agotado():
    d = sup().revisar(compra(10), Cartera("b", "BTC/USDT", 3), 1, T0)
    assert not d.aprobada and "agotado" in d.motivo


def test_limite_de_compras_por_hora():
    s, c = sup(max_compras_por_hora=2), Cartera("b", "BTC/USDT", 1000)
    assert s.revisar(compra(10), c, 1, T0).aprobada
    assert s.revisar(compra(10), c, 1, T0 + timedelta(minutes=10)).aprobada
    assert not s.revisar(compra(10), c, 1, T0 + timedelta(minutes=20)).aprobada
    assert s.revisar(compra(10), c, 1, T0 + timedelta(minutes=61)).aprobada


def test_pausa_por_perdida_diaria_y_reanuda_al_dia_siguiente():
    s, c = sup(perdida_diaria_max_pct=3), Cartera("b", "BTC/USDT", 1000)
    s.actualizar_valor(T0, 1000)
    s.actualizar_valor(T0 + timedelta(hours=5), 965)
    assert s.estado == "pausado"
    assert not s.revisar(compra(10), c, 1, T0 + timedelta(hours=6)).aprobada
    c.cantidad = 1
    assert s.revisar(Intencion("b", "BTC/USDT", "venta", cantidad=1), c, 100, T0 + timedelta(hours=6)).aprobada
    assert s.revisar(compra(10), c, 1, T0 + timedelta(days=1, hours=1)).aprobada
    assert s.estado == "activo"


def test_detencion_por_caida_maxima_requiere_reanudar_manual():
    s = sup(caida_maxima_pct=10, perdida_diaria_max_pct=50)
    s.actualizar_valor(T0, 1000)
    s.actualizar_valor(T0 + timedelta(days=3), 1200)
    s.actualizar_valor(T0 + timedelta(days=6), 1070)
    assert s.estado == "detenido"
    s.actualizar_valor(T0 + timedelta(days=20), 1300)
    assert s.estado == "detenido"
    s.reanudar(T0 + timedelta(days=20))
    assert s.estado == "activo" and s.valor_maximo == 1300


# ---------- indicadores ----------
def test_rsi_extremos():
    assert rsi(pd.Series(range(1, 50), dtype=float)).iloc[-1] == pytest.approx(100)
    assert rsi(pd.Series(range(50, 1, -1), dtype=float)).iloc[-1] == pytest.approx(0)


# ---------- estrategias ----------
def velas(cierres, altos=None, bajos=None):
    idx = pd.date_range(T0, periods=len(cierres), freq="h")
    c = pd.Series(cierres, index=idx, dtype=float)
    return pd.DataFrame({"open": c.shift(1).fillna(c.iloc[0]), "high": altos or c, "low": bajos or c, "close": c,
                         "volume": 1.0}, index=idx)


def test_dca_compra_programada_y_doble_en_caida():
    e = DCA("dca", "BTC/USDT", {"monto_usdt": 10, "cada_horas": 24})
    c = Cartera("dca", "BTC/USDT", 1000)
    sim = Simulador(0, 0)
    [i] = e.en_vela(velas([100]), c, T0)
    e.en_ejecucion(sim.ejecutar(i, c, 100, T0))
    assert e.en_vela(velas([100]), c, T0 + timedelta(hours=5)) == []
    [i] = e.en_vela(velas([94]), c, T0 + timedelta(hours=24))
    assert i.monto_usdt == 20


def test_dca_toma_ganancias_parcial_una_sola_vez_por_nivel():
    e = DCA("dca", "BTC/USDT", {"cada_horas": 10_000})
    c = Cartera("dca", "BTC/USDT", 1000)
    sim = Simulador(0, 0)
    [i] = e.en_vela(velas([100]), c, T0)
    e.en_ejecucion(sim.ejecutar(i, c, 100, T0))
    [v] = e.en_vela(velas([116]), c, T0 + timedelta(hours=1))
    assert v.lado == "venta" and v.cantidad == pytest.approx(c.cantidad * 0.25)
    e.en_ejecucion(sim.ejecutar(v, c, 116, T0))
    assert e.en_vela(velas([117]), c, T0 + timedelta(hours=2)) == []


def _tendencia_en_posicion(entrada=100.0):
    e = Tendencia("t", "ETH/USDT")
    c = Cartera("t", "ETH/USDT", 1000)
    sim = Simulador(0, 0)
    e.en_ejecucion(sim.ejecutar(Intencion("t", "ETH/USDT", "compra", monto_usdt=900), c, entrada, T0))
    return e, c


def _con_indicadores(df):
    df["ema_rapida"], df["ema_lenta"], df["rsi"] = 2.0, 1.0, 60.0  # sin cruce bajista
    return df


def test_tendencia_stop_loss_tiene_prioridad():
    e, c = _tendencia_en_posicion()
    df = _con_indicadores(velas([100, 100], altos=[100, 107], bajos=[100, 96]))
    [v] = e.en_vela(df, c, T0)
    assert v.lado == "venta" and v.precio == pytest.approx(97) and "Stop-loss" in v.motivo


def test_tendencia_take_profit():
    e, c = _tendencia_en_posicion()
    df = _con_indicadores(velas([100, 106.5], altos=[100, 107], bajos=[100, 99]))
    [v] = e.en_vela(df, c, T0)
    assert v.precio == pytest.approx(106) and "Take-profit" in v.motivo


def test_tendencia_compra_en_cruce_alcista_con_rsi():
    e = Tendencia("t", "ETH/USDT")
    df = velas([100, 101])
    df["ema_lenta"] = 100.0
    df["ema_rapida"] = [99.0, 101.0]
    df["rsi"] = 60.0
    [i] = e.en_vela(df, Cartera("t", "ETH/USDT", 1000), T0)
    assert i.lado == "compra" and i.monto_usdt == pytest.approx(900)
    df["rsi"] = 80.0  # sobrecompra: no entra
    assert e.en_vela(df, Cartera("t", "ETH/USDT", 1000), T0) == []


# ---------- datos ----------
def test_cache_de_velas_rellena_huecos(tmp_path, monkeypatch):
    from tradingbots import datos

    pedidos = []

    class Resp:
        def __init__(self, lote): self.lote = lote
        def raise_for_status(self): pass
        def json(self): return self.lote

    class Sesion:
        def get(self, url, params, timeout):
            pedidos.append(params["startTime"])
            desde, hasta = params["startTime"], params["endTime"]
            paso = 86_400_000
            lote = [[t, 1, 1, 1, 1, 1] for t in range(desde, hasta + 1, paso)][:1000]
            return Resp(lote)

    monkeypatch.setattr(datos, "RAIZ", tmp_path)
    monkeypatch.setattr(datos.requests, "Session", Sesion)
    a = datetime(2020, 1, 1, tzinfo=timezone.utc)
    datos.descargar_velas("ETH/USDT", "1d", a + timedelta(days=100), a + timedelta(days=110))
    datos.descargar_velas("ETH/USDT", "1d", a, a + timedelta(days=10))
    medio = datos.descargar_velas("ETH/USDT", "1d", a + timedelta(days=40), a + timedelta(days=50))
    assert len(medio) == 10
    assert len(pedidos) == 3
    assert len(datos.descargar_velas("ETH/USDT", "1d", a + timedelta(days=40), a + timedelta(days=50))) == 10
    assert len(pedidos) == 3  # ya estaba en caché
