"""Conexión con el mercado.

- BrokerPapel   -> precios y velas reales (datos públicos de Binance) con órdenes simuladas. Sin claves.
- BrokerBinance -> Binance Testnet o Binance real: velas, precios y órdenes salen de la MISMA bolsa,
                   para que las señales coincidan con los precios a los que se opera.
"""
from __future__ import annotations

import json
import logging
from datetime import datetime, timezone

import pandas as pd
import requests

from .datos import DURACION, URL_DATOS, simbolo
from .modelos import Cartera, Ejecucion, Intencion
from .simulador import Simulador

log = logging.getLogger(__name__)
URL_PRECIO = "https://data-api.binance.vision/api/v3/ticker/price"


class MercadoPublico:
    def __init__(self):
        self.sesion = requests.Session()

    def velas(self, par: str, temporalidad: str, limite: int = 300) -> pd.DataFrame:
        """Últimas velas CERRADAS (la vela que se está formando se descarta)."""
        r = self.sesion.get(URL_DATOS, params={"symbol": simbolo(par), "interval": temporalidad, "limit": limite},
                            timeout=20)
        r.raise_for_status()
        df = pd.DataFrame([f[:6] for f in r.json()], columns=["t", "open", "high", "low", "close", "volume"])
        df.index = pd.to_datetime(df.pop("t"), unit="ms", utc=True)
        df = df.astype(float)
        cierre = df.index + pd.Timedelta(seconds=DURACION[temporalidad])
        return df[cierre <= datetime.now(timezone.utc)]

    def precio(self, par: str) -> float:
        r = self.sesion.get(URL_PRECIO, params={"symbol": simbolo(par)}, timeout=15)
        r.raise_for_status()
        return float(r.json()["price"])

    def precios(self, pares: list[str]) -> dict[str, float]:
        """Todos los precios en una sola consulta."""
        por_simbolo = {simbolo(p): p for p in pares}
        r = self.sesion.get(URL_PRECIO, params={"symbols": json.dumps(sorted(por_simbolo), separators=(",", ":"))},
                            timeout=15)
        r.raise_for_status()
        return {por_simbolo[x["symbol"]]: float(x["price"]) for x in r.json()}


    def mercados(self) -> set[str] | None:
        return None  # en papel se puede "operar" cualquier par


class BrokerPapel(MercadoPublico):
    """Simula las órdenes con precios reales. Ideal para probar en cualquier computadora."""

    modo = "papel"

    def __init__(self, comision_pct: float, deslizamiento_pct: float):
        super().__init__()
        self.sim = Simulador(comision_pct, deslizamiento_pct)

    def ejecutar(self, intencion: Intencion, cartera: Cartera, ahora: datetime) -> Ejecucion:
        return self.sim.ejecutar(intencion, cartera, self.precio(intencion.par), ahora)


class BrokerBinance(MercadoPublico):
    """Envía órdenes de mercado reales a Binance (Testnet o real) usando ccxt."""

    def __init__(self, modo: str, api_key: str, api_secret: str, exchange=None):
        super().__init__()
        if modo not in ("testnet", "real"):
            raise ValueError("modo debe ser 'testnet' o 'real'")
        if exchange is None:
            from .verificar_conexion import crear_exchange
            exchange = crear_exchange(modo, api_key, api_secret)
        self.modo = modo
        self.ex = exchange
        self.ex.load_markets()

    def precio(self, par: str) -> float:
        return float(self.ex.fetch_ticker(par)["last"])

    def mercados(self) -> set[str]:
        return {s for s, m in self.ex.markets.items()
                if m.get("spot") and m.get("active", True) and m.get("quote") == "USDT"}

    def precios(self, pares: list[str]) -> dict[str, float]:
        t = self.ex.fetch_tickers(pares)
        return {p: float(t[p]["last"]) for p in pares}

    def velas(self, par: str, temporalidad: str, limite: int = 300) -> pd.DataFrame:
        filas = self.ex.fetch_ohlcv(par, temporalidad, limit=limite)
        df = pd.DataFrame([f[:6] for f in filas], columns=["t", "open", "high", "low", "close", "volume"])
        df.index = pd.to_datetime(df.pop("t"), unit="ms", utc=True)
        df = df.astype(float)
        cierre = df.index + pd.Timedelta(seconds=DURACION[temporalidad])
        return df[cierre <= datetime.now(timezone.utc)]

    def _comision_usdt(self, orden: dict, base: str, precio: float) -> tuple[float, float]:
        """Devuelve (comisión en USDT, comisión cobrada en la moneda base)."""
        usdt, en_base = 0.0, 0.0
        for f in orden.get("fees") or ([orden["fee"]] if orden.get("fee") else []):
            costo, moneda = float(f.get("cost") or 0), f.get("currency")
            if not costo:
                continue
            if moneda == base:
                en_base += costo
                usdt += costo * precio
            elif moneda == "USDT":
                usdt += costo
            else:  # p. ej. BNB
                try:
                    usdt += costo * float(self.ex.fetch_ticker(f"{moneda}/USDT")["last"])
                except Exception:
                    log.warning("No se pudo convertir la comisión en %s a USDT", moneda)
        return usdt, en_base

    def ejecutar(self, intencion: Intencion, cartera: Cartera, ahora: datetime) -> Ejecucion:
        par = intencion.par
        base, cotizada = par.split("/")
        saldo = self.ex.fetch_balance()

        if intencion.lado == "compra":
            libre = float(saldo.get(cotizada, {}).get("free") or 0)
            monto = float(intencion.monto_usdt)
            if libre < monto:
                raise RuntimeError(f"Saldo insuficiente en Binance: {libre:.2f} {cotizada} libres, se necesitan {monto:.2f}")
            orden = self.ex.create_market_buy_order_with_cost(par, float(self.ex.cost_to_precision(par, monto)))
        else:
            libre = float(saldo.get(base, {}).get("free") or 0)
            cantidad = min(float(intencion.cantidad), cartera.cantidad, libre)
            cantidad = float(self.ex.amount_to_precision(par, cantidad))
            if cantidad <= 0:
                raise RuntimeError(f"No hay {base} disponible para vender")
            orden = self.ex.create_market_sell_order(par, cantidad)

        llena = float(orden.get("filled") or 0)
        bruto = float(orden.get("cost") or 0)
        if llena <= 0:
            raise RuntimeError(f"Binance no llenó la orden ({orden.get('status')})")
        precio = float(orden.get("average") or bruto / llena)
        comision, comision_base = self._comision_usdt(orden, base, precio)

        if intencion.lado == "compra":
            recibido = llena - comision_base
            cartera.efectivo -= bruto
            cartera.cantidad += recibido
            cartera.costo += bruto + (comision - comision_base * precio)
            return Ejecucion(ahora, cartera.bot, par, "compra", precio, recibido, bruto, comision, intencion.motivo,
                             id_orden=str(orden.get("id")))

        neto = bruto - comision
        costo_vendido = cartera.costo * min(1.0, llena / cartera.cantidad)
        cartera.cantidad = max(0.0, cartera.cantidad - llena)
        cartera.costo -= costo_vendido
        cartera.efectivo += neto
        if cartera.cantidad * precio < 0.01:  # restos minúsculos ("polvo")
            cartera.cantidad, cartera.costo = 0.0, 0.0
        return Ejecucion(ahora, cartera.bot, par, "venta", precio, llena, bruto, comision, intencion.motivo,
                         ganancia_usdt=neto - costo_vendido, id_orden=str(orden.get("id")))
