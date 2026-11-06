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
- Fase: **2, en vivo (Testnet)**: motor + supervisor + Telegram + panel listos. Edgar ya verificó la conexión al Testnet.
- Bots: Bot 1 "DCA" (BTC/USDT, semanal) y Bot 2 "Tendencia" (ETH/USDT, **velas diarias**).
- Hallazgo del backtest: ninguna estrategia gana de forma confiable todavía (`docs/RESULTADOS_BACKTEST.md`).
- GitHub: https://github.com/RomeroEG44/trading-bots (privado).
- Capital real previsto: ~40 USD (Fase 3), `config/real.yaml`.
- **Binance bloquea su API (testnet y real) desde la nube de Claude**, y Telegram también está bloqueado aquí.
  Solo funciona `data-api.binance.vision` → aquí: backtests y modo papel; los bots que operan corren en la PC de Edgar.
- Pendiente de Edgar: configurar Telegram y dejar el motor corriendo en Testnet 2-4 semanas (`docs/GUIA_INSTALACION.md`).

## Arquitectura en vivo
- `motor.py`: ciclo cada 15 s; vigila stops con el precio actual, decide al cerrar cada vela, guarda todo en SQLite
  (`data/bots_<modo>.sqlite`), atiende comandos (Telegram y panel) y manda avisos.
- `mercado.py`: las velas siempre vienen de los datos públicos; las órdenes van a `BrokerPapel` (simulado) o `BrokerBinance` (ccxt).
- Cada bot tiene su **cartera virtual** (presupuesto propio) dentro de la misma cuenta de Binance.
- `panel.py` + `panel.html`: FastAPI en 127.0.0.1:8000; Chart.js guardado en `tradingbots/static/` (sin depender de internet).
- Modo real exige `--confirmo-dinero-real` y `config/real.yaml`.

## Comandos
- Pruebas: `python -m pytest -q`
- Backtest: `python -m tradingbots.backtest [--config config/real.yaml] [--dias 365]`
- En vivo: `python -m tradingbots.motor [--modo papel|testnet|real]` (panel en http://localhost:8000)
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
