"""Base de datos SQLite: todo lo que hacen los bots queda guardado aquí.

El motor escribe; el panel web lee y deja comandos (pausar, reanudar...) que el motor ejecuta.
"""
from __future__ import annotations

import json
import sqlite3
import threading
from dataclasses import asdict
from datetime import datetime, timezone
from pathlib import Path

from .modelos import Cartera, Ejecucion

ESQUEMA = """
CREATE TABLE IF NOT EXISTS ejecuciones (
    id INTEGER PRIMARY KEY, tiempo TEXT, bot TEXT, par TEXT, lado TEXT, precio REAL, cantidad REAL,
    monto_usdt REAL, comision_usdt REAL, ganancia_usdt REAL, motivo TEXT, id_orden TEXT);
CREATE TABLE IF NOT EXISTS eventos (id INTEGER PRIMARY KEY, tiempo TEXT, tipo TEXT, bot TEXT, mensaje TEXT);
CREATE TABLE IF NOT EXISTS valores (tiempo TEXT PRIMARY KEY, total REAL, detalle TEXT);
CREATE TABLE IF NOT EXISTS kv (clave TEXT PRIMARY KEY, valor TEXT);
CREATE TABLE IF NOT EXISTS comandos (
    id INTEGER PRIMARY KEY, tiempo TEXT, accion TEXT, bot TEXT, origen TEXT, procesado INTEGER DEFAULT 0);
CREATE TABLE IF NOT EXISTS bots (
    nombre TEXT PRIMARY KEY, par TEXT, presupuesto REAL, efectivo REAL, cantidad REAL, costo REAL,
    estado_estrategia TEXT, ultima_vela TEXT);
"""


def _iso(t: datetime) -> str:
    return t.astimezone(timezone.utc).isoformat(timespec="seconds")


class Almacen:
    def __init__(self, ruta: str | Path):
        Path(ruta).parent.mkdir(parents=True, exist_ok=True)
        self._con = sqlite3.connect(str(ruta), check_same_thread=False, timeout=10)
        self._con.row_factory = sqlite3.Row
        self._lock = threading.Lock()
        with self._lock:
            self._con.execute("PRAGMA journal_mode=WAL")
            self._con.executescript(ESQUEMA)
            self._con.commit()

    def _ejecutar(self, sql: str, params=()) -> sqlite3.Cursor:
        with self._lock:
            cur = self._con.execute(sql, params)
            self._con.commit()
            return cur

    def _filas(self, sql: str, params=()) -> list[dict]:
        with self._lock:
            return [dict(r) for r in self._con.execute(sql, params).fetchall()]

    # ----- operaciones -----
    def guardar_ejecucion(self, e: Ejecucion) -> None:
        d = asdict(e)
        d["tiempo"] = _iso(e.tiempo)
        self._ejecutar(
            "INSERT INTO ejecuciones (tiempo, bot, par, lado, precio, cantidad, monto_usdt, comision_usdt, ganancia_usdt,"
            " motivo, id_orden) VALUES (:tiempo, :bot, :par, :lado, :precio, :cantidad, :monto_usdt, :comision_usdt,"
            " :ganancia_usdt, :motivo, :id_orden)", d)

    def ejecuciones(self, limite: int = 100) -> list[dict]:
        return self._filas("SELECT * FROM ejecuciones ORDER BY id DESC LIMIT ?", (limite,))

    def ejecuciones_por_bot(self) -> dict[str, list[dict]]:
        res: dict[str, list[dict]] = {}
        for f in self._filas("SELECT bot, lado, monto_usdt, comision_usdt, ganancia_usdt FROM ejecuciones ORDER BY id"):
            res.setdefault(f["bot"], []).append(f)
        return res

    def ejecuciones_desde(self, desde: datetime) -> list[dict]:
        return self._filas("SELECT * FROM ejecuciones WHERE tiempo >= ? ORDER BY id", (_iso(desde),))

    # ----- eventos -----
    def guardar_evento(self, tiempo: datetime, tipo: str, mensaje: str, bot: str | None = None) -> None:
        self._ejecutar("INSERT INTO eventos (tiempo, tipo, bot, mensaje) VALUES (?, ?, ?, ?)",
                       (_iso(tiempo), tipo, bot, mensaje))

    def eventos(self, limite: int = 50) -> list[dict]:
        return self._filas("SELECT * FROM eventos ORDER BY id DESC LIMIT ?", (limite,))

    # ----- valor total en el tiempo -----
    def guardar_valor(self, tiempo: datetime, total: float, detalle: dict) -> None:
        self._ejecutar("INSERT OR REPLACE INTO valores VALUES (?, ?, ?)", (_iso(tiempo), total, json.dumps(detalle)))

    def valores(self, desde: datetime) -> list[dict]:
        return self._filas("SELECT tiempo, total FROM valores WHERE tiempo >= ? ORDER BY tiempo", (_iso(desde),))

    def ejecuciones_completas(self, limite: int = 2000) -> list[dict]:
        return list(reversed(self._filas("SELECT * FROM ejecuciones ORDER BY id DESC LIMIT ?", (limite,))))

    def curvas_por_bot(self, desde: datetime) -> dict[str, list[float]]:
        res: dict[str, list[float]] = {}
        for f in self._filas("SELECT detalle FROM valores WHERE tiempo >= ? ORDER BY tiempo", (_iso(desde),)):
            for bot, v in json.loads(f["detalle"] or "{}").items():
                res.setdefault(bot, []).append(v)
        return res

    # ----- clave/valor (estado del supervisor, foto en vivo para el panel) -----
    def poner(self, clave: str, valor) -> None:
        self._ejecutar("INSERT OR REPLACE INTO kv VALUES (?, ?)", (clave, json.dumps(valor)))

    def obtener(self, clave: str, defecto=None):
        filas = self._filas("SELECT valor FROM kv WHERE clave = ?", (clave,))
        return json.loads(filas[0]["valor"]) if filas else defecto

    # ----- comandos de Edgar -----
    def agregar_comando(self, accion: str, bot: str | None = None, origen: str = "panel") -> None:
        self._ejecutar("INSERT INTO comandos (tiempo, accion, bot, origen) VALUES (?, ?, ?, ?)",
                       (_iso(datetime.now(timezone.utc)), accion, bot, origen))

    def tomar_comandos(self) -> list[dict]:
        with self._lock:
            filas = [dict(r) for r in self._con.execute("SELECT * FROM comandos WHERE procesado = 0 ORDER BY id")]
            if filas:
                self._con.execute(f"UPDATE comandos SET procesado = 1 WHERE id IN ({','.join('?' * len(filas))})",
                                  [f["id"] for f in filas])
                self._con.commit()
            return filas

    # ----- carteras y memoria de cada bot -----
    def guardar_bot(self, cartera: Cartera, estado_estrategia: dict, ultima_vela: datetime | None) -> None:
        self._ejecutar(
            "INSERT OR REPLACE INTO bots VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
            (cartera.bot, cartera.par, cartera.presupuesto, cartera.efectivo, cartera.cantidad, cartera.costo,
             json.dumps(estado_estrategia), _iso(ultima_vela) if ultima_vela else None))

    def cargar_bot(self, nombre: str) -> tuple[Cartera, dict, datetime | None] | None:
        filas = self._filas("SELECT * FROM bots WHERE nombre = ?", (nombre,))
        if not filas:
            return None
        f = filas[0]
        c = Cartera(f["nombre"], f["par"], f["presupuesto"])
        c.efectivo, c.cantidad, c.costo = f["efectivo"], f["cantidad"], f["costo"]
        ultima = datetime.fromisoformat(f["ultima_vela"]) if f["ultima_vela"] else None
        return c, json.loads(f["estado_estrategia"] or "{}"), ultima
