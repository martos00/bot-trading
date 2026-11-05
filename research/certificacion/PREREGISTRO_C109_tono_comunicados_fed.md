# PREREGISTRO C109 — Tono de los comunicados de la Fed (FOMC) y bono, dólar y oro en los días siguientes — 05-nov-2026

Redactado y subido a git ANTES de descargar los comunicados y calcular. Hipótesis (literatura de análisis de texto de bancos
centrales): un comunicado más «duro» que el anterior predice, en los días siguientes y no solo en el primer minuto, bonos a la baja,
dólar al alza y oro a la baja (el mercado tarda en incorporar del todo el cambio de tono).

## Medida del tono (mecánica; NO se puntúa a mano para evitar sesgo de conocimiento posterior)
Texto del comunicado de política monetaria (federalreserve.gov, monetaryAAAAMMDDa.htm), en minúsculas. Recuento de expresiones:
- Duras: "raise the target range", "increase the target range", "firming", "tighten", "tightening", "strong", "strengthened",
  "solid", "robust", "elevated", "upside risk", "further increases", "additional increases", "reduce its holdings",
  "reducing its holdings", "balance sheet reduction".
- Blandas: "lower the target range", "reduce the target range", "decrease the target range", "accommodative", "accommodation",
  "easing", "weak", "weakened", "slowed", "moderated", "downside risk", "patient", "increase its holdings", "purchases of",
  "exceptionally low", "slack", "subdued", "soft".
Tono = (D − B) / (D + B). Señal = tono − tono del comunicado anterior; si es 0, no se opera. Reuniones programadas de
`n/fomc.csv` con comunicado disponible, 2010-01 → 2026-10.

## Operación (futuros Databento 1 h, hora NY; precio = cierre de la barra de las 15:00, ≈ 16:00 ET)
Posición contraria al endurecimiento: si la señal > 0 → corto ZN (bono 10 años), corto 6E (euro = dólar al alza), corto GC (oro);
al revés si < 0. Desde las 16:00 del día del comunicado hasta las 16:00 del día hábil +1 (h1) y +5 (h5). Resultados en desviaciones
de cada activo para poder juntarlos.

## Criterio
Prueba principal (2): media de los 3 activos juntos para h1 y para h5. Descubrimiento 2010-2017: media > 0. Confirmación 2018-2026:
media > 0 con t ≥ 2,24 (Bonferroni 0,05/2). Informativo: cada activo por separado y la señal binaria (subida/bajada de tipos).
Contador +2.
