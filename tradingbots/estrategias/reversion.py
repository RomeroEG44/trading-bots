"""Reversión a la media: compra cuando el precio cae por debajo de la banda de Bollinger inferior
(sobreventa) y vende cuando vuelve al promedio."""
from __future__ import annotations

from ..indicadores import rsi
from .base import SALIDAS, EstrategiaDePosicion, f2


class Reversion(EstrategiaDePosicion):
    DESCRIPCION = "Reversión a la media (Bollinger + RSI)"
    PARAMETROS = {"periodo": 20, "desviaciones": 2.0, "rsi_periodo": 14, "rsi_max_entrada": 35.0,
                  **SALIDAS, "take_profit_pct": 0.0, "trailing_pct": 0.0}
    velas_minimas = 40

    def preparar(self, velas):
        v = velas.copy()
        media = v["close"].rolling(self.p["periodo"]).mean()
        desv = v["close"].rolling(self.p["periodo"]).std()
        v["media"] = media
        v["banda_inferior"] = media - self.p["desviaciones"] * desv
        v["banda_superior"] = media + self.p["desviaciones"] * desv
        v["rsi"] = rsi(v["close"], self.p["rsi_periodo"])
        return v

    def senal_entrada(self, velas):
        u = velas.iloc[-1]
        if u["close"] < u["banda_inferior"] and u["rsi"] < self.p["rsi_max_entrada"]:
            return f"Sobreventa: precio {f2(u['close'])} bajo la banda inferior {f2(u['banda_inferior'])}, RSI {u['rsi']:.0f}"
        return None

    def senal_salida(self, velas):
        u = velas.iloc[-1]
        if u["close"] >= u["media"]:
            return f"Volvió al promedio ({f2(u['media'])})"
        return None

    def analisis_sin_posicion(self, velas):
        u, p = velas.iloc[-1], self.p
        dist = (u["close"] / u["banda_inferior"] - 1) * 100
        texto = (f"Precio {f2(u['close'])} · banda inferior {f2(u['banda_inferior'])} ({dist:+.2f}%) · "
                 f"promedio {f2(u['media'])} · RSI {u['rsi']:.0f}. "
                 f"Espera: cierre bajo la banda inferior con RSI < {p['rsi_max_entrada']:g}.")
        return texto, {"banda_inferior": round(u["banda_inferior"], 2), "media": round(u["media"], 2),
                       "banda_superior": round(u["banda_superior"], 2), "rsi": round(u["rsi"], 1)}
