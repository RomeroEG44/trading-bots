"""Carga la configuración (archivos .yaml en config/) y los secretos (.env)."""
from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path

import yaml
from dotenv import load_dotenv

from .supervisor import LimitesRiesgo

RAIZ = Path(__file__).resolve().parent.parent


@dataclass
class BotConfig:
    nombre: str
    estrategia: str
    par: str
    temporalidad: str
    presupuesto_usdt: float
    parametros: dict


@dataclass
class Config:
    nombre: str
    comision_pct: float
    deslizamiento_pct: float
    riesgo: LimitesRiesgo
    bots: list[BotConfig]


def cargar_config(ruta: str | Path) -> Config:
    ruta = Path(ruta)
    if not ruta.is_absolute():
        ruta = RAIZ / ruta
    d = yaml.safe_load(ruta.read_text(encoding="utf-8"))
    bots = [BotConfig(
        nombre=b["nombre"], estrategia=b["estrategia"], par=b["par"],
        temporalidad=b.get("temporalidad", "1h"), presupuesto_usdt=float(b["presupuesto_usdt"]),
        parametros=b.get("parametros") or {},
    ) for b in d["bots"]]
    r = d.get("riesgo", {})
    riesgo = LimitesRiesgo(pares_permitidos=r.get("pares_permitidos") or sorted({b.par for b in bots}),
                           **{k: v for k, v in r.items() if k != "pares_permitidos"})
    return Config(
        nombre=ruta.stem, comision_pct=float(d.get("comision_pct", 0.1)),
        deslizamiento_pct=float(d.get("deslizamiento_pct", 0.05)), riesgo=riesgo, bots=bots,
    )


def cargar_secretos() -> dict:
    """Lee el archivo .env (que nunca se sube a GitHub)."""
    load_dotenv(RAIZ / ".env")
    return {
        "modo": os.getenv("MODO", "testnet").strip().lower(),
        "api_key": os.getenv("BINANCE_API_KEY", "").strip(),
        "api_secret": os.getenv("BINANCE_API_SECRET", "").strip(),
        "telegram_token": os.getenv("TELEGRAM_BOT_TOKEN", "").strip(),
        "telegram_chat_id": os.getenv("TELEGRAM_CHAT_ID", "").strip(),
    }
