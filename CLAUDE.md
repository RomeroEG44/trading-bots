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
- Fase: **0, Fundación** (plan en borrador, aún sin código de trading).
- Bots de prueba elegidos: Bot 1 "DCA" (BTC/USDT) y Bot 2 "Tendencia" (ETH/USDT). Ver `docs/PLAN.md`.
- GitHub: pendiente de conectar.

## Dónde está cada cosa
- `docs/PLAN.md`: plan completo, fases y diseño de los bots.
- `docs/DECISIONES.md`: decisiones tomadas y por qué (no re-discutir lo que ya está ahí).
- `docs/BITACORA.md`: qué se hizo en cada sesión y qué sigue.
- `docs/PREGUNTAS.md`: preguntas abiertas para Edgar.

## Al terminar cada sesión, Claude debe
- Actualizar "Estado actual" arriba y agregar una entrada en `docs/BITACORA.md`.
- Hacer commit y push a GitHub.
