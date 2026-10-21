# Resultados E2 y E3 — Mejoras del bot del euro

**E2 (ADOPTADO)** — `PREREGISTRO_E2_filtro_dias_sin_flujo.md`, salida `e2_resultados.txt`. 2018-2026, coste 0,70 pb, riesgo 0,5%.
| | Efecto bruto 06-08 NY | Días |
|---|---|---|
| Festivos europeos/británicos | +0,74 pb (t 0,75) | 66 |
| Días del BCE | +0,37 pb (t 0,13) | 60 |
| Resto | +1,41 pb (t 4,52) | 2.015 |
E1: 5,5%/año, Sharpe 0,66, DD −17,8% → **E2: 6,2%/año, Sharpe 0,77, DD −16,7%.** Coherente con el mecanismo (sin flujo
corporativo europeo no hay ventaja). El EA debe incorporar el filtro (festivos TARGET + Reino Unido + calendario del BCE).

**E3 (RECHAZADO)** — `PREREGISTRO_E3_segunda_pata.md`, salida `e3_resultados.txt`. La primera parte de la mañana europea
(07:00 Londres → 06:00 NY) no tiene efecto en 2018-2026 (+0,18 pb bruto, t 0,41); combinada baja el Sharpe a 0,29.
El efecto del euro se concentra en 06:00-08:00 NY.
