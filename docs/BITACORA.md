# Bitácora de sesiones

## 2026-11-06 · Sesión 1
**Hecho:**
- Se definió la idea: bots en Binance + bot supervisor + panel.
- Se creó la memoria del proyecto (`CLAUDE.md`, `docs/`).
- Borrador del plan v0.1 con 2 bots de prueba (DCA BTC y Tendencia ETH).

**Pendiente / siguiente:**
- Edgar: conectar GitHub y crear el repo `trading-bots`; responder `docs/PREGUNTAS.md`.
- Claude: subir todo a GitHub y arrancar la Fase 0 (estructura de código + conexión de solo lectura al Testnet).

## 2026-11-06 · Sesión 1 (continuación)
**Hecho:**
- Repo conectado y subido a GitHub.
- Entorno de Claude "trading-bots" con acceso a datos de Binance. La API de trading está bloqueada desde la nube.
- Código base: supervisor de riesgo, simulador con comisiones, estrategias DCA y Tendencia, backtest, verificador de conexión.
- 14 pruebas automáticas (pytest) pasando.
- Backtest de 2 años + validación 2020-2024. Resultados en `docs/RESULTADOS_BACKTEST.md`.
- Se corrigió un error del caché de datos que dejaba huecos.

**Siguiente:**
- Edgar: instalar en su PC (`docs/GUIA_INSTALACION.md`), crear claves del Testnet y correr `verificar_conexion`.
- Claude: Fase 2, motor "en vivo" (papel/Testnet) con base de datos, bot de Telegram y panel web; en paralelo, mejorar estrategias con validación fuera de muestra.
