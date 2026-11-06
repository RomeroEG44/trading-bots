"""Motor en vivo: corre los bots 24/7, con el supervisor, Telegram y el panel web.

Uso:
    python -m tradingbots.motor                                 # modo del archivo .env (papel/testnet/real)
    python -m tradingbots.motor --config config/real.yaml --confirmo-dinero-real
Abre el panel en http://localhost:8000
"""
from __future__ import annotations

import argparse
import html
import logging
import sys
import threading
import time
from dataclasses import dataclass, field
from datetime import datetime, timedelta, timezone

from .almacen import Almacen
from .config import RAIZ, BotConfig, Config, cargar_config, cargar_secretos
from .datos import DURACION
from .estrategias import crear_estrategia
from .estrategias.base import Estrategia
from .modelos import Cartera, Ejecucion, Intencion
from .notificador import Notificador
from .supervisor import Supervisor

log = logging.getLogger("motor")

AYUDA = (
    "<b>Comandos</b>\n"
    "/estado: cómo van los bots\n"
    "/reporte: resumen de las últimas 24 h\n"
    "/pausar: pausa las compras de todos (las ventas de protección siguen)\n"
    "/pausar nombre_bot: pausa solo ese bot\n"
    "/reanudar o /reanudar nombre_bot\n"
    "/detener_todo: freno de emergencia (solo se reanuda con /reanudar)\n"
    "/ayuda"
)


@dataclass
class BotVivo:
    cfg: BotConfig
    estrategia: Estrategia
    cartera: Cartera
    ultima_vela: datetime | None = None  # hora de apertura de la última vela ya procesada
    proxima_revision: datetime = field(default_factory=lambda: datetime.min.replace(tzinfo=timezone.utc))


class Motor:
    def __init__(self, config: Config, broker, almacen: Almacen, notificador: Notificador,
                 reloj=lambda: datetime.now(timezone.utc), hora_reporte: int = 8):
        self.config = config
        self.broker = broker
        self.db = almacen
        self.tg = notificador
        self.reloj = reloj
        self.hora_reporte = hora_reporte  # hora local de la PC para el resumen diario
        self.sup = Supervisor(config.riesgo)
        self.sup.cargar(self.db.obtener("supervisor", {}))
        self.precios: dict[str, float] = {}
        self._ultimo_valor_guardado: datetime | None = None
        self._rechazos_avisados: dict[tuple[str, str], datetime] = {}
        self._errores_avisados: dict[str, datetime] = {}

        self.bots: dict[str, BotVivo] = {}
        for b in config.bots:
            estrategia = crear_estrategia(b.estrategia, b.nombre, b.par, b.parametros)
            guardado = self.db.cargar_bot(b.nombre)
            if guardado:
                cartera, estado, ultima = guardado
                estrategia.cargar_estado(estado)
                if cartera.presupuesto != b.presupuesto_usdt:
                    log.warning("%s: el presupuesto en config (%s) es distinto al guardado (%s); se usa el guardado",
                                b.nombre, b.presupuesto_usdt, cartera.presupuesto)
            else:
                cartera, ultima = Cartera(b.nombre, b.par, b.presupuesto_usdt), None
            self.bots[b.nombre] = BotVivo(b, estrategia, cartera, ultima)

    # ================= ciclo principal =================
    def paso(self) -> None:
        ahora = self.reloj()
        self._procesar_comandos(ahora)

        for par in {b.cfg.par for b in self.bots.values()}:
            self.precios[par] = self.broker.precio(par)

        for bot in self.bots.values():
            try:
                precio = self.precios[bot.cfg.par]
                for intencion in bot.estrategia.revisar_salidas(precio, bot.cartera):
                    self._intentar(bot, intencion, precio, ahora)
                if ahora >= bot.proxima_revision:
                    self._procesar_velas(bot, ahora)
            except Exception as e:
                self._error(ahora, f"{bot.cfg.nombre}: {e}")
            self.db.guardar_bot(bot.cartera, bot.estrategia.exportar_estado(), bot.ultima_vela)

        n_eventos = len(self.sup.eventos)
        total = self.valor_total()
        self.sup.actualizar_valor(ahora, total)
        self._avisar_eventos_supervisor(n_eventos)
        self.db.poner("supervisor", self.sup.exportar())

        if self._ultimo_valor_guardado is None or ahora - self._ultimo_valor_guardado >= timedelta(minutes=5):
            self.db.guardar_valor(ahora, total, {n: b.cartera.valor(self.precios[b.cfg.par]) for n, b in self.bots.items()})
            self._ultimo_valor_guardado = ahora
        self._reporte_diario(ahora)
        self.db.poner("en_vivo", self.foto(ahora))

    def correr(self, intervalo_s: int = 15) -> None:
        self.tg.enviar(f"🤖 <b>Bots iniciados</b> en modo <b>{self.broker.modo.upper()}</b>.\n"
                       f"Bots: {', '.join(self.bots)}. Escribe /ayuda para ver los comandos.")
        self.db.guardar_evento(self.reloj(), "inicio", f"motor iniciado en modo {self.broker.modo}")
        while True:
            inicio = time.monotonic()
            try:
                self.paso()
            except Exception as e:
                self._error(self.reloj(), f"ciclo: {e}")
            time.sleep(max(1.0, intervalo_s - (time.monotonic() - inicio)))

    # ================= velas y órdenes =================
    def _procesar_velas(self, bot: BotVivo, ahora: datetime) -> None:
        dur = timedelta(seconds=DURACION[bot.cfg.temporalidad])
        velas = self.broker.velas(bot.cfg.par, bot.cfg.temporalidad, max(300, bot.estrategia.velas_minimas + 50))
        if velas.empty:
            return
        ultima = velas.index[-1].to_pydatetime()
        # la siguiente vela cierra en ultima + 2*dur; se revisa 5 s después
        bot.proxima_revision = ultima + 2 * dur + timedelta(seconds=5)
        if bot.ultima_vela is not None and ultima <= bot.ultima_vela:
            return
        primera_vez = bot.ultima_vela is None
        bot.ultima_vela = ultima
        if len(velas) < bot.estrategia.velas_minimas:
            log.warning("%s: solo hay %d velas, se necesitan %d", bot.cfg.nombre, len(velas), bot.estrategia.velas_minimas)
            return
        if primera_vez:
            self.db.guardar_evento(ahora, "info", f"empieza a vigilar {bot.cfg.par} en velas de {bot.cfg.temporalidad}",
                                   bot.cfg.nombre)
        preparadas = bot.estrategia.preparar(velas)
        for intencion in bot.estrategia.en_vela(preparadas, bot.cartera, ultima + dur):
            self._intentar(bot, intencion, self.precios[bot.cfg.par], ahora)

    def _intentar(self, bot: BotVivo, intencion: Intencion, precio: float, ahora: datetime) -> None:
        decision = self.sup.revisar(intencion, bot.cartera, precio, ahora)
        if not decision.aprobada:
            self._registrar_rechazo(bot, intencion, decision.motivo, ahora)
            return
        try:
            ej = self.broker.ejecutar(decision.intencion, bot.cartera, ahora)
        except Exception as e:
            self._error(ahora, f"{bot.cfg.nombre}: no se pudo ejecutar la {intencion.lado}: {e}", bot.cfg.nombre)
            return
        bot.estrategia.en_ejecucion(ej)
        self.db.guardar_ejecucion(ej)
        self.db.guardar_bot(bot.cartera, bot.estrategia.exportar_estado(), bot.ultima_vela)
        self.tg.enviar(self._texto_ejecucion(ej))

    def _registrar_rechazo(self, bot: BotVivo, intencion: Intencion, motivo: str, ahora: datetime) -> None:
        clave = (bot.cfg.nombre, motivo.split(" (")[0])
        anterior = self._rechazos_avisados.get(clave)
        if anterior and ahora - anterior < timedelta(hours=6):
            return
        self._rechazos_avisados[clave] = ahora
        texto = f"el supervisor rechazó una {intencion.lado}: {motivo}"
        self.db.guardar_evento(ahora, "rechazo", texto, bot.cfg.nombre)
        self.tg.enviar(f"🛑 <b>{bot.cfg.nombre}</b>: {html.escape(texto)}")

    # ================= comandos de Edgar =================
    def _procesar_comandos(self, ahora: datetime) -> None:
        pendientes = [(c["accion"], c["bot"], "panel") for c in self.db.tomar_comandos()]
        for texto in self.tg.leer_comandos():
            partes = texto.lstrip("/").split()
            accion = partes[0].split("@")[0].lower()
            pendientes.append((accion, partes[1] if len(partes) > 1 else None, "telegram"))
        for accion, bot, origen in pendientes:
            self._ejecutar_comando(accion, bot, origen, ahora)

    def _ejecutar_comando(self, accion: str, bot: str | None, origen: str, ahora: datetime) -> None:
        if bot and bot not in self.bots:
            self.tg.enviar(f"No existe el bot '{html.escape(bot)}'. Bots: {', '.join(self.bots)}")
            return
        n = len(self.sup.eventos)
        if accion == "pausar":
            self.sup.pausar_bot(ahora, bot) if bot else self.sup.pausar(ahora, f"pausa manual ({origen})")
        elif accion == "reanudar":
            self.sup.reanudar_bot(ahora, bot) if bot else self.sup.reanudar(ahora)
        elif accion in ("detener_todo", "detener"):
            self.sup.detener_todo(ahora, f"freno de emergencia ({origen})")
        elif accion in ("estado", "start"):
            self.tg.enviar(self.texto_estado())
            return
        elif accion == "reporte":
            self.tg.enviar(self.texto_reporte(ahora))
            return
        elif accion == "ayuda":
            self.tg.enviar(AYUDA)
            return
        else:
            self.tg.enviar(f"No conozco el comando /{html.escape(accion)}.\n\n{AYUDA}")
            return
        self._avisar_eventos_supervisor(n)
        self.db.poner("supervisor", self.sup.exportar())

    # ================= textos y avisos =================
    def _avisar_eventos_supervisor(self, desde: int) -> None:
        iconos = {"pausa": "⏸️", "detencion": "🚨", "reanudacion": "▶️"}
        for e in self.sup.eventos[desde:]:
            self.db.guardar_evento(e.tiempo, e.tipo, e.mensaje)
            self.tg.enviar(f"{iconos.get(e.tipo, 'ℹ️')} <b>Supervisor · {e.tipo}</b>: {html.escape(e.mensaje)}")

    def _error(self, ahora: datetime, texto: str, bot: str | None = None) -> None:
        log.exception(texto) if sys.exc_info()[0] else log.error(texto)
        self.db.guardar_evento(ahora, "error", texto, bot)
        clave = texto[:80]
        if clave not in self._errores_avisados or ahora - self._errores_avisados[clave] > timedelta(minutes=30):
            self._errores_avisados[clave] = ahora
            self.tg.enviar(f"⚠️ <b>Error</b>: {html.escape(texto)}")

    @staticmethod
    def _texto_ejecucion(e: Ejecucion) -> str:
        moneda = e.par.split("/")[0]
        if e.lado == "compra":
            cabeza = f"🟢 <b>{e.bot}</b> compró {e.cantidad:.6f} {moneda} ({e.monto_usdt:,.2f} USDT)"
        else:
            icono = "💰" if (e.ganancia_usdt or 0) >= 0 else "🔻"
            cabeza = (f"{icono} <b>{e.bot}</b> vendió {e.cantidad:.6f} {moneda} ({e.monto_usdt:,.2f} USDT), "
                      f"resultado <b>{e.ganancia_usdt:+,.2f} USDT</b>")
        return f"{cabeza}\nPrecio: {e.precio:,.2f}\nMotivo: {html.escape(e.motivo)}"

    def valor_total(self) -> float:
        return sum(b.cartera.valor(self.precios.get(b.cfg.par, 0.0)) for b in self.bots.values())

    def texto_estado(self) -> str:
        presupuesto = sum(b.cartera.presupuesto for b in self.bots.values())
        total = self.valor_total()
        estado = {"activo": "🟢 activo", "pausado": "⏸️ pausado", "detenido": "🚨 detenido"}[self.sup.estado]
        L = [f"<b>Estado</b> · modo {self.broker.modo.upper()}",
             f"Supervisor: {estado}" + (f" ({html.escape(self.sup.motivo_estado)})" if self.sup.motivo_estado else ""),
             f"Total: <b>{total:,.2f} USDT</b> ({(total / presupuesto - 1) * 100:+.2f}%)", ""]
        for n, b in self.bots.items():
            precio = self.precios.get(b.cfg.par, 0.0)
            v = b.cartera.valor(precio)
            pausa = " ⏸️" if n in self.sup.bots_pausados else ""
            L.append(f"<b>{n}</b>{pausa} · {b.cfg.par} {precio:,.2f}\n"
                     f"  {v:,.2f} USDT ({(v / b.cartera.presupuesto - 1) * 100:+.2f}%) · efectivo {b.cartera.efectivo:,.2f}"
                     + (f" · posición {b.cartera.cantidad:.6f} a {b.cartera.precio_promedio:,.2f}" if b.cartera.cantidad else ""))
        return "\n".join(L)

    def texto_reporte(self, ahora: datetime) -> str:
        ops = self.db.ejecuciones_desde(ahora - timedelta(hours=24))
        compras = sum(o["lado"] == "compra" for o in ops)
        ventas = [o for o in ops if o["lado"] == "venta"]
        ganancia = sum(o["ganancia_usdt"] or 0 for o in ventas)
        return (f"📊 <b>Resumen de las últimas 24 h</b>\n"
                f"Operaciones: {compras} compras, {len(ventas)} ventas · ganancia realizada {ganancia:+,.2f} USDT\n\n"
                + self.texto_estado())

    def _reporte_diario(self, ahora: datetime) -> None:
        local = ahora.astimezone()
        hoy = local.date().isoformat()
        if local.hour >= self.hora_reporte and self.db.obtener("ultimo_reporte") != hoy:
            self.db.poner("ultimo_reporte", hoy)
            self.tg.enviar(self.texto_reporte(ahora))

    def foto(self, ahora: datetime) -> dict:
        """Todo lo que el panel necesita para dibujar el estado actual."""
        bots = []
        for n, b in self.bots.items():
            precio = self.precios.get(b.cfg.par, 0.0)
            bots.append({
                "nombre": n, "estrategia": b.cfg.estrategia, "par": b.cfg.par, "temporalidad": b.cfg.temporalidad,
                "precio": precio, "presupuesto": b.cartera.presupuesto, "efectivo": b.cartera.efectivo,
                "cantidad": b.cartera.cantidad, "precio_promedio": b.cartera.precio_promedio,
                "valor": b.cartera.valor(precio), "pausado": n in self.sup.bots_pausados,
                "ultima_vela": b.ultima_vela.isoformat() if b.ultima_vela else None,
                "proxima_revision": b.proxima_revision.isoformat() if b.proxima_revision.year > 1 else None,
            })
        return {
            "latido": ahora.isoformat(), "modo": self.broker.modo,
            "supervisor": {"estado": self.sup.estado, "motivo": self.sup.motivo_estado,
                           "valor_maximo": self.sup.valor_maximo, "valor_inicio_dia": self.sup.valor_inicio_dia,
                           "limites": {"perdida_diaria_max_pct": self.config.riesgo.perdida_diaria_max_pct,
                                       "caida_maxima_pct": self.config.riesgo.caida_maxima_pct}},
            "total": self.valor_total(), "presupuesto": sum(b["presupuesto"] for b in bots), "bots": bots,
        }


# ================= arranque =================
def crear_broker(modo: str, config: Config, secretos: dict):
    from .mercado import BrokerBinance, BrokerPapel
    if modo == "papel":
        return BrokerPapel(config.comision_pct, config.deslizamiento_pct)
    if not secretos["api_key"] or not secretos["api_secret"]:
        raise SystemExit("Faltan BINANCE_API_KEY / BINANCE_API_SECRET en el archivo .env")
    return BrokerBinance(modo, secretos["api_key"], secretos["api_secret"])


def main() -> None:
    ap = argparse.ArgumentParser(description="Motor en vivo de los bots")
    ap.add_argument("--config", default="config/pruebas.yaml")
    ap.add_argument("--modo", choices=["papel", "testnet", "real"], help="por defecto, MODO del archivo .env")
    ap.add_argument("--intervalo", type=int, default=15, help="segundos entre revisiones")
    ap.add_argument("--sin-panel", action="store_true")
    ap.add_argument("--puerto", type=int, default=8000)
    ap.add_argument("--hora-reporte", type=int, default=8, help="hora local del resumen diario por Telegram")
    ap.add_argument("--confirmo-dinero-real", action="store_true")
    args = ap.parse_args()

    (RAIZ / "logs").mkdir(exist_ok=True)
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s: %(message)s",
                        handlers=[logging.StreamHandler(), logging.FileHandler(RAIZ / "logs" / "motor.log", encoding="utf-8")])
    for ruidoso in ("urllib3", "ccxt", "httpx"):
        logging.getLogger(ruidoso).setLevel(logging.WARNING)

    secretos = cargar_secretos()
    modo = args.modo or secretos["modo"]
    if modo == "real" and not args.confirmo_dinero_real:
        raise SystemExit("Modo REAL: agrega --confirmo-dinero-real para operar con dinero de verdad.")
    if modo != "real" and "real" in args.config:
        raise SystemExit("config/real.yaml solo se usa en modo real.")

    config = cargar_config(args.config)
    db = Almacen(RAIZ / "data" / f"bots_{modo}.sqlite")
    motor = Motor(config, crear_broker(modo, config, secretos), db,
                  Notificador(secretos["telegram_token"], secretos["telegram_chat_id"]), hora_reporte=args.hora_reporte)

    if not args.sin_panel:
        from .panel import iniciar_panel
        threading.Thread(target=iniciar_panel, args=(db, args.puerto), daemon=True).start()
        log.info("Panel en http://localhost:%d", args.puerto)
    if not motor.tg.activo:
        log.info("Telegram no configurado: los mensajes solo se verán en esta ventana y en el panel.")
    try:
        motor.correr(args.intervalo)
    except KeyboardInterrupt:
        motor.tg.enviar("⏹️ Bots apagados manualmente.")
        db.guardar_evento(datetime.now(timezone.utc), "fin", "motor apagado manualmente")
        log.info("Apagado.")


if __name__ == "__main__":
    main()
