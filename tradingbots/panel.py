"""Panel web en tiempo real. Solo accesible desde tu propia computadora (localhost).

Normalmente lo arranca el motor. Para abrirlo solo:  python -m tradingbots.panel --modo testnet
"""
from __future__ import annotations

import argparse
import math
from datetime import datetime, timedelta, timezone
from pathlib import Path

from fastapi import FastAPI, HTTPException
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

from .almacen import Almacen
from .config import RAIZ
from .metricas import metricas_bot

AQUI = Path(__file__).parent
ACCIONES = {"pausar", "reanudar", "detener_todo"}


class Comando(BaseModel):
    accion: str
    bot: str | None = None


def _json_seguro(d):
    """JSON no acepta infinito: se manda como null + bandera."""
    return {k: (None if isinstance(v, float) and math.isinf(v) else v) for k, v in d.items()}


def operaciones_cerradas(ejecuciones: list[dict], limite: int = 40) -> list[dict]:
    """Cada venta con su % de ganancia y cuánto tiempo se mantuvo la posición."""
    abiertas: dict[tuple[str, str], str] = {}
    cerradas = []
    for e in ejecuciones:  # en orden cronológico
        clave = (e["bot"], e["par"])
        if e["lado"] == "compra":
            abiertas.setdefault(clave, e["tiempo"])
            continue
        inicio = abiertas.get(clave)
        g = e["ganancia_usdt"] or 0.0
        costo = (e["monto_usdt"] or 0) - (e["comision_usdt"] or 0) - g
        segundos = (datetime.fromisoformat(e["tiempo"]) - datetime.fromisoformat(inicio)).total_seconds() if inicio else None
        cerradas.append({"tiempo": e["tiempo"], "bot": e["bot"], "par": e["par"], "ganancia_usdt": g,
                         "pct": g / costo * 100 if costo > 0 else None, "segundos": segundos, "motivo": e["motivo"]})
        abiertas.pop(clave, None)  # simplificación: una venta cierra el ciclo
    return list(reversed(cerradas))[:limite]


def crear_app(db: Almacen) -> FastAPI:
    app = FastAPI(title="Panel de bots", docs_url=None, redoc_url=None)
    app.mount("/static", StaticFiles(directory=AQUI / "static"), name="static")

    @app.get("/", response_class=HTMLResponse)
    def inicio():
        return (AQUI / "panel.html").read_text(encoding="utf-8")

    @app.get("/api/estado")
    def estado(horas: int = 24):
        ahora = datetime.now(timezone.utc)
        desde = ahora - timedelta(hours=max(1, min(horas, 24 * 90)))
        por_bot = db.ejecuciones_por_bot()
        curvas = db.curvas_por_bot(desde)
        en_vivo = db.obtener("en_vivo")
        nombres = [b["nombre"] for b in en_vivo["bots"]] if en_vivo else list(por_bot)
        metricas = {}
        for n in nombres:
            m = metricas_bot(por_bot.get(n, []), curvas.get(n))
            m["factor_infinito"] = m["factor_beneficio"] == float("inf")
            metricas[n] = _json_seguro(m)
        global_ = metricas_bot([e for lista in por_bot.values() for e in lista])
        mini = {n: v[-90:] for n, v in curvas.items()}
        global_["factor_infinito"] = global_["factor_beneficio"] == float("inf")
        return {
            "ahora": ahora.isoformat(),
            "en_vivo": en_vivo,
            "metricas": metricas,
            "global": _json_seguro(global_),
            "ejecuciones": db.ejecuciones(300),
            "eventos": db.eventos(150),
            "valores": db.valores(desde),
            "curvas_bots": mini,
            "cerradas": operaciones_cerradas(db.ejecuciones_completas()),
        }

    @app.post("/api/comando")
    def comando(c: Comando):
        if c.accion not in ACCIONES:
            raise HTTPException(400, f"acción no válida: {c.accion}")
        db.agregar_comando(c.accion, c.bot, "panel")
        return {"ok": True}

    return app


def iniciar_panel(db: Almacen, puerto: int = 8000) -> None:
    import uvicorn
    # 127.0.0.1 = solo esta computadora puede abrir el panel
    uvicorn.run(crear_app(db), host="127.0.0.1", port=puerto, log_level="warning")


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--modo", default="testnet", choices=["papel", "testnet", "real"])
    ap.add_argument("--puerto", type=int, default=8000)
    a = ap.parse_args()
    iniciar_panel(Almacen(RAIZ / "data" / f"bots_{a.modo}.sqlite"), a.puerto)


if __name__ == "__main__":
    main()
