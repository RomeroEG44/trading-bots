"""Moldes comunes para todas las estrategias."""
from __future__ import annotations

from abc import ABC, abstractmethod
from datetime import datetime

import pandas as pd

from ..modelos import Cartera, Ejecucion, Intencion


def _a_json(v):
    return {"__fecha__": v.isoformat()} if isinstance(v, datetime) else v


def _de_json(v):
    return datetime.fromisoformat(v["__fecha__"]) if isinstance(v, dict) and "__fecha__" in v else v


def f2(x: float) -> str:
    """Precio legible: 2 decimales para BTC, más para monedas baratas (PEPE, BONK...)."""
    a = abs(x)
    return f"{x:,.2f}" if a >= 100 else f"{x:,.4f}" if a >= 1 else f"{x:.6g}"


def rd(x: float) -> float:
    """Redondeo que no convierte en 0 los precios muy pequeños."""
    return float(f"{x:.6g}")


class Estrategia(ABC):
    PARAMETROS: dict = {}  # valores por defecto; el .yaml puede cambiarlos
    CAMPOS_ESTADO: tuple = ()  # lo que la estrategia recuerda si se reinicia el programa
    DESCRIPCION = ""
    velas_minimas = 50  # velas de historia necesarias antes de decidir

    def __init__(self, nombre: str, par: str, parametros: dict | None = None):
        desconocidos = set(parametros or {}) - set(self.PARAMETROS)
        if desconocidos:
            raise ValueError(f"{nombre}: parámetros desconocidos {sorted(desconocidos)}")
        self.nombre = nombre
        self.par = par
        self.p = {**self.PARAMETROS, **(parametros or {})}

    def preparar(self, velas: pd.DataFrame) -> pd.DataFrame:
        """Agrega columnas de indicadores (solo usan datos del pasado)."""
        return velas

    @abstractmethod
    def en_vela(self, velas: pd.DataFrame, cartera: Cartera, ahora: datetime) -> list[Intencion]:
        """Se llama al cerrar cada vela. velas.iloc[-1] es la última vela cerrada."""

    def en_precio(self, precio: float, cartera: Cartera) -> list[Intencion]:
        """Se llama cada pocos segundos con el precio actual (stops, rejilla...)."""
        return []

    def en_ejecucion(self, ejecucion: Ejecucion) -> None:
        """Aviso de que una orden de este bot (o del Master por él) se ejecutó."""

    def analisis(self, velas: pd.DataFrame | None, cartera: Cartera, precio: float, ahora: datetime) -> dict:
        """Qué está viendo el bot ahora mismo. Se muestra en el panel."""
        return {"senal": "espera", "texto": "", "indicadores": {}}

    def exportar_estado(self) -> dict:
        return {c: _a_json(getattr(self, c)) for c in self.CAMPOS_ESTADO}

    def cargar_estado(self, datos: dict) -> None:
        for c in self.CAMPOS_ESTADO:
            if c in datos:
                setattr(self, c, _de_json(datos[c]))

    def _intencion(self, lado, **kw) -> Intencion:
        return Intencion(bot=self.nombre, par=self.par, lado=lado, **kw)


SALIDAS = {
    "stop_loss_pct": 3.0,
    "take_profit_pct": 6.0,  # 0 = sin take-profit fijo
    "trailing_activacion_pct": 3.0,  # el trailing se activa tras ganar esto...
    "trailing_pct": 2.0,  # ...y vende si el precio retrocede esto desde su máximo (0 = sin trailing)
    "fraccion_capital": 0.9,  # qué parte del efectivo usar en cada entrada
}


class EstrategiaDePosicion(Estrategia):
    """Una posición a la vez, con stop-loss, take-profit y trailing stop.

    Las subclases solo definen cuándo entrar (senal_entrada) y, opcionalmente, cuándo salir (senal_salida).
    Si en una misma vela se tocan stop y take-profit, se asume lo peor (stop).
    """

    CAMPOS_ESTADO = ("precio_entrada", "maximo")

    def __init__(self, nombre, par, parametros=None):
        super().__init__(nombre, par, parametros)
        self.precio_entrada: float | None = None
        self.maximo: float | None = None

    def senal_entrada(self, velas: pd.DataFrame) -> str | None:
        return None

    def senal_salida(self, velas: pd.DataFrame) -> str | None:
        return None

    def analisis_sin_posicion(self, velas: pd.DataFrame) -> tuple[str, dict]:
        return "", {}

    # ---------- lógica común ----------
    def en_posicion(self, cartera: Cartera) -> bool:
        return cartera.cantidad > 0 and self.precio_entrada is not None

    def _niveles(self) -> dict:
        p, e = self.p, self.precio_entrada
        n = {"stop": e * (1 - p["stop_loss_pct"] / 100)}
        if p["take_profit_pct"]:
            n["objetivo"] = e * (1 + p["take_profit_pct"] / 100)
        if p["trailing_pct"]:
            n["trailing_activa"] = e * (1 + p["trailing_activacion_pct"] / 100)
            if self.maximo >= n["trailing_activa"]:
                n["trailing"] = self.maximo * (1 - p["trailing_pct"] / 100)
        return n

    def _salida_por_rango(self, abre, alto, bajo, cartera, precio_fijo=True) -> list[Intencion]:
        n, e, p = self._niveles(), self.precio_entrada, self.p
        vender = lambda precio, motivo: [self._intencion(
            "venta", cantidad=cartera.cantidad, precio=precio if precio_fijo else None, motivo=motivo)]
        if bajo <= n["stop"]:
            return vender(min(n["stop"], abre), f"Stop-loss: bajó {p['stop_loss_pct']}% desde la entrada {f2(e)}")
        if "objetivo" in n and alto >= n["objetivo"]:
            return vender(max(n["objetivo"], abre), f"Take-profit: subió {p['take_profit_pct']}% desde la entrada {f2(e)}")
        if "trailing" in n and bajo <= n["trailing"]:
            return vender(min(n["trailing"], abre),
                          f"Trailing stop: retrocedió {p['trailing_pct']}% desde el máximo {f2(self.maximo)}")
        return []

    def en_vela(self, velas, cartera, ahora):
        u = velas.iloc[-1]
        if self.en_posicion(cartera):
            salida = self._salida_por_rango(float(u["open"]), float(u["high"]), float(u["low"]), cartera)
            if salida:
                return salida
            self.maximo = max(self.maximo, float(u["high"]))
            motivo = self.senal_salida(velas)
            return [self._intencion("venta", cantidad=cartera.cantidad, motivo=motivo)] if motivo else []
        motivo = self.senal_entrada(velas)
        if motivo:
            return [self._intencion("compra", monto_usdt=cartera.efectivo * self.p["fraccion_capital"], motivo=motivo)]
        return []

    def en_precio(self, precio, cartera):
        if not self.en_posicion(cartera):
            return []
        salida = self._salida_por_rango(precio, precio, precio, cartera, precio_fijo=False)
        if salida:
            return salida
        self.maximo = max(self.maximo, precio)
        return []

    def en_ejecucion(self, e):
        if e.lado == "compra":
            self.precio_entrada, self.maximo = e.precio, e.precio
        else:
            self.precio_entrada, self.maximo = None, None

    def analisis(self, velas, cartera, precio, ahora):
        if self.en_posicion(cartera):
            n = self._niveles()
            pl = (precio / self.precio_entrada - 1) * 100
            partes = [f"En posición desde {f2(self.precio_entrada)} ({pl:+.2f}%)", f"stop {f2(n['stop'])}"]
            if "objetivo" in n:
                partes.append(f"objetivo {f2(n['objetivo'])}")
            if "trailing" in n:
                partes.append(f"trailing {f2(n['trailing'])}")
            elif "trailing_activa" in n:
                partes.append(f"trailing se activa en {f2(n['trailing_activa'])}")
            return {"senal": "en_posicion", "texto": " · ".join(partes),
                    "indicadores": {k: rd(v) for k, v in n.items()}}
        if velas is None or len(velas) < 2:
            return {"senal": "espera", "texto": "Esperando datos…", "indicadores": {}}
        texto, ind = self.analisis_sin_posicion(velas)
        senal = "compra" if self.senal_entrada(velas) else "espera"
        return {"senal": senal, "texto": texto, "indicadores": ind}
