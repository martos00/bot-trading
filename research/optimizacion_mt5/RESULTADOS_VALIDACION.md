# Resultados de la validación (según PREREGISTRO_VALIDACION_OPTIMIZACION.md y apéndices)

## Paso 0a — Reproducción 2025.01.02 – 2026.09.21, OHLC de 1 minuto, archivos `REPRO_*.set` (riesgo 1,5%)
| Candidata | Informe: ops / PF / beneficio | Reproducción: ops / PF / beneficio | Estado |
|---|---|---|---|
| CAND1 (p1400) | 103 / 1,93 / 27.540 $ | **103 / 1,93 / 27.540 $** (20-oct-2026) | **Reproducida exactamente** |
| CAND2 (p2815) | 133 / 1,71 / 23.968 $ | igual al informe (el usuario lo confirma, 20-oct-2026) | **Reproducida** |
| CAND3 (p1374) | 112 / 1,86 / 20.065 $ | igual al informe (el usuario lo confirma, 20-oct-2026) | **Reproducida** |
| CAND4 (p1310) | 158 / 1,80 / 35.702 $ | igual al informe (el usuario lo confirma, 20-oct-2026) | **Reproducida** |
| CAND5 (p2709) | 139 / 1,93 / 33.290 $ | igual al informe (el usuario lo confirma, 20-oct-2026) | **Reproducida** |
| CAND6 (p1381) | 195 / 1,60 / 34.540 $ | igual al informe (el usuario lo confirma, 20-oct-2026) | **Reproducida** |

CAND1 reproducida al dólar: el EA local es el mismo que se optimizó, el riesgo del informe F era **1,5% (verificado)** y el
historial del servidor no ha cambiado. (`InpFixedRR` no interviene en CAND1, que usa TP dinámico.)

Las 6 candidatas se reproducen (el usuario confirma que coinciden con el informe). Queda **verificado**: riesgo 1,5% en
los informes B, D, E y F, mismo EA y mismo historial. CAND6 (TP fijo) también se reproduce con `InpFixedRR = 2`, así que
ese valor queda verificado.

## Paso 0b — Mismas 6 configuraciones, 2025.01.02 – 2026.09.21, "Cada tick basado en ticks reales"
Pendiente.
