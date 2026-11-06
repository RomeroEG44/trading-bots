"""Indicadores técnicos. Todos son 'causales': solo usan datos del pasado."""
import pandas as pd


def ema(serie: pd.Series, periodo: int) -> pd.Series:
    """Media móvil exponencial."""
    return serie.ewm(span=periodo, adjust=False).mean()


def rsi(cierre: pd.Series, periodo: int = 14) -> pd.Series:
    """RSI de Wilder (0-100). >70 suele considerarse sobrecompra, <30 sobreventa."""
    delta = cierre.diff()
    ganancia = delta.clip(lower=0)
    perdida = -delta.clip(upper=0)
    prom_g = ganancia.ewm(alpha=1 / periodo, adjust=False, min_periods=periodo).mean()
    prom_p = perdida.ewm(alpha=1 / periodo, adjust=False, min_periods=periodo).mean()
    rs = prom_g / prom_p
    return 100 - 100 / (1 + rs)
