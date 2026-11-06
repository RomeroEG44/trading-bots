# Estructura del sistema (v0.4: Escáner de todos los mercados + cazadores + Sala de bots)

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

## El Escáner (tradingbots/escaner.py)
Cada minuto revisa **todos los pares en USDT de Binance** (unos 565 de criptomonedas reales). Descarta las monedas estables
(USDC, FDUSD…), el oro tokenizado y las **acciones tokenizadas** (AAPLB, NVDAB, SPYB…). En Testnet solo cuenta los pares
que existen en el Testnet. A cada mercado le aplica 3 filtros y le pone 3 puntajes:

| Filtro (Verificador) | Umbral | Por qué |
|---|---|---|
| Volumen 24 h | ≥ 15 millones USDT | Que haya gente comprando y vendiendo |
| Rango 24 h | ≥ 2 % | Que el precio se mueva lo suficiente para ganarle a las comisiones |
| Spread | ≤ 0.15 % | Que comprar y vender no cueste de más |

| Puntaje (0-100) | Qué premia |
|---|---|
| impulso | Subió en el día y está cerca de su máximo |
| caída | Bajó en el día y está cerca de su mínimo |
| volátil | Se mueve mucho y tiene mucho volumen |

## Los 6 agentes (config/testnet.yaml)
| Agente | Estrategia | Mercado | Velas | Idea |
|---|---|---|---|---|
| 🎯 francotirador | Tendencia EMA 9/21 + RSI | **auto**: los más volátiles | 1 min | Entradas rápidas; stop 0.6 %, objetivo 1.2 % |
| 🚀 impulso | Ruptura de máximos | **auto**: los que más suben | 5 min | Compra cuando rompe el máximo de 20 velas |
| 🎣 cazacaidas | Reversión (Bollinger + RSI) | **auto**: los que más cayeron | 5 min | Compra caídas exageradas, vende al volver al promedio |
| 🐋 ballena | Picos de volumen comprador | **auto**: los más volátiles | 5 min | Entra cuando una vela tiene 3 veces el volumen normal y es verde |
| 🧱 rejilla_btc | Rejilla | BTC/USDT fijo | en vivo | Compra cada −0.4 % y vende cada lote a +0.4 % |
| 🪙 dca_eth | DCA rápido | ETH/USDT fijo | 15 min | Compra cada 30 min, doble si baja 0.7 % |

Los **cazadores** (par `auto`), cuando no tienen posición, revisan al cerrar cada vela los 4 mejores mercados del Escáner
según su puntaje y entran en el primero que da señal. Mientras tienen posición se quedan en ese mercado hasta salir.
Cada agente tiene su propio presupuesto de 400 USDT.

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

## El panel: Sala de bots (http://localhost:8000)
- **Billetera:** valor total, ganancia, multiplicador desde el inicio y barra de metas (+5 %, +10 %, +25 %).
- **Equipo:** Master, Escáner, Verificador, Riesgo, Ejecución y Tamaño, cada uno con su dato y su último mensaje.
- **Agentes:** tarjeta por bot con su mercado actual, qué está haciendo, curva de su valor, % de ganancia y cierres.
- **La sala:** diagrama animado; las líneas se iluminan cuando el Master corrige a un bot o el Escáner le manda mercados.
- **Detalle:** gráfica del mercado del bot con sus compras ▲ y ventas ▼, más su análisis en este momento.
- **Mercados vigilados:** los 30 mejores del Escáner con filtros ✓/✗, puntajes y qué bot los mira o está dentro.
- **umbrales.py:** todos los umbrales del Escáner, el Master y el Supervisor.
- **Cerradas, Feedback en vivo, Balance y Operaciones.**

## Archivos
```
tradingbots/
  motor.py            ciclo en vivo: agentes en paralelo + Escáner + Master + Supervisor
  escaner.py          revisa todos los mercados, filtra y califica
  master.py           el bot principal (feedback y correcciones)
  supervisor.py       límites duros de riesgo
  estrategias/        dca, tendencia, reversion, ruptura, rejilla, volumen (+ base con stops)
  mercado.py          Binance Testnet/real (ccxt) y modo papel
  almacen.py          base de datos SQLite
  metricas.py         acierto, factor de beneficio, caída, comisiones
  panel.py + panel.html   panel web en tiempo real
  backtest.py         pruebas con datos históricos (con o sin Master)
config/
  testnet.yaml        los 6 agentes + Escáner + reglas del Master   ← el que se usa ahora
  pruebas.yaml        bots lentos para backtests largos
  real.yaml           40 USD reales (Fase 3, aún no)
```

## Qué dicen los datos (backtest de 7 días de la versión anterior, con bots fijos)
| | Sin Master | Con Master |
|---|---:|---:|
| Resultado total | −8.2 % | **−2.0 %** |
| Peor bot (tendencia_btc_1m) | −28.7 % | −3.2 % |
| Comisiones del peor bot | 74.87 USDT | 8.16 USDT |

**El Master reduce mucho las pérdidas, pero ninguna de las 6 estrategias rápidas ganó en esa semana.**
Con comisiones de 0.1 % por operación, ganar en velas de 1 a 15 minutos es muy difícil. El Testnet sirve para ver en
horas qué bot sobrevive y para afinar el Master; no garantiza nada para el dinero real.

Los cazadores todavía no se pueden probar en backtest, porque eso requiere historial de cientos de mercados a la vez.
Su prueba es el Testnet.
