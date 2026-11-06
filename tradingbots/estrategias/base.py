"""Molde común para todas las estrategias."""
from __future__ import annotations

from abc import ABC, abstractmethod
from datetime import datetime

import pandas as pd

from ..modelos import Cartera, Ejecucion, Intencion


class Estrategia(ABC):
    PARAMETROS: dict = {}  # valores por defecto; config.yaml puede cambiarlos
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

    def en_ejecucion(self, ejecucion: Ejecucion) -> None:
        """Avisa a la estrategia que una orden suya sí se ejecutó."""

    def _intencion(self, lado, **kw) -> Intencion:
        return Intencion(bot=self.nombre, par=self.par, lado=lado, **kw)
