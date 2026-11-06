"""Descarga velas históricas de Binance (datos públicos, sin claves) y las guarda en data/."""
from __future__ import annotations

from datetime import datetime, timezone

import pandas as pd
import requests

from .config import RAIZ

URL_DATOS = "https://data-api.binance.vision/api/v3/klines"
DURACION = {"1m": 60, "5m": 300, "15m": 900, "1h": 3600, "4h": 14400, "1d": 86400}


def simbolo(par: str) -> str:
    return par.replace("/", "")


def a_ms(t: datetime) -> int:
    return int(t.timestamp() * 1000)


def descargar_velas(par: str, temporalidad: str, inicio: datetime, fin: datetime) -> pd.DataFrame:
    """Devuelve un DataFrame indexado por la hora de APERTURA (UTC) con open/high/low/close/volume.
    Usa un caché en data/ para no descargar dos veces lo mismo."""
    carpeta = RAIZ / "data"
    carpeta.mkdir(exist_ok=True)
    cache = carpeta / f"{simbolo(par)}_{temporalidad}.csv"
    df = pd.read_csv(cache, index_col=0, parse_dates=True) if cache.exists() else pd.DataFrame()

    paso_ms = DURACION[temporalidad] * 1000
    if not df.empty:
        df.index = pd.to_datetime(df.index, utc=True)
    fin_efectivo = min(fin, datetime.now(timezone.utc) - pd.Timedelta(seconds=DURACION[temporalidad]))
    esperadas = max(0, int((fin_efectivo - inicio).total_seconds() // DURACION[temporalidad]))
    en_cache = 0 if df.empty else int(((df.index >= inicio) & (df.index < fin)).sum())
    if en_cache < esperadas * 0.99:  # faltan datos (o hay huecos): se descarga el rango completo
        filas, desde = [], a_ms(inicio)
        sesion = requests.Session()
        while desde < a_ms(fin):
            r = sesion.get(URL_DATOS, params={
                "symbol": simbolo(par), "interval": temporalidad, "startTime": desde, "endTime": a_ms(fin) - 1, "limit": 1000,
            }, timeout=30)
            r.raise_for_status()
            lote = r.json()
            if not lote:
                break
            filas += lote
            desde = lote[-1][0] + paso_ms
        if filas:
            nuevo = pd.DataFrame([f[:6] for f in filas], columns=["t", "open", "high", "low", "close", "volume"])
            nuevo.index = pd.to_datetime(nuevo.pop("t"), unit="ms", utc=True)
            nuevo = nuevo.astype(float)
            df = pd.concat([df, nuevo]) if not df.empty else nuevo
            df = df[~df.index.duplicated(keep="last")].sort_index()
            df.to_csv(cache)

    df.index = pd.to_datetime(df.index, utc=True)
    ultima_cerrada = datetime.now(timezone.utc) - pd.Timedelta(seconds=DURACION[temporalidad])
    return df[(df.index >= inicio) & (df.index < fin) & (df.index <= ultima_cerrada)]
