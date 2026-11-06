# Backtest · `testnet` · 2026-10-30 → 2026-11-06

Comisión 0.1% por operación · deslizamiento 0.05% · límites: pérdida diaria 3%, caída máxima 10% · tras una detención se simula que Edgar reanuda a los 7 días.

## Resumen

| Bot | Par | Capital | Valor final | Resultado | Peor caída | Comprar y esperar | Ventas | Acierto | Factor | Comisiones |
|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| tendencia_btc_1m | BTC/USDT | 400.00 | 387.39 | -3.2% | -3.2% | -1.5% | 65 | 3% | 0.05 | 8.16 |
| tendencia_eth_5m | ETH/USDT | 400.00 | 391.53 | -2.1% | -2.1% | -0.7% | 39 | 13% | 0.20 | 5.39 |
| reversion_btc_5m | BTC/USDT | 400.00 | 394.93 | -1.3% | -1.3% | -1.5% | 20 | 20% | 0.04 | 3.48 |
| ruptura_eth_15m | ETH/USDT | 400.00 | 394.07 | -1.5% | -2.5% | -0.6% | 9 | 33% | 0.49 | 3.68 |
| rejilla_btc | BTC/USDT | 400.00 | 396.14 | -1.0% | -2.9% | -1.5% | 27 | 56% | 0.50 | 2.66 |
| dca_eth_15m | ETH/USDT | 400.00 | 387.70 | -3.1% | -8.4% | -0.6% | 8 | 75% | 0.60 | 3.68 |
| **Total** | | 2,400.00 | 2,351.77 | **-2.0%** | -2.3% | | | | | |

Master: activo · 144 intervenciones.

## tendencia_btc_1m

Precio BTC/USDT: 76,970.00 → 75,882.00.

- Ventas ganadoras: 2 de 65 (3%); ganancia realizada: -12.61 USDT.
- Motivos de venta: Cruce bajista (63), Trailing stop (1), Stop-loss (1).
- Órdenes rechazadas por el supervisor: Master: debe esperar 60 min entre compras (55), Master: bot en retirado hasta las 22:47 UTC (34), Master: bot en retirado hasta las 05:50 UTC (33), Master: bot en retirado hasta las 13:31 UTC (30), Master: bot en enfriamiento hasta las 13:02 UTC (2), Master: bot en enfriamiento hasta las 02:36 UTC (1), Master: bot en enfriamiento hasta las 04:31 UTC (1), Master: bot en enfriamiento hasta las 12:42 UTC (1), Master: bot en enfriamiento hasta las 17:19 UTC (1), Master: bot en enfriamiento hasta las 15:39 UTC (1), Master: bot en enfriamiento hasta las 19:35 UTC (1), Master: bot en enfriamiento hasta las 23:40 UTC (1), Master: bot en enfriamiento hasta las 04:19 UTC (1), Master: bot en enfriamiento hasta las 08:08 UTC (1), Master: bot en enfriamiento hasta las 16:58 UTC (1).

Últimas 10 operaciones:

| Fecha (UTC) | Lado | Precio | USDT | Resultado | Motivo |
|---|---|---:|---:|---:|---|
| 2026-11-06 13:49 | compra | 75,997.99 | 48.54 |  | Cruce alcista EMA9/EMA21 con RSI 57 · tamaño x0.25 (Master) |
| 2026-11-06 13:59 | venta | 75,809.43 | 48.37 | -0.22 | Cruce bajista: EMA rápida cruzó hacia abajo la lenta |
| 2026-11-06 15:15 | compra | 75,886.92 | 48.51 |  | Cruce alcista EMA9/EMA21 con RSI 61 · tamaño x0.25 (Master) |
| 2026-11-06 15:29 | venta | 75,545.59 | 48.25 | -0.31 | Stop-loss: bajó 0.4% desde la entrada 75,886.92 |
| 2026-11-06 16:26 | compra | 75,821.90 | 48.47 |  | Cruce alcista EMA9/EMA21 con RSI 59 · tamaño x0.25 (Master) |
| 2026-11-06 16:43 | venta | 75,674.14 | 48.33 | -0.19 | Cruce bajista: EMA rápida cruzó hacia abajo la lenta |
| 2026-11-06 18:00 | compra | 75,819.49 | 48.45 |  | Cruce alcista EMA9/EMA21 con RSI 59 · tamaño x0.25 (Master) |
| 2026-11-06 18:51 | venta | 75,802.21 | 48.39 | -0.11 | Cruce bajista: EMA rápida cruzó hacia abajo la lenta |
| 2026-11-06 19:42 | compra | 75,799.89 | 48.43 |  | Cruce alcista EMA9/EMA21 con RSI 54 · tamaño x0.25 (Master) |
| 2026-11-06 20:18 | venta | 75,807.92 | 48.39 | -0.09 | Cruce bajista: EMA rápida cruzó hacia abajo la lenta |

## tendencia_eth_5m

Precio ETH/USDT: 2,242.36 → 2,229.37.

- Ventas ganadoras: 5 de 39 (13%); ganancia realizada: -8.35 USDT.
- Motivos de venta: Cruce bajista (33), Take-profit (3), Trailing stop (2), Stop-loss (1).
- Órdenes rechazadas por el supervisor: Master: bot en retirado hasta las 20:40 UTC (8), Master: debe esperar 60 min entre compras (4), Master: debe esperar 40 min entre compras (2), Master: bot en enfriamiento hasta las 08:35 UTC (1), Master: bot en enfriamiento hasta las 15:55 UTC (1), Master: bot en enfriamiento hasta las 02:00 UTC (1).

Últimas 10 operaciones:

| Fecha (UTC) | Lado | Precio | USDT | Resultado | Motivo |
|---|---|---:|---:|---:|---|
| 2026-11-06 07:05 | venta | 2,218.98 | 48.77 | -0.39 | Cruce bajista: EMA rápida cruzó hacia abajo la lenta |
| 2026-11-06 07:50 | compra | 2,235.32 | 49.07 |  | Cruce alcista EMA9/EMA21 con RSI 59 · tamaño x0.25 (Master) |
| 2026-11-06 11:15 | venta | 2,234.09 | 48.99 | -0.12 | Cruce bajista: EMA rápida cruzó hacia abajo la lenta |
| 2026-11-06 11:30 | compra | 2,242.11 | 49.05 |  | Cruce alcista EMA9/EMA21 con RSI 57 · tamaño x0.25 (Master) |
| 2026-11-06 13:00 | venta | 2,237.83 | 48.91 | -0.19 | Cruce bajista: EMA rápida cruzó hacia abajo la lenta |
| 2026-11-06 16:35 | compra | 2,234.89 | 49.03 |  | Cruce alcista EMA9/EMA21 con RSI 55 · tamaño x0.25 (Master) |
| 2026-11-06 16:45 | venta | 2,225.01 | 48.76 | -0.31 | Cruce bajista: EMA rápida cruzó hacia abajo la lenta |
| 2026-11-06 18:35 | compra | 2,234.56 | 48.99 |  | Cruce alcista EMA9/EMA21 con RSI 57 · tamaño x0.25 (Master) |
| 2026-11-06 19:35 | venta | 2,227.82 | 48.79 | -0.25 | Cruce bajista: EMA rápida cruzó hacia abajo la lenta |
| 2026-11-06 19:40 | compra | 2,232.53 | 48.96 |  | Cruce alcista EMA9/EMA21 con RSI 55 · tamaño x0.25 (Master) |

## reversion_btc_5m

Precio BTC/USDT: 76,954.00 → 75,882.00.

- Ventas ganadoras: 4 de 20 (20%); ganancia realizada: -5.07 USDT.
- Motivos de venta: Stop-loss (5), Volvió al promedio (77,223.21) (1), Volvió al promedio (77,555.18) (1), Volvió al promedio (77,920.92) (1), Volvió al promedio (77,828.78) (1), Volvió al promedio (77,848.69) (1), Volvió al promedio (78,142.53) (1), Volvió al promedio (77,936.88) (1), Volvió al promedio (77,313.19) (1), Volvió al promedio (76,966.65) (1), Volvió al promedio (76,962.95) (1), Volvió al promedio (76,715.12) (1), Volvió al promedio (78,346.18) (1), Volvió al promedio (75,819.18) (1), Volvió al promedio (75,684.78) (1), Volvió al promedio (75,795.35) (1).
- Órdenes rechazadas por el supervisor: Master: bot en enfriamiento hasta las 03:15 UTC (2), Master: bot en enfriamiento hasta las 15:05 UTC (2), Master: debe esperar 60 min entre compras (2), Master: bot en retirado hasta las 14:50 UTC (1).

Últimas 10 operaciones:

| Fecha (UTC) | Lado | Precio | USDT | Resultado | Motivo |
|---|---|---:|---:|---:|---|
| 2026-11-05 14:15 | compra | 79,439.16 | 49.49 |  | Sobreventa: precio 79,399.46 bajo la banda inferior 79,478.46, RSI 30 · tamaño x0.25 (Master) |
| 2026-11-05 14:50 | venta | 78,764.24 | 49.02 | -0.52 | Stop-loss: bajó 0.8% desde la entrada 79,439.16 |
| 2026-11-05 15:15 | compra | 77,058.42 | 49.42 |  | Sobreventa: precio 77,019.91 bajo la banda inferior 77,364.76, RSI 7 · tamaño x0.25 (Master) |
| 2026-11-05 15:30 | venta | 76,403.73 | 48.95 | -0.52 | Stop-loss: bajó 0.8% desde la entrada 77,058.42 |
| 2026-11-05 23:10 | compra | 75,557.46 | 49.36 |  | Sobreventa: precio 75,519.70 bajo la banda inferior 75,559.46, RSI 32 · tamaño x0.25 (Master) |
| 2026-11-05 23:25 | venta | 75,800.09 | 49.47 | +0.06 | Volvió al promedio (75,819.18) |
| 2026-11-06 05:25 | compra | 75,525.31 | 49.36 |  | Sobreventa: precio 75,487.57 bajo la banda inferior 75,521.22, RSI 33 · tamaño x0.25 (Master) |
| 2026-11-06 05:40 | venta | 75,674.17 | 49.41 | -0.00 | Volvió al promedio (75,684.78) |
| 2026-11-06 14:10 | compra | 75,644.87 | 49.36 |  | Sobreventa: precio 75,607.07 bajo la banda inferior 75,641.64, RSI 30 · tamaño x0.25 (Master) |
| 2026-11-06 14:50 | venta | 75,821.65 | 49.43 | +0.02 | Volvió al promedio (75,795.35) |

## ruptura_eth_15m

Precio ETH/USDT: 2,240.15 → 2,229.37.

- Ventas ganadoras: 3 de 9 (33%); ganancia realizada: -5.93 USDT.
- Motivos de venta: Stop-loss (4), Trailing stop (3), Perdió el mínimo de 10 velas (2,247.32) (1), Perdió el mínimo de 10 velas (2,266.88) (1).

Últimas 10 operaciones:

| Fecha (UTC) | Lado | Precio | USDT | Resultado | Motivo |
|---|---|---:|---:|---:|---|
| 2026-11-03 09:45 | compra | 2,269.05 | 199.27 |  | Rompió el máximo de 20 velas (2,267.27) |
| 2026-11-03 13:45 | venta | 2,293.33 | 201.20 | +1.73 | Trailing stop: retrocedió 0.6% desde el máximo 2,309.00 |
| 2026-11-04 05:45 | compra | 2,298.48 | 200.13 |  | Rompió el máximo de 20 velas (2,286.29) |
| 2026-11-04 12:15 | venta | 2,324.07 | 202.16 | +1.82 | Trailing stop: retrocedió 0.6% desde el máximo 2,339.27 |
| 2026-11-04 14:45 | compra | 2,353.94 | 231.20 |  | Rompió el máximo de 20 velas (2,339.27) · tamaño x1.15 (Master) |
| 2026-11-04 15:15 | venta | 2,329.23 | 228.55 | -2.88 | Stop-loss: bajó 1.0% desde la entrada 2,353.94 |
| 2026-11-04 22:45 | compra | 2,444.14 | 229.55 |  | Rompió el máximo de 20 velas (2,437.00) · tamaño x1.15 (Master) |
| 2026-11-05 01:00 | venta | 2,418.49 | 226.91 | -2.86 | Stop-loss: bajó 1.0% desde la entrada 2,444.14 |
| 2026-11-06 09:15 | compra | 2,242.67 | 182.32 |  | Rompió el máximo de 20 velas (2,236.43) · tamaño x0.92 (Master) |
| 2026-11-06 14:45 | venta | 2,219.13 | 180.23 | -2.27 | Stop-loss: bajó 1.0% desde la entrada 2,242.67 |

## rejilla_btc

Precio BTC/USDT: 76,970.00 → 75,882.00.

- Ventas ganadoras: 15 de 27 (56%); ganancia realizada: -3.82 USDT.
- Motivos de venta: Rejilla (26), Master (1).
- Órdenes rechazadas por el supervisor: Master: bot en retirado hasta las 15:10 UTC (1439), Master: debe esperar 60 min entre compras (267).

Últimas 10 operaciones:

| Fecha (UTC) | Lado | Precio | USDT | Resultado | Motivo |
|---|---|---:|---:|---:|---|
| 2026-11-05 12:33 | compra | 80,008.46 | 28.91 |  | Rejilla: bajó 0.4% desde 80,301.13, compro otro lote (4/6) · tamaño x0.58 (Master) |
| 2026-11-05 13:33 | compra | 79,697.84 | 28.91 |  | Rejilla: bajó 0.4% desde 80,008.46, compro otro lote (5/6) · tamaño x0.58 (Master) |
| 2026-11-05 14:37 | compra | 79,149.55 | 28.91 |  | Rejilla: bajó 0.4% desde 79,697.84, compro otro lote (6/6) · tamaño x0.58 (Master) |
| 2026-11-05 15:10 | venta | 77,251.56 | 159.91 | -6.09 | Master: cierre de seguridad (pérdida 3.5%) |
| 2026-11-06 15:10 | compra | 75,366.74 | 12.50 |  | Rejilla: primer lote a 75,329.08 · tamaño x0.25 (Master) |
| 2026-11-06 15:15 | venta | 75,811.08 | 12.56 | +0.05 | Rejilla: lote comprado a 75,366.74 subió 0.4% |
| 2026-11-06 16:10 | compra | 75,733.84 | 12.50 |  | Rejilla: primer lote a 75,695.99 · tamaño x0.25 (Master) |
| 2026-11-06 17:07 | venta | 76,032.05 | 12.54 | +0.02 | Rejilla: lote comprado a 75,733.84 subió 0.4% |
| 2026-11-06 17:10 | compra | 76,050.02 | 12.50 |  | Rejilla: primer lote a 76,012.01 · tamaño x0.25 (Master) |
| 2026-11-06 18:12 | compra | 75,781.52 | 12.50 |  | Rejilla: bajó 0.4% desde 76,050.02, compro otro lote (2/6) · tamaño x0.25 (Master) |

## dca_eth_15m

Precio ETH/USDT: 2,240.15 → 2,229.37.

- Ventas ganadoras: 6 de 8 (75%); ganancia realizada: -11.69 USDT.
- Motivos de venta: Toma de ganancias (6), Master (2).
- Órdenes rechazadas por el supervisor: Supervisor: presupuesto del bot agotado (222), Master: bot en cuarentena hasta las 09:30 UTC (3).

Últimas 10 operaciones:

| Fecha (UTC) | Lado | Precio | USDT | Resultado | Motivo |
|---|---|---:|---:|---:|---|
| 2026-11-06 16:30 | compra | 2,231.56 | 6.35 |  | Compra programada (cada 0.5 h) · tamaño x0.32 (Master) |
| 2026-11-06 17:00 | compra | 2,237.14 | 6.35 |  | Compra programada (cada 0.5 h) · tamaño x0.32 (Master) |
| 2026-11-06 17:30 | compra | 2,233.04 | 6.35 |  | Compra programada (cada 0.5 h) · tamaño x0.32 (Master) |
| 2026-11-06 18:00 | compra | 2,228.40 | 6.35 |  | Compra programada (cada 0.5 h) · tamaño x0.32 (Master) |
| 2026-11-06 18:30 | compra | 2,229.16 | 6.35 |  | Compra programada (cada 0.5 h) · tamaño x0.32 (Master) |
| 2026-11-06 19:00 | compra | 2,232.55 | 6.35 |  | Compra programada (cada 0.5 h) · tamaño x0.32 (Master) |
| 2026-11-06 19:30 | compra | 2,228.83 | 6.35 |  | Compra programada (cada 0.5 h) · tamaño x0.32 (Master) |
| 2026-11-06 20:00 | compra | 2,236.91 | 6.35 |  | Compra programada (cada 0.5 h) · tamaño x0.32 (Master) |
| 2026-11-06 20:30 | compra | 2,233.12 | 6.35 |  | Compra programada (cada 0.5 h) · tamaño x0.32 (Master) |
| 2026-11-06 21:00 | compra | 2,230.48 | 6.35 |  | Compra programada (cada 0.5 h) · tamaño x0.32 (Master) |

## Feedback del Master (últimos 25)

- 2026-11-05 11:05 · tendencia_eth_5m · Termina su enfriamiento: vuelve a operar con tamaño x0.25.
- 2026-11-05 13:31 · tendencia_btc_1m · 3 pérdidas seguidas: pausa de 15 min y bajo su tamaño a x0.25.
- 2026-11-05 13:31 · tendencia_btc_1m · Retiro al bot 24 h: pierde de forma persistente (factor 0.00, 0% ganadoras). Volverá con tamaño mínimo x0.25.
- 2026-11-05 14:50 · reversion_btc_5m · 3 pérdidas seguidas: pausa de 15 min y bajo su tamaño a x0.25.
- 2026-11-05 15:00 · dca_eth_15m · Cayó 4.0% desde su máximo: le bajo el tamaño a x0.99.
- 2026-11-05 15:05 · reversion_btc_5m · Termina su enfriamiento: vuelve a operar con tamaño x0.25.
- 2026-11-05 15:15 · dca_eth_15m · Corrijo su operación: la posición pierde 5.2% (límite 4%). La cierro.
- 2026-11-05 15:15 · dca_eth_15m · Rendimiento flojo (factor 0.79, 86% ganadoras): le bajo el tamaño a x0.79.
- 2026-11-05 15:10 · rejilla_btc · Corrijo su operación: la posición pierde 3.5% (límite 3.5%). La cierro.
- 2026-11-05 15:10 · rejilla_btc · Retiro al bot 24 h: pierde de forma persistente (factor 0.44, 70% ganadoras). Volverá con tamaño mínimo x0.25.
- 2026-11-06 01:45 · tendencia_eth_5m · 3 pérdidas seguidas: pausa de 15 min y bajo su tamaño a x0.25.
- 2026-11-06 02:00 · tendencia_eth_5m · Termina su enfriamiento: vuelve a operar con tamaño x0.25.
- 2026-11-06 07:30 · dca_eth_15m · Cuarentena de 120 min: cayó 8.1% desde su máximo. Cierro su posición y bajo su tamaño a x0.40.
- 2026-11-06 07:30 · dca_eth_15m · Rendimiento flojo (factor 0.60, 75% ganadoras): le bajo el tamaño a x0.32.
- 2026-11-06 09:30 · dca_eth_15m · Termina su cuarentena: vuelve a operar con tamaño x0.32.
- 2026-11-06 13:00 · tendencia_eth_5m · 3 pérdidas seguidas: pausa de 15 min y bajo su tamaño a x0.25.
- 2026-11-06 13:15 · tendencia_eth_5m · Termina su enfriamiento: vuelve a operar con tamaño x0.25.
- 2026-11-06 13:31 · tendencia_btc_1m · Termina su retirado: vuelve a operar con tamaño x0.25.
- 2026-11-06 14:45 · ruptura_eth_15m · 3 pérdidas seguidas: pausa de 15 min y bajo su tamaño a x0.69.
- 2026-11-06 14:45 · ruptura_eth_15m · Rendimiento flojo (factor 0.49, 33% ganadoras): le bajo el tamaño a x0.55.
- 2026-11-06 14:50 · reversion_btc_5m · Retiro al bot 24 h: pierde de forma persistente (factor 0.03, 20% ganadoras). Volverá con tamaño mínimo x0.25.
- 2026-11-06 15:00 · ruptura_eth_15m · Termina su enfriamiento: vuelve a operar con tamaño x0.55.
- 2026-11-06 15:10 · rejilla_btc · Termina su retirado: vuelve a operar con tamaño x0.25.
- 2026-11-06 16:43 · tendencia_btc_1m · 3 pérdidas seguidas: pausa de 15 min y bajo su tamaño a x0.25.
- 2026-11-06 16:58 · tendencia_btc_1m · Termina su enfriamiento: vuelve a operar con tamaño x0.25.

## Eventos del supervisor

- Ninguno.
