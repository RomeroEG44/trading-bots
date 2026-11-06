"""Ruptura (canal de Donchian): compra cuando el precio rompe el máximo de las últimas N velas
y vende si pierde el mínimo de las últimas M velas."""
from __future__ import annotations

from .base import SALIDAS, EstrategiaDePosicion, f2


class Ruptura(EstrategiaDePosicion):
    DESCRIPCION = "Ruptura de máximos (Donchian)"
    PARAMETROS = {"entrada_velas": 20, "salida_velas": 10, **SALIDAS, "take_profit_pct": 0.0}
    velas_minimas = 30

    def preparar(self, velas):
        v = velas.copy()
        v["techo"] = v["high"].rolling(self.p["entrada_velas"]).max().shift(1)
        v["piso"] = v["low"].rolling(self.p["salida_velas"]).min().shift(1)
        return v

    def senal_entrada(self, velas):
        u = velas.iloc[-1]
        if u["close"] > u["techo"]:
            return f"Rompió el máximo de {self.p['entrada_velas']} velas ({f2(u['techo'])})"
        return None

    def senal_salida(self, velas):
        u = velas.iloc[-1]
        if u["close"] < u["piso"]:
            return f"Perdió el mínimo de {self.p['salida_velas']} velas ({f2(u['piso'])})"
        return None

    def analisis_sin_posicion(self, velas):
        u = velas.iloc[-1]
        falta = (u["techo"] / u["close"] - 1) * 100
        texto = (f"Precio {f2(u['close'])} · techo de {self.p['entrada_velas']} velas {f2(u['techo'])} "
                 f"(falta {falta:+.2f}%). Espera: cierre por encima del techo.")
        return texto, {"techo": round(u["techo"], 2), "piso": round(u["piso"], 2)}
