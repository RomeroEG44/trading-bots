# Backtest · `pruebas` · 2024-11-06 → 2026-11-06

Comisión 0.1% por operación · deslizamiento 0.05% · límites: pérdida diaria 3%, caída máxima 10% · tras una detención se simula que Edgar reanuda a los 7 días.

## Resumen

| Bot | Par | Capital | Valor final | Resultado | Peor caída | Si solo compraba y esperaba | Compras | Ventas | Comisiones |
|---|---|---:|---:|---:|---:|---:|---:|---:|---:|
| dca_btc | BTC/USDT | 1,000.00 | 930.37 | -7.0% | -28.0% | +2.5% | 89 | 3 | 1.12 |
| tendencia_eth | ETH/USDT | 1,000.00 | 1,000.98 | +0.1% | -6.3% | -22.8% | 10 | 10 | 18.03 |
| **Total** | | 2,000.00 | 1,931.35 | **-3.4%** | -14.4% | | | | |

## dca_btc

Precio BTC/USDT: 73,756.34 → 75,680.00.

- Ventas ganadoras: 3 de 3 (100%); ganancia realizada: 21.62 USDT.
- Motivos de venta: Toma de ganancias (3).
- Órdenes rechazadas por el supervisor: venta menor al mínimo de Binance (2568), compras bloqueadas: supervisor detenido (1).

Últimas 10 operaciones:

| Fecha (UTC) | Lado | Precio | USDT | Resultado | Motivo |
|---|---|---:|---:|---:|---|
| 2026-09-02 19:00 | compra | 77,416.45 | 10.00 |  | Compra programada (cada 168 h) |
| 2026-09-09 19:00 | compra | 78,453.63 | 10.00 |  | Compra programada (cada 168 h) |
| 2026-09-16 19:00 | compra | 75,669.82 | 10.00 |  | Compra programada (cada 168 h) |
| 2026-09-23 19:00 | compra | 84,372.16 | 10.00 |  | Compra programada (cada 168 h) |
| 2026-09-30 19:00 | compra | 83,991.97 | 10.00 |  | Compra programada (cada 168 h) |
| 2026-10-07 19:00 | compra | 83,463.73 | 10.00 |  | Compra programada (cada 168 h) |
| 2026-10-14 19:00 | compra | 81,764.86 | 10.00 |  | Compra programada (cada 168 h) |
| 2026-10-21 19:00 | compra | 84,458.68 | 10.00 |  | Compra programada (cada 168 h) |
| 2026-10-28 19:00 | compra | 81,052.19 | 10.00 |  | Compra programada (cada 168 h) |
| 2026-11-04 19:00 | compra | 80,391.67 | 10.00 |  | Compra programada (cada 168 h) |

## tendencia_eth

Precio ETH/USDT: 2,895.47 → 2,238.01.

- Ventas ganadoras: 5 de 10 (50%); ganancia realizada: 0.98 USDT.
- Motivos de venta: Stop-loss (5), Trailing stop (3), Take-profit (2).

Últimas 10 operaciones:

| Fecha (UTC) | Lado | Precio | USDT | Resultado | Motivo |
|---|---|---:|---:|---:|---|
| 2025-12-10 00:00 | compra | 3,319.70 | 918.98 |  | Cruce alcista EMA9/EMA21 con RSI 58 |
| 2025-12-12 00:00 | venta | 3,218.50 | 890.07 | -29.80 | Stop-loss: bajó 3% desde la entrada 3,319.70 |
| 2026-01-03 00:00 | compra | 3,127.01 | 892.16 |  | Cruce alcista EMA9/EMA21 con RSI 59 |
| 2026-01-07 00:00 | venta | 3,198.75 | 911.71 | +18.64 | Trailing stop: retrocedió 2% desde el máximo 3,265.66 |
| 2026-03-14 00:00 | compra | 2,093.27 | 908.94 |  | Cruce alcista EMA9/EMA21 con RSI 52 |
| 2026-03-17 00:00 | venta | 2,217.75 | 962.03 | +52.13 | Take-profit: subió 6% desde la entrada 2,093.27 |
| 2026-04-08 00:00 | compra | 2,241.13 | 955.85 |  | Cruce alcista EMA9/EMA21 con RSI 61 |
| 2026-04-10 00:00 | venta | 2,172.81 | 925.79 | -30.99 | Stop-loss: bajó 3% desde la entrada 2,241.13 |
| 2026-07-06 00:00 | compra | 1,786.54 | 927.96 |  | Cruce alcista EMA9/EMA21 con RSI 57 |
| 2026-07-07 00:00 | venta | 1,732.08 | 898.77 | -30.09 | Stop-loss: bajó 3% desde la entrada 1,786.54 |

## Eventos del supervisor

- 2026-02-03 19:00 · **detencion** · caída de 10.0% desde el máximo (2111.24 → 1899.39 USDT)
- 2026-02-11 00:00 · **reanudacion** · reanudado
