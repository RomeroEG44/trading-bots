# Plan del proyecto: Trading Bots en Binance (v0.2)

> v0.2: Bot Tendencia en velas diarias y DCA semanal, por los resultados del backtest (`docs/RESULTADOS_BACKTEST.md`).

## 1. Qué vamos a construir

```
                 ┌──────────────────────────────┐
   Edgar  ◄──────┤   BOT SUPERVISOR (principal) │◄──── Panel web (ver todo en vivo)
 (Telegram)      │ - vigila a los bots          │
                 │ - aplica límites de riesgo   │
                 │ - botón de pánico (detener)  │
                 │ - reportes y alertas         │
                 └──────┬───────────────┬───────┘
                        │ permiso/alto  │
                ┌───────▼─────┐   ┌─────▼────────┐
                │  Bot 1: DCA │   │ Bot 2:       │
                │  BTC/USDT   │   │ Tendencia    │
                │             │   │ ETH/USDT     │
                └───────┬─────┘   └─────┬────────┘
                        └──────┬────────┘
                         ┌─────▼─────┐        ┌───────────────┐
                         │  Binance  │        │ Base de datos │
                         │ (Testnet) │        │ (operaciones, │
                         └───────────┘        │  saldos, logs)│
                                              └───────────────┘
```

Regla clave: **ningún bot manda una orden a Binance sin que el supervisor la apruebe.**

## 2. Los 2 bots de prueba

### Bot 1: "DCA" (compra programada), BTC/USDT
- **Idea:** comprar una cantidad fija cada cierto tiempo, sin importar el precio. Es la estrategia más simple
  y la menos arriesgada. Nos sirve para comprobar que toda la maquinaria funciona (conexión, órdenes,
  registro, reportes).
- **Reglas propuestas:**
  - Comprar 10 USDT de BTC cada 24 h.
  - "DCA inteligente": si el precio cayó más de 5 % desde la última compra, comprar el doble (máximo 2x).
  - Vender una parte solo si la ganancia total supera el +15 % (toma de ganancias parcial, 25 % de la posición).
  - Tope de capital asignado: si ya usó todo su presupuesto, deja de comprar y avisa.
- **Riesgo:** bajo a medio. Si BTC cae mucho por mucho tiempo, la posición pierde valor.

### Bot 2: "Tendencia" (cruce de medias móviles + RSI), ETH/USDT
- **Idea:** comprar cuando el precio empieza a subir con fuerza y vender cuando la subida se agota.
- **Reglas propuestas (velas de 1 hora):**
  - **Compra** cuando la media rápida (EMA 9) cruza hacia arriba la media lenta (EMA 21) **y** el RSI(14) está
    entre 50 y 70 (hay fuerza, pero aún no está "sobrecomprado").
  - **Venta** cuando ocurre cualquiera de estas:
    - La EMA 9 cruza hacia abajo la EMA 21.
    - **Stop-loss:** el precio cae 3 % desde la compra.
    - **Take-profit:** el precio sube 6 % desde la compra.
    - **Trailing stop:** después de +3 %, si el precio retrocede 2 % desde su máximo.
  - Solo una posición abierta a la vez.
- **Riesgo:** medio. En mercados laterales da señales falsas y pierde poco a poco (por eso hay stop-loss).

> Los números (10 USDT, 3 %, 6 %, etc.) son puntos de partida. Los ajustamos con el backtest, no por intuición.

## 3. El bot supervisor

| Función | Detalle |
|---|---|
| Aprobación de órdenes | Revisa cada orden antes de enviarla: par permitido, tamaño máximo, saldo suficiente. |
| Límite de pérdida diaria | Si el total pierde más de **3 %** en el día, pausa a todos hasta el día siguiente. |
| Límite de pérdida total | Si cae **10 %** desde el máximo, detiene todo y espera que Edgar lo reactive. |
| Límite por bot | Cada bot tiene su presupuesto; no puede usar dinero de otro. |
| Anti-errores | Máximo de órdenes por hora; si un bot "se vuelve loco", se pausa solo. |
| Salud | Si Binance no responde o un bot deja de reportar, avisa. |
| Reportes | Resumen diario y alertas inmediatas por Telegram; todo visible en el panel. |
| Comandos de Edgar | Por Telegram: `/estado`, `/pausar`, `/reanudar`, `/detener_todo`, `/reporte`. |

## 4. Panel web (para "ver qué están haciendo")
- Estado de cada bot (activo, pausado, detenido) y por qué.
- Saldo y ganancias o pérdidas por bot y en total (hoy, semana, total).
- Lista de operaciones con hora, precio, cantidad y motivo ("compré porque EMA9 cruzó EMA21").
- Gráfica de precio con marcas donde compró o vendió cada bot.
- Botón de pánico: detener todo.

## 5. Tecnología (decisión técnica de Claude, explicada simple)
- **Python**: el lenguaje más usado para bots de trading.
- **ccxt**: librería que habla con Binance (y con otros exchanges si algún día cambiamos). Soporta el Testnet.
- **SQLite**: base de datos en un solo archivo; guarda operaciones, saldos y registros.
- **FastAPI + página web sencilla**: el panel.
- **Telegram**: canal de mensajes entre el supervisor y Edgar (gratis, llega al celular).
- **Docker** (más adelante): para correr todo igual en tu PC o en un servidor.

## 6. Fases

| Fase | Qué se hace | Cómo sabemos que terminó | Dinero real |
|---|---|---|---|
| **0. Fundación** | Repo en GitHub, memoria, estructura, conexión de **solo lectura** al Testnet. | Vemos el saldo de prueba desde el código. | No |
| **1. Backtest** | Los 2 bots se prueban con 1-2 años de datos históricos reales, incluyendo comisiones. | Reporte con ganancia, peor caída y número de operaciones. Decidimos si vale la pena. | No |
| **2. Testnet** | Bots + supervisor + Telegram + panel corriendo 24/7 con dinero de prueba. | Mínimo 2-4 semanas sin errores y con resultados parecidos al backtest. | No |
| **3. Real (pequeño)** | Mismo sistema con poco dinero real (ej. 50-100 USD en total). | 1 mes estable. Edgar decide si sube el monto. | Sí, poco |
| **4. Crecer** | Más bots o estrategias, ajustar parámetros, servidor definitivo. | — | Según decida Edgar |

## 7. Dónde van a correr los bots
Esta sesión de Claude es temporal y **Binance bloquea su API desde los servidores de Claude**, así que los bots
que operan no pueden correr aquí (aquí solo se programan y se hacen backtests). Opciones:
1. **Tu computadora**: gratis, pero debe estar prendida siempre.
2. **Servidor VPS** (≈ 5-6 USD/mes) **en un país donde Binance esté permitido**: recomendado a partir de la Fase 2.

## 8. Lo que Edgar tiene que hacer (checklist)
- [x] Conectar GitHub a Claude.
- [x] Crear el repositorio `trading-bots` en GitHub.
- [ ] Instalar el proyecto en tu PC: `docs/GUIA_INSTALACION.md`.
- [ ] Crear cuenta en el **Binance Spot Testnet** (testnet.binance.vision) y generar claves de prueba. *(Fase 0)*
- [ ] Crear un bot de Telegram con @BotFather (te guío paso a paso). *(Fase 2)*
- [ ] Revisar este plan y responder `docs/PREGUNTAS.md`.
