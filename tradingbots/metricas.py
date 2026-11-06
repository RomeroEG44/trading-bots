"""Métricas de rendimiento de cada bot (para el panel y los reportes)."""
from __future__ import annotations


def _v(e, campo):
    return e[campo] if isinstance(e, dict) else getattr(e, campo)


def caida_maxima_pct(curva: list[float]) -> float:
    pico, peor = None, 0.0
    for v in curva:
        pico = v if pico is None or v > pico else pico
        if pico:
            peor = max(peor, (1 - v / pico) * 100)
    return peor


def metricas_bot(ejecuciones: list, curva: list[float] | None = None) -> dict:
    ventas = [e for e in ejecuciones if _v(e, "lado") == "venta"]
    g = [_v(e, "ganancia_usdt") or 0.0 for e in ventas]
    gan = [x for x in g if x > 0]
    per = [x for x in g if x < 0]
    return {
        "operaciones": len(ejecuciones),
        "compras": len(ejecuciones) - len(ventas),
        "ventas": len(ventas),
        "ganadoras": len(gan),
        "tasa_acierto": len(gan) / len(ventas) if ventas else None,
        "ganancia_realizada": sum(g),
        "factor_beneficio": (sum(gan) / -sum(per)) if per else (None if not gan else float("inf")),
        "ganancia_media": sum(gan) / len(gan) if gan else None,
        "perdida_media": sum(per) / len(per) if per else None,
        "mejor": max(g) if g else None,
        "peor": min(g) if g else None,
        "comisiones": sum(_v(e, "comision_usdt") or 0.0 for e in ejecuciones),
        "volumen": sum(_v(e, "monto_usdt") or 0.0 for e in ejecuciones),
        "caida_maxima_pct": caida_maxima_pct(curva) if curva else 0.0,
    }
