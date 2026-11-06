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

## 2026-11-06 · Sesión 2: parte en vivo
**Hecho:**
- Edgar verificó la conexión al Testnet desde su PC.
- Motor en vivo (`motor.py`) con supervisor, vigilancia de stops con el precio actual y memoria entre reinicios (SQLite).
- Brokers: papel (simulado con precios reales) y Binance (Testnet/real vía ccxt, con comisiones y precisión de Binance).
- Telegram: avisos de cada operación, del supervisor, de errores y resumen diario; comandos /estado /reporte /pausar /reanudar /detener_todo.
- Panel web en http://localhost:8000 con valor total, bots, gráfica, avisos, operaciones con su motivo y botones de control.
- `iniciar_bots.bat` para arrancar con doble clic.
- 24 pruebas pasando. Prueba real en modo papel: compra ejecutada, panel y comandos funcionando, 0 errores.

**Siguiente:**
- Edgar: configurar Telegram, arrancar en Testnet y dejarlo correr; reportar cualquier error.
- Claude: investigar mejores estrategias (validación fuera de muestra); opcional, gráfica de precio con marcas de compra/venta.
