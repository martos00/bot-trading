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

## Paso 0b — Mismas 6 configuraciones, 2025.01.02 – 2026.09.21, "Cada tick basado en ticks reales" (riesgo 1,5%)
Informes en `informes_paso0b/` (Excel del Probador, 20-oct-2026); análisis con `analizar_informes_mt5.py`
(operaciones reconstruidas: el beneficio coincide al céntimo con el informe). **Calidad del historial: 76% ticks reales
en las seis** (el 24% restante, ticks generados). Esto sigue siendo dentro de muestra: es el período optimizado.

| Candidata | OHLC 1 min: ops / PF / beneficio | Ticks reales: ops / PF / beneficio | DD equidad | Cambio del beneficio |
|---|---|---|---|---|
| CAND1 | 103 / 1,93 / 27.540 $ | 101 / 1,71 / 20.143 $ | 12,9% | −27% |
| CAND2 | 133 / 1,71 / 23.968 $ | 127 / 1,46 / 14.834 $ | 10,6% | −38% |
| CAND3 | 112 / 1,86 / 20.065 $ | 111 / 1,78 / 18.266 $ | 12,4% | −9% |
| CAND4 | 158 / 1,80 / 35.702 $ | 151 / 1,40 / 17.042 $ | 17,9% | −52% |
| CAND5 | 139 / 1,93 / 33.290 $ | 136 / 1,59 / 21.217 $ | 8,0% | −36% |
| CAND6 | 195 / 1,60 / 34.540 $ | 187 / 1,33 / 16.867 $ | 15,0% | −51% |

Detalle con ticks reales (posiciones; MT5 cuenta cada cierre parcial como otra operación):

| | CAND1 | CAND2 | CAND3 | CAND4 | CAND5 | CAND6 |
|---|---|---|---|---|---|---|
| Posiciones | 90 | 121 | 84 | 140 | 130 | 187 |
| Aciertos | 45,6% | 47,9% | 41,7% | 42,9% | 45,4% | 42,2% |
| Resultado medio (R) | 0,46 | 0,27 | 0,46 | 0,27 | 0,33 | 0,20 |
| t de la media | 2,64 | 2,05 | 2,41 | 2,04 | 2,56 | 1,94 |
| Racha máx. de pérdidas | 9 | 6 | 9 | 12 | 6 | 10 |
| 2025: posiciones / beneficio / PF | 53 / 15.259 / 2,13 | 81 / 10.816 / 1,54 | 46 / 11.834 / 2,15 | 93 / 11.783 / 1,45 | 84 / 13.996 / 1,70 | 130 / 5.428 / 1,16 |
| 2026: posiciones / beneficio / PF | 37 / 4.884 / 1,33 | 40 / 4.017 / 1,32 | 38 / 6.432 / 1,49 | 47 / 5.259 / 1,32 | 46 / 7.221 / 1,46 | 57 / 11.439 / 1,67 |
| Cortos: beneficio / PF | 12.389 / 2,01 | 8.867 / 1,57 | 10.605 / 2,00 | 8.983 / 1,48 | 9.880 / 1,59 | 9.792 / 1,49 |
| Largos: beneficio / PF | 7.754 / 1,48 | 5.967 / 1,36 | 7.662 / 1,59 | 8.059 / 1,34 | 11.337 / 1,60 | 7.075 / 1,23 |

Lectura: con ticks reales las seis siguen ganando en 2025 y en 2026 y en las dos direcciones, pero pierden entre el 9% y
el 52% del beneficio; las que más dependían del modelado son CAND4 y CAND6 (región R4) y CAND2. Las t (1,9-2,6) están
**infladas por la selección** (mejores de 18.152 combinaciones en este mismo período) y no son evidencia fuera de
muestra. Siguen las seis al paso 1 (2023-2024), como está pre-registrado.
