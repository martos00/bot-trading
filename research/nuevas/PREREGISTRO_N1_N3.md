# Pre-registro N1-N3 — Tres familias nuevas con datos distintos del precio (21-oct-2026)

Redactado y enviado a git ANTES de calcular ningún resultado. Ninguna se había probado así en el proyecto. N acumulado: +4.
Costes de CFD de fondeo para mantener una noche (cruza el cierre de las 17:00 NY): índice S&P 500 — spread 0,5 pb +
financiación 2,0 pb por noche en largo (≈ tipo + 2,5% anual / 360); divisas — spread 1,0 pb + financiación 0,5 pb por noche.

## N1 — Estructura de plazos del VIX → S&P 500 al día siguiente
Datos: CBOE VIX y VIX3M (cierres diarios, desde 2006), S&P 500 (^GSPC, Yahoo). Señal al cierre del día t:
cociente VIX / VIX3M. Inversión (> 1, pánico de corto plazo) frente a normal (< 1). Rentabilidad = cierre t → cierre t+1.
Hipótesis bilateral: la rentabilidad del día siguiente difiere entre los dos estados.
- Descubrimiento 2006-07 → 2015-12: diferencia de medias con |t| ≥ 2,5. El signo decide la regla:
  largo el día siguiente solo en el estado bueno (si es "inversión → peor", la regla es "largo solo en estado normal").
- Confirmación 2016 → 2026-10: la regla, neta de costes, con Sharpe mayor que estar siempre largo (neto) y la diferencia de
  medias del mismo signo con t ≥ 2.
Aviso para fondeo: mantener el índice de un día para otro tiene caídas de mercado; se informa del drawdown.

## N2 — Días de anuncio del FOMC (Savor-Wilson 2013; Lucca-Moench 2015)
Datos: fechas oficiales de las reuniones programadas del FOMC 1994-2026 (federalreserve.gov, `fechas_fomc.py`; 8 al año,
7 en 2020), S&P 500 diario. Regla: largo del cierre del día anterior al cierre del día del anuncio.
- Descubrimiento 1994-2009 (período de los estudios originales): media > 0 con t ≥ 2.
- **Confirmación 2010-2026 (posterior a la publicación)**: media neta > 0 con t ≥ 2 y mayor que la media de los demás
  días (t de la diferencia ≥ 1,645); positiva en ≥ 60% de los años.

## N3 — Materias primas → divisas al día siguiente
Datos: petróleo WTI (CL=F) y cobre (HG=F) de Yahoo (cierre ≈ liquidación, antes de las 15:00 NY); USDCAD y AUDUSD de
HistData M1 (hora de NY). Señal: signo de la rentabilidad de la materia prima del día t. Operación de 16:00 NY del día t a
16:00 NY del día t+1 (evita el artefacto de las 16:55-17:00). Previsión: petróleo ↑ → CAD se aprecia → venta de USDCAD;
cobre ↑ → AUD se aprecia → compra de AUDUSD (y al revés si bajan). 2 pruebas.
- Descubrimiento 2010-2017: media > 0 con t ≥ 2,24 (Bonferroni para 2).
- Confirmación 2018-2026: media neta > 0 con t ≥ 2,24; positiva en ≥ 6 de 9 años.

Lo que pase va a certificación con otra fuente de datos, como C1.
