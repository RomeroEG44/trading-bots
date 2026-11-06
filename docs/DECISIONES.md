# Decisiones del proyecto

Formato: fecha · decisión · por qué · quién decidió.

- 2026-11-06 · Empezar con 2 bots de prueba · Pedido de Edgar · Edgar
- 2026-11-06 · Bot 1 = DCA en BTC/USDT; Bot 2 = Tendencia (EMA 9/21 + RSI) en ETH/USDT · Uno simple para validar la maquinaria y otro con señales reales; pares con mucha liquidez · Claude (propuesta, pendiente de confirmar)
- 2026-11-06 · Solo Spot, sin apalancamiento · Sin riesgo de liquidación mientras aprendemos · Claude (propuesta, pendiente de confirmar)
- 2026-11-06 · Memoria del proyecto en archivos del repo (`CLAUDE.md` + `docs/`) en lugar de un servidor MCP propio · Claude lee `CLAUDE.md` solo al iniciar sesión; queda guardado en GitHub, con historial y gratis · Claude
- 2026-11-06 · Stack: Python + ccxt + SQLite + FastAPI + Telegram · Simple, estándar y con soporte para el Testnet de Binance · Claude
