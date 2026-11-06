# Backtest · `testnet` · 2026-10-30 → 2026-11-06

Comisión 0.1% por operación · deslizamiento 0.05% · límites: pérdida diaria 3%, caída máxima 10% · tras una detención se simula que Edgar reanuda a los 7 días.

## Resumen

| Bot | Par | Capital | Valor final | Resultado | Peor caída | Comprar y esperar | Ventas | Acierto | Factor | Comisiones |
|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| tendencia_btc_1m | BTC/USDT | 400.00 | 285.29 | -28.7% | -28.7% | -1.5% | 220 | 5% | 0.05 | 74.87 |
| tendencia_eth_5m | ETH/USDT | 400.00 | 364.96 | -8.8% | -8.8% | -0.7% | 55 | 13% | 0.22 | 21.30 |
| reversion_btc_5m | BTC/USDT | 400.00 | 386.00 | -3.5% | -4.1% | -1.5% | 22 | 23% | 0.15 | 8.66 |
| ruptura_eth_15m | ETH/USDT | 400.00 | 394.62 | -1.3% | -2.3% | -0.6% | 9 | 33% | 0.52 | 3.59 |
| rejilla_btc | BTC/USDT | 400.00 | 387.01 | -3.2% | -4.7% | -1.5% | 27 | 56% | 2.92 | 3.00 |
| dca_eth_15m | ETH/USDT | 400.00 | 385.95 | -3.5% | -9.3% | -0.6% | 6 | 100% | ∞ | 2.35 |
| **Total** | | 2,400.00 | 2,203.82 | **-8.2%** | -8.2% | | | | | |

Master: desactivado.

## tendencia_btc_1m

Precio BTC/USDT: 76,970.00 → 75,882.00.

- Ventas ganadoras: 10 de 220 (5%); ganancia realizada: -114.71 USDT.
- Motivos de venta: Cruce bajista (204), Trailing stop (7), Take-profit (5), Stop-loss (4).
- Órdenes rechazadas por el supervisor: Supervisor: compras bloqueadas: supervisor pausado (9).

Últimas 10 operaciones:

| Fecha (UTC) | Lado | Precio | USDT | Resultado | Motivo |
|---|---|---:|---:|---:|---|
| 2026-11-06 16:26 | compra | 75,821.90 | 143.57 |  | Cruce alcista EMA9/EMA21 con RSI 59 |
| 2026-11-06 16:43 | venta | 75,674.14 | 143.14 | -0.57 | Cruce bajista: EMA rápida cruzó hacia abajo la lenta |
| 2026-11-06 16:50 | compra | 75,827.89 | 143.28 |  | Cruce alcista EMA9/EMA21 con RSI 54 |
| 2026-11-06 17:15 | venta | 75,921.65 | 143.32 | -0.11 | Trailing stop: retrocedió 0.25% desde el máximo 76,150.00 |
| 2026-11-06 18:00 | compra | 75,819.49 | 143.23 |  | Cruce alcista EMA9/EMA21 con RSI 59 |
| 2026-11-06 18:51 | venta | 75,802.21 | 143.05 | -0.32 | Cruce bajista: EMA rápida cruzó hacia abajo la lenta |
| 2026-11-06 19:42 | compra | 75,799.89 | 143.07 |  | Cruce alcista EMA9/EMA21 con RSI 54 |
| 2026-11-06 20:18 | venta | 75,807.92 | 142.94 | -0.27 | Cruce bajista: EMA rápida cruzó hacia abajo la lenta |
| 2026-11-06 20:34 | compra | 75,957.35 | 142.93 |  | Cruce alcista EMA9/EMA21 con RSI 63 |
| 2026-11-06 20:56 | venta | 75,803.66 | 142.50 | -0.57 | Cruce bajista: EMA rápida cruzó hacia abajo la lenta |

## tendencia_eth_5m

Precio ETH/USDT: 2,242.36 → 2,229.37.

- Ventas ganadoras: 7 de 55 (13%); ganancia realizada: -34.60 USDT.
- Motivos de venta: Cruce bajista (49), Trailing stop (3), Take-profit (3).
- Órdenes rechazadas por el supervisor: Supervisor: compras bloqueadas: supervisor pausado (1).

Últimas 10 operaciones:

| Fecha (UTC) | Lado | Precio | USDT | Resultado | Motivo |
|---|---|---:|---:|---:|---|
| 2026-11-06 11:15 | venta | 2,234.09 | 184.71 | -0.47 | Cruce bajista: EMA rápida cruzó hacia abajo la lenta |
| 2026-11-06 11:30 | compra | 2,242.11 | 184.76 |  | Cruce alcista EMA9/EMA21 con RSI 57 |
| 2026-11-06 13:00 | venta | 2,237.83 | 184.23 | -0.72 | Cruce bajista: EMA rápida cruzó hacia abajo la lenta |
| 2026-11-06 16:35 | compra | 2,234.89 | 184.40 |  | Cruce alcista EMA9/EMA21 con RSI 55 |
| 2026-11-06 16:45 | venta | 2,225.01 | 183.40 | -1.18 | Cruce bajista: EMA rápida cruzó hacia abajo la lenta |
| 2026-11-06 16:50 | compra | 2,232.59 | 183.81 |  | Cruce alcista EMA9/EMA21 con RSI 52 |
| 2026-11-06 17:40 | venta | 2,221.16 | 182.69 | -1.31 | Cruce bajista: EMA rápida cruzó hacia abajo la lenta |
| 2026-11-06 18:35 | compra | 2,234.56 | 183.16 |  | Cruce alcista EMA9/EMA21 con RSI 57 |
| 2026-11-06 19:35 | venta | 2,227.82 | 182.42 | -0.92 | Cruce bajista: EMA rápida cruzó hacia abajo la lenta |
| 2026-11-06 19:40 | compra | 2,232.53 | 182.70 |  | Cruce alcista EMA9/EMA21 con RSI 55 |

## reversion_btc_5m

Precio BTC/USDT: 76,954.00 → 75,882.00.

- Ventas ganadoras: 5 de 22 (23%); ganancia realizada: -14.00 USDT.
- Motivos de venta: Stop-loss (6), Volvió al promedio (77,223.21) (1), Volvió al promedio (77,555.18) (1), Volvió al promedio (77,920.92) (1), Volvió al promedio (77,828.78) (1), Volvió al promedio (77,848.69) (1), Volvió al promedio (78,142.53) (1), Volvió al promedio (77,936.88) (1), Volvió al promedio (77,313.19) (1), Volvió al promedio (76,966.65) (1), Volvió al promedio (76,962.95) (1), Volvió al promedio (76,715.12) (1), Volvió al promedio (76,401.82) (1), Volvió al promedio (78,346.18) (1), Volvió al promedio (75,684.78) (1), Volvió al promedio (75,795.35) (1), Volvió al promedio (75,682.87) (1).
- Órdenes rechazadas por el supervisor: Supervisor: compras bloqueadas: supervisor pausado (3).

Últimas 10 operaciones:

| Fecha (UTC) | Lado | Precio | USDT | Resultado | Motivo |
|---|---|---:|---:|---:|---|
| 2026-11-05 14:55 | compra | 78,633.30 | 194.33 |  | Sobreventa: precio 78,594.00 bajo la banda inferior 78,744.20, RSI 17 |
| 2026-11-05 15:05 | venta | 77,965.23 | 192.49 | -2.04 | Stop-loss: bajó 0.8% desde la entrada 78,633.30 |
| 2026-11-05 15:10 | compra | 77,328.86 | 193.32 |  | Sobreventa: precio 77,290.21 bajo la banda inferior 77,772.55, RSI 8 |
| 2026-11-05 15:25 | venta | 76,671.87 | 191.48 | -2.03 | Stop-loss: bajó 0.8% desde la entrada 77,328.86 |
| 2026-11-06 05:25 | compra | 75,525.31 | 192.30 |  | Sobreventa: precio 75,487.57 bajo la banda inferior 75,521.22, RSI 33 |
| 2026-11-06 05:40 | venta | 75,674.17 | 192.49 | -0.01 | Volvió al promedio (75,684.78) |
| 2026-11-06 14:10 | compra | 75,644.87 | 192.30 |  | Sobreventa: precio 75,607.07 bajo la banda inferior 75,641.64, RSI 30 |
| 2026-11-06 14:50 | venta | 75,821.65 | 192.56 | +0.06 | Volvió al promedio (75,795.35) |
| 2026-11-06 15:05 | compra | 75,137.56 | 192.33 |  | Sobreventa: precio 75,100.01 bajo la banda inferior 75,294.80, RSI 30 |
| 2026-11-06 15:15 | venta | 75,811.08 | 193.86 | +1.34 | Volvió al promedio (75,682.87) |

## ruptura_eth_15m

Precio ETH/USDT: 2,240.15 → 2,229.37.

- Ventas ganadoras: 3 de 9 (33%); ganancia realizada: -5.38 USDT.
- Motivos de venta: Stop-loss (4), Trailing stop (3), Perdió el mínimo de 10 velas (2,247.32) (1), Perdió el mínimo de 10 velas (2,266.88) (1).

Últimas 10 operaciones:

| Fecha (UTC) | Lado | Precio | USDT | Resultado | Motivo |
|---|---|---:|---:|---:|---|
| 2026-11-03 09:45 | compra | 2,269.05 | 199.27 |  | Rompió el máximo de 20 velas (2,267.27) |
| 2026-11-03 13:45 | venta | 2,293.33 | 201.20 | +1.73 | Trailing stop: retrocedió 0.6% desde el máximo 2,309.00 |
| 2026-11-04 05:45 | compra | 2,298.48 | 200.13 |  | Rompió el máximo de 20 velas (2,286.29) |
| 2026-11-04 12:15 | venta | 2,324.07 | 202.16 | +1.82 | Trailing stop: retrocedió 0.6% desde el máximo 2,339.27 |
| 2026-11-04 14:45 | compra | 2,353.94 | 201.05 |  | Rompió el máximo de 20 velas (2,339.27) |
| 2026-11-04 15:15 | venta | 2,329.23 | 198.74 | -2.51 | Stop-loss: bajó 1.0% desde la entrada 2,353.94 |
| 2026-11-04 22:45 | compra | 2,444.14 | 199.79 |  | Rompió el máximo de 20 velas (2,437.00) |
| 2026-11-05 01:00 | venta | 2,418.49 | 197.50 | -2.49 | Stop-loss: bajó 1.0% desde la entrada 2,444.14 |
| 2026-11-06 09:15 | compra | 2,242.67 | 198.55 |  | Rompió el máximo de 20 velas (2,236.43) |
| 2026-11-06 14:45 | venta | 2,219.13 | 196.27 | -2.48 | Stop-loss: bajó 1.0% desde la entrada 2,242.67 |

## rejilla_btc

Precio BTC/USDT: 76,970.00 → 75,882.00.

- Ventas ganadoras: 15 de 27 (56%); ganancia realizada: 2.59 USDT.
- Motivos de venta: Rejilla (27).

Últimas 10 operaciones:

| Fecha (UTC) | Lado | Precio | USDT | Resultado | Motivo |
|---|---|---:|---:|---:|---|
| 2026-11-04 19:02 | compra | 80,274.13 | 50.00 |  | Rejilla: bajó 0.4% desde 80,582.27, compro otro lote (3/6) |
| 2026-11-04 19:53 | compra | 79,992.74 | 50.00 |  | Rejilla: bajó 0.4% desde 80,274.13, compro otro lote (4/6) |
| 2026-11-04 20:33 | venta | 80,293.16 | 50.14 | -0.09 | Rejilla: lote comprado a 79,992.74 subió 0.4% |
| 2026-11-04 22:20 | venta | 80,555.71 | 50.13 | +0.07 | Rejilla: lote comprado a 80,274.13 subió 0.4% |
| 2026-11-04 22:43 | venta | 80,865.47 | 50.13 | +0.26 | Rejilla: lote comprado a 80,582.27 subió 0.4% |
| 2026-11-04 23:01 | compra | 80,564.69 | 50.00 |  | Rejilla: bajó 0.4% desde 80,885.96, compro otro lote (2/6) |
| 2026-11-05 10:51 | compra | 80,275.96 | 50.00 |  | Rejilla: bajó 0.4% desde 80,564.69, compro otro lote (3/6) |
| 2026-11-05 12:34 | compra | 79,917.94 | 50.00 |  | Rejilla: bajó 0.4% desde 80,275.96, compro otro lote (4/6) |
| 2026-11-05 12:54 | compra | 79,617.35 | 50.00 |  | Rejilla: bajó 0.4% desde 79,917.94, compro otro lote (5/6) |
| 2026-11-05 14:37 | compra | 79,149.55 | 50.00 |  | Rejilla: bajó 0.4% desde 79,617.35, compro otro lote (6/6) |

## dca_eth_15m

Precio ETH/USDT: 2,240.15 → 2,229.37.

- Ventas ganadoras: 6 de 6 (100%); ganancia realizada: 17.71 USDT.
- Motivos de venta: Toma de ganancias (6).
- Órdenes rechazadas por el supervisor: Supervisor: presupuesto del bot agotado (251), Supervisor: compras bloqueadas: supervisor pausado (15).

Últimas 10 operaciones:

| Fecha (UTC) | Lado | Precio | USDT | Resultado | Motivo |
|---|---|---:|---:|---:|---|
| 2026-11-04 19:30 | compra | 2,427.88 | 20.00 |  | Compra programada (cada 0.5 h) |
| 2026-11-04 20:00 | compra | 2,407.67 | 40.00 |  | Compra x2: el precio cayó 0.9% desde la última compra |
| 2026-11-04 20:30 | compra | 2,418.61 | 20.00 |  | Compra programada (cada 0.5 h) |
| 2026-11-04 21:00 | compra | 2,422.20 | 20.00 |  | Compra programada (cada 0.5 h) |
| 2026-11-04 21:30 | compra | 2,421.49 | 20.00 |  | Compra programada (cada 0.5 h) |
| 2026-11-04 22:00 | compra | 2,419.55 | 20.00 |  | Compra programada (cada 0.5 h) |
| 2026-11-04 22:30 | compra | 2,436.20 | 20.00 |  | Compra programada (cada 0.5 h) |
| 2026-11-04 23:00 | compra | 2,437.49 | 20.00 |  | Compra programada (cada 0.5 h) |
| 2026-11-04 23:30 | compra | 2,425.52 | 20.00 |  | Compra programada (cada 0.5 h) |
| 2026-11-05 00:00 | compra | 2,425.82 | 6.75 |  | Compra programada (cada 0.5 h) |

## Eventos del supervisor

- 2026-11-05 15:47 · **pausa** · pérdida de 3.0% en el día
- 2026-11-06 00:00 · **reanudacion** · nuevo día: se reanudan las compras
