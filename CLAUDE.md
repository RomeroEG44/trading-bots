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
- Fase: **2, en vivo (Testnet) v0.3**: 6 bots rápidos en paralelo + **Master** + Supervisor + panel en tiempo real.
- **Telegram eliminado** por decisión de Edgar: todo se ve en el panel web.
- **Autonomía total** por decisión de Edgar: nada pide confirmación; el Supervisor se reanuda solo tras 2 h.
  Única excepción: el modo REAL exige `--confirmo-dinero-real` una vez al arrancar.
- Estructura y reglas: `docs/ESTRUCTURA.md`. Bots y reglas del Master: `config/testnet.yaml`.
- Backtest de 7 días de los bots rápidos: −8.2 % sin Master, −2.0 % con Master. Ninguno gana todavía.
- GitHub: https://github.com/RomeroEG44/trading-bots (privado). Capital real previsto: ~40 USD (`config/real.yaml`).
- **Binance bloquea su API (testnet y real) desde la nube de Claude.** Solo funciona `data-api.binance.vision`
  → aquí: backtests y modo papel; el Testnet corre en la PC de Edgar.

## Arquitectura en vivo
- Orden de cada decisión: Estrategia → Master (`master.py`, ajusta/veta/ordena cierres) → Supervisor (límites duros) → broker.
- `motor.py`: ciclo cada 5 s; las ventas nunca se bloquean; estado de bots, Master y Supervisor en SQLite (`data/bots_<modo>.sqlite`).
- `mercado.py`: en testnet/real, velas, precios y órdenes salen del mismo exchange (ccxt); en papel, de los datos públicos.
- Cada bot tiene una **cartera virtual** con su presupuesto dentro de la misma cuenta.
- `panel.py` + `panel.html`: FastAPI en 127.0.0.1:8000, se actualiza cada 3 s; Chart.js está en `tradingbots/static/`.

## Comandos
- Pruebas: `python -m pytest -q`
- Backtest: `python -m tradingbots.backtest --config config/testnet.yaml --dias 7 [--sin-master]`
- En vivo: `python -m tradingbots.motor [--modo papel|testnet|real]` (panel en http://localhost:8000)
- Conexión (solo en la PC de Edgar): `python -m tradingbots.verificar_conexion`

## Dónde está cada cosa
- `docs/PLAN.md`: plan completo, fases y diseño de los bots.
- `docs/DECISIONES.md`: decisiones tomadas y por qué (no re-discutir lo que ya está ahí).
- `docs/BITACORA.md`: qué se hizo en cada sesión y qué sigue.
- `docs/PREGUNTAS.md`: preguntas abiertas para Edgar.
- `docs/RESULTADOS_BACKTEST.md`: qué aprendimos de los backtests.
- `docs/GUIA_INSTALACION.md`: cómo instalar y correr en la PC de Edgar.
- `docs/ESTRUCTURA.md`: cómo funcionan los bots, el Master y el Supervisor.
- `tradingbots/`: código (supervisor.py, estrategias/, backtest.py, simulador.py, datos.py).

## Al terminar cada sesión, Claude debe
- Actualizar "Estado actual" arriba y agregar una entrada en `docs/BITACORA.md`.
- Hacer commit y push a GitHub.
