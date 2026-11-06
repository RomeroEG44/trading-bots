"""Estructuras de datos básicas que comparten todos los módulos."""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from typing import Literal

Lado = Literal["compra", "venta"]


@dataclass
class Intencion:
    """Lo que un bot QUIERE hacer. El supervisor decide si se permite."""

    bot: str
    par: str
    lado: Lado
    monto_usdt: float | None = None  # para compras: cuántos USDT gastar
    cantidad: float | None = None  # para ventas: cuánta moneda (BTC, ETH...) vender
    precio: float | None = None  # precio al que se quiere ejecutar (stops); None = precio de mercado
    motivo: str = ""


@dataclass
class Ejecucion:
    """Una operación que sí se realizó."""

    tiempo: datetime
    bot: str
    par: str
    lado: Lado
    precio: float
    cantidad: float
    monto_usdt: float  # valor bruto de la operación
    comision_usdt: float
    motivo: str
    ganancia_usdt: float | None = None  # solo en ventas: ganancia/pérdida realizada


@dataclass
class Cartera:
    """El dinero asignado a un bot. Ningún bot puede tocar el dinero de otro."""

    bot: str
    par: str
    presupuesto: float
    efectivo: float = field(init=False)  # USDT disponibles
    cantidad: float = 0.0  # moneda que tiene (BTC, ETH...)
    costo: float = 0.0  # USDT gastados en la cantidad que todavía tiene (incluye comisiones)

    def __post_init__(self) -> None:
        self.efectivo = self.presupuesto

    @property
    def precio_promedio(self) -> float:
        return self.costo / self.cantidad if self.cantidad > 0 else 0.0

    def valor(self, precio: float) -> float:
        return self.efectivo + self.cantidad * precio
