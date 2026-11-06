"""Bot 1: DCA (compra programada) con compra doble en caídas y toma de ganancias parcial."""
from __future__ import annotations

from datetime import datetime, timedelta

from ..modelos import Cartera, Ejecucion, Intencion
from .base import Estrategia


class DCA(Estrategia):
    PARAMETROS = {
        "monto_usdt": 10.0,  # cuánto comprar cada vez
        "cada_horas": 24,  # cada cuánto comprar
        "caida_para_doble_pct": 5.0,  # si el precio cayó esto desde la última compra...
        "multiplicador_caida": 2.0,  # ...se compra este múltiplo
        "toma_ganancia_pct": 15.0,  # vender una parte si la ganancia sobre el precio promedio supera esto
        "fraccion_venta": 0.25,  # qué parte de la posición vender en la toma de ganancias
    }
    velas_minimas = 1

    def __init__(self, nombre, par, parametros=None):
        super().__init__(nombre, par, parametros)
        self.ultima_compra_t: datetime | None = None
        self.ultima_compra_precio: float | None = None
        self.ultima_toma_precio: float | None = None

    def en_vela(self, velas, cartera: Cartera, ahora: datetime) -> list[Intencion]:
        p = self.p
        precio = float(velas["close"].iloc[-1])

        if cartera.cantidad > 0:
            objetivo = cartera.precio_promedio * (1 + p["toma_ganancia_pct"] / 100)
            if self.ultima_toma_precio:  # la siguiente toma exige otro +X% desde la anterior
                objetivo = max(objetivo, self.ultima_toma_precio * (1 + p["toma_ganancia_pct"] / 100))
            if precio >= objetivo:
                return [self._intencion(
                    "venta", cantidad=cartera.cantidad * p["fraccion_venta"],
                    motivo=f"Toma de ganancias: precio {precio:,.2f} ≥ objetivo {objetivo:,.2f}",
                )]

        if self.ultima_compra_t is None or ahora - self.ultima_compra_t >= timedelta(hours=p["cada_horas"]):
            self.ultima_compra_t = ahora
            monto = p["monto_usdt"]
            motivo = f"Compra programada (cada {p['cada_horas']} h)"
            if self.ultima_compra_precio:
                caida = (1 - precio / self.ultima_compra_precio) * 100
                if caida >= p["caida_para_doble_pct"]:
                    monto *= p["multiplicador_caida"]
                    motivo = f"Compra x{p['multiplicador_caida']:g}: el precio cayó {caida:.1f}% desde la última compra"
            return [self._intencion("compra", monto_usdt=monto, motivo=motivo)]
        return []

    def en_ejecucion(self, e: Ejecucion) -> None:
        if e.lado == "compra":
            self.ultima_compra_precio = e.precio
        else:
            self.ultima_toma_precio = e.precio
