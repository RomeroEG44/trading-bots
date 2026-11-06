"""Ejecuta órdenes de forma simulada (backtest y modo 'papel'), cobrando comisión y deslizamiento."""
from __future__ import annotations

from datetime import datetime

from .modelos import Cartera, Ejecucion, Intencion


class Simulador:
    def __init__(self, comision_pct: float = 0.1, deslizamiento_pct: float = 0.05):
        self.comision = comision_pct / 100
        self.deslizamiento = deslizamiento_pct / 100

    def ejecutar(self, intencion: Intencion, cartera: Cartera, precio_mercado: float, tiempo: datetime) -> Ejecucion:
        precio_base = intencion.precio if intencion.precio is not None else precio_mercado

        if intencion.lado == "compra":
            precio = precio_base * (1 + self.deslizamiento)  # al comprar, el precio real sale un poco peor
            monto = float(intencion.monto_usdt)
            comision = monto * self.comision
            cantidad = (monto - comision) / precio
            cartera.efectivo -= monto
            cartera.cantidad += cantidad
            cartera.costo += monto
            return Ejecucion(tiempo, cartera.bot, cartera.par, "compra", precio, cantidad, monto, comision, intencion.motivo)

        precio = precio_base * (1 - self.deslizamiento)
        cantidad = min(float(intencion.cantidad), cartera.cantidad)
        bruto = cantidad * precio
        comision = bruto * self.comision
        neto = bruto - comision
        costo_vendido = cartera.costo * (cantidad / cartera.cantidad)
        cartera.cantidad -= cantidad
        cartera.costo -= costo_vendido
        cartera.efectivo += neto
        if cartera.cantidad < 1e-12:
            cartera.cantidad = 0.0
            cartera.costo = 0.0
        return Ejecucion(
            tiempo, cartera.bot, cartera.par, "venta", precio, cantidad, bruto, comision, intencion.motivo,
            ganancia_usdt=neto - costo_vendido,
        )
