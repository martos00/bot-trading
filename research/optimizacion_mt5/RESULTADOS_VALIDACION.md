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

## Paso 1 — 2023.01.01 – 2024.12.31, riesgo 0,5%, parámetros congelados (informes del 20-oct-2026)
Informes en `informes_paso1/`. Comprobado que los parámetros de entrada de los seis informes son **idénticos** a los `.set`
congelados (salvo el riesgo, 0,5%, como estaba previsto). **Calidad del historial: 0% ticks reales en los seis**: el
servidor MetaQuotes-Demo no tiene ticks reales de XAUUSD en 2023-2024 y MT5 los generó desde las velas de 1 minuto.

| | CAND1 | CAND2 | CAND3 | CAND4 | CAND5 | CAND6 |
|---|---|---|---|---|---|---|
| Región | R1 | R2 | R3 | R4 | R2 | R4 |
| Beneficio neto | **+278 $** | **−2.581 $** | **−186 $** | **−2.075 $** | **−1.742 $** | **−1.579 $** |
| Profit factor | 1,03 | 0,80 | 0,98 | 0,86 | 0,88 | 0,92 |
| Operaciones MT5 / posiciones | 125 / 119 | 175 / 168 | 161 / 134 | 225 / 217 | 193 / 186 | 270 / 270 |
| DD de equidad | 11,3% | 14,7% | 11,9% | 17,4% | 12,8% | 15,6% |
| Aciertos | 35,3% | 33,9% | 36,6% | 36,9% | 36,0% | 38,1% |
| Resultado medio (R) | +0,02 | −0,13 | −0,01 | −0,08 | −0,07 | −0,04 |
| t de la media / p bootstrap | 0,18 / 0,43 | −1,19 / 0,88 | −0,04 / 0,51 | −0,81 / 0,79 | −0,74 / 0,77 | −0,56 / 0,71 |
| Racha máx. de pérdidas | 10 | 11 | 12 | 14 | 10 | 18 |
| 2023: beneficio / PF | +397 / 1,10 | −642 / 0,90 | +434 / 1,09 | −3.355 / 0,56 | −602 / 0,92 | −2.015 / 0,80 |
| 2024: beneficio / PF | −119 / 0,98 | −1.938 / 0,69 | −620 / 0,88 | +1.281 / 1,17 | −1.140 / 0,83 | +436 / 1,05 |
| Cortos: beneficio / PF | −1.615 / 0,64 | −2.261 / 0,66 | −1.080 / 0,80 | −2.243 / 0,65 | −1.812 / 0,76 | −485 / 0,94 |
| Largos: beneficio / PF | +1.894 / 1,43 | −320 / 0,95 | +894 / 1,18 | +169 / 1,02 | +71 / 1,01 | −1.094 / 0,91 |

Frente a 2025-2026 con ticks reales: el resultado medio pasa de +0,20 / +0,46 R a −0,13 / +0,02 R y los aciertos de 42-48%
a 34-38%, en las seis y en las cuatro regiones a la vez.

### Clasificación según el apéndice 1
- **Etiqueta principal de las seis: "Calidad de datos insuficiente"** (0% de ticks reales < 90%). Por la regla
  pre-registrada, este resultado no se interpreta formalmente ni a favor ni en contra.
- Atendiendo solo a las cifras, las seis caerían en "sin rentabilidad" (beneficio ≤ 0 o PF < 1,1); ninguna se acerca a
  "prometedora" (ninguna gana los dos años, ninguna llega a PF 1,3, ninguna tiene t > 0,2).
- **Argumento adicional (no pre-registrado, se declara como tal):** el sesgo de los ticks generados va **a favor** de la
  estrategia. En 2025-2026, pasar de OHLC de 1 minuto a ticks reales redujo el beneficio de las seis (−9% a −52%). Si con
  un simulador optimista 2023-2024 sale plano o negativo, con ticks reales lo esperable es igual o peor. Por eso la falta de
  ventaja es informativa aunque la etiqueta formal sea de calidad.
- Las cuatro regiones fallan en la misma dirección: no hay ninguna región con evidencia a favor.

### Conclusión
No hay evidencia de una ventaja reproducible fuera del período optimizado. El patrón (muy bueno en el período optimizado,
plano o negativo fuera de él, en todas las candidatas a la vez) es el típico del sobreajuste por selección entre 18.152
combinaciones. **No procede la simulación de fondeo ni el forward en demo.** No se cambia ningún parámetro.
Única prueba pendiente que podría cambiar la etiqueta formal: repetir 2023-2024 con ticks reales de otra fuente (por
ejemplo, ticks de Dukascopy importados como símbolo personalizado en MT5); por el argumento anterior, no se espera que
cambie la conclusión.

## Cierre (20-oct-2026)
**Descartada por decisión del usuario** tras el paso 1. Las 6 configuraciones quedan archivadas sin modificar. No se
reabrirá esta optimización ni se buscarán nuevas combinaciones de la misma arquitectura sobre estos datos.
