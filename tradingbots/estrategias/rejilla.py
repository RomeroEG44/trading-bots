"""Rejilla (grid): compra un "lote" cada vez que el precio baja un paso y vende cada lote cuando
sube un paso por encima de su precio de compra. Gana con el sube y baja del precio."""
from __future__ import annotations

from .base import Estrategia, f2, rd


class Rejilla(Estrategia):
    DESCRIPCION = "Rejilla (compra en bajadas, vende en subidas)"
    PARAMETROS = {"paso_pct": 0.5, "monto_usdt": 50.0, "max_lotes": 6}
    CAMPOS_ESTADO = ("lotes",)
    velas_minimas = 1

    def __init__(self, nombre, par, parametros=None):
        super().__init__(nombre, par, parametros)
        self.lotes: list[dict] = []  # [{"precio": ..., "cantidad": ...}]
        self._lote_en_venta: dict | None = None

    def en_vela(self, velas, cartera, ahora):
        return []  # trabaja con el precio en vivo

    def en_precio(self, precio, cartera):
        self._lote_en_venta = None
        if self.lotes and cartera.cantidad <= 0:
            self.lotes = []  # la posición se cerró desde fuera (por ejemplo, el Master)
        paso = self.p["paso_pct"] / 100

        listos = [l for l in self.lotes if precio >= l["precio"] * (1 + paso)]
        if listos:
            lote = min(listos, key=lambda l: l["precio"])
            self._lote_en_venta = lote
            return [self._intencion("venta", cantidad=min(lote["cantidad"], cartera.cantidad),
                                    motivo=f"Rejilla: lote comprado a {f2(lote['precio'])} subió {self.p['paso_pct']}%")]

        if not self.lotes:
            return [self._intencion("compra", monto_usdt=self.p["monto_usdt"], motivo=f"Rejilla: primer lote a {f2(precio)}")]
        mas_bajo = min(l["precio"] for l in self.lotes)
        if len(self.lotes) < self.p["max_lotes"] and precio <= mas_bajo * (1 - paso):
            return [self._intencion("compra", monto_usdt=self.p["monto_usdt"],
                                    motivo=f"Rejilla: bajó {self.p['paso_pct']}% desde {f2(mas_bajo)}, compro otro lote "
                                           f"({len(self.lotes) + 1}/{self.p['max_lotes']})")]
        return []

    def en_ejecucion(self, e):
        if e.lado == "compra":
            self.lotes.append({"precio": e.precio, "cantidad": e.cantidad})
        elif self._lote_en_venta is not None and self._lote_en_venta in self.lotes:
            self.lotes.remove(self._lote_en_venta)
        else:
            self.lotes = []  # venta forzada de todo (Master)
        self._lote_en_venta = None

    def analisis(self, velas, cartera, precio, ahora):
        paso = self.p["paso_pct"] / 100
        if not self.lotes:
            return {"senal": "compra", "texto": "Sin lotes: compra el primero en la siguiente revisión.", "indicadores": {}}
        mas_bajo = min(l["precio"] for l in self.lotes)
        compra = mas_bajo * (1 - paso)
        venta = mas_bajo * (1 + paso)
        texto = (f"{len(self.lotes)}/{self.p['max_lotes']} lotes abiertos · próxima compra en {f2(compra)} "
                 f"({(compra / precio - 1) * 100:+.2f}%) · próxima venta en {f2(venta)} ({(venta / precio - 1) * 100:+.2f}%)")
        return {"senal": "en_posicion", "texto": texto,
                "indicadores": {"lotes": len(self.lotes), "proxima_compra": rd(compra), "proxima_venta": rd(venta)}}
