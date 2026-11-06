"""El Escáner: revisa TODOS los mercados de Binance cada minuto, los filtra y los califica.

Los bots "cazadores" (par: auto) toman de aquí sus candidatos en lugar de operar un par fijo.
Los datos vienen del mercado real (datos públicos de Binance). En Testnet solo se consideran los pares
que también existen en el Testnet.
"""
from __future__ import annotations

from dataclasses import dataclass, field, fields
from datetime import datetime

import requests

URL_24H = "https://data-api.binance.vision/api/v3/ticker/24hr"
ESTABLES = {"USDC", "FDUSD", "TUSD", "USDP", "DAI", "BUSD", "USD1", "RLUSD", "PYUSD", "USDE", "EUR", "EURI",
            "AEUR", "XUSD", "BFUSD", "U", "UST", "PAXG", "WBTC", "WBETH", "BNSOL", "XAUT"}
CRIPTO_CON_B = {"SHIB", "ARB", "BNB", "ORB", "SNB", "MOB", "SXB", "COB"}  # monedas reales que terminan en "B"


def es_accion_tokenizada(base: str) -> bool:
    """Binance lista acciones y ETFs tokenizados con una B al final (AAPLB, TSLAB, NVDAB, SPYB...)."""
    return len(base) >= 3 and base.endswith("B") and base not in CRIPTO_CON_B


@dataclass
class FiltrosEscaner:
    cotizada: str = "USDT"
    volumen_min_usdt: float = 15_000_000  # volumen de 24 h: que haya gente comprando y vendiendo
    rango_min_pct: float = 2.0  # que el precio se mueva lo suficiente para ganarle a las comisiones
    spread_max_pct: float = 0.15  # diferencia entre compra y venta
    max_candidatos: int = 30
    cada_seg: float = 60
    excluir: list[str] = field(default_factory=list)  # monedas extra a ignorar
    excluir_acciones: bool = True  # ignorar acciones/ETFs tokenizados (AAPLB, NVDAB...): no son cripto

    @classmethod
    def desde(cls, d: dict | None) -> "FiltrosEscaner":
        d = d or {}
        malos = set(d) - {f.name for f in fields(cls)}
        if malos:
            raise ValueError(f"Filtros del escáner desconocidos: {sorted(malos)}")
        return cls(**d)


@dataclass
class Candidato:
    par: str
    precio: float
    cambio_pct: float  # cambio en 24 h
    volumen_usdt: float
    rango_pct: float  # (máximo - mínimo) / mínimo en 24 h
    posicion_rango: float  # 0 = en el mínimo del día, 1 = en el máximo
    spread_pct: float
    filtros: list[tuple[str, float, float, bool]]  # (nombre, valor, umbral, pasa)
    puntajes: dict[str, float]

    @property
    def aprobado(self) -> bool:
        return all(f[3] for f in self.filtros)

    def a_dict(self) -> dict:
        return {"par": self.par, "precio": self.precio, "cambio_pct": round(self.cambio_pct, 2),
                "volumen_usdt": round(self.volumen_usdt), "rango_pct": round(self.rango_pct, 2),
                "posicion_rango": round(self.posicion_rango, 2), "spread_pct": round(self.spread_pct, 3),
                "aprobado": self.aprobado, "puntajes": {k: round(v) for k, v in self.puntajes.items()},
                "filtros": [{"nombre": n, "valor": round(v, 3), "umbral": u, "ok": ok} for n, v, u, ok in self.filtros]}


def _rango_0_100(x: float, bajo: float, alto: float) -> float:
    return max(0.0, min(100.0, (x - bajo) / (alto - bajo) * 100))


def calificar(t: dict, f: FiltrosEscaner) -> Candidato | None:
    """Convierte un ticker de 24 h de Binance en un candidato con filtros y puntajes."""
    s = t["symbol"]
    if not s.endswith(f.cotizada):
        return None
    base = s[: -len(f.cotizada)]
    if not base or base in ESTABLES or base in set(f.excluir) or base.endswith(("UP", "DOWN", "BULL", "BEAR")):
        return None
    if f.excluir_acciones and es_accion_tokenizada(base):
        return None
    precio, alto, bajo = float(t["lastPrice"]), float(t["highPrice"]), float(t["lowPrice"])
    volumen = float(t["quoteVolume"])
    if precio <= 0 or bajo <= 0 or volumen <= 0:
        return None
    compra, venta = float(t.get("bidPrice") or 0), float(t.get("askPrice") or 0)
    spread = (venta / compra - 1) * 100 if compra > 0 and venta > 0 else 0.0
    rango = (alto / bajo - 1) * 100
    pos = (precio - bajo) / (alto - bajo) if alto > bajo else 0.5
    cambio = float(t["priceChangePercent"])
    filtros = [
        ("volumen_24h_usdt", volumen, f.volumen_min_usdt, volumen >= f.volumen_min_usdt),
        ("rango_24h_pct", rango, f.rango_min_pct, rango >= f.rango_min_pct),
        ("spread_pct", spread, f.spread_max_pct, spread <= f.spread_max_pct),
    ]
    liquidez = _rango_0_100(volumen, f.volumen_min_usdt, f.volumen_min_usdt * 20)
    puntajes = {
        # impulso: sube en el día y cerca de su máximo
        "impulso": 0.45 * _rango_0_100(cambio, 0, 12) + 0.35 * pos * 100 + 0.2 * liquidez,
        # caída: bajó en el día y está cerca de su mínimo (para reversión)
        "caida": 0.45 * _rango_0_100(-cambio, 0, 12) + 0.35 * (1 - pos) * 100 + 0.2 * liquidez,
        # volátil: se mueve mucho y hay mucho volumen
        "volatil": 0.6 * _rango_0_100(rango, f.rango_min_pct, 15) + 0.4 * liquidez,
    }
    puntajes["general"] = max(puntajes["impulso"], puntajes["caida"], puntajes["volatil"])
    return Candidato(f"{base}/{f.cotizada}", precio, cambio, volumen, rango, pos, spread, filtros, puntajes)


class Escaner:
    def __init__(self, filtros: FiltrosEscaner | None = None, sesion=None):
        self.f = filtros or FiltrosEscaner()
        self.sesion = sesion or requests.Session()
        self.disponibles: set[str] | None = None  # pares que existen en el exchange donde se opera (None = todos)
        self.candidatos: list[Candidato] = []
        self.escaneados = 0
        self.ultimo: datetime | None = None

    def toca(self, ahora: datetime) -> bool:
        return self.ultimo is None or (ahora - self.ultimo).total_seconds() >= self.f.cada_seg

    def escanear(self, ahora: datetime) -> list[Candidato]:
        r = self.sesion.get(URL_24H, timeout=30)
        r.raise_for_status()
        todos = [c for c in (calificar(t, self.f) for t in r.json()) if c]
        if self.disponibles is not None:
            todos = [c for c in todos if c.par in self.disponibles]
        self.escaneados = len(todos)
        todos.sort(key=lambda c: (c.aprobado, c.puntajes["general"]), reverse=True)
        self.candidatos = todos[: self.f.max_candidatos]
        self.ultimo = ahora
        return self.candidatos

    def mejores(self, tipo: str, n: int = 4) -> list[Candidato]:
        aprobados = [c for c in self.candidatos if c.aprobado]
        return sorted(aprobados, key=lambda c: c.puntajes.get(tipo, 0), reverse=True)[:n]

    @property
    def aprobados(self) -> list[str]:
        return [c.par for c in self.candidatos if c.aprobado]

    def foto(self) -> dict:
        return {"escaneados": self.escaneados, "aprobados": len(self.aprobados),
                "ultimo": self.ultimo.isoformat() if self.ultimo else None,
                "filtros": {"volumen_min_usdt": self.f.volumen_min_usdt, "rango_min_pct": self.f.rango_min_pct,
                            "spread_max_pct": self.f.spread_max_pct},
                "candidatos": [c.a_dict() for c in self.candidatos]}
