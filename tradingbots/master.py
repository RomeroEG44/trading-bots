"""El Master: el bot principal que vigila a los demás, les da feedback y corrige sus operaciones.

Capas de decisión de cada orden:
    Estrategia (quiere comprar/vender)
      -> Master (ajusta el tamaño o la veta según cómo le está yendo al bot y al mercado)
      -> Supervisor (límites duros de riesgo para todo el sistema)
      -> Binance

Lo que hace el Master, sin pedir confirmación:
- Racha de pérdidas  -> pausa temporal del bot ("enfriamiento") y reduce su tamaño.
- Caída fuerte del bot -> "cuarentena": cierra su posición, lo pausa y reduce su tamaño a la mitad.
- Posición que pierde demasiado -> la cierra él mismo (corrige al bot si su stop no funcionó).
- Buen rendimiento -> le sube el tamaño (hasta un tope). Rendimiento flojo -> se lo baja.
- Comisiones que se comen la ganancia -> obliga al bot a esperar más entre compras.
- Bot que pierde de forma persistente -> lo retira 24 h y luego le da otra oportunidad con tamaño mínimo.
- Movimiento brusco del mercado -> bloquea compras nuevas en ese par por unos minutos.
Las VENTAS nunca se bloquean.
"""
from __future__ import annotations

from collections import defaultdict, deque
from dataclasses import asdict, dataclass, field, fields, replace
from datetime import datetime, timedelta

from .modelos import Cartera, Ejecucion, Intencion


@dataclass
class ReglasMaster:
    racha_perdidas: int = 3  # pérdidas seguidas para pausar al bot
    enfriamiento_min: float = 15
    caida_reducir_pct: float = 4.0  # caída del bot desde su máximo para reducirle el tamaño
    caida_cuarentena_pct: float = 8.0  # caída para ponerlo en cuarentena
    cuarentena_min: float = 120
    perdida_max_posicion_pct: float = 2.5  # el Master cierra cualquier posición que pierda más que esto
    operaciones_para_evaluar: int = 5
    ventana_operaciones: int = 10
    factor_bueno: float = 1.3  # factor de beneficio para subir el tamaño
    factor_malo: float = 0.8  # por debajo, se baja el tamaño
    tamano_min: float = 0.25
    tamano_max: float = 1.5
    comisiones_max_pct: float = 50.0  # % de la ganancia bruta que se pueden llevar las comisiones
    movimiento_brusco_pct: float = 1.5  # movimiento del precio en la ventana para bloquear compras
    ventana_brusca_min: float = 5
    bloqueo_brusco_min: float = 10
    retirar_min_ventas: int = 20  # tras estas ventas, si el factor sigue por debajo de retirar_factor...
    retirar_factor: float = 0.5
    retiro_horas: float = 24  # ...el bot queda retirado este tiempo y vuelve con el tamaño mínimo

    @classmethod
    def desde(cls, d: dict | None) -> "ReglasMaster":
        d = d or {}
        validos = {f.name for f in fields(cls)}
        malos = set(d) - validos
        if malos:
            raise ValueError(f"Reglas del Master desconocidas: {sorted(malos)}")
        return cls(**d)


@dataclass
class FichaBot:
    """Lo que el Master sabe de cada bot."""
    tamano: float = 1.0
    estado: str = "activo"  # activo | enfriamiento | cuarentena | retirado
    hasta: datetime | None = None
    motivo: str = ""
    pico: float | None = None
    reduccion_hecha: bool = False
    racha: int = 0
    espera_min: float = 0.0  # minutos mínimos entre compras
    ultima_compra: datetime | None = None
    comision_abierta: float = 0.0
    ventas: list = field(default_factory=list)  # [(ganancia, comisiones), ...] de las últimas ventas
    nota: str = "Sin ventas todavía: aún no hay con qué juzgar."
    ultimo_cierre: datetime | None = None
    ventas_evaluadas: int = 0  # ventas desde el último retiro


@dataclass
class Feedback:
    tiempo: datetime
    bot: str | None
    nivel: str  # info | accion | alerta
    mensaje: str


def _fecha(v):
    return v.isoformat() if isinstance(v, datetime) else v


class Master:
    def __init__(self, reglas: ReglasMaster | None = None, por_bot: dict[str, dict] | None = None):
        self.reglas_base = reglas or ReglasMaster()
        self._reglas = {b: replace(self.reglas_base, **(o or {})) for b, o in (por_bot or {}).items()}
        self.fichas: dict[str, FichaBot] = defaultdict(FichaBot)
        self.precios: dict[str, deque] = defaultdict(deque)
        self.bloqueos: dict[str, tuple[datetime, str]] = {}
        self.feedback: list[Feedback] = []

    def reglas(self, bot: str) -> ReglasMaster:
        return self._reglas.get(bot, self.reglas_base)

    def _decir(self, ahora, bot, nivel, mensaje):
        self.feedback.append(Feedback(ahora, bot, nivel, mensaje))

    def tomar_feedback(self) -> list[Feedback]:
        f, self.feedback = self.feedback, []
        return f

    # ---------- mercado ----------
    def registrar_precio(self, par: str, ahora: datetime, precio: float) -> None:
        r = self.reglas_base
        dq = self.precios[par]
        dq.append((ahora, precio))
        while dq and ahora - dq[0][0] > timedelta(minutes=r.ventana_brusca_min):
            dq.popleft()
        if par in self.bloqueos and ahora >= self.bloqueos[par][0]:
            del self.bloqueos[par]
            self._decir(ahora, None, "info", f"{par} se calmó: vuelvo a permitir compras.")
        if par in self.bloqueos or len(dq) < 2:
            return
        bajo, alto = min(p for _, p in dq), max(p for _, p in dq)
        movimiento = (alto / bajo - 1) * 100
        if movimiento >= r.movimiento_brusco_pct:
            motivo = f"se movió {movimiento:.1f}% en {r.ventana_brusca_min:g} min"
            self.bloqueos[par] = (ahora + timedelta(minutes=r.bloqueo_brusco_min), motivo)
            self._decir(ahora, None, "alerta",
                        f"Mercado agitado: {par} {motivo}. Bloqueo compras nuevas en {par} por {r.bloqueo_brusco_min:g} min.")

    # ---------- antes de cada orden ----------
    def ajustar(self, intencion: Intencion, ahora: datetime) -> tuple[Intencion | None, str]:
        if intencion.lado == "venta":
            return intencion, ""
        f = self.fichas[intencion.bot]
        self._expirar(intencion.bot, ahora)
        if f.estado != "activo":
            return None, f"Master: bot en {f.estado} hasta las {f.hasta:%H:%M} UTC ({f.motivo})"
        if intencion.par in self.bloqueos:
            return None, f"Master: compras bloqueadas en {intencion.par} ({self.bloqueos[intencion.par][1]})"
        if f.espera_min and f.ultima_compra and ahora - f.ultima_compra < timedelta(minutes=f.espera_min):
            return None, f"Master: debe esperar {f.espera_min:g} min entre compras (comisiones altas)"
        if f.tamano == 1.0:
            return intencion, ""
        return replace(intencion, monto_usdt=intencion.monto_usdt * f.tamano,
                       motivo=f"{intencion.motivo} · tamaño x{f.tamano:.2f} (Master)"), ""

    # ---------- después de cada orden ----------
    def en_ejecucion(self, e: Ejecucion) -> None:
        f, r = self.fichas[e.bot], self.reglas(e.bot)
        if e.lado == "compra":
            f.ultima_compra = e.tiempo
            f.comision_abierta += e.comision_usdt
            return
        comisiones = f.comision_abierta + e.comision_usdt
        f.comision_abierta = 0.0
        f.ventas = (f.ventas + [(e.ganancia_usdt or 0.0, comisiones)])[-r.ventana_operaciones:]
        f.racha = f.racha + 1 if (e.ganancia_usdt or 0) < 0 else 0
        f.ventas_evaluadas += 1
        if f.racha >= r.racha_perdidas:
            f.tamano = max(r.tamano_min, f.tamano * 0.75)
            self._poner(e.bot, "enfriamiento", e.tiempo, r.enfriamiento_min, f"{f.racha} pérdidas seguidas")
            self._decir(e.tiempo, e.bot, "accion",
                        f"{f.racha} pérdidas seguidas: pausa de {r.enfriamiento_min:g} min y bajo su tamaño a x{f.tamano:.2f}.")
            f.racha = 0
        self._evaluar_rendimiento(e.bot, e.tiempo)

    def _evaluar_rendimiento(self, bot: str, ahora: datetime) -> None:
        f, r = self.fichas[bot], self.reglas(bot)
        v = f.ventas
        ganancias = sum(g for g, _ in v if g > 0)
        perdidas = -sum(g for g, _ in v if g < 0)
        ganadoras = sum(1 for g, _ in v if g > 0)
        comisiones = sum(c for _, c in v)
        factor = ganancias / perdidas if perdidas > 0 else float("inf")
        txt_factor = "∞" if factor == float("inf") else f"{factor:.2f}"
        f.nota = (f"Últimas {len(v)} ventas: {ganadoras} ganadoras ({ganadoras / len(v):.0%}), factor {txt_factor}, "
                  f"resultado {sum(g for g, _ in v):+.2f} USDT, comisiones {comisiones:.2f}")
        if len(v) < r.operaciones_para_evaluar:
            f.nota += " · aún pocas operaciones para juzgar"
            return
        tasa = ganadoras / len(v)
        resumen = f"factor {txt_factor}, {tasa:.0%} ganadoras"
        if f.ventas_evaluadas >= r.retirar_min_ventas and factor < r.retirar_factor and f.estado != "retirado":
            f.tamano = r.tamano_min
            f.ventas_evaluadas = 0
            self._poner(bot, "retirado", ahora, r.retiro_horas * 60, f"pierde de forma persistente ({resumen})")
            self._decir(ahora, bot, "alerta",
                        f"Retiro al bot {r.retiro_horas:g} h: pierde de forma persistente ({resumen}). "
                        f"Volverá con tamaño mínimo x{f.tamano:.2f}.")
            return
        if factor >= r.factor_bueno and tasa >= 0.5 and f.tamano < r.tamano_max:
            f.tamano = min(r.tamano_max, f.tamano * 1.15)
            self._decir(ahora, bot, "info", f"Buen rendimiento ({resumen}): le subo el tamaño a x{f.tamano:.2f}.")
        elif factor < r.factor_malo and f.tamano > r.tamano_min:
            f.tamano = max(r.tamano_min, f.tamano * 0.8)
            self._decir(ahora, bot, "accion", f"Rendimiento flojo ({resumen}): le bajo el tamaño a x{f.tamano:.2f}.")
        bruto = ganancias + comisiones
        if bruto > 0 and comisiones >= bruto * r.comisiones_max_pct / 100 and f.espera_min < 60:
            f.espera_min = min(60.0, max(5.0, f.espera_min * 2))
            self._decir(ahora, bot, "accion",
                        f"Las comisiones ({comisiones:.2f} USDT) se llevan {comisiones / bruto:.0%} de lo ganado: "
                        f"ahora debe esperar {f.espera_min:g} min entre compras.")

    # ---------- revisión continua ----------
    def revisar(self, ahora: datetime, bot: str, cartera: Cartera, precio: float) -> list[Intencion]:
        """Se llama cada pocos segundos por bot. Puede devolver ventas que el Master ordena."""
        f, r = self.fichas[bot], self.reglas(bot)
        self._expirar(bot, ahora)
        valor = cartera.valor(precio)
        if f.pico is None or valor > f.pico:
            f.pico, f.reduccion_hecha = valor, False
        caida = (1 - valor / f.pico) * 100 if f.pico else 0.0
        vender_todo = lambda motivo: [Intencion(bot, cartera.par, "venta", cantidad=cartera.cantidad, motivo=motivo)]
        tiene_posicion = cartera.cantidad * precio >= 1

        if caida >= r.caida_cuarentena_pct and f.estado != "cuarentena":
            f.tamano = max(r.tamano_min, f.tamano * 0.5)
            self._poner(bot, "cuarentena", ahora, r.cuarentena_min, f"cayó {caida:.1f}% desde su máximo")
            f.pico, f.reduccion_hecha = valor, False
            self._decir(ahora, bot, "alerta",
                        f"Cuarentena de {r.cuarentena_min:g} min: cayó {caida:.1f}% desde su máximo. "
                        + ("Cierro su posición y " if tiene_posicion else "") + f"bajo su tamaño a x{f.tamano:.2f}.")
            return vender_todo("Master: cierre por cuarentena") if tiene_posicion else []

        if caida >= r.caida_reducir_pct and not f.reduccion_hecha:
            f.reduccion_hecha = True
            f.tamano = max(r.tamano_min, f.tamano * 0.75)
            self._decir(ahora, bot, "accion", f"Cayó {caida:.1f}% desde su máximo: le bajo el tamaño a x{f.tamano:.2f}.")

        if tiene_posicion and cartera.precio_promedio > 0:
            perdida = (1 - precio / cartera.precio_promedio) * 100
            if perdida >= r.perdida_max_posicion_pct and (f.ultimo_cierre is None or ahora - f.ultimo_cierre > timedelta(minutes=1)):
                f.ultimo_cierre = ahora
                self._decir(ahora, bot, "alerta",
                            f"Corrijo su operación: la posición pierde {perdida:.1f}% (límite {r.perdida_max_posicion_pct:g}%). La cierro.")
                return vender_todo(f"Master: cierre de seguridad (pérdida {perdida:.1f}%)")
        return []

    # ---------- internos ----------
    def _poner(self, bot, estado, ahora, minutos, motivo):
        f = self.fichas[bot]
        f.estado, f.hasta, f.motivo = estado, ahora + timedelta(minutes=minutos), motivo

    def _expirar(self, bot, ahora):
        f = self.fichas[bot]
        if f.estado != "activo" and f.hasta and ahora >= f.hasta:
            anterior = f.estado
            f.estado, f.hasta, f.motivo = "activo", None, ""
            self._decir(ahora, bot, "info", f"Termina su {anterior}: vuelve a operar con tamaño x{f.tamano:.2f}.")

    def resumen(self, bot: str) -> dict:
        f = self.fichas[bot]
        return {"estado": f.estado, "hasta": _fecha(f.hasta), "motivo": f.motivo, "tamano": round(f.tamano, 3),
                "espera_min": f.espera_min, "racha": f.racha, "nota": f.nota}

    def exportar(self) -> dict:
        return {
            "fichas": {b: {k: _fecha(v) for k, v in asdict(f).items()} for b, f in self.fichas.items()},
            "bloqueos": {p: [_fecha(h), m] for p, (h, m) in self.bloqueos.items()},
        }

    def cargar(self, d: dict) -> None:
        fechas = {"hasta", "ultima_compra", "ultimo_cierre"}
        for b, datos in (d.get("fichas") or {}).items():
            datos = {k: (datetime.fromisoformat(v) if k in fechas and v else v) for k, v in datos.items()}
            datos["ventas"] = [tuple(x) for x in datos.get("ventas", [])]
            self.fichas[b] = FichaBot(**{k: v for k, v in datos.items() if k in FichaBot.__dataclass_fields__})
        self.bloqueos = {p: (datetime.fromisoformat(h), m) for p, (h, m) in (d.get("bloqueos") or {}).items()}
