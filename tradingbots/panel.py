"""Panel web para ver qué hacen los bots. Solo accesible desde tu propia computadora (localhost).

Normalmente lo arranca el motor. Para abrirlo solo:  python -m tradingbots.panel --modo testnet
"""
from __future__ import annotations

import argparse
from datetime import datetime, timedelta, timezone
from pathlib import Path

from fastapi import FastAPI, HTTPException
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

from .almacen import Almacen
from .config import RAIZ

HTML = (Path(__file__).parent / "panel.html").read_text(encoding="utf-8")
ACCIONES = {"pausar", "reanudar", "detener_todo"}


class Comando(BaseModel):
    accion: str
    bot: str | None = None


def crear_app(db: Almacen) -> FastAPI:
    app = FastAPI(title="Panel de bots", docs_url=None, redoc_url=None)
    app.mount("/static", StaticFiles(directory=Path(__file__).parent / "static"), name="static")

    @app.get("/", response_class=HTMLResponse)
    def inicio():
        return HTML

    @app.get("/api/estado")
    def estado(dias: int = 7):
        en_vivo = db.obtener("en_vivo")
        ejecuciones = db.ejecuciones(200)
        ganancia_realizada = sum(e["ganancia_usdt"] or 0 for e in ejecuciones if e["lado"] == "venta")
        return {
            "en_vivo": en_vivo,
            "ahora": datetime.now(timezone.utc).isoformat(),
            "ejecuciones": ejecuciones,
            "eventos": db.eventos(60),
            "valores": db.valores(datetime.now(timezone.utc) - timedelta(days=max(1, min(dias, 365)))),
            "ganancia_realizada": ganancia_realizada,
        }

    @app.post("/api/comando")
    def comando(c: Comando):
        if c.accion not in ACCIONES:
            raise HTTPException(400, f"acción no válida: {c.accion}")
        db.agregar_comando(c.accion, c.bot, "panel")
        return {"ok": True, "mensaje": "Comando enviado; el motor lo aplica en unos segundos."}

    return app


def iniciar_panel(db: Almacen, puerto: int = 8000) -> None:
    import uvicorn
    # 127.0.0.1 = solo esta computadora puede abrir el panel (nadie de afuera)
    uvicorn.run(crear_app(db), host="127.0.0.1", port=puerto, log_level="warning")


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--modo", default="testnet", choices=["papel", "testnet", "real"])
    ap.add_argument("--puerto", type=int, default=8000)
    a = ap.parse_args()
    iniciar_panel(Almacen(RAIZ / "data" / f"bots_{a.modo}.sqlite"), a.puerto)


if __name__ == "__main__":
    main()
