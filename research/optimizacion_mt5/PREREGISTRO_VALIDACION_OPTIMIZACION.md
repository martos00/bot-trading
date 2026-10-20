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
| CAND1 | régimen H4 | 1,93 | 103 | 1,92 | `CAND1_F_sinH4.set` |
| CAND2 | régimen H4 + sesión | 1,71 | 133 | 1,78 | `CAND2_B_sinH4_sinSesion.set` |
| CAND3 | régimen H4 + FVG mínimo | 1,86 | 112 | 1,72 | `CAND3_E_sinH4_sinFVGmin.set` |
| CAND4 | régimen H4 + sesión + FVG mínimo ("SIN NADA") | 1,80 | 158 | 1,69 | `CAND4_D_sinNingunFiltro.set` |

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
