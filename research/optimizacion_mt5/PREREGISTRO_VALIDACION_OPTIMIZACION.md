# Validación de la optimización de MT5 del EA Sweep → MSS → FVG (archivo `XAUUSD_SupplyDemand_RSI_EA.mq5`)

Redactado el 20-oct-2026, ANTES de ejecutar ninguna prueba nueva. No se cambia nada después de ver resultados.

## Qué hay en los 6 informes (leídos completos: `leer_optimizaciones.py`)
- XAUUSD M15, **2025-01-02 → 2026-09-21**, depósito de 25.000 $, servidor MetaQuotes-Demo.
- **18.152 combinaciones** probadas en total. El número de pasadas (≈1.400-4.900 de ≈420.000 posibles) indica
  que se usó el **algoritmo genético**: busca alrededor de las mejores, así que el porcentaje de combinaciones
  positivas (52-77%) está inflado y no mide la robustez de la estrategia.
- Las mejores (+600% a +858%) arriesgan **≈4% por operación** (informe A, riesgo optimizado), con un drawdown
  del 20-25%: incompatibles con cualquier cuenta de fondeo (FTMO: pérdida máxima 10%).
- El informe C (todos los filtros) tiene una mediana de 7 operaciones en 21 meses: no es evaluable.

## Problemas que impiden dar por buena la optimización
1. **No queda ningún dato sin usar dentro del período**: la optimización cubre train 2025, validación 2026-H1 y
   OOS 2026 jul-sep. Todo lo que muestran los informes es dentro de muestra.
2. **Sesgo de selección**: el mejor de 18.152 intentos sale alto aunque no haya ventaja.
3. **Calidad de datos**: en 2025 el historial tenía solo un 60% de ticks reales (README); las entradas con orden
   límite en el FVG son sensibles a ticks sintéticos.
4. 2025 fue un año de subida del oro del +70%; casi todas las operaciones de train fueron compras.

## Candidatas (regla de selección por meseta, `seleccionar_candidatas.py`)
En cada informe: ≥ 60 operaciones, ≥ 4 vecinas evaluadas, máxima **mediana del profit factor de las vecinas**.
A y F son el mismo filtro y la misma zona de parámetros: se valida solo la de F. Total: **4 candidatas**.

| Candidata | Filtros desactivados | PF en el informe | Ops | PF mediano de vecinas | Archivo |
|---|---|---|---|---|---|
| CAND1 | régimen H4 | 1,93 | 103 | 1,92 | `CAND1_SIN_REGIMEN_H4_SOLAM_p1400.set` |
| CAND2 | régimen H4 + sesión | 1,71 | 133 | 1,78 | `CAND2_SIN_REGIMEN_H4_Y_SIN_p2815.set` |
| CAND3 | régimen H4 + FVG mínimo | 1,86 | 112 | 1,72 | `CAND3_SIN_REGIMEN_H4_Y_SIN_p1374.set` |
| CAND4 | régimen H4 + sesión + FVG mínimo ("SIN NADA") | 1,80 | 158 | 1,69 | `CAND4_SIN_NADA_p1310.set` |

Todas usan TP dinámico (Modo B). Supuesto a confirmar por el usuario: "SIN NADA" = los tres filtros desactivados.

## Protocolo
**Paso 0 — Reproducción** (comprueba que los `.set` son correctos). Cada `.set` en 2025-01-02 → 2026-09-21, con el
mismo riesgo que en la optimización original. Debe salir el mismo número de operaciones (±2) y el mismo PF (±0,05)
que el informe; si no, se revisa la configuración antes de seguir.

**Paso 1 — Fuera de muestra hacia atrás: 2023-01-01 → 2024-12-31** (datos que la optimización no vio).
"Cada tick basado en ticks reales", **riesgo 0,5%**, el resto igual. Anotar la calidad del historial (% de ticks reales).
Una candidata pasa si cumple **todo**: beneficio neto > 0 en 2023 **y** en 2024 por separado; PF ≥ 1,3 en el conjunto;
≥ 50 operaciones; drawdown de equity ≤ 10%.
Con 4 candidatas, que una pase por azar es posible: si pasa una, se exige también el paso 2.

**Paso 2 — Simulación de fondeo y forward**: con la lista de operaciones de 2023-2024, Monte Carlo de FTMO 2-Step y
Topstep (`research/fondeo/simulador_fondeo.py`), comparado con una estrategia sin ventaja con el mismo riesgo; después,
demo en tiempo real ≥ 3 meses sin tocar nada.

Si ninguna pasa el paso 1, la optimización queda descartada como sobreajuste y la familia se cierra definitivamente.

---

## Apéndice 1 (20-oct-2026, antes de ejecutar ninguna prueba): 6 candidatas, regiones, verificaciones y plan de análisis

Este apéndice **sustituye** al protocolo y a los criterios de arriba en lo que contradiga. Se añaden dos pasadas
propuestas por el usuario. Todavía no existe ningún resultado de reproducción ni de 2023-2024.

### Candidatas y regiones de parámetros
| Candidata | Informe | Pasada | PF | Ops | DD | Región |
|---|---|---|---|---|---|---|
| CAND1 | SIN_REGIMEN_H4_SOLAMENTE | 1400 | 1,93 | 103 | 13,4% | **R1** |
| CAND2 | SIN_REGIMEN_H4_Y_SIN_SOLO_BUSCAR_SEEPS… | 2815 | 1,71 | 133 | 10,3% | **R2** |
| CAND5 | SIN_REGIMEN_H4_Y_SIN_SOLO_BUSCAR_SEEPS… | 2709 | 1,93 | 139 | 7,5% | **R2** |
| CAND3 | SIN_REGIMEN_H4_Y_SIN_IGNORAR_FVG… | 1374 | 1,86 | 112 | 13,7% | **R3** |
| CAND4 | SIN_NADA | 1310 | 1,80 | 158 | 17,5% | **R4** |
| CAND6 | SIN_NADA | 1381 | 1,60 | 195 | 8,3% | **R4** |

- **R2 = CAND2 + CAND5:** mismos filtros; solo cambia `InpFVGEntryPercent` (25 → 50), un paso de rejilla.
- **R4 = CAND4 + CAND6:** mismos filtros (ninguno). `InpFVGMinSizeATRMult` no tiene efecto en ese informe (verificado:
  108 de 108 grupos dan resultado idéntico), así que la diferencia efectiva es sweep 1,0 → 0,9 y SL 0,4 → 0,3 (un paso
  cada uno) y la salida (TP dinámico frente a TP fijo). Las entradas son casi las mismas: se tratan como **dos
  variantes de salida de la misma región**, no como estrategias independientes.
- R1 y R3 están a ≥ 11 pasos de cualquier otra. **Hay 4 regiones, no 6 estrategias.** Además todas comparten la lógica
  Sweep → MSS → FVG y el mismo período de optimización, así que incluso las 4 regiones están correlacionadas.
- Para el control de pruebas múltiples se cuentan **6 configuraciones probadas** (lo conservador).

### Verificaciones hechas con los archivos (sin suponer valores por defecto)
- Los XML de MT5 **no contienen los parámetros fijos** (solo las columnas optimizadas): el riesgo de los informes
  B, D, E, F y `InpFixedRR` **no se pueden leer** de ellos.
- **Riesgo**: estimación indirecta, no verificación. La configuración de CAND1 gana 131.289 $ con 4,0% de riesgo en el
  informe A y 27.540 $ en el informe F; por la capitalización compuesta, F usó ≈ 1,5%. Para B, D y E no hay forma de
  estimarlo con los archivos.
- **`InpFixedRR`**: el EA solo acepta una operación con TP fijo si `InpFixedRR ≥ InpMinimumRR`. En los 6 informes,
  con TP fijo hay operaciones si `InpMinimumRR ≤ 2,00` y **cero si ≥ 2,25** → **2,00 ≤ InpFixedRR < 2,25** en todas
  las optimizaciones. Valor exacto pendiente de confirmar en MT5.
- **Filtro de FVG mínimo**: desactivado en SIN_NADA y en SIN_REGIMEN_H4_Y_SIN_IGNORAR_FVG… (el parámetro no tiene
  ningún efecto en ellos) y activo en los demás (sí lo tiene). El filtro de sesión no se puede comprobar con los datos.
- **Modo de modelado**: los XML tienen `<Condition>0</Condition>`; si corresponde al modo de modelado sería "Cada tick"
  (ticks generados), no "ticks reales". **Sin confirmar**.
- El informe COMPLETO se generó con un EA llamado "XAUUSD_SupplyDemand_RSI_EA **(1)**": puede ser otra copia del
  archivo. Pendiente de confirmar que todas las optimizaciones usaron la misma versión.

### Paso 0 — Reproducción con la configuración original exacta (obligatorio antes del paso 1)
La configuración exacta se recupera de MT5 (no de supuestos): en el Probador, pestaña de resultados de cada
optimización, doble clic en la pasada; MT5 carga **todos** los parámetros con que se ejecutó, incluidos los fijos.
Se guarda ese conjunto como `.set` y se ejecuta una prueba simple 2025.01.02 – 2026.09.21 con el mismo modelado.
- **Reproducida**: mismas operaciones (±2) y PF (±0,05) que el informe.
- Si no se reproduce, se documenta la diferencia y **no se pasa al paso 1 con esa candidata** hasta entender la causa
  (versión del EA, modelado, datos del servidor o parámetros).
- Los `.set` exportados de MT5 sustituyen a los generados por `generar_set.py` en todo lo que no sea el riesgo.

### Paso 1 — 2023-01-01 → 2024-12-31, sin cambiar ningún parámetro, riesgo 0,5% en las 6
Modelado "Cada tick basado en ticks reales" si el servidor los tiene; si no, el mejor disponible, declarado.

### Qué se informa de cada candidata (todo, sin descartes automáticos)
Rentabilidad neta, profit factor, drawdown de equity (máximo y relativo), número de operaciones, % de aciertos,
resultado medio por operación en R, y **lo mismo por año (2023 y 2024)**; compras frente a ventas; calidad del
historial (% de ticks reales) y huecos detectados; con la lista de operaciones, t de la media por operación y p de
bootstrap.

### Clasificación (sustituye a los criterios de "pasa / no pasa" de arriba)
Cada candidata recibe **una** etiqueta principal, y se muestran todas las cifras aunque no cumpla algún umbral:
1. **Calidad de datos insuficiente**: < 90% de ticks reales en algún año, o huecos > 3 días hábiles. El resultado se
   muestra pero no se interpreta como prueba a favor ni en contra.
2. **Operaciones insuficientes**: < 50 operaciones en los dos años, o < 20 en alguno. No concluyente por tamaño.
3. **Sin rentabilidad**: datos y muestra suficientes, pero beneficio neto ≤ 0 o PF < 1,1.
4. **Débil / inconsistente**: beneficio > 0 pero PF entre 1,1 y 1,3, o un año negativo, o DD > 10%.
5. **Prometedora**: beneficio > 0 en 2023 **y** en 2024, PF ≥ 1,3, ≥ 50 operaciones, DD ≤ 10%, y t ≥ 2 de la media
   por operación.

**Lectura por regiones**: una región cuenta como evidencia solo si sus variantes van en la misma dirección; R2 y R4
con una variante "prometedora" y otra "sin rentabilidad" se consideran frágiles. Con 6 configuraciones, una sola
"prometedora" puede ser azar (p ≈ 1 − 0,95⁶ ≈ 26% de que al menos una pase el umbral de t ≥ 2 por suerte):
cualquier "prometedora" necesita además el paso 2 (simulación de fondeo y forward en demo ≥ 3 meses) antes de
considerarse una ventaja.

### Prohibido después de ver 2023-2024
Cambiar cualquier parámetro, filtro, período o riesgo de las 6 configuraciones; añadir candidatas nuevas elegidas
mirando 2023-2024; repetir la optimización sobre 2023-2024. Cualquier idea nueva será una hipótesis nueva con sus
propios datos sin usar.
