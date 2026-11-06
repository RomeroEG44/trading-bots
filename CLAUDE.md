# Memoria del proyecto: Trading Bots (Binance)

> Claude lee este archivo automáticamente al empezar cada sesión.
> Aquí va todo lo que NO se debe volver a preguntar. Mantenerlo corto y actualizado.

## Quién y cómo
- Dueño: Edgar. Habla español; responder siempre en español, claro y sin jerga innecesaria.
- Edgar no es programador: explicar cada paso en palabras simples y decir qué tiene que hacer él.
- Claude escribe, prueba y documenta el código. Edgar decide estrategia, dinero y riesgo.

## Objetivo
Varios bots que compran y venden cripto en Binance de forma automática, más un
**bot supervisor** que los vigila, aplica límites de riesgo y le reporta a Edgar.
Edgar también debe poder ver en un panel qué está haciendo cada bot.

## Reglas que NUNCA se rompen
1. Nada de dinero real hasta pasar backtest + Testnet (ver `docs/PLAN.md`, fases).
2. Claves de API solo en `.env` (está en `.gitignore`). Nunca en el código, en commits ni en el chat.
3. Claves de Binance SIN permiso de retiro. Solo lectura + trading spot.
4. Solo **Spot**, sin apalancamiento ni futuros, salvo que Edgar lo decida explícitamente por escrito.
5. Todo bot pasa por el supervisor: si el supervisor dice "alto", todos se detienen.
6. Cualquier cambio a límites de riesgo se anota en `docs/DECISIONES.md`.

## Estado actual
- Fase: **0 casi terminada, 1 (backtest) primera ronda hecha**. Ver `docs/RESULTADOS_BACKTEST.md`.
- Bots: Bot 1 "DCA" (BTC/USDT, semanal) y Bot 2 "Tendencia" (ETH/USDT, **velas diarias**).
- Hallazgo clave: ninguna estrategia gana de forma confiable todavía; en 1 h las comisiones destruyen al bot Tendencia.
- GitHub: https://github.com/RomeroEG44/trading-bots (privado).
- Capital real previsto: ~40 USD (Fase 3), `config/real.yaml`.
- **Binance bloquea su API desde la nube de Claude** (error "restricted location"). Solo funciona
  `data-api.binance.vision` (datos públicos) → aquí se hacen backtests; los bots que operan corren en la PC de Edgar.
- Pendiente de Edgar: seguir `docs/GUIA_INSTALACION.md` y correr `python -m tradingbots.verificar_conexion`.

## Comandos
- Pruebas: `python -m pytest -q`
- Backtest: `python -m tradingbots.backtest [--config config/real.yaml] [--dias 365]`
- Conexión (solo en la PC de Edgar): `python -m tradingbots.verificar_conexion`

## Dónde está cada cosa
- `docs/PLAN.md`: plan completo, fases y diseño de los bots.
- `docs/DECISIONES.md`: decisiones tomadas y por qué (no re-discutir lo que ya está ahí).
- `docs/BITACORA.md`: qué se hizo en cada sesión y qué sigue.
- `docs/PREGUNTAS.md`: preguntas abiertas para Edgar.
- `docs/RESULTADOS_BACKTEST.md`: qué aprendimos de los backtests.
- `docs/GUIA_INSTALACION.md`: cómo instalar y correr en la PC de Edgar.
- `tradingbots/`: código (supervisor.py, estrategias/, backtest.py, simulador.py, datos.py).

## Al terminar cada sesión, Claude debe
- Actualizar "Estado actual" arriba y agregar una entrada en `docs/BITACORA.md`.
- Hacer commit y push a GitHub.
