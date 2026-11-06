"""El bot supervisor: aprueba o rechaza cada orden y frena todo si hay demasiadas pérdidas.

Reglas:
- Las COMPRAS solo se permiten si el supervisor está "activo".
- Las VENTAS (reducir riesgo, stop-loss) siempre se permiten, aunque esté pausado o detenido.
- Pérdida diaria > límite  -> "pausado" hasta el siguiente día (UTC); se reanuda solo.
- Caída desde el máximo > límite -> "detenido"; se reanuda solo tras `reanudar_auto_horas` (si está configurado).
"""
from __future__ import annotations

from collections import defaultdict, deque
from dataclasses import dataclass, field, replace
from datetime import datetime, timedelta

from .modelos import Cartera, Intencion


@dataclass
class LimitesRiesgo:
    pares_permitidos: list[str]
    orden_minima_usdt: float = 5.0  # mínimo que acepta Binance
    orden_maxima_usdt: float = 50.0
    max_compras_por_hora: int = 4
    perdida_diaria_max_pct: float = 3.0
    caida_maxima_pct: float = 10.0
    reanudar_auto_horas: float | None = None  # tras una detención AUTOMÁTICA, reanuda solo después de N horas


@dataclass
class Decision:
    aprobada: bool
    motivo: str
    intencion: Intencion | None = None


@dataclass
class Evento:
    tiempo: datetime
    tipo: str  # "pausa", "detencion", "reanudacion"
    mensaje: str


class Supervisor:
    def __init__(self, limites: LimitesRiesgo):
        self.limites = limites
        self.estado = "activo"  # activo | pausado | detenido
        self.motivo_estado = ""
        self.pausado_hasta: datetime | None = None
        self.dia_actual = None
        self.valor_inicio_dia: float | None = None
        self.valor_maximo: float | None = None
        self.ultimo_valor: float | None = None
        self.eventos: list[Evento] = []
        self.bots_pausados: set[str] = set()
        self.detenido_desde: datetime | None = None
        self.detencion_automatica = False
        self._compras: dict[str, deque] = defaultdict(deque)

    # ---------- revisión de órdenes ----------
    def revisar(self, intencion: Intencion, cartera: Cartera, precio: float, ahora: datetime) -> Decision:
        self._reanudar_si_toca(ahora)
        lim = self.limites

        if intencion.par not in lim.pares_permitidos:
            return Decision(False, f"par {intencion.par} no está en la lista permitida")

        if intencion.lado == "venta":
            cantidad = min(intencion.cantidad or 0.0, cartera.cantidad)
            if cantidad * precio < lim.orden_minima_usdt:
                return Decision(False, "venta menor al mínimo de Binance")
            return Decision(True, "venta aprobada", replace(intencion, cantidad=cantidad))

        # compras
        if self.estado != "activo":
            return Decision(False, f"compras bloqueadas: supervisor {self.estado} ({self.motivo_estado})")
        if intencion.bot in self.bots_pausados:
            return Decision(False, "compras bloqueadas: bot pausado por Edgar")

        recientes = self._compras[intencion.bot]
        while recientes and ahora - recientes[0] >= timedelta(hours=1):
            recientes.popleft()
        if len(recientes) >= lim.max_compras_por_hora:
            return Decision(False, "demasiadas compras en la última hora")

        monto = min(intencion.monto_usdt or 0.0, lim.orden_maxima_usdt, cartera.efectivo)
        if monto < lim.orden_minima_usdt:
            if cartera.efectivo < lim.orden_minima_usdt:
                return Decision(False, "presupuesto del bot agotado")
            return Decision(False, "compra menor al mínimo de Binance")

        recientes.append(ahora)
        return Decision(True, "compra aprobada", replace(intencion, monto_usdt=monto))

    # ---------- vigilancia del valor total ----------
    def actualizar_valor(self, ahora: datetime, valor_total: float) -> None:
        self._reanudar_si_toca(ahora)
        self.ultimo_valor = valor_total
        if ahora.date() != self.dia_actual:
            self.dia_actual = ahora.date()
            self.valor_inicio_dia = valor_total
        self.valor_maximo = valor_total if self.valor_maximo is None else max(self.valor_maximo, valor_total)

        if self.estado == "detenido":
            h = self.limites.reanudar_auto_horas
            if (h is not None and self.detencion_automatica and self.detenido_desde
                    and ahora - self.detenido_desde >= timedelta(hours=h)):
                self.reanudar(ahora, f"reanudación automática tras {h:g} h")
            return
        caida = 1 - valor_total / self.valor_maximo
        if caida * 100 >= self.limites.caida_maxima_pct:
            self._cambiar(ahora, "detenido", "detencion",
                          f"caída de {caida:.1%} desde el máximo ({self.valor_maximo:.2f} → {valor_total:.2f} USDT)")
            self.detenido_desde, self.detencion_automatica = ahora, True
            return
        if self.estado == "activo":
            perdida_dia = 1 - valor_total / self.valor_inicio_dia
            if perdida_dia * 100 >= self.limites.perdida_diaria_max_pct:
                manana = datetime.combine(ahora.date() + timedelta(days=1), datetime.min.time(), tzinfo=ahora.tzinfo)
                self.pausado_hasta = manana
                self._cambiar(ahora, "pausado", "pausa", f"pérdida de {perdida_dia:.1%} en el día")

    # ---------- comandos de Edgar ----------
    def detener_todo(self, ahora: datetime, motivo: str = "orden manual de Edgar") -> None:
        self._cambiar(ahora, "detenido", "detencion", motivo)
        self.detenido_desde, self.detencion_automatica = ahora, False  # una detención manual no se reanuda sola

    def pausar(self, ahora: datetime, motivo: str = "pausa manual de Edgar") -> None:
        """Pausa las compras de todos los bots hasta que Edgar reanude."""
        self.pausado_hasta = None
        self._cambiar(ahora, "pausado", "pausa", motivo)

    def pausar_bot(self, ahora: datetime, bot: str) -> None:
        self.bots_pausados.add(bot)
        self.eventos.append(Evento(ahora, "pausa", f"bot {bot} pausado por Edgar"))

    def reanudar_bot(self, ahora: datetime, bot: str) -> None:
        self.bots_pausados.discard(bot)
        self.eventos.append(Evento(ahora, "reanudacion", f"bot {bot} reanudado por Edgar"))

    def reanudar(self, ahora: datetime, motivo: str = "reanudado") -> None:
        self.pausado_hasta = None
        self.detenido_desde, self.detencion_automatica = None, False
        if self.ultimo_valor is not None:
            self.valor_maximo = self.ultimo_valor  # se empieza a medir la caída desde aquí
        self.valor_inicio_dia = self.ultimo_valor
        self._cambiar(ahora, "activo", "reanudacion", motivo)

    # ---------- guardar / recuperar (para reinicios) ----------
    def exportar(self) -> dict:
        return {
            "estado": self.estado, "motivo_estado": self.motivo_estado,
            "pausado_hasta": self.pausado_hasta.isoformat() if self.pausado_hasta else None,
            "dia_actual": self.dia_actual.isoformat() if self.dia_actual else None,
            "valor_inicio_dia": self.valor_inicio_dia, "valor_maximo": self.valor_maximo,
            "ultimo_valor": self.ultimo_valor, "bots_pausados": sorted(self.bots_pausados),
            "detenido_desde": self.detenido_desde.isoformat() if self.detenido_desde else None,
            "detencion_automatica": self.detencion_automatica,
        }

    def cargar(self, d: dict) -> None:
        from datetime import date
        self.estado = d.get("estado", "activo")
        self.motivo_estado = d.get("motivo_estado", "")
        self.pausado_hasta = datetime.fromisoformat(d["pausado_hasta"]) if d.get("pausado_hasta") else None
        self.dia_actual = date.fromisoformat(d["dia_actual"]) if d.get("dia_actual") else None
        self.valor_inicio_dia = d.get("valor_inicio_dia")
        self.valor_maximo = d.get("valor_maximo")
        self.ultimo_valor = d.get("ultimo_valor")
        self.bots_pausados = set(d.get("bots_pausados", []))
        self.detenido_desde = datetime.fromisoformat(d["detenido_desde"]) if d.get("detenido_desde") else None
        self.detencion_automatica = d.get("detencion_automatica", False)

    # ---------- internos ----------
    def _reanudar_si_toca(self, ahora: datetime) -> None:
        if self.estado == "pausado" and self.pausado_hasta and ahora >= self.pausado_hasta:
            self.pausado_hasta = None
            self._cambiar(ahora, "activo", "reanudacion", "nuevo día: se reanudan las compras")

    def _cambiar(self, ahora: datetime, estado: str, tipo: str, mensaje: str) -> None:
        self.estado = estado
        self.motivo_estado = mensaje if estado != "activo" else ""
        self.eventos.append(Evento(ahora, tipo, mensaje))
