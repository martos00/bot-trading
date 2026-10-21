# N1-N3 — Familias nuevas con datos distintos del precio: RESULTADOS (21-oct-2026)

Pre-registro: `PREREGISTRO_N1_N3.md` (commit 82ecc27, antes de calcular). Código: `n_familias.py`, `fechas_fomc.py`.
Salida: `n_resultados.txt`. Datos: CBOE (VIX, VIX3M), Yahoo (^GSPC, CL=F, HG=F), federalreserve.gov (FOMC), HistData (FX).

| Familia | Descubrimiento | Confirmación | Veredicto |
|---|---|---|---|
| **N1** VIX/VIX3M → S&P 500 al día siguiente | inversión +11,6 pb vs normal +3,5 pb, t = 0,46 | +9,6 vs +4,5 pb, t = 0,27; regla neta Sharpe 0,12 < siempre largo 0,41 | No confirmada: no hay diferencia significativa |
| **N2** S&P 500 el día del FOMC (1994-2009 / 2010-2026) | **+35,2 pb, t = 3,40** (reproduce Savor-Wilson / Lucca-Moench) | **+10,6 pb, t = 1,08**; neta +8,1 pb (t 0,83); resto de días +4,4 pb | No confirmada: tras la publicación cae ~70% y deja de ser significativa |
| **N3** petróleo → USDCAD | −0,03 pb, t −0,03 | +0,83 pb bruto, neto −0,67 pb | No confirmada |
| **N3** cobre → AUDUSD | +1,25 pb, t 0,82 | −1,05 pb bruto, neto −2,55 pb | No confirmada |

Nota: el precio negativo del WTI de abril de 2020 da un logaritmo no definido; ese día queda excluido.

## Lectura
N2 es el patrón ya visto en todo el proyecto: un efecto académico muy fuerte en su período de estudio (t = 3,4) que, tras
publicarse (2013-2015), se reduce a una fracción no significativa. N1 y N3 no muestran señal en ningún tramo.
Ninguna ventaja nueva. N acumulado: +4.
