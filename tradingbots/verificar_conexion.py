"""Prueba la conexión con Binance SIN operar (solo lectura).

Uso (en tu computadora, con el archivo .env lleno):
    python -m tradingbots.verificar_conexion
"""
from __future__ import annotations

import sys

import ccxt
import requests

from .config import cargar_secretos


def crear_exchange(modo: str, api_key: str, api_secret: str) -> ccxt.binance:
    ex = ccxt.binance({
        "apiKey": api_key, "secret": api_secret, "enableRateLimit": True,
        "options": {"defaultType": "spot"},
    })
    if modo == "testnet":
        ex.set_sandbox_mode(True)
    elif modo != "real":
        raise ValueError(f"MODO debe ser 'testnet' o 'real', no '{modo}'")
    return ex


def main() -> int:
    s = cargar_secretos()
    print(f"Modo: {s['modo'].upper()}")

    print("\n1) Precio público de BTC (no necesita claves)...")
    r = requests.get("https://data-api.binance.vision/api/v3/ticker/price", params={"symbol": "BTCUSDT"}, timeout=15)
    print(f"   OK · BTC/USDT = {float(r.json()['price']):,.2f}")

    if not s["api_key"] or not s["api_secret"]:
        print("\n2) No hay claves en el archivo .env: llena BINANCE_API_KEY y BINANCE_API_SECRET.")
        return 1

    print(f"\n2) Conectando a tu cuenta de Binance ({s['modo']}) en modo solo lectura...")
    ex = crear_exchange(s["modo"], s["api_key"], s["api_secret"])
    try:
        saldo = ex.fetch_balance()
    except ccxt.AuthenticationError:
        print("   ✗ Binance rechazó las claves. Revisa que estén bien copiadas y que sean del "
              f"{'Testnet' if s['modo'] == 'testnet' else 'Binance real'}.")
        return 1
    except ccxt.ExchangeNotAvailable as e:
        if "restricted location" in str(e):
            print("   ✗ Binance bloquea la conexión desde esta ubicación/servidor.")
        else:
            print(f"   ✗ Binance no está disponible: {e}")
        return 1
    except ccxt.NetworkError as e:
        print(f"   ✗ Problema de red: {e}")
        return 1

    con_saldo = {m: v for m, v in saldo["total"].items() if v}
    print("   OK · Conexión exitosa. Saldos:")
    for moneda, cantidad in sorted(con_saldo.items(), key=lambda kv: -kv[1])[:15]:
        print(f"      {moneda:>6}: {cantidad:,.8f}")
    if not con_saldo:
        print("      (cuenta sin saldo)")

    try:
        permisos = ex.sapi_get_account_apirestrictions() if s["modo"] == "real" else None
        if permisos and permisos.get("enableWithdrawals"):
            print("\n   ⚠️  PELIGRO: tu clave tiene permiso de RETIRO. Desactívalo en Binance > Gestión de API.")
    except Exception:
        pass
    print("\nTodo listo ✔")
    return 0


if __name__ == "__main__":
    sys.exit(main())
