# Decisiones del proyecto

Formato: fecha · decisión · por qué · quién decidió.

- 2026-11-06 · Empezar con 2 bots de prueba · Pedido de Edgar · Edgar
- 2026-11-06 · Bot 1 = DCA en BTC/USDT; Bot 2 = Tendencia (EMA 9/21 + RSI) en ETH/USDT · Uno simple para validar la maquinaria y otro con señales reales; pares con mucha liquidez · Claude (propuesta, pendiente de confirmar)
- 2026-11-06 · Solo Spot, sin apalancamiento · Sin riesgo de liquidación mientras aprendemos · Claude (propuesta, pendiente de confirmar)
- 2026-11-06 · Memoria del proyecto en archivos del repo (`CLAUDE.md` + `docs/`) en lugar de un servidor MCP propio · Claude lee `CLAUDE.md` solo al iniciar sesión; queda guardado en GitHub, con historial y gratis · Claude
- 2026-11-06 · Stack: Python + ccxt + SQLite + FastAPI + Telegram · Simple, estándar y con soporte para el Testnet de Binance · Claude
- 2026-11-06 · Capital real inicial (Fase 3): ~40 USD en total · Dato de Edgar · Edgar
- 2026-11-06 · Con 40 USD: 20 USDT por bot; DCA compra 5 USDT cada 3 días (mínimo de orden en Binance ≈ 5 USDT); Bot Tendencia opera con hasta 18 USDT por operación · Ajuste al capital real; los montos del plan v0.1 (10 USDT/día) se aplican solo en Testnet · Claude (propuesta)
- 2026-11-06 · GitHub: usuario RomeroEG44, repo privado `trading-bots` · Dato de Edgar · Edgar
- 2026-11-06 · Bot Tendencia pasa de velas 1 h a **1 día** · En 1 h: −59 % por exceso de operaciones y comisiones; en 1 d: +0.1 % con caída máx. −6 % (ver RESULTADOS_BACKTEST) · Claude (propuesta, pendiente de confirmar)
- 2026-11-06 · Bot DCA compra **semanal** (antes cada 3 días) · Que el presupuesto dure todo el periodo · Claude (propuesta)
- 2026-11-06 · Los bots que operan corren en la PC de Edgar (o VPS en país permitido) · Binance bloquea la API desde la nube de Claude · Restricción técnica
- 2026-11-06 · Ventas siempre permitidas aunque el supervisor esté pausado/detenido; solo se bloquean compras · Un stop-loss nunca debe quedar bloqueado · Claude
- 2026-11-06 · **Se elimina Telegram**; todo el seguimiento se hace en el panel web · Pedido de Edgar · Edgar
- 2026-11-06 · **Bot Master** que supervisa a los demás: ajusta tamaño, enfría, pone en cuarentena, cierra posiciones y retira bots · Pedido de Edgar; reglas propuestas por Claude · Edgar + Claude
- 2026-11-06 · **6 bots rápidos en paralelo** (1 a 15 min) en Testnet, en lugar de un DCA semanal · Pedido de Edgar: resultados en horas · Edgar
- 2026-11-06 · **Autonomía total**: nada pide confirmación; el Supervisor se reanuda solo 2 h después de una detención automática · Pedido de Edgar · Edgar
- 2026-11-06 · El modo REAL sigue exigiendo `--confirmo-dinero-real` una sola vez al arrancar (nunca por operación) · Evitar arrancar con dinero real por error · Claude
- 2026-11-06 · En Testnet, las velas y los precios vienen del propio Testnet (antes, de los datos públicos) · Que las señales coincidan con los precios a los que se opera · Claude
- 2026-11-06 · **Escáner** de todos los pares USDT y bots **cazadores** que eligen su mercado (par `auto`) · Pedido de Edgar ("que los bots vean todos los mercados") · Edgar
- 2026-11-06 · Panel estilo "Sala de bots" (oscuro, agentes, sala animada, mercados, umbrales, metas) · Referencia visual de Edgar (videos de Grokbot) · Edgar
- 2026-11-06 · Se excluyen monedas estables, oro y acciones tokenizadas (AAPLB, NVDAB...) · No son cripto o no se mueven · Claude
- 2026-11-06 · No se copian los bots de memecoins de Solana de los videos · Riesgo extremo, fuera de Binance, y esas promociones suelen ser estafas · Claude
