# Backtest · `real` · 2025-11-06 → 2026-11-06

Comisión 0.1% por operación · deslizamiento 0.05% · límites: pérdida diaria 3%, caída máxima 10% · tras una detención se simula que Edgar reanuda a los 7 días.

## Resumen

| Bot | Par | Capital | Valor final | Resultado | Peor caída | Si solo compraba y esperaba | Compras | Ventas | Comisiones |
|---|---|---:|---:|---:|---:|---:|---:|---:|---:|
| dca_btc | BTC/USDT | 20.00 | 15.57 | -22.2% | -40.6% | -26.5% | 3 | 0 | 0.02 |
| tendencia_eth | ETH/USDT | 20.00 | 19.82 | -0.9% | -5.8% | -34.9% | 3 | 3 | 0.11 |
| **Total** | | 40.00 | 35.39 | **-11.5%** | -19.3% | | | | |

## dca_btc

Precio BTC/USDT: 102,810.01 → 75,680.00.

- Órdenes rechazadas por el supervisor: presupuesto del bot agotado (48), compras bloqueadas: supervisor detenido (2).

Últimas 10 operaciones:

| Fecha (UTC) | Lado | Precio | USDT | Resultado | Motivo |
|---|---|---:|---:|---:|---|
| 2025-11-06 10:00 | compra | 102,861.42 | 5.00 |  | Compra programada (cada 168 h) |
| 2025-11-13 10:00 | compra | 102,878.41 | 5.00 |  | Compra programada (cada 168 h) |
| 2025-11-20 10:00 | compra | 91,995.97 | 10.00 |  | Compra x2: el precio cayó 10.6% desde la última compra |

## tendencia_eth

Precio ETH/USDT: 3,436.05 → 2,238.01.

- Ventas ganadoras: 1 de 3 (33%); ganancia realizada: -0.18 USDT.
- Motivos de venta: Stop-loss (2), Take-profit (1).

Últimas 10 operaciones:

| Fecha (UTC) | Lado | Precio | USDT | Resultado | Motivo |
|---|---|---:|---:|---:|---|
| 2026-03-14 00:00 | compra | 2,093.27 | 18.00 |  | Cruce alcista EMA9/EMA21 con RSI 52 |
| 2026-03-17 00:00 | venta | 2,217.75 | 19.05 | +1.03 | Take-profit: subió 6% desde la entrada 2,093.27 |
| 2026-04-08 00:00 | compra | 2,241.13 | 18.93 |  | Cruce alcista EMA9/EMA21 con RSI 61 |
| 2026-04-10 00:00 | venta | 2,172.81 | 18.33 | -0.61 | Stop-loss: bajó 3% desde la entrada 2,241.13 |
| 2026-07-06 00:00 | compra | 1,786.54 | 18.38 |  | Cruce alcista EMA9/EMA21 con RSI 57 |
| 2026-07-07 00:00 | venta | 1,732.08 | 17.80 | -0.60 | Stop-loss: bajó 3% desde la entrada 1,786.54 |

## Eventos del supervisor

- 2025-11-20 19:00 · **pausa** · pérdida de 3.1% en el día
- 2025-11-21 00:00 · **reanudacion** · nuevo día: se reanudan las compras
- 2026-01-31 19:00 · **detencion** · caída de 10.3% desde el máximo (40.18 → 36.05 USDT)
- 2026-02-08 00:00 · **reanudacion** · reanudado
- 2026-06-04 00:00 · **detencion** · caída de 10.1% desde el máximo (37.39 → 33.61 USDT)
- 2026-06-11 00:00 · **reanudacion** · reanudado
