from datetime import datetime, timedelta, timezone

import pandas as pd
import pytest

from tradingbots.estrategias import Rejilla, Reversion, Ruptura
from tradingbots.master import Master, ReglasMaster
from tradingbots.modelos import Cartera, Ejecucion, Intencion
from tradingbots.simulador import Simulador

T0 = datetime(2026, 1, 1, tzinfo=timezone.utc)


def venta(bot, ganancia, t=T0, comision=0.1):
    return Ejecucion(t, bot, "BTC/USDT", "venta", 100, 1, 100, comision, "x", ganancia_usdt=ganancia)


def compra_intencion(bot="b", monto=100):
    return Intencion(bot, "BTC/USDT", "compra", monto_usdt=monto, motivo="señal")


def test_racha_de_perdidas_enfria_al_bot_y_baja_tamano():
    m = Master(ReglasMaster(racha_perdidas=3, enfriamiento_min=15))
    for k in range(3):
        m.en_ejecucion(venta("b", -1, T0 + timedelta(minutes=k)))
    f = m.fichas["b"]
    assert f.estado == "enfriamiento" and f.tamano == pytest.approx(0.75)
    i, motivo = m.ajustar(compra_intencion(), T0 + timedelta(minutes=5))
    assert i is None and "enfriamiento" in motivo
    i, _ = m.ajustar(compra_intencion(), T0 + timedelta(minutes=20))
    assert i is not None and i.monto_usdt == pytest.approx(75)
    assert any("Termina" in x.mensaje for x in m.tomar_feedback())


def test_ventas_nunca_se_bloquean():
    m = Master()
    m.fichas["b"].estado, m.fichas["b"].hasta = "cuarentena", T0 + timedelta(hours=1)
    v = Intencion("b", "BTC/USDT", "venta", cantidad=1)
    assert m.ajustar(v, T0)[0] is v


def test_buen_rendimiento_sube_tamano_y_malo_lo_baja():
    m = Master(ReglasMaster(operaciones_para_evaluar=5))
    for g in [2, 2, -1, 2, 2]:
        m.en_ejecucion(venta("bueno", g, comision=0.01))
    assert m.fichas["bueno"].tamano == pytest.approx(1.15)
    for g in [-2, 1, -2, 1, -2]:
        m.en_ejecucion(venta("malo", g, comision=0.01))
    assert m.fichas["malo"].tamano < 1


def test_comisiones_altas_obligan_a_esperar():
    m = Master(ReglasMaster(operaciones_para_evaluar=5, comisiones_max_pct=50))
    for _ in range(5):
        m.en_ejecucion(venta("b", 0.05, comision=0.2))
    f = m.fichas["b"]
    assert f.espera_min == 5
    m.en_ejecucion(Ejecucion(T0, "b", "BTC/USDT", "compra", 100, 1, 100, 0.1, "x"))
    assert m.ajustar(compra_intencion(), T0 + timedelta(minutes=2))[0] is None
    assert m.ajustar(compra_intencion(), T0 + timedelta(minutes=6))[0] is not None


def test_cuarentena_por_caida_cierra_posicion():
    m = Master(ReglasMaster(caida_cuarentena_pct=8, perdida_max_posicion_pct=99))
    c = Cartera("b", "BTC/USDT", 1000)
    Simulador(0, 0).ejecutar(compra_intencion(monto=1000), c, 100, T0)
    assert m.revisar(T0, "b", c, 100) == []
    [v] = m.revisar(T0 + timedelta(minutes=1), "b", c, 91)
    assert v.lado == "venta" and v.cantidad == c.cantidad
    assert m.fichas["b"].estado == "cuarentena" and m.fichas["b"].tamano == 0.5


def test_movimiento_brusco_bloquea_compras_del_par():
    m = Master(ReglasMaster(movimiento_brusco_pct=1.5, ventana_brusca_min=5, bloqueo_brusco_min=10))
    m.registrar_precio("BTC/USDT", T0, 100)
    m.registrar_precio("BTC/USDT", T0 + timedelta(minutes=2), 98)
    assert "BTC/USDT" in m.bloqueos
    assert m.ajustar(compra_intencion(), T0 + timedelta(minutes=3))[0] is None
    m.registrar_precio("BTC/USDT", T0 + timedelta(minutes=13), 98)
    assert "BTC/USDT" not in m.bloqueos


def test_reglas_por_bot_y_guardado():
    m = Master(ReglasMaster(), {"rejilla": {"perdida_max_posicion_pct": 4}})
    assert m.reglas("rejilla").perdida_max_posicion_pct == 4
    assert m.reglas("otro").perdida_max_posicion_pct == 2.5
    m.en_ejecucion(venta("b", -1))
    m.fichas["b"].estado, m.fichas["b"].hasta = "cuarentena", T0
    m2 = Master()
    m2.cargar(m.exportar())
    assert m2.fichas["b"].estado == "cuarentena" and m2.fichas["b"].hasta == T0 and m2.fichas["b"].ventas == [(-1, 0.1)]
    with pytest.raises(ValueError):
        ReglasMaster.desde({"inventado": 1})


# ---------- estrategias nuevas ----------
def _df(cierres):
    idx = pd.date_range(T0, periods=len(cierres), freq="5min")
    c = pd.Series(cierres, index=idx, dtype=float)
    return pd.DataFrame({"open": c, "high": c, "low": c, "close": c, "volume": 1.0}, index=idx)


def test_reversion_compra_en_sobreventa_y_vende_en_la_media():
    e = Reversion("r", "BTC/USDT", {"stop_loss_pct": 5})
    precios = [100 + (k % 2) * 0.5 for k in range(40)] + [99.5, 99, 98, 96.5]
    v = e.preparar(_df(precios))
    c = Cartera("r", "BTC/USDT", 1000)
    [i] = e.en_vela(v, c, T0)
    assert i.lado == "compra" and "Sobreventa" in i.motivo
    e.en_ejecucion(Simulador(0, 0).ejecutar(i, c, 96.5, T0))
    v = e.preparar(_df(precios + [101]))
    [s] = e.en_vela(v, c, T0)
    assert s.lado == "venta" and "promedio" in s.motivo


def test_ruptura_compra_al_romper_el_techo():
    e = Ruptura("x", "ETH/USDT")
    v = e.preparar(_df([100 + (k % 3) for k in range(35)] + [105]))
    [i] = e.en_vela(v, Cartera("x", "ETH/USDT", 1000), T0)
    assert i.lado == "compra" and "Rompió" in i.motivo


def test_rejilla_compra_en_bajadas_y_vende_cada_lote():
    e = Rejilla("g", "BTC/USDT", {"paso_pct": 1.0, "monto_usdt": 100, "max_lotes": 3})
    c, sim = Cartera("g", "BTC/USDT", 1000), Simulador(0, 0)

    def paso(precio):
        out = e.en_precio(precio, c)
        for i in out:
            e.en_ejecucion(sim.ejecutar(i, c, precio, T0))
        return out

    assert paso(100)[0].lado == "compra"
    assert paso(99.5) == []
    assert paso(99)[0].lado == "compra" and len(e.lotes) == 2
    [v] = paso(100)  # el lote de 99 subió 1 %
    assert v.lado == "venta" and len(e.lotes) == 1 and e.lotes[0]["precio"] == 100
    c.cantidad = 0  # el Master cerró todo por fuera
    assert paso(100)[0].lado == "compra" and len(e.lotes) == 1


def test_bot_que_pierde_siempre_queda_retirado():
    m = Master(ReglasMaster(retirar_min_ventas=20, retirar_factor=0.5, racha_perdidas=99))
    for k in range(20):
        m.en_ejecucion(venta("b", -1 if k % 4 else 0.2, T0 + timedelta(minutes=k)))
    f = m.fichas["b"]
    assert f.estado == "retirado" and f.tamano == 0.25
    assert m.ajustar(compra_intencion(), T0 + timedelta(hours=12))[0] is None
    assert m.ajustar(compra_intencion(), T0 + timedelta(hours=25))[0].monto_usdt == pytest.approx(25)
