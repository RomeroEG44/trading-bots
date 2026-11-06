"""Molde común para todas las estrategias."""
from __future__ import annotations

from abc import ABC, abstractmethod
from datetime import datetime

import pandas as pd

from ..modelos import Cartera, Ejecucion, Intencion


def _a_json(v):
    return {"__fecha__": v.isoformat()} if isinstance(v, datetime) else v


def _de_json(v):
    return datetime.fromisoformat(v["__fecha__"]) if isinstance(v, dict) and "__fecha__" in v else v


class Estrategia(ABC):
    PARAMETROS: dict = {}  # valores por defecto; config.yaml puede cambiarlos
    CAMPOS_ESTADO: tuple = ()  # lo que la estrategia debe recordar si se reinicia el programa
    velas_minimas = 50  # velas de historia necesarias antes de empezar a decidir

    def __init__(self, nombre: str, par: str, parametros: dict | None = None):
        desconocidos = set(parametros or {}) - set(self.PARAMETROS)
        if desconocidos:
            raise ValueError(f"{nombre}: parámetros desconocidos {sorted(desconocidos)}")
        self.nombre = nombre
        self.par = par
        self.p = {**self.PARAMETROS, **(parametros or {})}

    def preparar(self, velas: pd.DataFrame) -> pd.DataFrame:
        """Agrega columnas de indicadores. Se llama una vez con todas las velas."""
        return velas

    @abstractmethod
    def en_vela(self, velas: pd.DataFrame, cartera: Cartera, ahora: datetime) -> list[Intencion]:
        """Se llama al cerrar cada vela. velas.iloc[-1] es la última vela cerrada."""

    def revisar_salidas(self, precio: float, cartera: Cartera) -> list[Intencion]:
        """En vivo: se llama cada pocos segundos con el precio actual (stops, take-profit)."""
        return []

    def en_ejecucion(self, ejecucion: Ejecucion) -> None:
        """Avisa a la estrategia que una orden suya sí se ejecutó."""

    def exportar_estado(self) -> dict:
        return {c: _a_json(getattr(self, c)) for c in self.CAMPOS_ESTADO}

    def cargar_estado(self, datos: dict) -> None:
        for c in self.CAMPOS_ESTADO:
            if c in datos:
                setattr(self, c, _de_json(datos[c]))

    def _intencion(self, lado, **kw) -> Intencion:
        return Intencion(bot=self.nombre, par=self.par, lado=lado, **kw)
