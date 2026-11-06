"""Tendencia: cruce de medias móviles (EMA rápida/lenta) confirmado con RSI."""
from __future__ import annotations

from ..indicadores import ema, rsi
from .base import SALIDAS, EstrategiaDePosicion, f2, rd


class Tendencia(EstrategiaDePosicion):
    DESCRIPCION = "Tendencia (EMA + RSI)"
    PARAMETROS = {"ema_rapida": 9, "ema_lenta": 21, "rsi_periodo": 14, "rsi_min": 50.0, "rsi_max": 70.0, **SALIDAS}
    velas_minimas = 60

    def preparar(self, velas):
        v = velas.copy()
        v["ema_rapida"] = ema(v["close"], self.p["ema_rapida"])
        v["ema_lenta"] = ema(v["close"], self.p["ema_lenta"])
        v["rsi"] = rsi(v["close"], self.p["rsi_periodo"])
        return v

    def senal_entrada(self, velas):
        u, ant, p = velas.iloc[-1], velas.iloc[-2], self.p
        cruce = ant["ema_rapida"] <= ant["ema_lenta"] and u["ema_rapida"] > u["ema_lenta"]
        if cruce and p["rsi_min"] <= u["rsi"] <= p["rsi_max"]:
            return f"Cruce alcista EMA{p['ema_rapida']}/EMA{p['ema_lenta']} con RSI {u['rsi']:.0f}"
        return None

    def senal_salida(self, velas):
        u, ant = velas.iloc[-1], velas.iloc[-2]
        if ant["ema_rapida"] >= ant["ema_lenta"] and u["ema_rapida"] < u["ema_lenta"]:
            return "Cruce bajista: EMA rápida cruzó hacia abajo la lenta"
        return None

    def analisis_sin_posicion(self, velas):
        u, p = velas.iloc[-1], self.p
        alcista = u["ema_rapida"] > u["ema_lenta"]
        texto = (f"EMA{p['ema_rapida']} {f2(u['ema_rapida'])} {'sobre' if alcista else 'bajo'} "
                 f"EMA{p['ema_lenta']} {f2(u['ema_lenta'])} ({'alcista' if alcista else 'bajista'}) · RSI {u['rsi']:.0f}. "
                 f"Espera: cruce alcista con RSI entre {p['rsi_min']:g} y {p['rsi_max']:g}.")
        return texto, {"ema_rapida": rd(u["ema_rapida"]), "ema_lenta": rd(u["ema_lenta"]),
                       "rsi": round(u["rsi"], 1)}
