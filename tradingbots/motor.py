"""Motor en vivo: corre todos los bots en paralelo, 24/7 y sin pedir confirmación.

Cada ciclo (cada 5 s por defecto):
  1. Lee los precios de todos los pares en una sola consulta.
  2. Cada bot vigila su posición con el precio actual (stops, rejilla).
  3. Cuando cierra una vela de su temporalidad, el bot analiza y decide.
  4. El Master revisa a cada bot: puede corregir (cerrar posiciones), pausar o cambiar su tamaño.
  5. El Supervisor vigila los límites duros de todo el sistema.
  6. Todo se guarda en la base de datos y el panel lo muestra en tiempo real.

Uso:
    python -m tradingbots.motor                      # modo del archivo .env, config/testnet.yaml
    python -m tradingbots.motor --modo papel         # simulado con precios reales (sin claves)
Panel: http://localhost:8000
"""
from __future__ import annotations

import argparse
import logging
import sys
import threading
import time
from dataclasses import dataclass, field
from datetime import datetime, timedelta, timezone

import pandas as pd

from .almacen import Almacen
from .config import RAIZ, BotConfig, Config, cargar_config, cargar_secretos
from .datos import DURACION
from .estrategias import crear_estrategia
from .estrategias.base import Estrategia
from .master import Master, ReglasMaster
from .modelos import Cartera, Intencion
from .supervisor import Supervisor

log = logging.getLogger("motor")
PUNTOS_GRAFICA = 120


@dataclass
class BotVivo:
    cfg: BotConfig
    estrategia: Estrategia
    cartera: Cartera
    ultima_vela: datetime | None = None
    proxima_revision: datetime = field(default_factory=lambda: datetime.min.replace(tzinfo=timezone.utc))
    velas: pd.DataFrame | None = None
    analisis: dict = field(default_factory=dict)


class Motor:
    def __init__(self, config: Config, broker, almacen: Almacen, reloj=lambda: datetime.now(timezone.utc)):
        self.config = config
        self.broker = broker
        self.db = almacen
        self.reloj = reloj
        self.sup = Supervisor(config.riesgo)
        self.sup.cargar(self.db.obtener("supervisor", {}))
        self.master = Master(ReglasMaster.desde(config.master), {b.nombre: b.master for b in config.bots if b.master})
        self.master.cargar(self.db.obtener("master", {}))
        self.precios: dict[str, float] = {}
        self._ultimo_valor_guardado: datetime | None = None
        self._rechazos_vistos: dict[tuple[str, str], datetime] = {}
        self._errores_vistos: dict[str, datetime] = {}
        self._eventos_sup = len(self.sup.eventos)

        self.bots: dict[str, BotVivo] = {}
        for b in config.bots:
            estrategia = crear_estrategia(b.estrategia, b.nombre, b.par, b.parametros)
            guardado = self.db.cargar_bot(b.nombre)
            if guardado:
                cartera, estado, ultima = guardado
                estrategia.cargar_estado(estado)
            else:
                cartera, ultima = Cartera(b.nombre, b.par, b.presupuesto_usdt), None
            self.bots[b.nombre] = BotVivo(b, estrategia, cartera, ultima)
        self.pares = sorted({b.cfg.par for b in self.bots.values()})

    # ================= ciclo principal =================
    def paso(self) -> None:
        ahora = self.reloj()
        self._procesar_comandos(ahora)
        self.precios.update(self.broker.precios(self.pares))
        for par in self.pares:
            self.master.registrar_precio(par, ahora, self.precios[par])

        for bot in self.bots.values():
            try:
                precio = self.precios[bot.cfg.par]
                for i in bot.estrategia.en_precio(precio, bot.cartera):
                    self._intentar(bot, i, precio, ahora)
                if ahora >= bot.proxima_revision:
                    self._procesar_velas(bot, ahora)
                for i in self.master.revisar(ahora, bot.cfg.nombre, bot.cartera, precio):
                    self._intentar(bot, i, precio, ahora)
                bot.analisis = bot.estrategia.analisis(bot.velas, bot.cartera, precio, ahora)
            except Exception as e:
                self._error(ahora, f"{bot.cfg.nombre}: {e}", bot.cfg.nombre)
            self.db.guardar_bot(bot.cartera, bot.estrategia.exportar_estado(), bot.ultima_vela)

        total = self.valor_total()
        self.sup.actualizar_valor(ahora, total)
        self._guardar_eventos()
        self.db.poner("supervisor", self.sup.exportar())
        self.db.poner("master", self.master.exportar())

        if self._ultimo_valor_guardado is None or ahora - self._ultimo_valor_guardado >= timedelta(minutes=1):
            self.db.guardar_valor(ahora, total, {n: round(b.cartera.valor(self.precios[b.cfg.par]), 4)
                                                 for n, b in self.bots.items()})
            self._ultimo_valor_guardado = ahora
        self.db.poner("en_vivo", self.foto(ahora))

    def correr(self, intervalo_s: int = 5) -> None:
        self.db.guardar_evento(self.reloj(), "inicio",
                               f"motor iniciado en modo {self.broker.modo} con {len(self.bots)} bots: {', '.join(self.bots)}")
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
        velas = self.broker.velas(bot.cfg.par, bot.cfg.temporalidad, max(200, bot.estrategia.velas_minimas + 50))
        if velas.empty:
            return
        ultima = velas.index[-1].to_pydatetime()
        bot.proxima_revision = ultima + 2 * dur + timedelta(seconds=3)  # 3 s después de que cierre la siguiente
        bot.velas = bot.estrategia.preparar(velas)
        if bot.ultima_vela is not None and ultima <= bot.ultima_vela:
            return
        primera_vez = bot.ultima_vela is None
        bot.ultima_vela = ultima
        if len(velas) < bot.estrategia.velas_minimas:
            return
        if primera_vez:
            self.db.guardar_evento(ahora, "info", f"empieza a operar {bot.cfg.par} en velas de {bot.cfg.temporalidad}",
                                   bot.cfg.nombre)
        for i in bot.estrategia.en_vela(bot.velas, bot.cartera, ultima + dur):
            self._intentar(bot, i, self.precios[bot.cfg.par], ahora)

    def _intentar(self, bot: BotVivo, intencion: Intencion, precio: float, ahora: datetime) -> None:
        ajustada, motivo = self.master.ajustar(intencion, ahora)
        if ajustada is None:
            self._registrar_rechazo(bot, intencion, motivo, ahora)
            return
        decision = self.sup.revisar(ajustada, bot.cartera, precio, ahora)
        if not decision.aprobada:
            self._registrar_rechazo(bot, intencion, f"Supervisor: {decision.motivo}", ahora)
            return
        try:
            ej = self.broker.ejecutar(decision.intencion, bot.cartera, ahora)
        except Exception as e:
            self._error(ahora, f"{bot.cfg.nombre}: no se pudo ejecutar la {intencion.lado}: {e}", bot.cfg.nombre)
            return
        bot.estrategia.en_ejecucion(ej)
        self.master.en_ejecucion(ej)
        self.db.guardar_ejecucion(ej)
        self.db.guardar_bot(bot.cartera, bot.estrategia.exportar_estado(), bot.ultima_vela)
        log.info("%s %s %.6f %s a %.2f · %s", ej.bot, ej.lado, ej.cantidad, ej.par, ej.precio, ej.motivo)

    def _registrar_rechazo(self, bot: BotVivo, intencion: Intencion, motivo: str, ahora: datetime) -> None:
        clave = (bot.cfg.nombre, motivo.split(" (")[0])
        anterior = self._rechazos_vistos.get(clave)
        if anterior and ahora - anterior < timedelta(minutes=30):
            return
        self._rechazos_vistos[clave] = ahora
        self.db.guardar_evento(ahora, "rechazo", f"{intencion.lado} rechazada · {motivo}", bot.cfg.nombre)

    # ================= comandos manuales (opcionales) =================
    def _procesar_comandos(self, ahora: datetime) -> None:
        for c in self.db.tomar_comandos():
            accion, bot = c["accion"], c["bot"]
            if bot and bot not in self.bots:
                continue
            if accion == "pausar":
                self.sup.pausar_bot(ahora, bot) if bot else self.sup.pausar(ahora, "pausa manual desde el panel")
            elif accion == "reanudar":
                self.sup.reanudar_bot(ahora, bot) if bot else self.sup.reanudar(ahora)
            elif accion == "detener_todo":
                self.sup.detener_todo(ahora, "freno de emergencia desde el panel")
        self._guardar_eventos()

    # ================= registro =================
    def _guardar_eventos(self) -> None:
        for e in self.sup.eventos[self._eventos_sup:]:
            self.db.guardar_evento(e.tiempo, e.tipo, f"Supervisor: {e.mensaje}")
        self._eventos_sup = len(self.sup.eventos)
        for f in self.master.tomar_feedback():
            self.db.guardar_evento(f.tiempo, f"master_{f.nivel}", f.mensaje, f.bot)

    def _error(self, ahora: datetime, texto: str, bot: str | None = None) -> None:
        log.exception(texto) if sys.exc_info()[0] else log.error(texto)
        clave = texto[:80]
        if clave not in self._errores_vistos or ahora - self._errores_vistos[clave] > timedelta(minutes=10):
            self._errores_vistos[clave] = ahora
            self.db.guardar_evento(ahora, "error", texto, bot)

    def valor_total(self) -> float:
        return sum(b.cartera.valor(self.precios.get(b.cfg.par, 0.0)) for b in self.bots.values())

    def foto(self, ahora: datetime) -> dict:
        """Todo lo que el panel necesita para dibujar el estado en vivo."""
        bots = []
        for n, b in self.bots.items():
            precio = self.precios.get(b.cfg.par, 0.0)
            grafica = []
            if b.velas is not None:
                v = b.velas.tail(PUNTOS_GRAFICA)
                grafica = [[int(t.timestamp() * 1000), round(float(c), 6)] for t, c in zip(v.index, v["close"])]
            bots.append({
                "nombre": n, "estrategia": b.cfg.estrategia, "descripcion": b.estrategia.DESCRIPCION,
                "par": b.cfg.par, "temporalidad": b.cfg.temporalidad, "precio": precio,
                "presupuesto": b.cartera.presupuesto, "efectivo": b.cartera.efectivo, "cantidad": b.cartera.cantidad,
                "precio_promedio": b.cartera.precio_promedio, "valor": b.cartera.valor(precio),
                "pausado": n in self.sup.bots_pausados, "analisis": b.analisis, "master": self.master.resumen(n),
                "proxima_revision": b.proxima_revision.isoformat() if b.proxima_revision.year > 1 else None,
                "grafica": grafica, "parametros": b.estrategia.p,
            })
        return {
            "latido": ahora.isoformat(), "modo": self.broker.modo,
            "supervisor": {"estado": self.sup.estado, "motivo": self.sup.motivo_estado,
                           "valor_maximo": self.sup.valor_maximo, "valor_inicio_dia": self.sup.valor_inicio_dia,
                           "limites": {"perdida_diaria_max_pct": self.config.riesgo.perdida_diaria_max_pct,
                                       "caida_maxima_pct": self.config.riesgo.caida_maxima_pct}},
            "mercado": {p: {"precio": self.precios.get(p), "bloqueo": self.master.bloqueos.get(p, (None, None))[1]}
                        for p in self.pares},
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
    ap.add_argument("--config", default=None, help="por defecto config/testnet.yaml (o config/real.yaml en modo real)")
    ap.add_argument("--modo", choices=["papel", "testnet", "real"], help="por defecto, MODO del archivo .env")
    ap.add_argument("--intervalo", type=int, default=5, help="segundos entre revisiones")
    ap.add_argument("--sin-panel", action="store_true")
    ap.add_argument("--puerto", type=int, default=8000)
    ap.add_argument("--confirmo-dinero-real", action="store_true",
                    help="obligatorio en modo real (se pide una sola vez al arrancar, nunca por operación)")
    args = ap.parse_args()

    (RAIZ / "logs").mkdir(exist_ok=True)
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s: %(message)s",
                        handlers=[logging.StreamHandler(), logging.FileHandler(RAIZ / "logs" / "motor.log", encoding="utf-8")])
    for ruidoso in ("urllib3", "ccxt", "httpx"):
        logging.getLogger(ruidoso).setLevel(logging.WARNING)

    secretos = cargar_secretos()
    modo = args.modo or secretos["modo"]
    ruta = args.config or ("config/real.yaml" if modo == "real" else "config/testnet.yaml")
    if modo == "real" and not args.confirmo_dinero_real:
        raise SystemExit("Modo REAL: agrega --confirmo-dinero-real para operar con dinero de verdad.")
    if modo != "real" and "real" in ruta:
        raise SystemExit("config/real.yaml solo se usa en modo real.")

    config = cargar_config(ruta)
    db = Almacen(RAIZ / "data" / f"bots_{modo}.sqlite")
    motor = Motor(config, crear_broker(modo, config, secretos), db)

    if not args.sin_panel:
        from .panel import iniciar_panel
        threading.Thread(target=iniciar_panel, args=(db, args.puerto), daemon=True).start()
        log.info("Panel en http://localhost:%d", args.puerto)
    log.info("Modo %s · %d bots en paralelo: %s", modo.upper(), len(motor.bots), ", ".join(motor.bots))
    try:
        motor.correr(args.intervalo)
    except KeyboardInterrupt:
        db.guardar_evento(datetime.now(timezone.utc), "fin", "motor apagado manualmente")
        log.info("Apagado.")


if __name__ == "__main__":
    main()
