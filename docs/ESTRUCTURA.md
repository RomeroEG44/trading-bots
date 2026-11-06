# Estructura del sistema (v0.3: bots en paralelo + Master)

## Cómo se toma cada decisión
```
            cada 5 segundos, para cada uno de los 6 bots
┌────────────────────────────────────────────────────────────────────┐
│ 1. ESTRATEGIA del bot     "quiero comprar 200 USDT: cruce alcista"   │
│            │                                                       │
│ 2. MASTER  ▼  ¿cómo le va a este bot? ¿el mercado está agitado?     │
│            · lo deja pasar, le cambia el tamaño (x0.25 – x1.5) o lo veta │
│            · puede ORDENAR ventas: cierre de seguridad o cuarentena  │
│            │                                                       │
│ 3. SUPERVISOR ▼ límites duros de todo el sistema                     │
│            · pares permitidos, montos mín./máx., pérdida diaria, caída │
│            │                                                       │
│ 4. BINANCE TESTNET ▼  orden de mercado real (dinero de prueba)      │
│            │                                                       │
│ 5. BASE DE DATOS ▼  → PANEL WEB (tiempo real, cada 3 s)              │
└────────────────────────────────────────────────────────────────────┘
```
Las **ventas nunca se bloquean**: un stop-loss o un cierre del Master siempre pasa.

## Los 6 bots (config/testnet.yaml)
| Bot | Estrategia | Par | Velas | Idea |
|---|---|---|---|---|
| tendencia_btc_1m | Tendencia EMA 9/21 + RSI | BTC/USDT | 1 min | Sigue subidas cortas; stop 0.4 %, objetivo 0.8 % |
| tendencia_eth_5m | Tendencia EMA 9/21 + RSI | ETH/USDT | 5 min | Igual, más lento; stop 0.8 %, objetivo 1.6 % |
| reversion_btc_5m | Reversión a la media (Bollinger) | BTC/USDT | 5 min | Compra caídas exageradas y vende al volver al promedio |
| ruptura_eth_15m | Ruptura de máximos (Donchian) | ETH/USDT | 15 min | Compra cuando rompe el máximo de 20 velas |
| rejilla_btc | Rejilla (grid) | BTC/USDT | en vivo | Compra cada −0.4 % y vende cada lote a +0.4 % |
| dca_eth_15m | DCA rápido | ETH/USDT | 15 min | Compra cada 30 min, doble si baja 0.7 %, vende la mitad a +1 % |

Cada bot tiene su propio presupuesto (400 USDT) dentro de la misma cuenta de Testnet.

## El Master (tradingbots/master.py)
| Situación | Qué hace (solo, sin preguntar) |
|---|---|
| 3 pérdidas seguidas | Pausa al bot 15 min ("enfriamiento") y baja su tamaño ×0.75 |
| El bot cae 4 % desde su máximo | Baja su tamaño ×0.75 |
| El bot cae 8 % desde su máximo | **Cuarentena 2 h**: cierra su posición y baja su tamaño a la mitad |
| Una posición pierde más de 2.5 % | **La cierra él mismo** (corrige al bot). Rejilla 3.5 % y DCA 4 % |
| Buen rendimiento (factor ≥ 1.3 y ≥ 50 % de aciertos) | Sube su tamaño ×1.15 (máx. ×1.5) |
| Rendimiento flojo (factor < 0.8) | Baja su tamaño ×0.8 (mín. ×0.25) |
| Las comisiones se llevan ≥ 50 % de lo ganado | Lo obliga a esperar 5, 10, 20… min entre compras |
| Un par se mueve ≥ 1.5 % en 5 min | Bloquea compras nuevas en ese par 10 min |
| 20 ventas con factor < 0.5 | **Retira al bot 24 h**; vuelve con tamaño mínimo |

Todas estas reglas se cambian en la sección `master:` de `config/testnet.yaml`, y cada bot puede tener las suyas.

## El Supervisor (tradingbots/supervisor.py)
- Pérdida de 3 % en el día → pausa todas las compras hasta el día siguiente.
- Caída de 10 % desde el máximo → detiene todas las compras y **se reanuda solo a las 2 h**.
- Botón 🛑 del panel: detención manual. Es la única que espera a que tú reanudes.

## Archivos
```
tradingbots/
  motor.py            ciclo en vivo: bots en paralelo + Master + Supervisor
  master.py           el bot principal (feedback y correcciones)
  supervisor.py       límites duros de riesgo
  estrategias/        dca, tendencia, reversion, ruptura, rejilla (+ base con stops)
  mercado.py          Binance Testnet/real (ccxt) y modo papel
  almacen.py          base de datos SQLite
  metricas.py         acierto, factor de beneficio, caída, comisiones
  panel.py + panel.html   panel web en tiempo real
  backtest.py         pruebas con datos históricos (con o sin Master)
config/
  testnet.yaml        los 6 bots rápidos + reglas del Master   ← el que se usa ahora
  pruebas.yaml        bots lentos para backtests largos
  real.yaml           40 USD reales (Fase 3, aún no)
```

## Qué dicen los datos (backtest de los últimos 7 días)
| | Sin Master | Con Master |
|---|---:|---:|
| Resultado total | −8.2 % | **−2.0 %** |
| Peor bot (tendencia_btc_1m) | −28.7 % | −3.2 % |
| Comisiones del peor bot | 74.87 USDT | 8.16 USDT |

**El Master reduce mucho las pérdidas, pero ninguna de las 6 estrategias rápidas ganó en esa semana.**
Con comisiones de 0.1 % por operación, ganar en velas de 1 a 15 minutos es muy difícil. El Testnet sirve para ver en
horas qué bot sobrevive y para afinar el Master; no garantiza nada para el dinero real.
