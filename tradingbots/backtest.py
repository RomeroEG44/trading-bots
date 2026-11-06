"""Backtest: prueba los bots con datos históricos reales, con el supervisor activo.

Uso:
    python -m tradingbots.backtest                       # config/pruebas.yaml, últimos 2 años
    python -m tradingbots.backtest --config config/real.yaml --dias 365
"""
from __future__ import annotations

import argparse
from collections import Counter
from dataclasses import dataclass, field
from datetime import datetime, timedelta, timezone

import pandas as pd

from .config import RAIZ, Config, cargar_config
from .datos import DURACION, descargar_velas
from .estrategias import crear_estrategia
from .modelos import Cartera, Ejecucion
from .simulador import Simulador
from .master import Feedback, Master, ReglasMaster
from .metricas import metricas_bot
from .supervisor import Evento, Supervisor


@dataclass
class ResultadoBot:
    nombre: str
    estrategia: str
    par: str
    presupuesto: float
    valor_final: float
    caida_maxima_pct: float
    ejecuciones: list[Ejecucion]
    rechazos: Counter
    comprar_y_mantener_pct: float
    precio_inicio: float
    precio_fin: float

    @property
    def rendimiento_pct(self) -> float:
        return (self.valor_final / self.presupuesto - 1) * 100


@dataclass
class Resultado:
    config: Config
    inicio: datetime
    fin: datetime
    bots: list[ResultadoBot]
    eventos: list[Evento]
    curva: pd.Series = field(repr=False)
    reanudar_tras_dias: float | None = None
    feedback: list = field(default_factory=list)
    usar_master: bool = True

    @property
    def presupuesto(self) -> float:
        return sum(b.presupuesto for b in self.bots)

    @property
    def valor_final(self) -> float:
        return sum(b.valor_final for b in self.bots)


def caida_maxima(curva: pd.Series) -> float:
    return float(((curva.cummax() - curva) / curva.cummax()).max() * 100) if len(curva) else 0.0


def ejecutar_backtest(config: Config, inicio: datetime, fin: datetime,
                      reanudar_tras_dias: float | None = None, usar_master: bool = True) -> Resultado:
    """reanudar_tras_dias: simula que Edgar reanuda N días después de una detención (None = nunca)."""
    sim = Simulador(config.comision_pct, config.deslizamiento_pct)
    sup = Supervisor(config.riesgo)
    master = Master(ReglasMaster.desde(config.master), {b.nombre: b.master for b in config.bots if b.master}) if usar_master else None
    feedback: list = []
    bots = []
    for b in [b for b in config.bots if not b.auto]:  # los cazadores (par auto) solo corren en vivo
        estrategia = crear_estrategia(b.estrategia, b.nombre, b.par, b.parametros)
        velas = descargar_velas(b.par, b.temporalidad, inicio, fin)
        if velas.empty:
            raise RuntimeError(f"No hay datos para {b.par} {b.temporalidad}")
        bots.append({
            "cfg": b, "estrategia": estrategia, "cartera": Cartera(b.nombre, b.par, b.presupuesto_usdt),
            "velas": estrategia.preparar(velas), "duracion": timedelta(seconds=DURACION[b.temporalidad]),
            "ejecuciones": [], "rechazos": Counter(), "ultimo_precio": float(velas["close"].iloc[0]), "curva": {},
        })

    linea_tiempo = sorted(set().union(*(set(x["velas"].index) for x in bots)))
    posiciones = {x["cfg"].nombre: {t: i for i, t in enumerate(x["velas"].index)} for x in bots}
    curva = {}

    def intentar(x, intencion, ahora_bot):
        precio_ref = intencion.precio if intencion.precio is not None else x["ultimo_precio"]
        if master is not None:
            intencion, motivo = master.ajustar(intencion, ahora_bot)
            if intencion is None:
                x["rechazos"][motivo.split(" (")[0]] += 1
                return
        decision = sup.revisar(intencion, x["cartera"], precio_ref, ahora_bot)
        if not decision.aprobada:
            x["rechazos"]["Supervisor: " + decision.motivo.split(" (")[0]] += 1
            return
        ej = sim.ejecutar(decision.intencion, x["cartera"], x["ultimo_precio"], ahora_bot)
        x["estrategia"].en_ejecucion(ej)
        if master is not None:
            master.en_ejecucion(ej)
        x["ejecuciones"].append(ej)

    for t in linea_tiempo:
        ahora = None
        for x in bots:
            i = posiciones[x["cfg"].nombre].get(t)
            if i is None:
                continue
            ahora_bot = t + x["duracion"]  # la decisión se toma al CERRAR la vela
            ahora = max(ahora or ahora_bot, ahora_bot)
            ventana = x["velas"].iloc[: i + 1]
            x["ultimo_precio"] = float(ventana["close"].iloc[-1])
            if master is not None:
                master.registrar_precio(x["cfg"].par, ahora_bot, x["ultimo_precio"])
            if i + 1 < x["estrategia"].velas_minimas:
                continue
            for intencion in x["estrategia"].en_vela(ventana, x["cartera"], ahora_bot):
                intentar(x, intencion, ahora_bot)
            for intencion in x["estrategia"].en_precio(x["ultimo_precio"], x["cartera"]):
                intentar(x, intencion, ahora_bot)
            if master is not None:
                for intencion in master.revisar(ahora_bot, x["cfg"].nombre, x["cartera"], x["ultimo_precio"]):
                    intentar(x, intencion, ahora_bot)
        if ahora is None:
            continue
        total = 0.0
        for x in bots:
            v = x["cartera"].valor(x["ultimo_precio"])
            x["curva"][ahora] = v
            total += v
        curva[ahora] = total
        sup.actualizar_valor(ahora, total)
        if (reanudar_tras_dias is not None and sup.estado == "detenido"
                and ahora - sup.eventos[-1].tiempo >= timedelta(days=reanudar_tras_dias)):
            sup.reanudar(ahora)
        if master is not None:
            feedback += master.tomar_feedback()

    resultados = []
    for x in bots:
        b, v = x["cfg"], x["velas"]
        p0, p1 = float(v["close"].iloc[0]), float(v["close"].iloc[-1])
        resultados.append(ResultadoBot(
            nombre=b.nombre, estrategia=b.estrategia, par=b.par, presupuesto=b.presupuesto_usdt,
            valor_final=x["cartera"].valor(p1), caida_maxima_pct=caida_maxima(pd.Series(x["curva"])),
            ejecuciones=x["ejecuciones"], rechazos=x["rechazos"],
            comprar_y_mantener_pct=((1 - config.comision_pct / 100) * p1 / p0 - 1) * 100,
            precio_inicio=p0, precio_fin=p1,
        ))
    return Resultado(config, inicio, fin, resultados, sup.eventos, pd.Series(curva), reanudar_tras_dias,
                     feedback, usar_master)


# ---------------- reporte ----------------
def _usd(x: float) -> str:
    return f"{x:,.2f}"


def reporte_markdown(r: Resultado) -> str:
    L = [
        f"# Backtest · `{r.config.nombre}` · {r.inicio:%Y-%m-%d} → {r.fin:%Y-%m-%d}",
        "",
        f"Comisión {r.config.comision_pct}% por operación · deslizamiento {r.config.deslizamiento_pct}% · "
        f"límites: pérdida diaria {r.config.riesgo.perdida_diaria_max_pct}%, caída máxima {r.config.riesgo.caida_maxima_pct}%"
        + (f" · tras una detención se simula que Edgar reanuda a los {r.reanudar_tras_dias:g} días." if r.reanudar_tras_dias is not None else "."),
        "",
        "## Resumen",
        "",
        "| Bot | Par | Capital | Valor final | Resultado | Peor caída | Comprar y esperar | Ventas | Acierto | Factor | Comisiones |",
        "|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|",
    ]
    for b in r.bots:
        m = metricas_bot(b.ejecuciones)
        acierto = f"{m['tasa_acierto']:.0%}" if m["tasa_acierto"] is not None else "—"
        factor = "—" if m["factor_beneficio"] is None else ("∞" if m["factor_beneficio"] == float("inf") else f"{m['factor_beneficio']:.2f}")
        L.append(
            f"| {b.nombre} | {b.par} | {_usd(b.presupuesto)} | {_usd(b.valor_final)} | {b.rendimiento_pct:+.1f}% | "
            f"-{b.caida_maxima_pct:.1f}% | {b.comprar_y_mantener_pct:+.1f}% | {m['ventas']} | {acierto} | {factor} | "
            f"{_usd(m['comisiones'])} |"
        )
    total_pct = (r.valor_final / r.presupuesto - 1) * 100
    L += [f"| **Total** | | {_usd(r.presupuesto)} | {_usd(r.valor_final)} | **{total_pct:+.1f}%** | "
          f"-{caida_maxima(r.curva):.1f}% | | | | | |", "",
          f"Master: {'activo' if r.usar_master else 'desactivado'}"
          + (f" · {len(r.feedback)} intervenciones." if r.usar_master else "."), ""]

    for b in r.bots:
        L += [f"## {b.nombre}", "", f"Precio {b.par}: {_usd(b.precio_inicio)} → {_usd(b.precio_fin)}.", ""]
        ventas = [e for e in b.ejecuciones if e.lado == "venta"]
        if ventas:
            ganadoras = [e for e in ventas if (e.ganancia_usdt or 0) > 0]
            L.append(f"- Ventas ganadoras: {len(ganadoras)} de {len(ventas)} ({len(ganadoras) / len(ventas):.0%}); "
                     f"ganancia realizada: {_usd(sum(e.ganancia_usdt or 0 for e in ventas))} USDT.")
            motivos = Counter(e.motivo.split(":")[0] for e in ventas)
            L.append("- Motivos de venta: " + ", ".join(f"{m} ({n})" for m, n in motivos.most_common()) + ".")
        if b.rechazos:
            L.append("- Órdenes rechazadas por el supervisor: "
                     + ", ".join(f"{m} ({n})" for m, n in b.rechazos.most_common()) + ".")
        L += ["", "Últimas 10 operaciones:", "", "| Fecha (UTC) | Lado | Precio | USDT | Resultado | Motivo |",
              "|---|---|---:|---:|---:|---|"]
        for e in b.ejecuciones[-10:]:
            g = f"{e.ganancia_usdt:+.2f}" if e.ganancia_usdt is not None else ""
            L.append(f"| {e.tiempo:%Y-%m-%d %H:%M} | {e.lado} | {_usd(e.precio)} | {_usd(e.monto_usdt)} | {g} | {e.motivo} |")
        L.append("")

    if r.feedback:
        L += ["## Feedback del Master (últimos 25)", ""]
        L += [f"- {f.tiempo:%Y-%m-%d %H:%M} · {f.bot or 'mercado'} · {f.mensaje}" for f in r.feedback[-25:]]
        L.append("")
    L += ["## Eventos del supervisor", ""]
    L += [f"- {e.tiempo:%Y-%m-%d %H:%M} · **{e.tipo}** · {e.mensaje}" for e in r.eventos] or ["- Ninguno."]
    L.append("")
    return "\n".join(L)


def main() -> None:
    ap = argparse.ArgumentParser(description="Backtest de los bots")
    ap.add_argument("--config", default="config/pruebas.yaml")
    ap.add_argument("--dias", type=float, default=730)
    ap.add_argument("--fin", help="fecha final AAAA-MM-DD (por defecto: hoy)")
    ap.add_argument("--sin-master", action="store_true", help="correr sin el Master (para comparar)")
    ap.add_argument("--reanudar-tras-dias", type=float, default=7,
                    help="simula que Edgar reanuda N días después de una detención (por defecto 7)")
    args = ap.parse_args()

    fin = (datetime.fromisoformat(args.fin).replace(tzinfo=timezone.utc) if args.fin
           else datetime.now(timezone.utc).replace(minute=0, second=0, microsecond=0))
    inicio = fin - timedelta(days=args.dias)
    config = cargar_config(args.config)
    resultado = ejecutar_backtest(config, inicio, fin, args.reanudar_tras_dias, not args.sin_master)
    texto = reporte_markdown(resultado)

    carpeta = RAIZ / "reports"
    carpeta.mkdir(exist_ok=True)
    salida = carpeta / f"backtest_{config.nombre}_{args.dias:g}d{'_sin_master' if args.sin_master else ''}.md"
    salida.write_text(texto, encoding="utf-8")
    print(texto)
    print(f"\nReporte guardado en {salida.relative_to(RAIZ)}")


if __name__ == "__main__":
    main()
