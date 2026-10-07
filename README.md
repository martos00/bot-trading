# XAUUSD Liquidity Sweep -> MSS -> FVG Retest EA — Baseline 1 (cerrado como candidato de trading)

> **Estado: archivado como baseline de referencia, no como candidato activo
> de trading (octubre 2026).** Tras un proceso de validación en 3 fases
> (ablación de filtros estructurales, barrido de 2 ejes de parámetros
> numéricos, train/validación/out-of-sample separados correctamente) esta
> implementación de la hipótesis Sweep → MSS → FVG no mostró ventaja
> estadística convincente. Ver la sección **"Baseline 1: resultados y
> cierre de la rama"** más abajo para el detalle completo y el
> razonamiento. El código, la gestión de riesgo y el motor de logging se
> conservan intactos como punto de comparación obligatorio para cualquier
> estrategia futura: una hipótesis nueva solo se considera mejor si supera
> a este baseline bajo el mismo protocolo (mismos tramos de fechas, mismo
> criterio de descarte fijado de antemano).

Expert Advisor para MetaTrader 5, diseñado para operar **XAUUSD (Oro)**
combinando un régimen de tendencia en H4 con una secuencia de entrada
100% objetiva en M15: **Liquidity Sweep -> Market Structure Shift (MSS)
-> Fair Value Gap (FVG) Retest**.

> Este EA sustituyó en septiembre de 2026 a una versión anterior basada
> en zonas de Oferta/Demanda + rupturas de trendlines sobre el RSI. La
> gestión de riesgo, ejecución y position management (Kill Switch,
> filtro de spread, cierre de fin de semana, circuito de pérdidas
> consecutivas, breakeven, trailing stop y cierre parcial) se mantuvieron
> sin cambios; sólo cambió la lógica de generación de señales.

Archivo principal: `MQL5/Experts/XAUUSD_SupplyDemand_RSI_EA.mq5` (el
nombre del archivo es un resto de la versión anterior; se mantuvo para
no romper referencias/despliegues existentes — puede renombrarse sin
problema si se prefiere).

> **Hipótesis 2 en curso:** se ha recuperado la estrategia anterior
> (zonas de Oferta/Demanda + rupturas de líneas de tendencia sobre el
> RSI) en `MQL5/Experts/XAUUSD_RSI_Trendline_EA.mq5`, para someterla al
> mismo protocolo de validación que este Baseline 1 antes de decidir si
> reemplaza o complementa la búsqueda de una nueva hipótesis de entrada.
> Ver la sección **"Hipótesis 2: Oferta/Demanda + RSI Trendlines
> (recuperada, pendiente de validar)"** más abajo.

## Instalación

1. Copia el archivo `.mq5` dentro de `MQL5/Experts/` de tu terminal MetaTrader 5
   (`Archivo -> Abrir carpeta de datos -> MQL5 -> Experts`).
2. Compílalo con MetaEditor (F7).
3. Arrástralo sobre un gráfico de **XAUUSD** (el EA usa internamente M15
   para la señal y H4 para el régimen, independientemente de la
   temporalidad del gráfico donde se adjunte).
4. Activa "Permitir trading algorítmico" y, en la pestaña "Dependencias"
   de las propiedades del EA, activa el acceso a archivos si quieres el
   log CSV (`InpRegistrarCSV`).

## Arquitectura de la señal (100% objetiva, sin repintado)

Todas las reglas siguientes se evalúan exclusivamente sobre velas ya
CERRADAS (nunca sobre la vela en formación), y ningún cálculo de una
temporalidad usa información de una vela que temporalmente no habría
existido todavía en la otra temporalidad.

1. **Régimen de mercado (H4)** — `ActualizarRegimen()`:
   alcista si el cierre H4 > EMA(`InpEMARegimenPeriod`, 200 por defecto)
   Y los últimos `InpRegimenSwingsAConfirmar` swing highs y swing lows en
   H4 son crecientes (HH/HL); bajista si el cierre < EMA y los swings son
   decrecientes (LH/LL). Esos swings se buscan retrocediendo
   `InpRegimenHistorialBarras` velas H4 (60 por defecto, ~10 días de
   trading) — este parámetro es independiente de cuántos swings hacen
   falta confirmar (`InpRegimenSwingsAConfirmar`); si no hay swings
   suficientes en esa ventana o la estructura es mixta, el régimen queda
   **INDEFINIDO** y no se buscan setups nuevos. El régimen alcista sólo
   habilita setups LONG; el bajista, sólo SHORT (filtro estricto, no
   "principalmente" — ver "Decisiones de diseño").

2. **Liquidity zones (M15)** — `ReconstruirZonasLiquidez()`, recalculadas
   al cerrar cada vela M15:
   - Previous Week High/Low (importancia 5), Previous Day High/Low (4),
     Equal High/Low (4, agrupando swings dentro de
     `InpEqualToleranceATRMult`×ATR), Asia High/Low (3, sesión
     `InpAsiaInicioHoraNY`–`InpAsiaFinHoraNY` hora de Nueva York), Swing
     High/Low (2, con `InpSwingLeftBars`/`InpSwingRightBars` velas de
     confirmación).
   - Las zonas del mismo lado (buy-side/sell-side) que caen dentro de
     `InpZonaAgrupamientoATRMult`×ATR se fusionan en una sola,
     conservando la de mayor importancia.

3. **Liquidity Sweep** — `BuscarSweepSellSide()` / `BuscarSweepBuySide()`:
   sweep de una única vela cerrada cuya mecha penetra la zona una
   distancia limitada (≤ `InpMaxSweepDistanceATRMult`×ATR(`InpATRPeriod`))
   y cuyo **cierre** vuelve a quedar del lado seguro de la zona. Exige
   interacción real con una zona ya identificada, no cualquier mecha.
   Solo se consideran zonas con importancia ≥ `InpImportanciaMinimaZona`
   (2=Swing High/Low, 3=Asia High/Low, 4=Equal High/Low y PDH/PDL,
   5=PWH/PWL); por defecto vale 2, es decir, no filtra ninguna.

4. **Market Structure Shift (MSS)** — `ComprobarMSS()`: tras el sweep, se
   localiza el último swing significativo confirmado **antes** del sweep
   (nunca después) y se espera un cierre que lo supere (LONG) o lo pierda
   (SHORT) en una vela **posterior** al sweep.

5. **Fair Value Gap (FVG)** — `BuscarFVG()` / `DetectarFVG()`: tras el
   MSS, se busca el primer hueco de 3 velas en la dirección del
   movimiento (low actual > high de 2 velas atrás para FVG alcista, y a
   la inversa para bajista). Si `InpUsarFiltroFVGMinimo` está activo se
   ignoran los huecos menores a `InpFVGMinSizeATRMult`×ATR.

6. **Retest y entrada**: al encontrar un FVG válido, el EA coloca una
   **orden límite** (`BuyLimit`/`SellLimit`) al `InpFVGEntryPercent`%
   de profundidad del FVG (25/50/75/100, 50% por defecto), con
   expiración de `InpSetupMaxBarras` velas M15. La secuencia completa
   (Sweep → MSS → FVG → Retest → Entry) es obligatoria: si cualquier
   paso falla o expira, no hay operación.

7. **Invalidación**: si mientras se espera el FVG o el retest el precio
   cierra de nuevo más allá del nivel del MSS (en contra), la orden
   pendiente se cancela y el setup se descarta.

## Stop Loss y Take Profit

- **SL**: `sweep_low - InpSLBufferATRMult×ATR` (LONG) /
  `sweep_high + InpSLBufferATRMult×ATR` (SHORT) — invalida directamente
  la hipótesis del sweep.
- **TP — Modo A** (`InpModoTP = MODO_TP_FIJO_RR`): fijo a `InpFixedRR`
  (2.0 por defecto).
- **TP — Modo B** (`InpModoTP = MODO_TP_SIGUIENTE_LIQUIDEZ`): la
  liquidity zone relevante más cercana en dirección del trade cuyo RR
  implícito ya cumpla `InpMinimumRR`.
- Si el TP lógico más cercano no alcanza `InpMinimumRR` (2.0 por
  defecto), **no se abre la operación** (se descarta el setup), en
  ambos modos.

## Position Sizing y límites

- Riesgo como % del balance (`InpRiskPercent`, valores previstos
  0.25/0.50/0.75/1.00, **0.50% por defecto**), vía `CalcularLotaje()` +
  `OrderCalcProfit()` (sin martingala: el riesgo nunca cambia tras una
  pérdida).
- Antes de enviar la orden límite se comprueba con `OrderCalcMargin()` que
  el margen requerido para el lotaje calculado no supere el margen libre
  de la cuenta; si lo supera (SL anormalmente cerca del entry en momentos
  de ATR muy bajo, lo que dispara el lotaje según el % de riesgo) se
  descarta el setup en vez de enviar una orden que el bróker rechazaría
  igualmente por "not enough money".
- Máximo `InpMaxOperacionesPorSesion` operaciones por sesión (sesión =
  día de trading del servidor, 2 por defecto).
- Una única posición gestionada a la vez (no se buscan setups nuevos con
  una posición u orden pendiente ya abierta), lo que además impide
  automáticamente abrir una segunda operación en la misma dirección.
- Cada sweep que llega a abrir una operación queda consumido (el setup
  se resetea nada más rellenarse la orden), evitando reentradas sobre el
  mismo sweep.

## Gestión de posición, riesgo institucional y filtros (heredados sin cambios)

- **Breakeven** (`InpUsarBreakeven`, `InpBreakevenTriggerR`,
  `InpBreakevenBufferPips`), **cierre parcial + trailing**
  (`InpUsarCierreParcial`, `InpCierreParcialPercent`,
  `InpCierreParcialTriggerR`, `InpUsarTrailingStop`,
  `InpTrailingDistanceR`).
- **Kill Switch diario** (`InpMaxDailyLossPercent`), **filtro de spread**
  (`InpMaxSpreadPips`), **circuito de pérdidas consecutivas**
  (`InpMaxPerdidasConsecutivas`), **cierre de fin de semana**
  (`InpCerrarViernes`, `InpFridayCloseHourNY`, `InpBrokerGMTOffsetHrs`),
  **filtro de horario de sesión** (`InpUsarFiltroSesion`,
  `InpSesionInicioHoraNY`, `InpSesionFinHoraNY`; ahora sólo bloquea la
  búsqueda de sweeps **nuevos**, no la gestión de un setup/posición ya en
  curso).

## Log CSV de operaciones

Con `InpRegistrarCSV = true` (por defecto), cada operación cerrada se
añade a `InpNombreArchivoCSV` (`LiquiditySweepMSS_FVG_Log.csv` por
defecto, en la carpeta `MQL5/Files/` del terminal o `Tester/Files/` si
corre en el Strategy Tester) con: fecha/hora de apertura y cierre,
dirección, tipo e importancia de la liquidity zone barrida, precio y
distancia del sweep, nivel del MSS, límites del FVG, precio de entrada,
SL, TP, RR planeado, resultado en R, resultado monetario, duración,
drawdown durante la operación y régimen 4H vigente.

Este log es necesario porque el informe nativo del Strategy Tester de
MT5 no separa resultados por dirección ni por tipo de zona, ni calcula
CAGR o Sortino. Para esas métricas, usa el script complementario:

```
python3 analysis/analizar_backtest.py "<ruta al CSV>" --balance-inicial <balance_inicial_del_test>
```

(requiere `pandas`/`numpy`; instala con `pip install pandas numpy` si
hace falta). Calcula Net Profit, CAGR, Max Drawdown, Sharpe/Sortino
(aproximados a nivel de operación), Profit Factor, Win Rate, Average
Win/Loss, Expectancy, nº de operaciones, R medio, mejor/peor operación,
rachas de ganadoras/perdedoras consecutivas y exposición media —
globalmente y desglosado por LONG/SHORT y por tipo de liquidity zone.

## Validación / Walk-Forward

El repositorio no incluye un motor de backtesting propio: el backtest se
ejecuta en el Strategy Tester nativo de MetaTrader 5. Para la división
70% desarrollo / 15% validación / 15% out-of-sample, ejecuta tres
backtests separados (mismo EA compilado, mismos parámetros) cambiando
sólo el rango de fechas del Tester a los tres tramos correspondientes de
tu histórico disponible, y compara los informes (y los CSV, con el
script de arriba) entre sí. Para walk-forward, el Strategy Tester de
MT5 incluye un campo nativo "Forward" en la configuración del test que
reserva automáticamente el tramo final del rango como período de
validación separado del de optimización — actívalo si vas a optimizar
alguno de los parámetros listados más abajo.

**No optimices ningún parámetro usando el tramo out-of-sample.**

## Parámetros pensados para pruebas de robustez (no para maximizar el resultado histórico)

`InpSwingLeftBars`/`InpSwingRightBars`, `InpEqualToleranceATRMult`,
`InpMaxSweepDistanceATRMult`, `InpSLBufferATRMult`, `InpFVGMinSizeATRMult`,
`InpFVGEntryPercent`, `InpMinimumRR`, `InpRiskPercent`,
`InpUsarFiltroSesion`/`InpSesionInicioHoraNY`/`InpSesionFinHoraNY`.

## Pruebas de ablación de filtros (¿aporta este filtro, o solo resta operaciones?)

Para saber si un filtro concreto realmente mejora el resultado o solo
reduce la frecuencia de operaciones sin ninguna mejora a cambio,
desactívalo y compara contra el backtest base (mismo rango de fechas,
mismos parámetros, todo lo demás igual):

- `InpUsarFiltroRegimen = false` — el EA busca sweeps LONG y SHORT sin
  exigir que el régimen H4 esté definido ni que coincida con la
  dirección del sweep. **Este es el filtro que más operaciones
  descarta** (con datos reales del primer backtest, el régimen solo
  estuvo definido en 44 ventanas a lo largo de ~20 meses).
- `InpUsarFiltroSesion = false` — se buscan sweeps a cualquier hora,
  no solo en `InpSesionInicioHoraNY`–`InpSesionFinHoraNY`.
- `InpUsarFiltroFVGMinimo = false` — se aceptan FVG de cualquier
  tamaño, sin el mínimo de `InpFVGMinSizeATRMult`×ATR.

Compara siempre nº de operaciones, Net Profit, Profit Factor y Win
Rate (con `analizar_backtest.py`) entre el test base y cada variante
con un filtro desactivado — no solo el balance final, que con pocas
operaciones puede ser engañoso. Si desactivar un filtro sube el número
de operaciones pero hunde el Profit Factor, el filtro estaba haciendo
su trabajo; si el Profit Factor se mantiene o mejora, ese filtro era
prescindible.

## Baseline 1: resultados y cierre de la rama

Esta sección documenta el proceso completo de validación que llevó a
archivar esta implementación de Sweep → MSS → FVG como **Baseline 1** en
vez de seguir iterando sobre ella. El objetivo de dejarlo por escrito no
es decir "esto no sirve", sino dejar un punto de comparación reproducible:
cualquier estrategia futura sobre XAUUSD M15 debería, como mínimo, igualar
estos números bajo el mismo protocolo (mismos tramos de fechas, mismo
criterio de descarte fijado de antemano) antes de considerarse una mejora
real.

**Protocolo usado:** split temporal fijo, nunca reajustado a posteriori —
`train` = 2025 completo, `val` = 2026 H1, `OOS` (out-of-sample) = 2026
jul-sep. Los criterios de descarte se fijaron antes de ver los resultados
de cada fase. Todas las métricas de esta sección están extraídas de los
logs del Journal del Tester (no del CSV estructurado del EA), por lo que
el Win Rate es aproximado — ver la cabecera de
`analysis/extraer_metricas.py`-equivalente usado para el cálculo.

### Fase A — Ablación de filtros estructurales (V0–V5)

Variantes probadas (cada una desactivando uno o varios filtros respecto a
V0, la configuración base con todos los filtros activos):

- **V0** — baseline, todos los filtros activos.
- **V1** — `InpUsarFiltroRegimen = false`.
- **V2** — `InpUsarFiltroSesion = false`.
- **V3** — `InpUsarFiltroFVGMinimo = false`.
- **V4** — `InpUsarFiltroRegimen = false` + `InpUsarFiltroSesion = false`.
- **V5** — `InpImportanciaMinimaZona` subido respecto a V0 (filtro más
  estricto, no más laxo, usado como contraste).

| Variante | Trades (train+val+OOS) | Net Profit total | Max DD (peor tramo) | Trades OOS | Net Profit OOS |
|---|---|---|---|---|---|
| V0 | 27  | -4378.54 | 11.16% | 3  | -1283.37 |
| V1 | 149 | -4608.78 | 19.96% | 18 | -2120.61 |
| V2 | 187 | -2578.60 | 25.36% | 12 | -719.50  |
| V3 | 167 | -4431.58 | 18.69% | 23 | -1540.82 |
| V4 | 206 | -3641.60 | 32.05% | 13 | -673.07  |
| V5 | 42  | -210.83  | 14.43% | 4  | -1643.82 |

Criterios de descarte pre-registrados (una variante se consideraba viable
sólo si cumplía los tres a la vez): Net Profit total > 0, Max Drawdown en
el peor tramo ≤ 20%, y Net Profit en OOS ≥ 0 (no solo positivo en
train/val).

**Resultado: ninguna de las 6 variantes cumple los tres criterios a la
vez.** Quitar filtros (V1-V4) multiplica el número de operaciones por 5-8x
respecto a V0, pero en ningún caso convierte el resultado en rentable de
forma consistente en los tres tramos — de hecho empeora el drawdown
sustancialmente (V4 llega a 32% frente al 11% de V0). Apretar el filtro de
importancia de zona (V5) mejora el Net Profit total frente a V0 pero sigue
siendo negativo y con muy pocas operaciones (42 en ~20 meses) para sacar
conclusiones robustas. No hay ninguna variante donde "menos filtros, más
operaciones" se traduzca en una ventaja estadística real.

### Fase B — Barrido de sensibilidad en 2 ejes numéricos (solo tramo train)

Realizado únicamente sobre `train`, sin tocar `val` ni `OOS`, para buscar
si existía una **región de estabilidad** (varios valores vecinos
positivos o con tendencia clara) en vez de limitarse a optimizar un único
valor puntual.

**Eje 1 — Ratio Riesgo:Recompensa (`InpFixedRR` / `InpMinimumRR`):**

| RR | Trades | Net Profit | Max DD% | Win Rate~% |
|---|---|---|---|---|
| 1.2 | 16 | -1733.67 | 9.29%  | 31.2% |
| 1.4 | 16 | -2320.90 | 11.91% | 25.0% |
| 1.6 | 16 | -2563.53 | 11.59% | 18.8% |
| 1.8 | 16 | -2400.38 | 11.44% | 18.8% |
| 2.0 | 16 | -2199.80 | 11.16% | 18.8% |
| 2.2 | 15 | -1665.15 | 10.90% | 20.0% |
| 2.5 | 15 | -2138.60 | 10.48% | 13.3% |
| 3.0 | 15 | -1928.95 | 10.13% |  0.0% |

**Eje 2 — Colchón del stop loss (`InpSLBufferATRMult`):**

| SL buffer | Trades | Net Profit | Max DD% | Win Rate~% |
|---|---|---|---|---|
| 0.05 | 16 | -2190.97 | 11.25% | 18.8% |
| 0.10 | 16 | -2177.88 | 11.25% | 18.8% |
| 0.15 | 16 | -2251.88 | 11.31% | 18.8% |
| 0.20 | 16 | -2199.80 | 11.16% | 18.8% |
| 0.30 | 15 | -1905.14 | 11.37% | 20.0% |
| 0.40 | 15 | -1930.37 | 11.50% | 20.0% |
| 0.50 | 15 | -856.40  | 8.62%  | 26.7% |
| 0.60 | 15 | -1178.23 | 8.58%  | 26.7% |

**Resultado: en ninguno de los dos ejes aparece una región de
estabilidad ni un cruce a positivo.** Los 16 valores probados (8 por eje)
son negativos en train. Hay una mejora leve y gradual al final de cada
rango (RR alto, SL buffer alto) pero ninguna se acerca a Net Profit
positivo, y el patrón es consistente con ruido / achicamiento de muestra
(menos trades al ser más estricto) más que con una señal real. No se
encontró ningún valor ni combinación que justificara pasar a validar en
`val`/`OOS`.

### Veredicto y qué queda probado (y qué no)

- **No queda probado** que la secuencia Liquidity Sweep → MSS → FVG sea
  estructuralmente inviable en XAUUSD M15.
- **Sí queda probado** que *esta implementación concreta* — estas
  definiciones exactas de sweep, MSS, FVG, estos filtros y estos rangos
  de parámetros — no muestra una ventaja estadística convincente frente
  al protocolo de validación aplicado (34 pruebas en total: 18 de
  ablación + 16 de sensibilidad numérica), y que no hay indicios de que
  afinar más los parámetros vaya a cambiar esa conclusión: no apareció
  ninguna región de estabilidad, solo valores puntuales negativos.
- Seguir buscando una combinación ganadora dentro de esta misma
  arquitectura a base de más pruebas tiene alto riesgo de terminar en
  overfitting por pura casualidad estadística, no en una ventaja real.
- Por eso se archiva como **Baseline 1**: el código, la gestión de
  riesgo y el motor de logging se conservan intactos (no se borra nada),
  y cualquier estrategia nueva que se diseñe a partir de aquí debe
  compararse contra estos mismos números bajo el mismo protocolo antes
  de reemplazarla.

## Hipótesis 2: Oferta/Demanda + RSI Trendlines (recuperada, pendiente de validar)

Esta no es una hipótesis de entrada nueva: es la estrategia que este
repositorio usaba **antes** de la reescritura a Sweep → MSS → FVG,
recuperada del historial de git (commit `a9252a4`, el último antes de
`7bd8fb6` "Sustituir la estrategia de señal por Liquidity Sweep -> MSS ->
FVG Retest"). Se recupera porque, a diferencia de Sweep→MSS→FVG, nunca
pasó por el protocolo riguroso train/validación/OOS — se abandonó sin
haberse evaluado correctamente, así que es candidata legítima antes de
diseñar una hipótesis completamente distinta.

**Archivo:** `MQL5/Experts/XAUUSD_RSI_Trendline_EA.mq5`.

**Lógica de la señal:** zonas de Oferta/Demanda en una temporalidad macro
(`Temporalidad_Liquidez`, H1 por defecto) como contexto, con gatillo de
entrada por ruptura (breakout) de líneas de tendencia dibujadas sobre
pivotes del RSI en la temporalidad de ejecución (M5 por defecto) — un
enfoque de momentum/ruptura sobre un oscilador, conceptualmente distinto
de los conceptos de price-action puro (ICT/SMC) usados en Baseline 1.
Toda la detección de pivotes y rupturas usa velas cerradas (sin
repintado).

**Qué se cambió respecto a la versión original (`a9252a4`), y por qué:**

- **Se eliminó el módulo de auto-optimización semanal walk-forward**
  (`EjecutarOptimizacionSemanal`), que recalibraba en caliente el
  lookback de las zonas y el período del RSI cada semana según la
  volatilidad reciente. Ese ajuste dinámico de parámetros *dentro* del
  propio backtest hace que un split train/validación/OOS no mida lo que
  debería (el EA se reoptimiza solo según lo que ve en cada tramo, en
  vez de usarse con parámetros fijados de antemano). `InpZonaLookbackMacro`
  e `InpRSIPeriod` vuelven a ser inputs fijos normales (100 y 14 por
  defecto, los mismos valores con los que arrancaba el módulo antes de
  su primera recalibración).
- **Se añadió la misma comprobación de margen (`OrderCalcMargin` +
  `ACCOUNT_MARGIN_FREE`) que en Baseline 1**, antes de enviar la orden de
  venta o de compra, para descartar con un mensaje `[DIAG]`-equivalente
  cualquier operación cuyo lotaje por riesgo% exija más margen del
  disponible, en vez de dejar que el bróker la rechace en silencio.
- El resto (gestión de riesgo, Kill Switch, filtro de spread, cierre de
  fin de semana, circuito de pérdidas consecutivas, breakeven, trailing
  stop, cierre parcial, filtro de sesión, filtro de tendencia macro,
  filtro de zona fresca) se mantiene exactamente igual que en la versión
  original — no se ha tocado ninguna regla de gestión de posición.

**Protocolo de validación pendiente de ejecutar (idéntico al de
Baseline 1, para que la comparación sea justa):**

1. Backtest en `train` (2025 completo) con los parámetros por defecto, sin
   tocar nada todavía.
2. Si `train` muestra algo mínimamente prometedor, backtest en `val`
   (2026 H1) con los mismos parámetros exactos.
3. Sólo si ambos tramos son razonables, backtest final en `OOS` (2026
   jul-sep), una única vez, sin ajustar nada después de verlo.
4. Mismos criterios de descarte que en Baseline 1: Net Profit total > 0,
   Max Drawdown en el peor tramo ≤ 20%, Net Profit en OOS ≥ 0.
5. Si se quiere explorar sensibilidad de parámetros, aplicar la misma
   disciplina de Fase B de Baseline 1 (barrido en `train` únicamente,
   buscando región de estabilidad, nunca tocar `val`/`OOS` para elegir
   valores).

Todavía no se ha ejecutado ningún backtest de esta hipótesis en este
repositorio — esta sección se actualizará con la tabla de resultados y
el veredicto en cuanto estén disponibles los backtests de `train`.

## Objetivos de investigación (no garantizados)

CAGR ≥ 25%, Max Drawdown ≤ 20%, Profit Factor ≥ 1.5, Sharpe ≥ 1.0 sobre
un período histórico largo. Son objetivos a **comprobar empíricamente**
ejecutando el backtest — no se ha forzado ni asumido que la estrategia
los alcance; si no se alcanzan, el resultado real es el que hay que
reportar.

## Advertencia

Antes de usarlo en una cuenta de fondeo real, realiza pruebas
exhaustivas en el Strategy Tester (modo "Cada tick basado en datos
reales") y en cuenta demo. Verifica que `InpBrokerGMTOffsetHrs` esté
correctamente calibrado (afecta al cierre de fin de semana, la sesión
asiática y el filtro de horario de sesión) y que el símbolo `XAUUSD` de
tu bróker coincide con el usado en el gráfico donde se adjunta el EA.
