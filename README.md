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
>
> **Corrección importante (octubre 2026):** el diagnóstico forense de
> Hipótesis 2 reveló que su lógica de señal era una aproximación propia
> inspirada en dos indicadores de TradingView, no una réplica fiel de
> ellos. Se ha creado `MQL5/Experts/XAUUSD_RSI_Trendline_Fiel_EA.mq5`
> con una reconstrucción fiel de ambos indicadores ("Supply and Demand
> Visible Range [LuxAlgo]" y "RSI Trendlines with Breakouts [HG]" de
> HoanGhetti). Ver la sección **"Hipótesis 2 Fiel: reconstrucción exacta
> de los indicadores de TradingView"** más abajo. Todos los resultados
> previos de Hipótesis 2 (embudo de entrada, filtro de tendencia,
> distancia a MA200) siguen siendo válidos como hechos sobre *esa
> implementación concreta*, pero ya no pueden usarse para afirmar nada
> sobre los indicadores originales de LuxAlgo/HoanGhetti.
>
> **Hipótesis 2 cerrada (octubre 2026):** ninguna de las cuatro
> configuraciones probadas (aproximada/fiel, con/sin filtro de
> tendencia) mostró ventaja — ver la sección **"Cierre de Hipótesis 2
> (ambas variantes: aproximada y fiel)"** para la tabla completa de
> resultados. Se pasó a una hipótesis de **continuación de tendencia**
> (Tendencia H1 + Pullback + confirmación en M15, sólo a favor de
> tendencia), implementada en
> `MQL5/Experts/XAUUSD_Trend_Pullback_EA.mq5` tras 4 rondas de revisión
> de la especificación.
>
> **Hipótesis 3 también cerrada (octubre 2026):** Train 2025 pasó los
> criterios de descarte de forma poco convincente (Profit Factor 1,11,
> 92% de las operaciones en el lado de compra durante uno de los años
> más alcistas del oro en la historia); la Validación H1 2026, con
> 100% de datos reales, fue claramente perdedora en ambas direcciones
> (Profit Factor 0,46, Win Rate 25%). Se descarta como candidata a
> operar con dinero real — ver la sección **"Hipótesis 3: Tendencia
> (H1) + Pullback + confirmación de continuación (M15)"**, apartado
> "Cierre: resultados reales y decisión".

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

**Resultados obtenidos (Train 2025 → Validation H1 2026 → OOS jul-sep 2026):**

| Tramo | Operaciones | Resultado |
|---|---|---|
| Train 2025 | 7 | +1,28% |
| Validation H1 2026 | 1 | +4,39% |
| OOS jul-sep 2026 | 2 | -1,38% |
| **Total** | **10** | **≈ +4,3%** |

El +4,3% acumulado no es fiable como evidencia de ventaja: son sólo 10
operaciones en ~21 meses de histórico, una muestra demasiado pequeña
para afirmar nada estadísticamente. El OOS tampoco falla de forma
contundente (no hay un drawdown catastrófico) — el problema real es que
la estrategia **apenas encuentra ocasiones para operar** (2 operaciones
en casi 3 meses de OOS). Por tanto, de momento:

- No hay evidencia de edge.
- No hay frecuencia suficiente para evaluarlo con rigor estadístico.
- No tiene sentido optimizar RR/SL/etc. sobre esta muestra.
- Tampoco se puede concluir que la idea de Oferta/Demanda + RSI
  Trendlines sea mala en sí misma — sólo que *esta implementación* está
  demasiado restringida.

**Instrumentación de diagnóstico añadida (no afecta a ninguna regla de
trading, sólo cuenta):** antes de tocar ningún parámetro, se añadió un
embudo de contadores para medir, con datos, qué condición elimina más
oportunidades en vez de asumirlo:

- Ancho en $ de cada zona de Oferta/Demanda calculada (media y mediana)
  — la zona se define como el rango entre el extremo y el cierre de una
  sola vela de `Temporalidad_Liquidez`, así que puede ser muy estrecha.
- Nº de "toques" de cada zona (flanco de entrada, no cada tick dentro),
  y de esos toques, cuántos ocurrieron en horario de sesión válido y
  cuántos con un breakout de RSI ya vigente.
- Nº de breakouts de RSI detectados (bajista/alcista) por separado.
- Nº de veces que zona y breakout coinciden a la vez, y de esas
  coincidencias, cuántas se pierden por el filtro de tendencia, por el
  de sesión o por el de zona fresca.
- Nº de ventas/compras finalmente ejecutadas.

El resumen se imprime una única vez al final del backtest (`OnDeinit`),
con media/mediana del ancho de zona y el desglose completo separado
para el lado de venta y el de compra. No cambia ninguna condición de
entrada, salida ni gestión de posición — es sólo instrumentación de
lectura.

**Pendiente:** ejecutar un backtest en `train` (2025) con esta
instrumentación y usar el embudo resultante para decidir, con datos, si
el problema es que la estrategia es demasiado restrictiva (y en qué
punto exacto) o si la señal en sí apenas se da en la práctica.

**Resultado de esta investigación (resumen, ver detalle completo en
`XAUUSD_RSI_Trendline_Fiel_EA.mq5` más abajo):** la instrumentación
descartó la hipótesis del ancho de zona (se tocan miles de veces al
año) y mostró que el filtro de tendencia es imprescindible (quitarlo
da 81 operaciones pero -27,33% y 28,40% de drawdown), mientras que la
zona fresca apenas influye (quitarla sólo añade 2 operaciones). El
análisis de las operaciones que sobreviven mostró que ocurren muy
cerca de la MA200 (media 6,33$ en el Train original, frente a 64,26$
en las descartadas), aunque sin relación clara con cruces recientes de
la media. **En paralelo, al revisar el código fuente real de los
indicadores de TradingView en los que se basa esta hipótesis, se
descubrió que la implementación de este archivo es una aproximación
propia, no una réplica fiel** — ver la siguiente sección.

## Hipótesis 2 Fiel: reconstrucción exacta de los indicadores de TradingView

Al pedir el código fuente (Pine Script) de los dos indicadores en los
que se basa Hipótesis 2, se encontraron diferencias estructurales
importantes respecto a la implementación de
`XAUUSD_RSI_Trendline_EA.mq5`. Esta sección documenta esas diferencias
y la reconstrucción fiel, en
`MQL5/Experts/XAUUSD_RSI_Trendline_Fiel_EA.mq5` — un archivo hermano
que **no sustituye** al anterior (que se conserva intacto como
referencia de "nuestra propia aproximación"), sino que representa la
misma hipótesis implementada fielmente a los indicadores originales.

### Diferencias encontradas

**"Supply and Demand Visible Range [LuxAlgo]"** (zonas de Oferta/Demanda):

- El indicador real NO define la zona como "rango entre el extremo y el
  cierre de una vela" — eso era una simplificación propia. Calcula un
  **umbral de volumen acumulado**: divide el rango de precios en
  `Resolution` niveles (por defecto 50) y usa datos **intrabar** (de una
  temporalidad inferior) para acumular el volumen cuyo high/low cae en
  cada nivel, hasta que el acumulado supera `Threshold %` (por defecto
  10%) del volumen total.
- El indicador real opera sobre el **rango visible del gráfico**
  (`chart.left_visible_bar_time`/`right_visible_bar_time`), un concepto
  interactivo/manual sin equivalente automático — se sustituye por una
  ventana fija de `InpSDLookbackVelas` velas (300 por defecto), dejando
  el cálculo de umbral de volumen en sí fiel al original.
- Nota sobre el volumen: XAUUSD (como la mayoría de CFDs/Forex) no tiene
  volumen real centralizado — se usa `tick_volume` como proxy, igual que
  haría el feed del bróker del lado de TradingView para el mismo
  símbolo. No es una debilidad de esta réplica en particular.

**"RSI Trendlines with Breakouts [HG]"** (de HoanGhetti):

- Pivotes **asimétricos**: el original usa siempre 1 barra a la
  izquierda (fijo) y `Lookback Range` barras a la derecha (por defecto
  4) — no un mismo valor configurable para ambos lados como en
  Hipótesis 2 (que usaba 3/3 simétrico).
- La línea de tendencia sólo se **redefine** cuando dos pivotes
  consecutivos del mismo tipo mantienen la estructura esperada (valles
  cada vez más altos / picos cada vez más bajos); si el pivote más
  reciente rompe ese patrón, la línea activa no cambia y sigue
  extrapolándose desde el último par válido. Hipótesis 2 conectaba
  simplemente los dos pivotes más recientes, sin este filtro de
  coherencia direccional.
- La ruptura exige que el RSI supere la línea por un margen
  (`RSI Difference`, por defecto 3 puntos) — no un cruce marginal
  cualquiera como en Hipótesis 2 (margen cero).
- No hay ventana de validez temporal: una vez armada, la ruptura
  permanece válida hasta que la línea se redefine o una operación la
  consume — Hipótesis 2 inventó una caducidad de `InpSignalValidityBars`
  velas que no existe en el indicador original.

### Qué se mantiene igual

Toda la gestión de riesgo y posición (Kill Switch, filtro de spread,
cierre de fin de semana, circuito de pérdidas consecutivas, breakeven,
trailing stop, cierre parcial, filtro de sesión, filtro de tendencia
macro, filtro de zona fresca, comprobación de margen) y toda la
instrumentación de diagnóstico (embudo de entrada, estado de tendencia
por operación, resultado real por operación) se mantienen exactamente
iguales que en Hipótesis 2, sin tocar una sola línea.

### Protocolo pendiente (en orden, sin optimizar todavía)

1. **Compilar** `XAUUSD_RSI_Trendline_Fiel_EA.mq5` en MetaEditor.
2. **Verificar visualmente** 10-20 señales: comparar fecha/hora de
   zonas y rupturas de RSI generadas por el EA en el log contra el
   mismo símbolo/rango de fechas en TradingView con los dos indicadores
   originales cargados. Si no coinciden, seguir corrigiendo la
   implementación antes de continuar.
3. Sólo entonces, repetir el protocolo completo desde cero: Train 2025
   → Validation H1 2026 → OOS jul-sep 2026, con los mismos criterios de
   descarte pre-registrados que en Baseline 1.

**Resultado del Train 2025 completo (bug de indexación por buffer ya
corregido, ver más abajo):** **0 operaciones en todo el año** (0 ventas,
0 compras), con **el 100% de las 8.551 coincidencias zona+breakout
bloqueadas por el filtro de tendencia** en ambos lados (7.369 en venta,
1.182 en compra; "sobreviven AMBOS filtros" = 0 en los dos). Esto es
más restrictivo que Hipótesis 2 (que sí tenía 7 operaciones/año con el
mismo filtro de tendencia sin tocar).

**Causa raíz identificada: el filtro de tendencia macro no pertenece a
los indicadores originales de TradingView.** Revisando el historial de
git, el filtro (`FiltroTendenciaPermiteVenta()`/`Compra()`, MA200 sobre
`Temporalidad_Liquidez`) se añadió en el commit `8ed41fc` ("Add macro
trend filter to reduce counter-trend whipsaws"), **después** de que la
estrategia original ya existiera, y con el objetivo explícito (cita
textual del commit) de "sitting out counter-trend reversals that
previously worked" — es decir, se diseñó específicamente para bloquear
operaciones a contra-tendencia, mirando resultados de un backtest
anterior. La estrategia de Oferta/Demanda + ruptura de RSI es, por
construcción, una estrategia de **reversión** (se opera cuando el
precio toca una zona y el momentum del RSI rompe en el sentido
contrario al movimiento reciente) — casi siempre a contra-tendencia
macro. Un filtro diseñado para eliminar justo ese tipo de operación,
aplicado a una señal que es aún más "reversión pura" tras la
reconstrucción fiel (pivotes asimétricos + filtro de coherencia +
margen de RSI, menos señales pero más nítidas), explica sin necesidad
de ningún bug por qué el bloqueo llega al 100%.

Más importante: este filtro nunca debió formar parte de la línea base
de esta hipótesis — no es de LuxAlgo ni de HG, es un ajuste posterior
hecho mirando el backtest de una versión anterior y distinta del bot,
justo lo que el protocolo de este repositorio pretende evitar antes de
medir una línea base limpia. **Se ha desactivado por defecto**
(`InpUsarFiltroTendencia = false`) en `XAUUSD_RSI_Trendline_Fiel_EA.mq5`
para que el Train 2025 mida la estrategia tal como la definen los dos
indicadores, sin overlays añadidos después. Se mantiene el input como
toggle opcional por si se quiere estudiar como variante aparte, nunca
como parte del baseline inicial.

Se mantiene también la instrumentación añadida
(`g_diagDistMAVentaSobrevive/Bloqueada`, `g_diagDistMACompraSobrevive/Bloqueada`)
por si se retoma el filtro como variante más adelante, aunque ya no es
necesaria para explicar el resultado de 0 operaciones.

**Resultado real del Train 2025 sin el filtro de tendencia (primera
medición limpia de la estrategia tal cual la definen los dos
indicadores):** **167 operaciones** (148 ventas + 19 compras),
**balance final 16.159,03 € desde 25.000 € de partida (-35,36%)**. El
log muestra el `KILL SWITCH` (pérdida diaria ≥4%) y el circuito de 3
pérdidas consecutivas disparándose repetidamente durante casi todo el
año — las pérdidas llegan en rachas, no aisladas. Con el filtro de
tendencia desactivado, el filtro que ahora domina el bloqueo de
entradas es el de **zona fresca** (86% de las coincidencias en venta y
84% en compra se pierden por zona ya tocada), no la tendencia.

Esto confirma, con una muestra mucho mayor, lo que ya apuntaba
Hipótesis 2 (quitar el filtro de tendencia daba 81 operaciones pero
-27,33% y 28,40% de drawdown): la señal de zona + ruptura de RSI, sin
el filtro de tendencia que la bloquea casi por completo, **no tiene
ventaja real — pierde dinero de forma consistente**, no de forma
aislada o por mala suerte en un tramo concreto. Con el filtro puesto,
la estrategia casi no encuentra ocasión de operar (0 operaciones en
todo 2025); sin él, opera con frecuencia pero pierde. Ninguno de los
dos extremos muestra evidencia de edge.

**Conclusión sobre el criterio de descarte pre-registrado:** Net
Profit > 0 en Train falla de forma contundente (-35,36%), así que no
tiene sentido continuar a Validación H1 2026 ni a OOS jul-sep 2026 con
esta hipótesis — el resultado ya es lo bastante claro en Train. Queda
pendiente decidir si se abandona definitivamente la idea de
Oferta/Demanda + RSI Trendlines (en cualquiera de sus dos variantes,
aproximada o fiel) y se pasa a explorar una hipótesis de entrada
distinta del menú original (tendencia+pullback, breakout+retest,
momentum tras expansión de volatilidad, reversión a la media,
apertura/sesión+expansión, estructura de volatilidad+continuación,
enfoque cuantitativo puro).

Todavía no se ha completado la verificación manual de 10-20 señales
(paso 2) con rigor total — se hizo una verificación más ligera (3
rupturas de RSI comprobadas a mano contra TradingView) que encajó
razonablemente bien, con algo más de rupturas en el log que en
TradingView (atribuible a los límites de `max_bars_back` de Pine en
fechas antiguas, no investigado más a fondo).

## Cierre de Hipótesis 2 (ambas variantes: aproximada y fiel)

Ambas implementaciones de Oferta/Demanda + RSI Trendlines (`XAUUSD_RSI_Trendline_EA.mq5`
y `XAUUSD_RSI_Trendline_Fiel_EA.mq5`) se archivan sin continuar a
Validación/OOS. Resumen de todas las mediciones hechas en Train 2025:

| Configuración | Operaciones | Resultado Train 2025 |
|---|---|---|
| Aproximada, ambos filtros activos | 7 | +1,28% |
| Aproximada, sin filtro de tendencia | 81 | -27,33% (drawdown 28,40%) |
| Fiel, con filtro de tendencia | 0 | no evaluable |
| Fiel, sin filtro de tendencia | 167 | -35,36% |

**Veredicto:** con el filtro de tendencia puesto, la estrategia apenas
encuentra ocasión de operar; sin él, opera con frecuencia pero pierde
dinero de forma consistente (no por mala suerte en un tramo concreto:
las pérdidas llegan en rachas marcadas por disparos repetidos del kill
switch y del circuito de pérdidas consecutivas). Ninguna de las cuatro
configuraciones probadas muestra evidencia de ventaja. Esto demuestra
que **estas implementaciones concretas** no superan una prueba inicial
razonable — no se puede concluir que la idea de Oferta/Demanda + RSI
Trendlines de LuxAlgo/HoanGhetti sea en sí misma mala, sólo que no se
ha conseguido traducir a una regla de entrada rentable en MT5 con la
gestión de posición de este repositorio.

No se investiga más esta hipótesis (no se ajustan RSI, SL/TP ni
parámetros de zona buscando que 2025 salga rentable — sería la misma
búsqueda de parámetros que el proyecto evita). Se pasa a una familia de
estrategias distinta.

## Hipótesis 3: Tendencia (H1) + Pullback + confirmación de continuación (M15)

**Estado: CERRADA — no supera la Validación H1 2026, se descarta como
candidata a operar con dinero real (ver "Cierre" más abajo).**
Implementada en `MQL5/Experts/XAUUSD_Trend_Pullback_EA.mq5`, archivo
independiente — no comparte código con ningún otro EA del repositorio
(toda la infraestructura de riesgo/ejecución se copió, no se importó
ni se modificó ninguno de los otros archivos).

Se abandona la dependencia de dos indicadores de reversión/momentum
que, en las pruebas de Hipótesis 2, no demostraron ventaja. La nueva
hipótesis es de **continuación de tendencia**, no de reversión:

- **Tendencia principal:** determinada en H1 (estructura de precio +
  media móvil), igual que el filtro de tendencia usado en Hipótesis 2
  pero aquí como núcleo de la señal, no como overlay añadido después.
- **Pullback:** retroceso dentro de esa tendencia sin invalidar la
  estructura.
- **Confirmación:** señal objetiva de reanudación del movimiento en
  M15, sin anticiparse al pullback.
- **Dirección de las operaciones:** **solo a favor de la tendencia
  H1** — decisión explícita para no mezclar dos hipótesis distintas
  (continuación vs reversión) en la misma medición inicial. Se podrá
  explorar contra-tendencia más adelante como variante separada, nunca
  como parte de la línea base.
- **Objetivo de frecuencia** (de diseño, no demostrado): en torno a 2
  operaciones/semana de media — un objetivo que orienta el diseño de
  las reglas, no un mínimo que se fuerce ajustando las reglas después
  de ver que no se alcanza.

**Disciplina a seguir desde el principio** (acordada para evitar los
problemas de Hipótesis 2):

1. Reglas de entrada inequívocas, sin conceptos visuales que se
   traduzcan de forma distinta al código.
2. Verificar la ejecución real (señales, entradas/salidas, spread,
   gestión de riesgo) antes de sacar conclusiones del backtest.
3. Criterios de evaluación fijados antes de correr el backtest.
4. Train 2025 / Validación H1 2026 / OOS jul-sep 2026 sin reutilizar
   OOS para ajustar nada.
5. Evaluar rentabilidad y riesgo juntos (profit neto, drawdown, nº de
   operaciones, expectativa por operación, estabilidad temporal), no
   sólo si Train sale en positivo.
6. Revisar cómo afectan el kill switch y el circuito de pérdidas
   consecutivas a la distribución de resultados (en Hipótesis 2
   dispararon con mucha frecuencia y claramente dieron forma a las
   rachas de pérdida).

### Especificación final (tras 4 rondas de revisión)

- **Tendencia H1:** EMA200 + estructura (últimos 2 swing highs/lows
  confirmados crecientes/decrecientes, swings 3/3). Idéntico patrón al
  "régimen H4" de Baseline 1, retimetrizado a H1.
- **Secuencia de pivotes M15** (swings 2/2), compra: `Lo` (origen) →
  `HiImp` (impulso, ≥1,0×ATR(14) M15) → `LoPb` (retroceso, por encima
  de `Lo`) → `HiPb` (extremo relevante, máximo decreciente por debajo
  de `HiImp`) → cierre M15 > `HiPb`. Venta: secuencia espejo exacta.
  Cada pivote se re-ancla al candidato confirmado más reciente
  disponible en cada vela (evita quedarse enganchado al primer
  candidato si aparece uno mejor).
- **Cancelación:** cambio de régimen H1, cierre que rompe el nivel de
  origen, o caducidad de 48 velas M15 **contadas desde la confirmación
  del extremo relevante** (no desde su pivote ni desde el impulso).
- **Entrada:** intento único al confirmarse la ruptura — si se bloquea
  por spread, riesgo, distancia al SL/TP, margen o rechazo del
  servidor, la configuración se consume (no se reintenta en velas
  posteriores a un precio distinto).
- **SL:** extremo del propio retroceso (`LoPb`/`HiPb`) ∓ `max(spread
  actual, 0,1×ATR(14) M15)`. **TP:** RR=1,5 fijo. **Riesgo:** 0,5%,
  con redondeo de volumen **sólo hacia abajo** — si el volumen mínimo
  del bróker ya excede el riesgo autorizado, se rechaza la operación
  (nunca se sube el riesgo para poder ejecutar la señal).
- **Registro:** CSV con timestamps de pivote y de confirmación por
  separado para cada swing, velas entre impulso y ruptura, Bid/Ask
  antes del envío, precio solicitado vs. precio real de ejecución
  confirmado por MT5, riesgo estimado antes de ejecutar vs. riesgo real
  recalculado con el precio de ejecución, y el motivo exacto de
  cualquier intento rechazado.
- **Sin filtros nuevos:** no se añadió RSI, MACD, ATR como filtro de
  entrada, ni filtro horario — sólo la secuencia de tendencia+pullback.

### Protocolo de evaluación

Entrenamiento: 2025 completo. Validación: enero-junio 2026.
**Julio-septiembre de 2026 se trata como exploratorio, no como OOS
independiente** — ese tramo ya se miró en el cierre de Baseline 1 y en
la configuración por defecto de Hipótesis 2 aproximada, así que no es
una prueba intacta para esta hipótesis. Queda pendiente reservar un
tramo posterior aún no utilizado por ninguna hipótesis anterior como
evaluación fuera de muestra real — hay que comprobar en el terminal
MT5, en el momento de ejecutar cada test, hasta qué fecha llega el
histórico disponible (el Journal muestra las líneas `history
synchronized from ... to ...` / `ticks synchronized from ... to ...`).
En corridas anteriores de este repositorio, los ticks reales del
bróker demo empezaban el 2025-05-27 (antes de eso, Train 2025
enero-mayo se genera sintéticamente a partir de velas OHLC) — hay que
reconfirmar ambos límites antes de interpretar cualquier resultado,
porque el histórico del bróker demo puede haberse ampliado desde
entonces.

### Cierre: resultados reales y decisión

| Métrica | Train 2025 | Validación H1 2026 |
|---|---|---|
| Rentabilidad | +0,85% | **−4,49%** |
| Beneficio neto | +211,37 $ | **−1.121,99 $** |
| Profit Factor | 1,11 | **0,46** |
| Operaciones | 26 | 24 |
| Win rate | 42,31% | **25,00%** |
| Drawdown equity | 2,28% | 4,86% |
| Compras ganadoras | 11/24 (45,83%) | 4/13 |
| Ventas ganadoras | 0/2 | 2/11 |
| Calidad del histórico | 60% ticks reales | 100% ticks reales |

Train 2025 superó formalmente los criterios de descarte (Net Profit >
0, Max DD ≤ 20%), pero de forma poco convincente: Profit Factor 1,11
con sólo 26 operaciones, Z-Score de MT5 del 25,86% (la secuencia de
ganancias/pérdidas no se distingue de ser azar), y 24 de las 26
operaciones fueron compras — 2025 fue uno de los años más alcistas de
la historia del oro (+70%), así que Train casi no probó el lado de
venta ni ningún régimen distinto de tendencia alcista fuerte.

La Validación H1 2026 (con 100% de datos reales, sin el sesgo de ticks
sintéticos de Train) lo desmontó: pérdida clara, Profit Factor muy por
debajo de 1, y el fallo **no se concentra en un solo lado** — compras
4/13 y ventas 2/11, ambas direcciones perdiendo. Esto descarta que el
problema de Train fuera sólo "no hay datos de venta": con datos reales
de venta en Validación, tampoco funcionó.

Se encontró además, durante el análisis del CSV de Train, una
operación (2025-07-21) con un lotaje de **6,01 lotes** — un SL
anormalmente estrecho (el retroceso casi pegado al nivel de ruptura)
hizo que la fórmula de riesgo% calculara un volumen desproporcionado
para una cuenta de 25.000 $. No llegó a causar una pérdida fuera de lo
normal en ese caso, pero es un riesgo técnico latente (gaps o
slippage en un SL tan ajustado podrían costar mucho más del 0,5%
previsto) que quedaría pendiente de corregir si se retomara esta
lógica de entrada en el futuro.

**Decisión: se descarta Hipótesis 3 como candidata a operar con
dinero real.** No porque esté demostrado que la idea de
tendencia+pullback sea mala en sí misma, sino porque la evidencia
disponible —Train apenas positivo y poco representativo, Validación
claramente perdedora en ambas direcciones, muestra todavía pequeña—
no respalda seguir. No se ajustan EMA, ATR, swings ni RR para intentar
recuperar el resultado de Validación (eso la convertiría en otro tramo
de optimización), ni se sube el riesgo del 0,5% para amplificar un
sistema sin ventaja demostrada.

**Líneas de investigación para una hipótesis futura** (no para
rescatar ésta): si las rupturas del pullback llegan demasiado tarde
(ver las columnas de latencia del CSV: `VelasImpulsoARuptura` y la
diferencia entre `PrecioRupturaCierre` y `PrecioRealEjecucion`), si el
SL está mal dimensionado respecto a la volatilidad real (más allá del
caso de 6,01 lotes ya detectado), y si el filtro de tendencia H1
aporta algo una vez aislado de la señal de entrada.

### Pendiente antes de confiar en cualquier resultado (histórico, ya resuelto)

1. Compilar en MetaEditor y corregir cualquier error (no se ha podido
   compilar desde este entorno).
2. Verificar manualmente contra el gráfico (M15 + H1) al menos un
   puñado de configuraciones de cada tipo: compra válida, venta
   válida, y una cancelada por invalidación de estructura.
3. Sólo entonces, Train 2025 → Validación H1 2026 → jul-sep 2026
   (exploratorio) → tramo futuro reservado, con los mismos criterios de
   descarte pre-registrados que en Baseline 1 e Hipótesis 2.

## Hipótesis A: continuación tras ruptura de rango M15(20)

**Estado: CERRADA — sin ventaja predictiva robusta demostrada, archivada
sin optimizar N, horizontes ni añadir filtros.**

Tras el cierre de Hipótesis 3, se cambió de enfoque por sugerencia
explícita del revisor externo (ChatGPT, usado como segunda opinión):
en vez de construir otro EA completo con varios filtros combinados,
investigar primero si existe una ventaja estadística simple y medible
en XAUUSD, **antes** de programar cualquier EA operativo. Esta es la
primera de tres hipótesis de entrada candidatas; no se programó ningún
EA, SL, TP ni condición de entrada — solo un script de investigación
estadística independiente, `research/hipotesis_a_analisis.py`, que no
modifica ni depende de ningún EA del repositorio.

**Señal (100% objetiva, sin lookahead):** al cierre de cada vela M15
`t`, ruptura alcista si `Close[t] > max(High[t-20..t-1])`, bajista si
`Close[t] < min(Low[t-20..t-1])` (ventana de 20 velas que excluye la
propia vela de ruptura). Entrada en `Open[t+1]` (nunca en `Close[t]`).
Horizontes de medición fijos y pre-registrados: 4, 8 y 16 velas
(`Close[t+4]`, `Close[t+8]`, `Close[t+16]`), reportados siempre los
tres, nunca elegido el mejor a posteriori. **Cooldown global de 16
velas compartido entre ambas direcciones** (no uno independiente por
dirección) para evitar pseudo-replicación de la misma racha.

**Histórico usado:** M15 de XAUUSD exportado directamente desde MT5 vía
un script MQL5 independiente (`MQL5/Scripts/Export_XAUUSD_M15.mq5`, no
es un EA), 2023-01-03 a 2026-10-09 (88.567 velas). Verificado: sin
duplicados, orden estrictamente creciente, 100% alineado a bloques de
15 min, 0 inconsistencias OHLC, sin precios inválidos.

**Huecos de sesión** (clasificados por duración, umbral empírico, no
regla exacta de calendario): de 992 huecos >15 min, 656 son cierres
diarios (≤2h), 330 fines de semana (≤60h) y 6 festivos extendidos
(>60h). De las 3.205 señales finalmente usadas, 391 (12,2%) tienen su
ventana de medición (horizonte 16) interrumpida por alguno de estos
huecos, y 822 (25,6%) tienen su propio *lookback* de 20 velas
contaminado por un hueco — en esos casos, las "20 velas previas" no
representan 5 horas de mercado continuo sino un tramo más largo que
mezcla precio de antes y después de un cierre. No se descartaron estas
señales, solo se marcaron, y se reportó el tiempo real transcurrido
junto al nominal (p. ej. a horizonte 16, media real ≈310-320 min frente
a 240 min nominales).

**Resultados — cómputo:** 9.754 rupturas crudas (5.675 alcistas +
4.079 bajistas) → 6.549 descartadas por el cooldown global → **3.205
señales retenidas**.

| Período | n (alcistas/bajistas) | Alcistas: diff. señal-control (ATR, k=16) | Bajistas: diff. señal-control (ATR, k=16) |
|---|---|---|---|
| Robustez histórica 2023-2024 (nunca tocado antes) | 934 / 758 | −0,015 (sin ventaja) | −0,058 (peor que control) |
| Exploratorio ya quemado 2025-2026 (usado por H1-H3) | 861 / 652 | +0,197 (con ventaja aparente) | −0,109 (peor que control) |

El control se emparejó por dirección + hora de servidor (sin exigir
ruptura activa), con semilla fija y tope de reutilización por punto —
**no se seleccionaron controles favorables a posteriori**. Limitación
reconocida: la hora de emparejamiento usa hora de servidor, no UTC
calibrada (el *offset* exacto y el cambio de horario de verano no se
resolvieron antes de este análisis), y la ventana de ±30 días no aísla
completamente una tendencia secular de varios años.

**Interpretación:** no hay ventaja consistente entre periodos. En
2023-2024 ninguna dirección supera a su control a 16 velas. En
2025-2026 los alcistas sí superan a su control, pero ese periodo
coincide con la subida histórica más fuerte del oro de toda la muestra
— el propio control (asumiendo solo "largo aleatorio") ya capturaba
más de la mitad del movimiento bruto observado en la señal, así que el
"extra" atribuible específicamente a la ruptura es mucho más modesto
que la cifra bruta sugiere. Los bajistas rinden peor que su control en
**ambos** periodos — el hallazgo más repetido de todo el estudio es,
de hecho, negativo. Neto de costes estimados (escenarios de spread
0,15 / 0,30 + un escenario adicional de slippage conservador — nunca
se asumió el campo `Spread=0` como coste real de ejecución), la
mediana es negativa en la mayoría de combinaciones período×dirección.

**Validación prospectiva: no disponible.** 2023-2026 son, como mucho,
robustez histórica y exploración ya quemada — no se usan para afirmar
que la señal está validada; una validación real requeriría datos
posteriores a congelar esta metodología.

**Decisión:** se archiva esta definición de ruptura M15(20) sin
ventaja predictiva robusta demostrada. No se optimiza N, no se prueban
otros horizontes buscando uno favorable, no se añaden filtros de
tendencia/volatilidad para intentar rescatarla — eso sería la misma
búsqueda de parámetros que el proyecto evita en cada hipótesis. Se
pasa a investigar la Hipótesis B (reversión a la media tras
sobreextensión) como señal candidata independiente.

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
