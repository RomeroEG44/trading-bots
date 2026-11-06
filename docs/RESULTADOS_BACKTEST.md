# Resultados del backtest (primera ronda) · 2026-11-06

Datos reales de Binance, velas de 1 hora y de 1 día, del **2024-11-06 al 2026-11-06**, más una validación
con 2020-2024. Incluye comisión 0.1 % y deslizamiento 0.05 % por operación. Capital ficticio de 1,000 USDT por bot.

## Lo más importante en 4 frases
1. **Ninguna de las 2 estrategias, tal como las diseñamos, gana dinero de forma confiable.** Esto es normal
   y es exactamente para lo que sirve el backtest: lo descubrimos sin perder un centavo.
2. **Bot Tendencia en velas de 1 hora: pierde mucho** (−51 % a −59 %). Hace cientos de operaciones,
   acierta solo 1 de cada 3, y las comisiones (más de 500 USDT) se comen todo.
3. **Bot Tendencia en velas diarias: casi no gana, pero protege.** En el periodo 2024-2026 ETH cayó −18 % y el bot
   quedó en +0.1 % con una caída máxima de solo −6 %. Pero en los años en que el mercado subió fuerte, se
   quedó muy atrás (por ejemplo +1 % contra +256 %).
4. **Bot DCA = "comprar BTC poco a poco".** El resultado depende casi solo de lo que haga BTC. En este periodo
   compró caro en 2025 y BTC luego cayó, así que va en −7 % a −22 % según el ritmo de compra.

## Comparación de variantes del Bot Tendencia (ETH, 2024-11 → 2026-11, sin límites del supervisor)

| Variante | Resultado | Peor caída | Operaciones | Comisiones | ETH "comprar y esperar" |
|---|---:|---:|---:|---:|---:|
| Velas 1 h (plan original) | −58.7 % | −66 % | 826 | 534 USDT | −10 % |
| Velas 4 h | −43.7 % | −49 % | 244 | 169 USDT | −13 % |
| Velas 4 h, EMA 20/50, SL 5 %, TP 15 % | −44.9 % | −47 % | 76 | 48 USDT | −13 % |
| **Velas 1 día** | **+0.1 %** | **−6 %** | 20 | 18 USDT | −18 % |

## Validación del Bot Tendencia en velas diarias en otros periodos

| Par | Periodo | Bot | Peor caída del bot | Comprar y esperar |
|---|---|---:|---:|---:|
| ETH | 2020-11 → 2022-11 | +1.0 % | −12.7 % | +256.5 % |
| ETH | 2022-11 → 2024-11 | −11.6 % | −16.0 % | +54.3 % |
| ETH | 2024-11 → 2026-11 | +0.1 % | −6.3 % | −17.9 % |
| BTC | 2020-11 → 2022-11 | +6.1 % | −13.5 % | +36.6 % |
| BTC | 2022-11 → 2024-11 | +23.3 % | −5.7 % | +231.5 % |
| BTC | 2024-11 → 2026-11 | +2.0 % | −8.6 % | +0.6 % |

**Lectura:** en velas diarias el bot se comporta como un "seguro": pierde poco cuando el mercado cae, pero
gana muy poco cuando sube. Con solo 10-16 operaciones por periodo, la muestra es pequeña.

## El supervisor
- Con los límites actuales (−3 % diario, −10 % desde el máximo) **sí se activó** varias veces.
  En la primera prueba detuvo todo en enero de 2025 y, como nadie lo reanudó, el resto del backtest quedó congelado.
- Ahora el backtest simula que Edgar reanuda 7 días después de una detención (opción `--reanudar-tras-dias`).
- Los límites redujeron un poco las pérdidas (de −40 % a −37 % en la versión de 1 h), pero **no arreglan una
  mala estrategia**. Solo ponen un freno.

## Qué cambiamos por esto
- Bot Tendencia: de velas de 1 h a **velas de 1 día**.
- Bot DCA: de cada 3 días a **cada semana**, para que el presupuesto alcance todo el periodo.
- Reportes completos en `reports/`.

## Siguiente trabajo de estrategia (propuesto)
- Probar mejoras con método: ajustar con un periodo y validar en otro distinto, para no "hacerle trampa" al pasado.
- Ideas a probar: filtro de tendencia larga (solo comprar si el precio está sobre la media de 200 días), DCA que
  solo compra cuando el precio está bajo su promedio, rotación entre BTC y ETH.
- Seguir con la Fase 2 (Testnet) **en paralelo**, porque la maquinaria (supervisor, panel) sirve
  para cualquier estrategia.
