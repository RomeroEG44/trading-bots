"""Ballena: sigue a las compras grandes. Entra cuando una vela tiene muchísimo más volumen de lo normal,
cierra al alza y el precio está sobre su media; sale con stop y trailing."""
from __future__ import annotations

from ..indicadores import ema
from .base import SALIDAS, EstrategiaDePosicion, f2, rd


class Volumen(EstrategiaDePosicion):
    DESCRIPCION = "Ballena (picos de volumen comprador)"
    PARAMETROS = {"velas_media": 20, "multiplo_volumen": 3.0, "ema": 20, **SALIDAS, "take_profit_pct": 0.0}
    velas_minimas = 30

    def preparar(self, velas):
        v = velas.copy()
        v["vol_media"] = v["volume"].rolling(self.p["velas_media"]).mean().shift(1)
        v["ema"] = ema(v["close"], self.p["ema"])
        return v

    def senal_entrada(self, velas):
        u = velas.iloc[-1]
        if u["vol_media"] and u["volume"] >= self.p["multiplo_volumen"] * u["vol_media"] \
                and u["close"] > u["open"] and u["close"] > u["ema"]:
            return f"Ballena compradora: volumen x{u['volume'] / u['vol_media']:.1f} de lo normal y vela verde"
        return None

    def senal_salida(self, velas):
        u = velas.iloc[-1]
        if u["close"] < u["ema"]:
            return f"Perdió su media ({f2(u['ema'])})"
        return None

    def analisis_sin_posicion(self, velas):
        u = velas.iloc[-1]
        mult = u["volume"] / u["vol_media"] if u["vol_media"] else 0
        texto = (f"Volumen de la última vela x{mult:.1f} de lo normal · precio {'sobre' if u['close'] > u['ema'] else 'bajo'} "
                 f"su media {f2(u['ema'])}. Espera: volumen x{self.p['multiplo_volumen']:g} con vela verde.")
        return texto, {"volumen_x": rd(mult), "ema": rd(u["ema"])}
