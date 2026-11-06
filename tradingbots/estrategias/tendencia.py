"""Bot 2: Tendencia. Cruce de medias móviles (EMA rápida/lenta) confirmado con RSI.

Salidas: stop-loss, take-profit, trailing stop o cruce bajista.
Si en una misma vela se tocan stop y take-profit, se asume lo peor (stop).
"""
from __future__ import annotations

from datetime import datetime

from ..indicadores import ema, rsi
from ..modelos import Cartera, Ejecucion, Intencion
from .base import Estrategia


class Tendencia(Estrategia):
    PARAMETROS = {
        "ema_rapida": 9,
        "ema_lenta": 21,
        "rsi_periodo": 14,
        "rsi_min": 50.0,
        "rsi_max": 70.0,
        "stop_loss_pct": 3.0,
        "take_profit_pct": 6.0,
        "trailing_activacion_pct": 3.0,  # el trailing se activa tras ganar esto...
        "trailing_pct": 2.0,  # ...y vende si el precio retrocede esto desde su máximo
        "fraccion_capital": 0.9,  # qué parte del efectivo usar en cada entrada
    }
    velas_minimas = 60
    CAMPOS_ESTADO = ("precio_entrada", "maximo")

    def __init__(self, nombre, par, parametros=None):
        super().__init__(nombre, par, parametros)
        self.precio_entrada: float | None = None
        self.maximo: float | None = None

    def preparar(self, velas):
        v = velas.copy()
        v["ema_rapida"] = ema(v["close"], self.p["ema_rapida"])
        v["ema_lenta"] = ema(v["close"], self.p["ema_lenta"])
        v["rsi"] = rsi(v["close"], self.p["rsi_periodo"])
        return v

    def en_vela(self, velas, cartera: Cartera, ahora: datetime) -> list[Intencion]:
        p = self.p
        u = velas.iloc[-1]
        ant = velas.iloc[-2]
        abre, alto, bajo, cierre = float(u["open"]), float(u["high"]), float(u["low"]), float(u["close"])

        if cartera.cantidad > 0 and self.precio_entrada:
            e = self.precio_entrada
            vender = lambda precio, motivo: [self._intencion("venta", cantidad=cartera.cantidad, precio=precio, motivo=motivo)]

            stop = e * (1 - p["stop_loss_pct"] / 100)
            if bajo <= stop:
                return vender(min(stop, abre), f"Stop-loss: bajó {p['stop_loss_pct']}% desde la entrada {e:,.2f}")

            tp = e * (1 + p["take_profit_pct"] / 100)
            if alto >= tp:
                return vender(max(tp, abre), f"Take-profit: subió {p['take_profit_pct']}% desde la entrada {e:,.2f}")

            if self.maximo >= e * (1 + p["trailing_activacion_pct"] / 100):
                nivel = self.maximo * (1 - p["trailing_pct"] / 100)
                if bajo <= nivel:
                    return vender(min(nivel, abre), f"Trailing stop: retrocedió {p['trailing_pct']}% desde el máximo {self.maximo:,.2f}")

            self.maximo = max(self.maximo, alto)
            if ant["ema_rapida"] >= ant["ema_lenta"] and u["ema_rapida"] < u["ema_lenta"]:
                return vender(None, "Cruce bajista: EMA rápida cruzó hacia abajo la lenta")
            return []

        cruce_alcista = ant["ema_rapida"] <= ant["ema_lenta"] and u["ema_rapida"] > u["ema_lenta"]
        if cruce_alcista and p["rsi_min"] <= u["rsi"] <= p["rsi_max"]:
            return [self._intencion(
                "compra", monto_usdt=cartera.efectivo * p["fraccion_capital"],
                motivo=f"Cruce alcista EMA{p['ema_rapida']}/EMA{p['ema_lenta']} con RSI {u['rsi']:.0f}",
            )]
        return []

    def revisar_salidas(self, precio: float, cartera: Cartera) -> list[Intencion]:
        """En vivo: vigila stop-loss, take-profit y trailing con el precio actual, sin esperar al cierre de la vela."""
        if not (cartera.cantidad > 0 and self.precio_entrada):
            return []
        p, e = self.p, self.precio_entrada
        vender = lambda motivo: [self._intencion("venta", cantidad=cartera.cantidad, motivo=motivo)]
        if precio <= e * (1 - p["stop_loss_pct"] / 100):
            return vender(f"Stop-loss: bajó {p['stop_loss_pct']}% desde la entrada {e:,.2f}")
        if precio >= e * (1 + p["take_profit_pct"] / 100):
            return vender(f"Take-profit: subió {p['take_profit_pct']}% desde la entrada {e:,.2f}")
        if self.maximo >= e * (1 + p["trailing_activacion_pct"] / 100) and precio <= self.maximo * (1 - p["trailing_pct"] / 100):
            return vender(f"Trailing stop: retrocedió {p['trailing_pct']}% desde el máximo {self.maximo:,.2f}")
        self.maximo = max(self.maximo, precio)
        return []

    def en_ejecucion(self, e: Ejecucion) -> None:
        if e.lado == "compra":
            self.precio_entrada = e.precio
            self.maximo = e.precio
        else:
            self.precio_entrada = None
            self.maximo = None
