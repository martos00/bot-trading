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

## Hipótesis B: reversión a la media tras sobreextensión

**Estado: CERRADA — sin ventaja estadística demostrada, archivada sin
modificar EMA20, ATR14, el umbral de 2 ATR ni los horizontes.**

Script independiente `research/hipotesis_b_analisis.py` (no EA, no
modifica ningún EA). Reutiliza el mismo histórico M15 verificado que
Hipótesis A.

**Señal:** sobreextensión alcista/bajista = cruce (no estado sostenido)
de `desviacion(t) = (Close[t] - EMA20[t]) / ATR14[t]` por encima de
+2,0 o por debajo de −2,0, umbral fijo pre-registrado. **Dirección
operada: contraria** a la extensión (hipótesis de reversión) —
sobreextensión alcista → corto; bajista → largo. Entrada en
`Open[t+1]`. Horizontes 4/8/16 velas, cooldown global de 16 velas.
Métrica principal: retorno real de precio desde la entrada, nunca
"acercamiento a la EMA" (la EMA también se mueve, así que esa
distancia no es rentabilidad).

**Controles:** dos, nunca elegidos a posteriori — Control A (misma
hora de servidor + ATR comparable ±25%) y Control B (A + mismo signo
de momentum causal, `Close[t]-Close[t-8]` normalizado por ATR). El
régimen H1 se reportó de forma descriptiva, no como filtro de
emparejamiento. Incertidumbre calculada con **bootstrap de bloques**
(bloques de 10 señales consecutivas, 2.000 repeticiones) para no
subestimar la dependencia temporal entre señales.

**Cómputo:** 11.470 cruces crudos → **2.284 señales retenidas** tras
cooldown (665 cortos + 542 largos en 2023-24; 604 cortos + 473 largos
en 2025-26).

| Período / grupo | n | Bruto ATR (media, IC95% bootstrap) | Neto ATR (conservador+slippage) |
|---|---|---|---|
| Robustez 2023-24, TODAS | 1.207 | +0,018 [−0,181, +0,208] | −0,184 |
| Robustez 2023-24, cortos tras alcista | 665 | −0,017 [−0,274, +0,251] | −0,221 |
| Robustez 2023-24, largos tras bajista | 542 | +0,062 [−0,225, +0,337] | −0,138 |
| Exploratorio 2025-26, TODAS | 1.077 | **−0,235 [−0,415, −0,034]** | −0,310 |
| Exploratorio 2025-26, cortos tras alcista | 604 | **−0,456 [−0,723, −0,216]** | −0,537 |
| Exploratorio 2025-26, largos tras bajista | 473 | +0,048 [−0,217, +0,325] | −0,021 |

**Por año (combinado, k=16, bruto ATR):** 2023 +0,030 → 2024 +0,007 →
2025 −0,208 → 2026 −0,274. Tendencia de casi-cero a claramente
negativo, lo contrario de lo esperable en una ventaja real y estable.

**El único resultado estadísticamente distinguible de cero (IC95% sin
cruzar el cero) es negativo**: cortos tras sobreextensión alcista en
2025-2026, en los tres horizontes. Es explicable por ir contra la
tendencia secular alcista del oro en ese tramo, no por un fallo
específico de la lógica de reversión — el control B (momentum-matched)
también pierde fuerte ahí. El lado "prometedor" (largos tras
sobreextensión bajista) nunca tiene el IC95% fuera de cero en ningún
periodo, y su neto ATR en 2025-26 es prácticamente nulo (−0,021); por
instrucción explícita, no se trata como el hallazgo ganador solo
porque su signo apunte en la dirección deseada.

**Ventanas con hueco de sesión de por medio** (minoría: 102-118 de
~1.100 señales por periodo) reportadas aparte, sin ocultar resultados
desfavorables: si acaso, algo peores que las ventanas sin interrupción
en el periodo exploratorio (k=8 IC95%=[−0,844, −0,077], también
negativo y significativo).

**Distinción explícita (propiedad estadística vs. ventaja explotable):**
no hay aquí ni una propiedad estadística de mercado consistente entre
periodos, ni mucho menos una ventaja que sobreviva a costes — ambas
faltan. **Validación prospectiva: no disponible**, igual que en
Hipótesis A.

**Decisión:** se archiva sin ajustar EMA20, ATR14, el umbral de 2,0 ni
los horizontes 4/8/16 buscando mejorar la cifra — sería la misma
búsqueda de parámetros que el proyecto evita en cada hipótesis.

## Cambio de metodología: estrategias discrecionales conocidas (USTEC / US500)

Tras agotar varias hipótesis de anomalías estadísticas en XAUUSD sin
encontrar una ventaja robusta, y tras una comparación explícita de
mercados alternativos (Nasdaq/NQ, S&P500/ES, EURUSD) y un estudio
overnight-vs-intradía en US500/USTEC con resultado débil/inconsistente,
el proyecto cambió de enfoque: en lugar de seguir buscando anomalías
estadísticas, se traducen a reglas objetivas estrategias **realmente
usadas por traders discrecionales** y se comprueban por backtest, con
reglas fijadas por adelantado y sin optimización posterior.

Ambas estrategias se evalúan en **USTEC y US500**, CFDs confirmados
(no futuros) sobre el servidor MetaQuotes-Demo, con la correspondencia
horaria servidor↔ET reconstruida semana a semana (salto semanal de
mediana de TickVolume, proxy de la apertura de caja NYSE 9:30 ET),
solo en días con offset **confirmado** (régimen ≥20 días). El hueco de
datos ausentes 2025-07-16→2025-09-09 (55 días, idéntico en ambos
instrumentos) queda excluido, nunca interpolado. Contabilidad en
**R-múltiplos** (normaliza por el riesgo en puntos de índice de cada
operación) — nunca en dólares, porque el valor real del tick/contrato
de esta cuenta no está confirmado.

### Opening Range Breakout (ORB) — cerrado: ventaja débil/insuficiente

Regla fija: rango = vela M15 9:30-9:45 ET; señal = primer cierre
posterior que rompe el rango; entrada = Open de la vela siguiente; SL =
lado opuesto del rango; TP = 2R; cierre forzoso al Close de 16:00 ET;
empate SL/TP en la misma vela → gana SL. Con solo el spread real
verificado: USTEC media +0,044R/operación (PF 1,10, n=673), US500
+0,057R/operación (PF 1,12, n=796) — positivo pero débil, y ambos
pasan a negativo con un estrés de costes de apenas +1 a +3 puntos de
índice no confirmados; 2026 ya es negativo incluso en el escenario
optimista en ambos instrumentos.

**Auditoría de un bug de MAE (excursión flotante):** se detectó y
corrigió un bug donde la excursión flotante por vela (MAE) no estaba
acotada en -1R cuando la propia vela disparaba el stop, usando en su
lugar el High/Low bruto de esa vela — producía lecturas imposibles
(p.ej. -9,26R en USTEC) pese a que el modelo de ejecución ya asume
cierre instantáneo en el SL. Corregido acotando a un suelo de -1,0R
cuando la vela toca el stop (commit `fde1bd2`); verificado por diff que
el fix solo afecta las métricas de MAE, no el P&L realizado, el
Profit Factor, el %Acierto ni el drawdown de balance.

**Dos limitaciones documentadas, sin reabrir la investigación:**
1. Se verificó que la vela degenerada del 04/10/2024 (rango de 0,13
   puntos en USTEC) corresponde realmente al bloque horario 9:30-9:45
   ET — el régimen activo esa semana (slot servidor 16:30, abr-oct
   2024) es el mismo que en fechas de control de otras estaciones
   (feb-2023, jul-2023, ene-2024, jul-2024, feb-2025...), todas con el
   salto de volumen esperado en ese slot. No es un error de conversión
   horaria: es un artefacto genuino de datos (liquidez anómala/precio
   plano en ese tramo del feed demo), aislado (1 de 673 operaciones
   USTEC con rango de apertura <1 punto; 0 de 796 en US500).
2. El tope de MAE en -1R asume **ejecución ideal del stop** (fill
   exacto al precio nominal del SL). No garantiza una pérdida máxima
   real de -1R ante gaps o slippage de ejecución reales — sigue siendo
   un límite del modelo de backtest, no una garantía de la estrategia
   en cuenta real.

**Decisión:** cerrado como estrategia de ventaja débil/insuficientemente
demostrada. No se modificaron las reglas de ORB en ningún momento de la
auditoría.

### Liquidity Sweep + Reversal — cerrado: sin ventaja, resultado negativo

Regla fija (ver `research/liquidity_sweep_backtest.py` para el
docstring completo, registrado antes de ejecutar el backtest): nivel
de liquidez = High/Low de la sesión RTH completa (9:30-16:00 ET) del
día hábil anterior (PDH/PDL; descartado si el día de referencia está a
más de 3 días naturales, p.ej. tras un hueco u ocio extendido); barrido
= primera vela de la sesión actual cuyo High supera el PDH o cuyo Low
perfora el PDL (si ambos a la vez en la misma vela, se descarta el día
— ambiguo); confirmación = la misma vela cierra de nuevo dentro del
rango anterior; dirección opuesta al barrido; entrada = Open de la
vela siguiente; SL = extremo de la vela de barrido; TP = 2R; cierre
forzoso a las 16:00 ET; empate SL/TP → gana SL; máximo una operación
por día.

Resultado (solo spread real, sin estrés de costes): USTEC media
-0,211R/operación (PF 0,70, %acierto 31,2%, n=176), US500 media
-0,128R/operación (PF 0,82, %acierto 32,7%, n=208) — negativo en ambos
instrumentos ya en el escenario optimista, y empeora con cualquier
estrés de costes adicional. Solo US500-2024 es puntualmente positivo
(+0,22R/operación); el resto de combinaciones año/instrumento son
planas o negativas.

**Decisión:** cerrado sin ventaja demostrada, sin intentar ninguna
variante ni optimización retrospectiva de la confirmación de rechazo,
el SL o el TP.

### VWAP Mean Reversion — cerrado: sin ventaja, resultado negativo

**Aviso de datos (verificado antes de programar):** esta cuenta NO
tiene volumen real de contratos — `RealVolume` es 0 en el 100% de las
velas de ambos instrumentos. El VWAP se calculó ponderando por
`TickVolume` (número de cambios de precio por vela), un **VWAP
aproximado**, no necesariamente equivalente al VWAP de futuros ES/NQ
(que usa volumen de contratos realmente negociado).

Regla fija (ver `research/vwap_reversion_backtest.py`): VWAP reiniciado
cada día en la sesión RTH (9:30-16:00 ET); bandas ±2 desviaciones
estándar ponderadas por TickVolume, acumuladas causalmente; señal =
primera vela cuyo High alcanza la banda superior o cuyo Low perfora la
inferior; confirmación = la misma vela cierra de vuelta dentro de la
banda; dirección opuesta a la banda tocada; entrada = Open de la vela
siguiente; SL = extremo de la vela de señal; TP = reversión al propio
VWAP vigente vela a vela (objetivo variable, no un R fijo — es la
esencia de "mean reversion"); cierre forzoso a las 16:00 ET; empate
SL/TP → gana SL; máximo una operación por día.

**Nota de implementación (corregida antes de ejecutar, no tras ver
resultados):** la primera vela de cada sesión se excluye como posible
señal — con una sola vela de historial la varianza ponderada es
exactamente 0, así que ambas bandas coinciden con el precio típico de
esa misma vela y "tocarían" ambos lados de forma espuria en
prácticamente cualquier vela de apertura. Es una necesidad estructural
del cálculo (no hay una alternativa correcta distinta), no un ajuste de
parámetro buscado por resultado.

Resultado (solo spread real, sin estrés de costes): USTEC media
-0,183R/operación (PF 0,71, %acierto 39,9%, n=296), US500 media
-0,321R/operación (PF 0,53, %acierto 33,3%, n=303) — negativo en ambos
instrumentos ya en el escenario optimista, y se deteriora con rapidez
bajo estrés de costes (US500 llega a -1,34R/operación con solo 3 puntos
extra, porque el riesgo medio por operación es muy pequeño en este
instrumento, 5,79 puntos). Única combinación año/instrumento
levemente positiva: USTEC-2026 (+0,036R/operación, n=37, incompleto).

**Decisión:** cerrado sin ventaja demostrada, sin buscar variantes
(otro múltiplo de desviación, otra confirmación, otro SL) para
rescatarlo.

### Revisión de método: ¿sin ventaja, o versión mecánica simplificada?

Antes de seleccionar una cuarta estrategia, revisión explícita de en qué
medida cada cierre anterior refleja "la estrategia no tiene ventaja" vs.
"nuestra traducción mecánica es una versión simplificada de lo que usa
un discrecional" — distinción importante porque un resultado negativo en
una versión simplificada no cierra necesariamente la puerta a la
estrategia completa.

- **ORB:** versión de un solo filtro (rango M15 único, sin filtro de
  tendencia de marco superior, sin confirmación de volumen, TP fijo en
  2R en vez de objetivo por movimiento medido o trailing). Discrecionales
  reales suelen combinar ORB con un sesgo de tendencia previo y gestión
  de salida variable. **Conclusión:** descartamos la versión simple
  probada, no "ORB en general".
- **Liquidity Sweep + Reversal:** usamos únicamente el High/Low de la
  sesión RTH del día anterior como nivel de liquidez, con una
  confirmación de un solo cierre de vuelta dentro del rango. La práctica
  discrecional (SMC/ICT) habitual añade estructura de mercado (MSS) y a
  menudo una entrada de retroceso a un Fair Value Gap — exactamente el
  esquema de Baseline 1 (cerrado en XAUUSD, también sin ventaja probada,
  pero con una traducción más completa). **Conclusión:** nuestra versión
  aquí es más simple que esa, así que el resultado negativo pesa menos
  como evidencia contra "liquidity sweep" en general.
- **VWAP Mean Reversion:** usamos TickVolume en vez de volumen real
  (ya declarado), un único umbral de ±2σ sin escalado, y sobre todo
  **sin filtro de día de tendencia vs. día de rango** — la salvedad más
  repetida en la práctica discrecional de VWAP fade ("no hagas fade de
  VWAP en un día de tendencia fuerte"), que aquí no se aplicó. **Esto
  importa directamente para la estrategia de continuación que sigue**:
  si VWAP mean reversion falla en parte porque opera también en días de
  tendencia, cabe esperar que una estrategia de continuación de
  tendencia capture precisamente esos días.

Esta revisión no reabre ninguna de las tres investigaciones cerradas —
se mantienen cerradas con el resultado obtenido para la versión
efectivamente probada — pero deja constancia de que "sin ventaja
demostrada en nuestra versión mecánica" no equivale a "la estrategia
discrecional no funciona nunca".

### Trend Continuation Pullback (EMA) — definición pre-registrada

Estrategia reconocible: tras el impulso inicial de apertura, el precio
se mantiene en tendencia y hace retrocesos poco profundos a una media
móvil antes de continuar — la "pullback-to-the-moving-average" que usan
numerosos traders intradía de tendencia (p.ej. EMA9/EMA20 en M15), el
complemento natural de VWAP mean reversion: aquí se opera A FAVOR de la
tendencia, no en contra.

**Mercado principal de la comparación: USTEC. US500: comparación
secundaria** (se reporta igual, con las mismas reglas, pero USTEC es la
referencia para la decisión).

**Versión base (fija, pre-registrada):**
 - EMA: EMA20 de Close, calculada de forma CONTINUA sobre toda la serie
   M15 (no se reinicia por sesión, igual que la usaría un discrecional
   mirando su gráfico), causal (`ewm(adjust=False)`, sin look-ahead).
 - Sesgo de tendencia del día: se fija UNA vez, en la propia vela de
   apertura (9:30-9:45 ET) de la sesión RTH confirmada — Close de esa
   vela >= EMA20 de esa vela → sesgo ALCISTA; si no, BAJISTA. No se
   reevalúa el sesgo durante el día.
 - Señal de pullback/continuación: la primera vela posterior (dentro de
   la sesión RTH) cuyo Low toca o perfora la EMA20 Y cuyo Close cierra
   de vuelta por encima de ella (sesgo alcista) — o, simétricamente,
   cuyo High toca/supera la EMA20 y cuyo Close cierra de vuelta por
   debajo (sesgo bajista).
 - Dirección operada: LA MISMA que el sesgo del día (continuación, no
   reversión).
 - Entrada: Open de la vela siguiente a la señal (sin lookahead).
 - Stop-loss: extremo de la propia vela de la señal (Low para largo,
   High para corto).
 - Take-profit: 2R, misma convención que ORB/Liquidity Sweep (permite
   comparar entre estrategias).
 - Cierre forzoso: Close de la vela de las 16:00 ET. Empate SL/TP en la
   misma vela → gana SL. Máximo una operación por día.

**Variantes estructurales (máximo 2, justificadas de antemano, NO
elegidas mirando resultados):**
 - **Variante A — EMA9:** mismo esquema exacto que la base, sustituyendo
   EMA20 por EMA9 como única media de sesgo y de retroceso. Justificación
   previa: EMA9 y EMA20 son los dos periodos más citados en la práctica
   de "pullback a la media" intradía; probar ambos de antemano es una
   alternativa estándar reconocida, no una búsqueda de parámetro tras
   ver resultados.
 - **Variante B — doble media (EMA9/EMA20):** el sesgo del día se define
   por la alineación de las dos medias en la propia vela de apertura
   (EMA9 >= EMA20 → alcista; si no, bajista) en vez de precio-vs-una-
   media; el nivel de retroceso vigilado pasa a ser la media RÁPIDA
   (EMA9). Justificación previa: filtro de tendencia por alineación de
   dos medias (en vez de precio contra una sola media) es una variante
   estructural clásica y distinta en mecanismo, no una repetición del
   mismo filtro con otro número.

Las tres versiones (base + A + B) se ejecutan y se reportan TODAS, sin
descartar las que salgan negativas del informe. Un resultado positivo en
una sola de las tres NO se considera validado — haría falta además
verificar calidad de datos, mecánica de ejecución y un período
prospectivo nuevo antes de considerarlo un hallazgo.

### Cierre: las tres versiones, negativas en ambos instrumentos

Resultado (solo spread real, sin estrés de costes adicional), USTEC
como mercado principal:

| Versión (USTEC) | n | Media R/op | PF | %Acierto |
|---|---|---|---|---|
| BASE (EMA20) | 578 | -0,170 | 0,76 | 31,5% |
| Variante A (EMA9) | 668 | -0,092 | 0,86 | 33,2% |
| Variante B (doble EMA9/EMA20) | 667 | -0,073 | 0,89 | 34,9% |

| Versión (US500, comparación secundaria) | n | Media R/op | PF | %Acierto |
|---|---|---|---|---|
| BASE (EMA20) | 696 | -0,113 | 0,83 | 34,1% |
| Variante A (EMA9) | 788 | -0,070 | 0,90 | 34,9% |
| Variante B (doble EMA9/EMA20) | 786 | -0,065 | 0,90 | 35,2% |

Las seis combinaciones (3 versiones × 2 instrumentos) son negativas ya
con solo spread real, y se deterioran con rapidez bajo cualquier
estrés de costes adicional (PF cae por debajo de 0,5 con +3 puntos de
estrés en casi todas). Hay años puntualmente positivos (USTEC-2026 en
BASE y Variante A; US500-2025/2026 en Variante B), pero ninguna versión
es consistentemente positiva a través de años ni resiste el estrés de
costes — no se trata como hallazgo, conforme a lo acordado (un resultado
positivo aislado no valida la estrategia).

**Decisión:** se cierran las tres versiones (base + 2 variantes) sin
ventaja demostrada, sin buscar variantes adicionales.

## Auditoría diagnóstica del motor y de los resultados (4 familias)

Tras cerrar ORB, Liquidity Sweep, VWAP Mean Reversion y Trend
Continuation con resultado negativo/insuficiente, auditoría puntual
(ver `research/auditoria_motor.py`) para distinguir "el motor o los
datos distorsionan los resultados" de "las señales probadas no tienen
ventaja". No modifica ninguna estrategia ni prueba parámetros nuevos.

**1-2. Desglose por motivo de salida y distribución de R:** consistente
en las 4 familias — SL ≈ −1,0 a −1,1R (coincide con el diseño), TP ≈
+1,95 a +2,0R en las estrategias de TP fijo (coincide con el 2R
registrado), y CIERRE_SESION con media **positiva** (p.ej. ORB USTEC
+0,398R, US500 +0,422R) — indicio de que el movimiento de continuación
tras el impulso inicial suele seguir a favor pero el TP fijo de 2R no
siempre lo captura; una observación, no un hallazgo a explotar ahora.

**Spread como fracción del riesgo — confirmado excesivo en una cola de
operaciones:** la media es baja (1,1%-8,0% según estrategia), pero el
máximo individual llega a ser extremo — hasta 209% del riesgo en Trend
Continuation USTEC, 100% en Trend Continuation US500, 90,9%/66,7% en
VWAP, 58,8%/40,0% en Liquidity Sweep. Esto ocurre en operaciones con un
SL basado en el extremo de una vela casi sin mecha (riesgo_puntos muy
pequeño) — no es un bug: la resta de spread real sigue siendo
aritméticamente correcta, pero normalizar por un riesgo casi nulo
infla el R resultante (de ahí R realizados de hasta −3,09 o −2,00 en la
verificación de integridad, fuera del rango "esperado" de
aproximadamente [−1,1, 2,1] que sí se cumple en la inmensa mayoría de
operaciones). Entre 5,7% y 20,1% de operaciones según estrategia tienen
spread>10% del riesgo — una proporción real, no despreciable, y una
limitación de diseño del SL (vela de un solo toque) más que del motor
de costes.

**3. Mecánica Bid/Ask:** el OHLC exportado por MT5 son precios **Bid**
(el broker no almacena un histórico de Ask separado; nuestra columna
`Spread` es precisamente la herramienta para reconstruir Ask=Bid+spread).
El modelo actual resta el spread real como un coste plano en puntos del
R final, lo cual es correcto en el agregado del coste total por
operación. Imprecisión real y acotada: el disparo de SL/TP en
operaciones **cortas** se comprueba contra el High/Low en Bid, cuando
técnicamente cerrar un corto exige comprar al Ask — un sesgo
sistemático pero pequeño (acotado por el mismo ratio spread/riesgo ya
medido, 1,1%-8,0% de media) que no cambia la dirección de ningún
resultado agregado. No se encontró lookahead ni error de orden
temporal en ninguna de las 4 familias (entrada siempre en el Open de
la vela siguiente a la señal, señales siempre sobre velas ya
cerradas, empate SL/TP resuelto siempre a favor de SL).

**4. Concentración horaria:** sin patrón dominante que explique el
resultado agregado — hay bloques horarios puntualmente peores (p.ej.
Liquidity Sweep USTEC 14:30-16:00 media −0,984R, pero n=9, muestra
demasiado pequeña para concluir nada), pero ninguna familia tiene su
resultado negativo concentrado en una única franja con n grande; es
una pérdida repartida a lo largo de la sesión. **No se ha usado esta
información para añadir ningún filtro horario.**

**5. Referencia de entradas aleatorias** (mismos días, mismo riesgo por
operación, misma regla de salida y mismos costes que la estrategia
real; 100 repeticiones) — resultado más revelador de la auditoría:

| Estrategia | z (USTEC) | z (US500) | Lectura |
|---|---|---|---|
| ORB | +1,75 | +2,94 | señal con valor real modesto, por encima de lo aleatorio |
| Liquidity Sweep | −1,21 | −0,22 | indistinguible de (o peor que) entrada aleatoria |
| VWAP Mean Reversion | **+6,66** | **+5,18** | señal con valor real fuerte, muy por encima de lo aleatorio |
| Trend Continuation | −1,58 | −0,29 | indistinguible de (o peor que) entrada aleatoria |

Hallazgo importante sobre VWAP Mean Reversion: con la MISMA regla de
salida (reversión al VWAP) y el mismo riesgo, las entradas aleatorias
pierden mucho más (media ≈ −0,83R a −0,92R) que la señal real probada
(−0,18R a −0,32R). Es decir, **la señal de entrada (toque de banda +
rechazo) sí aporta información real** — el resultado agregado negativo
se explica mejor por lo exigente del objetivo (revertir al VWAP, un
nivel que se mueve) que por una señal sin valor. Esto no reabre la
investigación (la regla ya se registró y cerró tal cual se probó), pero
es una distinción relevante de cara al futuro: si se retoma un fade de
VWAP, el objetivo de salida sería lo primero a repensar, no la señal.
Liquidity Sweep y Trend Continuation, en cambio, no muestran evidencia
de que su lógica de entrada aporte nada sobre el azar.

**6. Limitaciones del feed CFD MetaQuotes-Demo vs. un backtest de
futuros:**
- *Específicas de este feed/cuenta:* ausencia de volumen real
  (TickVolume como proxy, ya declarado en VWAP); artefactos de
  liquidez del servidor demo (el tramo de precio plano del 04/10/2024
  ya documentado en el cierre de ORB); necesidad de reconstruir la
  correspondencia horaria servidor↔ET semana a semana por falta de
  metadato directo de zona horaria (un futuro listado en un exchange
  real trae timestamps UTC fiables, sin esa reconstrucción); swap
  financiero de CFD en vez de rollover de contrato.
- *Genéricas del motor, igual de presentes en un backtest con datos de
  futuros a M15:* la ambigüedad de orden intravela entre SL y TP (sin
  datos de tick no se puede saber cuál ocurrió primero — resuelto aquí
  siempre a favor de SL, conservador); la aproximación Bid/Ask para
  costes; la inflación de R en operaciones de riesgo casi nulo descrita
  en el punto 2, que depende del diseño del SL, no del proveedor de
  datos.

### Conclusión de la auditoría

**No hay indicios de que el motor o los datos estén distorsionando los
resultados de forma que oculten una ventaja real.** No se encontró
lookahead, ni error de ejecución direccional, ni un patrón horario
dominante, ni un bug de cómputo (la única imprecisión real — Bid/Ask en
cortos — está acotada y es demasiado pequeña para explicar los
resultados). Lo que sí se confirma es una **imagen diferenciada por
estrategia**: Liquidity Sweep y Trend Continuation no muestran ninguna
ventaja sobre entradas aleatorias — su cierre como "sin ventaja" queda
reforzado. ORB muestra una ventaja real pero modesta y fragil a costes
— consistente con el cierre ya hecho. VWAP Mean Reversion es el caso
más matizado: su señal de entrada sí tiene valor estadístico real y
notable, pero la regla de salida (reversión al VWAP) es exigente y
domina el resultado agregado negativo — una distinción útil para el
futuro, no un motivo para reabrir ahora la investigación.

### Auditoría profunda de VWAP Mean Reversion (verificación del z-score)

El resultado de la referencia aleatoria era llamativo (z=+6,66/+5,18),
así que antes de aceptarlo se verificó específicamente si la
comparación era justa, se corrigió un bug de ejecución real detectado
en la auditoría general, y se añadió MFE (excursión favorable máxima).
Ver `research/auditoria_vwap_profunda.py`. No se modificó ninguna regla
de la estrategia ni se probó ningún TP/filtro nuevo.

**1. Cómo se construyó la referencia original:** para cada operación
real, mismo día y mismo riesgo en puntos, vela de entrada
**uniformemente aleatoria dentro de TODA la sesión** (9:30-16:00 ET),
dirección aleatoria 50/50, misma regla de salida (reversión al VWAP de
ese día) y mismo spread real de esa vela — 100 repeticiones, z =
(media real − media de las repeticiones) / desviación de las
repeticiones.

**2. La comparación original NO era justa — confirmado y corregido:**
el 95-96% de las señales reales de VWAP ocurren entre 9:30 y 10:30 ET
(mediana=10:00h), mientras que un sorteo uniforme en 6,5 horas de
sesión solo pondría ~15% de las entradas ahí por azar. Entrar pronto
deja mucho más tiempo para revertir al VWAP antes del cierre forzoso
que entrar a media tarde, así que la referencia original estaba sesgada
a favor de la estrategia real. Corrección: nueva referencia que
preserva el offset EXACTO desde la apertura de sesión (misma hora ET,
mismo tiempo restante hasta el cierre) y sortea el DÍA donante al azar
— control real por horario y por tiempo disponible.

| | z original (sesgado) | z emparejado (corregido) |
|---|---|---|
| USTEC | +6,21 (ya con fix Bid/Ask) | **+5,70** |
| US500 | +4,89 (ya con fix Bid/Ask) | **+3,22** |

El z-score baja al corregir el sesgo (como se esperaba), pero **se
mantiene fuertemente significativo en ambos instrumentos** incluso bajo
la comparación correctamente emparejada — la señal de entrada sigue
mostrando información real, no es un artefacto del diseño de la
referencia.

**3. Corrección Bid/Ask aplicada (motor, no la estrategia):** el OHLC
exportado es Bid; cerrar un corto exige comprar a Ask=Bid+spread. El
disparo de SL/TP en cortos ahora se compara contra `sl-spread_vela` /
`vwap-spread_vela` (spread real de cada vela) en vez de contra el nivel
Bid puro. Efecto: USTEC media R real −0,1827R→**−0,1992R**; US500
−0,3213R→**−0,3371R** — cambio pequeño y en la dirección esperada
(ligeramente peor, como predecía el sesgo optimista ya descrito),
confirma que el motor no estaba generando el resultado positivo por
error de ejecución.

**4. Stops muy pequeños frente al spread (solo diagnóstico, SIN
filtro adoptado):**

| | n excluidas (>10% spread/riesgo) | Media R excluyéndolas | Media R con todas |
|---|---|---|---|
| USTEC | 46 (15,5%) | −0,1319 | −0,1992 |
| US500 | 61 (20,1%) | −0,3065 | −0,3371 |

Quitar la cola de stops casi nulos mejora el resultado pero NO lo
revierte a positivo — contribuye al resultado negativo, no lo explica
por completo. No se adopta ningún filtro.

**5. MFE/MAE tras la entrada (ya con el fix Bid/Ask, desglosado por
motivo de salida):**

| | MFE media | MAE media | n |
|---|---|---|---|
| USTEC — SL | **+1,320R** | −0,999R | 170 |
| USTEC — TP_VWAP | +1,054R | −0,467R | 126 |
| US500 — SL | **+1,163R** | −0,999R | 190 |
| US500 — TP_VWAP | +1,010R | −0,352R | 112 |

Hallazgo relevante: las operaciones que terminan paradas por SL habían
alcanzado, de media, **más de +1,2R de beneficio flotante** antes de
revertir del todo hasta el stop. Esto refuerza la lectura del z-score:
la señal identifica movimientos de reversión reales y aprovechables en
el corto plazo, pero la gestión de salida actual (esperar la reversión
completa al VWAP, sin proteger beneficio ni mover a breakeven) devuelve
gran parte de esa ventaja al mercado.

### Conclusión cuantitativa: ¿merece la pena una nueva versión de VWAP?

**Sí, con alcance acotado.** Tras corregir tanto el sesgo de horario en
la referencia aleatoria como el bug de ejecución Bid/Ask, la señal de
entrada de VWAP Mean Reversion sigue mostrando una ventaja
estadísticamente real y notable (z=+5,70 USTEC, +3,22 US500) sobre
entradas aleatorias correctamente emparejadas en horario, riesgo y
regla de salida. El MFE confirma el mismo patrón de forma independiente
(+1,2R de media alcanzado antes de los stops). La cola de stops casi
nulos frente al spread contribuye al resultado negativo pero no lo
explica por completo.

Esto NO significa que la estrategia tal cual esté lista — el resultado
agregado sigue siendo negativo (−0,20R USTEC, −0,34R US500) — pero sí
justifica un siguiente paso acotado: **rediseñar únicamente la regla de
salida** (gestión de riesgo/beneficio tras la entrada), manteniendo la
señal de entrada exactamente igual, con una única versión pre-registrada
(no una búsqueda de parámetros) y el mismo compromiso de cerrar si no
funciona. No se ha tocado ningún TP ni filtro en esta sesión, conforme
a lo pedido.

### Corrección adicional: el MFE reportado arriba tenía el mismo tipo de bug que el MAE

Antes de probar el TP fijo en +1R, verificación explícita de que el MFE
no incluye movimiento posterior a la ejecución del SL (mismo criterio
conservador exigido para el MAE). Se encontró que, efectivamente,
`mejor_flotante_r` se actualizaba con el High/Low de la MISMA vela que
dispara el SL sin excluirlo — igual que el bug de MAE ya corregido en
ORB, pero esta vez en el lado favorable. **Corregido** en
`research/vwap_reversion_backtest.py`: en la vela que dispara el SL no
se acredita MFE (podría ser posterior a la ejecución del stop); en la
que dispara el TP, se acota exactamente al R realizado. Verificado por
diff que el fix solo afecta a MFE, no a ningún R realizado ni métrica
de P&L.

**MFE corregido (operaciones resueltas por SL, versión original de
reversión al VWAP):** USTEC +1,320R→**+0,927R**; US500
+1,163R→**+0,714R**. Sigue siendo positivo en promedio (consistente con
que la señal captura algo de movimiento real), pero notablemente menor
de lo reportado antes de la corrección.

### Hipótesis registrada: TP fijo en +1R en vez de reversión completa al VWAP

**Hipótesis (basada en el MFE recién corregido sobre este MISMO
histórico — por tanto NO es una validación fuera de muestra):** la
señal de barrido de banda + confirmación podría capturar suficiente
movimiento favorable para alcanzar +1R aunque no complete la reversión
total hasta el VWAP. Único cambio frente a la versión original (ver
`research/vwap_reversion_tp1r_backtest.py`): TP fijo en +1R desde la
entrada. Señal, confirmación, SL inicial, horario operativo, corrección
Bid/Ask y modelo de costes — todos idénticos a la versión original.

**Resultado (solo spread real, sin estrés de costes):**

| | n | Media R/op | PF | %Acierto | Drawdown balance |
|---|---|---|---|---|---|
| USTEC — TP+1R | 296 | −0,311 | 0,54 | 37,8% | 95,87R |
| USTEC — original (revierte a VWAP) | 296 | −0,199 | 0,68 | 39,2% | 70,62R |
| US500 — TP+1R | 303 | −0,434 | 0,41 | 32,3% | 132,33R |
| US500 — original (revierte a VWAP) | 303 | −0,337 | 0,51 | 33,0% | 106,68R |

**El TP fijo en +1R es PEOR que la versión original en ambos
instrumentos**, no mejor — la hipótesis no se sostiene. Motivo visible:
la tasa de acierto baja (de 126/296=42,6% de cierres por VWAP a
112/296=37,8% de cierres por TP+1R en USTEC, patrón análogo en US500) —
alcanzar un objetivo fijo de +1R exige, en una fracción relevante de
operaciones, más recorrido que el que ofrecía el propio VWAP vigente en
ese momento (un objetivo variable que a menudo estaba más cerca que 1R
de distancia). Negativo también en los tres años completos y bajo los
tres escenarios de coste, sin ninguna combinación año/instrumento
consistentemente positiva.

**Decisión:** se descarta el TP fijo en +1R. Conforme a lo acordado, no
se prueban +0,5R, +1,5R, breakeven ni ninguna otra combinación para
rescatarlo. La investigación de una nueva regla de salida para VWAP
Mean Reversion queda cerrada sin éxito con esta única variante
pre-registrada.

### Cierre de VWAP Mean Reversion — matiz importante sobre lo que queda demostrado

Resultado final negativo en ambas variantes de salida probadas
(reversión al VWAP, TP fijo +1R), en USTEC y en US500. Se cierra la
investigación de VWAP Mean Reversion.

**Corrección deliberada de cómo se presentó la evidencia intermedia:**
los z-scores frente a entradas aleatorias (incluso la versión
emparejada por horario) y el MFE retrospectivo mostraron patrones
estadísticamente llamativos, y en turnos anteriores se describieron
como "ventaja real y robusta". Eso sobreinterpreta lo que esas pruebas
pueden demostrar: ambas se calcularon sobre el mismo histórico ya usado
para diseñar y cerrar la estrategia (ninguna es una validación fuera de
muestra), ninguna corrige por las múltiples comparaciones realizadas a
lo largo de todo el proyecto (4 estrategias × 2 instrumentos × varios
escenarios), y el propio TP+1R —motivado directamente por ese MFE—
resultó negativo y peor que la versión original. Son indicios
compatibles con que la señal capture algo de información real, no una
prueba de ventaja explotable. Se mantiene el hallazgo (z-scores, MFE)
como lo que es: una observación diagnóstica interesante, no una
conclusión validada.

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

## Propuesta: calidad de datos y validación antes de la siguiente estrategia

Tras cerrar ORB, Liquidity Sweep, VWAP Mean Reversion y Trend
Continuation (las cuatro con resultado negativo o insuficiente sobre
los mismos datos M15 del servidor MetaQuotes-Demo), propuesta concreta
para mejorar datos y validación ANTES de programar otra estrategia.
Sin código todavía — es una decisión de qué datos usar, pendiente de
que el usuario elija entre las opciones de abajo. Los precios/ofertas
de terceros marcados "(a verificar)" no están confirmados en firme —
mismo criterio del proyecto de no afirmar cifras no comprobadas;
verificar en la web del proveedor antes de pagar nada.

### 1. Qué datos necesitamos realmente

Para un backtest de NQ/MNQ (futuro CME) o USTEC (CFD) con la precisión
que nuestras propias auditorías han echado en falta:

- **Resolución mínima: M1.** La mayoría de los problemas de ejecución
  que hemos auditado (ambigüedad SL/TP intravela, aproximación Bid/Ask,
  MAE/MFE contaminados) vienen de operar sobre M15. Pasar a M1 no los
  elimina del todo, pero reduce muchísimo la ventana de ambigüedad por
  vela.
- **Tick-level Bid+Ask, si es asequible, para la validación final** (no
  necesariamente para el desarrollo diario) — es la única forma de
  conocer el orden real intravela y eliminar por completo la
  convención conservadora "gana el SL en caso de empate".
- **Volumen real de contratos** (no TickVolume) si queremos un VWAP
  genuino en vez de la aproximación ya declarada.
- **Timestamps de exchange fiables (UTC)** — evita la reconstrucción
  horaria semana a semana que hemos tenido que hacer por falta de
  metadato en el feed demo.
- **Si se usa el futuro NQ/MNQ (no CFD): calendario de vencimientos y
  método de rollover** (back-adjusted vs. sin ajustar, regla de fecha
  de roll) — complejidad nueva que el CFD actual nos evitaba.
- **Historial suficiente para dejar un tramo SIN TOCAR** (punto 4) —
  idealmente varios años antes de 2023.

### 2. Fuentes concretas

| Fuente | Instrumento | Resolución | Coste aproximado | Notas |
|---|---|---|---|---|
| **El propio bróker/firma de fondeo objetivo (demo o real)** | USTEC/US500 CFD | M1, Bid+spread real | Gratis | Mejora de mayor impacto y menor coste para el camino CFD: sustituye el feed genérico MetaQuotes-Demo por el feed del VENUE donde realmente se operaría. Mismo exportador MQL5 que ya tenemos. |
| **Dukascopy** (histórico tick gratuito, vía su propia herramienta o terceros como Tickstory/QuantDataManager) | Índices/CFD, FX | Tick Bid+Ask | Gratis, confirmado | Buena contrastación cruzada gratuita frente al feed demo. Verificar qué símbolo de índice Nasdaq tienen listado y desde qué fecha. |
| **Interactive Brokers (API TWS)** | NQ/MNQ futuro | M1 (bars cortos limitados a historial reciente) | Gratis con cuenta (a verificar tarificación de datos en vivo vs. histórico) | Requiere abrir cuenta IBKR (soporta demo/paper). Límites conocidos: contratos vencidos >2 años no disponibles, paginación por tramos cortos. |
| **Firstrate Data** | NQ desde 2008, MNQ desde 2019 | M1 y otras | ~$99,95/año tras el primer mes (a verificar vigencia del precio) | Historial largo, barato, pensado para backtesting retail — opción más directa si se quiere NQ/MNQ M1 de varios años sin montar infraestructura. |
| **Databento** | CME (NQ/MNQ), incl. tick/MBO | Tick a M1 | Variable, por dataset/GB (a verificar en su web, no confirmado aquí) | Más flexible si luego se quiere tick-level para la validación final; conviene cotizar solo el tramo de fechas necesario, no el histórico completo. |
| **Kibot** | Futuros incl. NQ | M1/tick | Precio inconsistente entre fuentes consultadas ($139/mes a varios cientos — NO confirmado) | No usar sin verificar directamente en kibot.com qué incluye el plan y si cubre NQ. |

**Recomendación de orden:** (1) Dukascopy gratis para una contrastación
rápida; (2) cambiar el feed CFD del broker demo genérico al demo del
bróker/firma real objetivo (gratis, mayor fidelidad para el caso de uso
real); (3) si se necesita NQ/MNQ de verdad (futuro, no CFD), Firstrate
Data es la opción barata y acotada; dejar Databento/tick-level como
mejora posterior solo para la validación final, no para el desarrollo
diario.

### 3. Reutilizar el motor actual sin rehacerlo

El motor (`cargar_y_verificar`, `clasificar_huecos`, detección de
régimen horario, contabilidad en R-múltiplos, escenarios de coste) solo
exige un CSV con las columnas `TimestampServidor;Open;High;Low;Close;
TickVolume;Spread;RealVolume`. Plan de reutilización:

- Un script adaptador por fuente nueva (Dukascopy/Firstrate/Databento/
  IBKR → ese mismo esquema de columnas) — cero cambios en
  `orb_backtest.py`/`vwap_reversion_backtest.py`/etc.
- Si la fuente trae Bid Y Ask reales: poblar `Spread` con el spread
  real por vela en vez de la cifra autoreportada del bróker — mejora
  de datos, no de reglas.
- Pasar de M15 a M1 solo exige retocar la función de detección de
  régimen (`slot = hora*4 + minuto//15`, 96 slots/día) a su equivalente
  de 1.440 slots/día — cambio mecánico acotado, no una reescritura.
- Tick-level, si se adopta, se trataría como una capa de ejecución
  ADICIONAL y posterior (solo para la validación final de una
  estrategia ya cerrada en M1), no como sustituto inmediato de todo el
  motor actual.

### 4. Separar desarrollo y validación (el período 2023-2026 ya está "quemado")

Regla explícita a partir de ahora: **2023-2026 no se vuelve a usar para
diseñar ni elegir una estrategia nueva** — se reserva como ventana de
"desarrollo" donde se prueba una única versión pre-registrada (igual
disciplina que hasta ahora), nunca para buscar entre variantes.

- **Validación casi-inmediata y casi gratis:** historial ANTERIOR a
  2023 (p.ej. 2018-2022 de NQ/MNQ, disponible en Firstrate/Databento) —
  nunca tocado en este proyecto, sirve de primer filtro rápido antes de
  invertir en nada más.
- **Validación definitiva: forward/demo en tiempo real** — una vez una
  estrategia pase el filtro anterior, demo-tradearla en vivo (o en el
  Strategy Tester con datos que aún no existían al diseñarla) durante
  un periodo pre-comprometido (p.ej. 2-3 meses) antes de arriesgar
  capital de una cuenta de fondeo real. Es la única validación
  realmente limpia; todo lo demás es un filtro previo más rápido y más
  barato, no un sustituto.

### 5. Modelar costes y reglas de una cuenta de fondeo real

- Sustituir los escenarios de estrés genéricos (0/1/3 puntos) por la
  tabla de spread/comisión/swap REAL de la firma y el bróker de
  ejecución concretos, una vez elegidos (FTMO/FundedNext/The5ers u
  otro) — dato verificable en sus condiciones publicadas, no inventado.
- Reglas específicas de la firma a modelar explícitamente: pérdida
  máxima diaria, drawdown máximo total, objetivo de beneficio, días
  mínimos de trading, reglas de consistencia (algunas firmas penalizan
  que un solo día aporte una fracción excesiva del beneficio total),
  prohibición de mantener posiciones el fin de semana (encaja bien con
  nuestro cierre forzoso diario ya existente), restricciones en
  ventanas de noticias.
- Dimensionar el riesgo como % de la equity de la TRANCHE de cuenta
  real (p.ej. $10k/$25k/$50k/$100k) en vez del `EQUITY_INICIAL`
  genérico de $25.000 usado hasta ahora — solo una vez se conozca el
  valor real del tick/contrato de la firma elegida (pendiente desde el
  inicio del proyecto, nunca confirmado para la cuenta demo genérica).
- Utilidad separada (no mezclada con la lógica de señal) para que
  cambiar de firma/tramo de cuenta no obligue a tocar ninguna
  estrategia.

**No se ha escrito código de esta propuesta** — pendiente de que el
usuario decida qué fuente(s) de datos usar antes de implementar nada.

## Cambio de metodología: identificar la ventaja antes de construir la estrategia

A partir de aquí, nuevo protocolo de 4 fases para cada hipótesis: (1)
identificar una ventaja con explicación económica/conductual, sin TP/SL
ni filtros; (2) decisión — solo si hay evidencia razonable se diseña la
estrategia; (3) construir filtros y gestión de riesgo; (4) forward
testing/incubación antes de real. Las estrategias anteriores (ORB,
Liquidity Sweep, VWAP, Trend Continuation) se construyeron completas
desde el principio — este cambio invierte el orden.

## FASE 1 — Reversión a la media de corto plazo (RSI(2) + SMA200) en tendencia alcista

Hipótesis inspirada en el enfoque RSI(2)+SMA200 (Connors, difundido por
Rubén Martínez): en índices en tendencia alcista, una sobreventa de
corto plazo va seguida de una recuperación mayor que la de días
equivalentes sin sobreventa. USTEC como mercado principal, US500 como
comparación. Ver `research/hipotesis_rsi2_sma200.py` para el
pre-registro completo (docstring) — ejecutado directamente, sin
construir TP/SL/filtros.

**Pre-registro (fijado antes de ejecutar):** barra diaria agregada
desde M15 por fecha de calendario del servidor; tendencia = Close
diario > SMA200 diaria; sobreventa = RSI(2) de Wilder por debajo de
TRES umbrales fijos (5, 10, 15 — los tres se reportan siempre);
horizontes futuros 1/3/5/10 días; retorno = Close[t+h]/Open[t+1]-1 (se
entra en el Open del día siguiente a la señal, sin lookahead); grupo de
CONTROL = mismos días en tendencia alcista pero SIN sobreventa (para no
confundir la deriva media del uptrend con información incremental del
RSI); incertidumbre con bootstrap de bloques de 10 señales consecutivas
(misma convención que Hipótesis A/B), 2.000 repeticiones.

**Resultado — el efecto (tratamiento−control) es positivo en las 24
combinaciones probadas** (2 instrumentos × 3 umbrales × 4 horizontes),
sin una sola excepción:

| Horizonte +5d (el más citado en la literatura) | n tratamiento | Media tratamiento | Media control (mismo uptrend) | Efecto |
|---|---|---|---|---|
| USTEC, RSI(2)<5 | 25 | +1,374% | +0,396% | +0,978 pp |
| USTEC, RSI(2)<10 | 58 | +1,005% | +0,378% | +0,626 pp |
| USTEC, RSI(2)<15 | 96 | +1,202% | +0,304% | +0,898 pp |
| US500, RSI(2)<5 | 24 | +1,537% | +0,283% | +1,254 pp |
| US500, RSI(2)<10 | 56 | +1,168% | +0,252% | +0,917 pp |
| US500, RSI(2)<15 | 93 | +0,789% | +0,254% | +0,535 pp |

*(Nota: esta tabla y el párrafo original de abajo describen el primer
cálculo, con la incertidumbre de tratamiento y control vistas por
separado. La sección "Verificación previa a Fase 3" más abajo corrige
esto con el IC95% de la DIFERENCIA directamente — el alcance real del
hallazgo es más estrecho de lo que este párrafo sugiere: léase junto
con esa corrección, no de forma aislada.)*

El IC95% bootstrap del grupo tratamiento excluye claramente el cero (y
en la mayoría de casos tampoco solapa con el del grupo control) para
RSI(2)<10 y <15 en ambos instrumentos y casi todos los horizontes —
RSI(2)<5 tiene menos observaciones (24-25) y por tanto intervalos más
anchos, ocasionalmente cruzando cero en el horizonte +10d. El
tratamiento supera de forma consistente no solo a cero sino a la propia
deriva del uptrend (grupo control) — la condición clave para no
confundir "el índice sube en tendencia alcista" con "el RSI(2) aporta
información".

**Persistencia por año (RSI(2)<10, +5d):** positiva en todos los años
con muestra informativa (2024: USTEC +1,12% vs control +0,41%; US500
+1,94% vs +0,28%. 2025: USTEC +0,54% vs +0,28%; US500 +0,49% vs +0,22%.
2026: USTEC +1,78% vs +0,29%; US500 +0,94% vs +0,17%). 2023 tiene
muestra demasiado pequeña (n=1-3, por el warm-up de SMA200 hasta
acumular 200 velas diarias) para ser informativo por sí solo.

**Limitaciones explícitas, sin forzar la conclusión:**
- Las observaciones por horizonte se solapan en el tiempo (no son
  independientes) — mitigado con bootstrap de bloques, no eliminado.
- 24 combinaciones probadas sin corrección por comparaciones múltiples;
  lo que compensa parcialmente es que el efecto es positivo en las 24,
  no solo en unas pocas — un patrón más difícil de explicar por azar
  puro que un hallazgo aislado, pero no es una prueba formal.
- Todo el periodo 2023-2026 ha sido fuertemente alcista en ambos
  índices — no se puede distinguir aquí si la ventaja persiste en un
  régimen de mercado distinto (lateral o bajista); exactamente el tipo
  de pregunta que corresponde a la validación fuera de muestra (Fase
  3), no a esta fase.
- **Este resultado usa el mismo periodo 2023-2026 ya explorado
  repetidamente en el proyecto — se trata como investigación
  exploratoria, NO como validación independiente.**

### Verificación previa a Fase 3 (corrige el alcance de la Fase 1)

Antes de programar, verificación explícita de 3 puntos sobre
`research/hipotesis_rsi2_sma200.py` — dos de ellos obligaron a corregir
el alcance de lo que la Fase 1 realmente demuestra.

**1. RSI(2)/SMA200 sin lookahead — confirmado, sin cambios.** Ambos se
calculan con `.rolling()`/`.ewm()` directamente sobre `Close` diario
(causales por construcción); la entrada usa `Open` del día siguiente y
la salida `Close` del día h — verificado leyendo el código, no solo
por diseño.

**2. La incertidumbre reportada era la de dos grupos por separado, NO
la de la diferencia — corregido, y cambia la conclusión.** La versión
original bootstrapeaba tratamiento y control con bloques tomados de
días distintos de cada grupo y restaba los dos puntos estimados; eso
no es el intervalo de confianza de la diferencia, solo una comparación
visual de dos IC. Se añadió un bootstrap de bloques CONJUNTO (bloques
de 10 días consecutivos de la secuencia real de días en tendencia
alcista, preservando el entrelazado cronológico de ambos grupos) que
calcula directamente la distribución de (media tratamiento − media
control). Resultado: el IC95% de la diferencia **cruza cero en una
fracción relevante de las 24 combinaciones**, incluyendo el combo más
citado antes (USTEC, RSI(2)<10, +5d: efecto puntual +0,626pp, pero
IC95% de la diferencia=[−0,287pp, +1,550pp]). A +10d, NINGUNA de las 6
combinaciones (2 instrumentos × 3 umbrales) excluye cero. El patrón que
sí se mantiene robusto bajo esta corrección: **RSI(2)<15 a horizontes
cortos (+1d a +5d)**, en ambos instrumentos (p.ej. USTEC +5d
IC95%=[+0,300pp,+1,512pp]; US500 +5d IC95%=[+0,055pp,+0,978pp]).

**3. Señales repetidas dentro de la misma caída — confirmado que
inflan parcialmente el efecto, sobre todo en RSI(2)<10.** Las señales
no son eventos independientes: se agrupan en episodios (días
consecutivos de sobreventa dentro de la misma caída). USTEC RSI(2)<10:
58 señales en solo 32 episodios distintos; al quedarse solo con el
PRIMER día de cada episodio, la media a +5d cae de +1,005% a +0,525%
(casi la mitad). El mismo chequeo en RSI(2)<15 (96 señales, 57
episodios) es más estable: +1,202%→+0,963%. US500 muestra el mismo
patrón, más moderado.

**Conclusión revisada:** la ventaja es más débil y mucho menos uniforme
de lo que se reportó inicialmente. Sigue habiendo una señal defendible,
pero acotada a **RSI(2)<15, horizontes cortos (+1d a +5d)** — no al
umbral más estricto (RSI(2)<10, muestra pequeña y gran parte del efecto
viene de contar la misma caída varias veces) ni a horizontes largos
(+10d, ningún combo sobrevive la corrección del punto 2). Esto no
invalida la Fase 1, pero sí reduce su alcance real frente a lo
presentado antes de esta verificación.

### FASE 2 — Decisión (revisada tras la verificación)

**Hay evidencia acotada, no la "ventaja robusta" descrita inicialmente**
— suficiente para intentar una versión estrecha y específica en Fase 3
(RSI(2)<15, salida corta), no la versión más laxa originalmente
propuesta. Propuesta concreta (pendiente de confirmación del usuario
antes de programar nada): entrada en el Open del día siguiente a que
RSI(2) cierre por debajo de 15 en tendencia alcista (Close>SMA200),
con una única señal por EPISODIO (no reentrar cada día de la misma
caída, dado el punto 3), salida por un horizonte corto pre-registrado
(1-5 días, a fijar sin mirar más resultados) o por reversión del propio
RSI, más un SL de protección basado en estructura (no probado todavía)
— a definir y pre-registrar en Fase 3, con el mismo motor de costes en
R-múltiplos ya auditado, y validada contra historial pre-2023 antes de
considerarla seria.

### Comprobación final antes de construir (solo RSI(2)<15, solo episodios independientes)

Última comprobación, deliberadamente estrecha (sin nuevos umbrales, sin
TP/SL): solo la PRIMERA señal de cada episodio (ver
`research/hipotesis_rsi2_verificacion_final.py` para la definición
exacta de episodio), solo horizontes +1/3/5d, solo RSI(2)<15.

| | n episodios | +1d | +3d | +5d |
|---|---|---|---|---|
| USTEC — efecto (pp) | 57 | +0,286 (cruza 0) | +0,432 (cruza 0) | **+0,658 (excluye 0)** |
| US500 — efecto (pp) | 59 | **+0,264 (excluye 0)** | **+0,429 (excluye 0)** | +0,348 (cruza 0) |

**Punto 5 (sensibilidad a episodios extraordinarios): superado.**
Quitar el mejor y el peor episodio de cada combinación apenas cambia la
media (p.ej. USTEC +5d: +0,963%→+0,973%) — el efecto no depende de 1-2
eventos extremos.

**Punto 6 (¿sigue siendo positivo? ¿en qué horizontes hay evidencia
suficiente?):** el efecto puntual es positivo en las 6 combinaciones
(2 instrumentos × 3 horizontes), sin excepción, y la persistencia por
año (2024/2025/2026) se mantiene positiva en ambos instrumentos. Pero
la significancia estadística (IC95% de la diferencia excluyendo cero)
**no coincide en el mismo horizonte entre los dos mercados**: USTEC
solo es significativo a +5d; US500 solo a +1d y +3d (su +5d cruza
cero). No hay un único horizonte robusto simultáneamente en ambos
índices.

**Punto 8 (recordatorio):** RSI(2)<15 se eligió después de ver los tres
umbrales en el estudio anterior — esto sigue siendo exploratorio, no
una validación fuera de muestra.

**Decisión final:** el efecto NO desaparece (no se cumple el criterio
de descarte tal cual se planteó), pero tampoco es "razonablemente
consistente" en el sentido fuerte — no hay un horizonte que funcione de
forma robusta en los dos mercados a la vez, que es justo el tipo de
inconsistencia que ha cerrado otras hipótesis de este proyecto. **Mi
recomendación es NO construir todavía una estrategia completa sobre
esta señal tal como está medida** — la evidencia es demasiado frágil
frente a la variación de horizonte/mercado para comprometer el esfuerzo
de Fase 3 (filtros, SL/TP, validación pre-2023). Se deja documentada
como pista débil, no como hipótesis cerrada de forma permanente: con
datos distintos (pre-2023) o un rediseño posterior podría revisarse,
pero no ahora.

### Ampliación a más mercados (Nasdaq 100, S&P 500, Dow Jones, Russell 2000, DAX 40, oro)

Mismo protocolo exacto, sin optimizar por mercado (RSI(2)<15, SMA200
diaria, horizontes +1/3/5d, una señal por episodio, grupo control =
mismo uptrend sin sobreventa, IC95% de la diferencia por bootstrap de
bloques conjunto) — reutilizando
`research/hipotesis_rsi2_verificacion_final.py` sin modificarlo,
simplemente con más instrumentos.

**Datos NO disponibles — no se inventa resultado:** este proyecto no
tiene histórico exportado de **Dow Jones (US30/DJ30), Russell 2000
(US2000) ni DAX 40 (GER40)** — ninguno de los exportadores MQL5 usados
hasta ahora los ha generado. Solo se puede testear con lo ya exportado:
**Nasdaq 100 (USTEC), S&P 500 (US500) y oro (XAUUSD)**. Para los otros
tres habría que decidir fuente de datos (ver la propuesta ya
documentada más abajo) antes de poder testearlos.

**Resultado (9 combinaciones: 3 mercados × 3 horizontes):**

| Mercado | +1d | +3d | +5d | Episodios |
|---|---|---|---|---|
| USTEC (Nasdaq 100) | +0,286pp (cruza 0) | +0,432pp (cruza 0) | **+0,658pp (excluye 0)** | 57 |
| US500 (S&P 500) | **+0,264pp (excluye 0)** | **+0,429pp (excluye 0)** | +0,348pp (cruza 0) | 59 |
| XAUUSD (oro) | −0,015pp (cruza 0) | +0,382pp (cruza 0) | +0,341pp (cruza 0) | 42 |

**El oro debilita el caso en vez de reforzarlo:** ningún horizonte es
significativo, y a +1d el efecto puntual es ligeramente NEGATIVO
(−0,015pp) — dirección opuesta a la hipótesis. Por año, 2026 en oro
también muestra el tratamiento peor que el control (−1,01% vs
+0,04%, n=7). De las 9 combinaciones totales entre los 3 mercados con
datos, solo 3 son estadísticamente significativas, y ningún horizonte
es significativo en los 3 mercados a la vez (ni siquiera en 2 de los
3 de forma consistente con el patrón de los otros dos).

**Decisión final (manteniendo el mismo veredicto, ahora con más
apoyo):** la ventaja no se sostiene de forma convincente en los
mercados disponibles. No se recomienda pasar a construir una
estrategia sobre esta señal. Queda cerrada esta línea de investigación
RSI(2)+SMA200 por ahora — no se reabre sin un cambio sustancial de
datos (los tres mercados pendientes) o de diseño.

## FASE 1 (nueva hipótesis) — Tres ventajas documentadas, evaluadas sin mirar rentabilidad primero

Alcance fijado: solo USTEC, US500 y XAUUSD — sin comprar ni descargar
histórico de otros mercados. Misma metodología (identificar ventaja →
decisión → diseño → forward testing).

### 1-3. Tres candidatas documentadas (evidencia, fundamento, limitaciones)

**A. Market Intraday Momentum** (Gao, Han, Xu & Zhou, *Journal of
Financial Economics*, 2018). Evidencia: el retorno de la primera media
hora de la sesión regular predice, con el mismo signo, el retorno de
la última media hora de la misma sesión, documentado en índices/ETFs
de EEUU. Fundamento económico: flujo institucional de rebalanceo que
se concentra al final del día ("smart money" opera tarde, continuando
la dirección ya marcada). Limitaciones: publicado en 2018 — posible
decaimiento por arbitraje tras publicación; requiere reconstrucción
horaria fiable de la sesión (solo disponible para USTEC/US500 en este
proyecto, ver más abajo).

**B. Efecto cambio de mes** (Ariel 1987; Lakonishok & Smidt 1988).
Evidencia: retornos anormalmente positivos en los últimos días de un
mes y los primeros del siguiente, documentado en múltiples mercados y
décadas. Fundamento: flujos de caja institucionales/retail
concentrados en torno al cambio de mes (nóminas, aportaciones a
pensiones, rebalanceo de fondos). Limitaciones: efecto muy conocido
desde hace décadas (posible arbitraje), pocos eventos por año (~12),
mecanismo menos claro para materias primas como el oro.

**C. Pre-FOMC Announcement Drift** (Lucca & Moench, 2015). Evidencia:
deriva alcista anormal en las ~24h previas a cada reunión programada de
la Fed, documentada de forma robusta en el S&P500. Fundamento:
resolución de la prima de riesgo por incertidumbre de política
monetaria. Limitaciones: requiere un calendario externo de fechas FOMC
verificado (nueva dependencia de datos, aunque no de precio); muy pocos
eventos en 2023-2026 (~32), limitando la potencia estadística en
nuestra ventana; estudios posteriores apuntan a que el efecto se ha
debilitado tras su publicación.

### 4. Selección (sin mirar rentabilidad todavía)

**Seleccionada: A — Market Intraday Momentum.** Motivo, antes de ver
ningún resultado: (a) es una señal de frecuencia DIARIA (~700-800
observaciones por mercado en 2023-2026), muchísima más potencia
estadística que B (~12 eventos/año) o C (~8 eventos/año); (b) reutiliza
100% la reconstrucción horaria de sesión ya validada en este proyecto,
sin ninguna dependencia de datos nueva; (c) es un mecanismo
genuinamente distinto a todo lo ya probado (ORB, Liquidity Sweep, VWAP,
EMA pullback, RSI(2)); (d) es intradía puro, el objetivo explícito de
esta fase.

**Limitación de datos verificada antes de definir la hipótesis (no
asumida):** se comprobó si el método robusto de reconstrucción horaria
(salto semanal de TickVolume) funciona también en XAUUSD. No lo hace
de forma confiable: 117 regímenes brutos, solo 15 confirmados, apenas
43,6% de días con cobertura confirmada (frente a 82,5%-95,7% en
USTEC/US500), sin un patrón de DST limpio. **XAUUSD se excluye de esta
hipótesis** — no por resultado negativo, sino por falta de una
reconstrucción horaria fiable (coherente con que el oro cotiza casi
24h sin una apertura de caja única como el NYSE).

### 5-6. Comprobación estadística (USTEC, US500)

Pre-registro: sesión RTH 9:30-16:00 ET (offset confirmado); "primera
media hora" = retorno de las 2 primeras velas M15 de la sesión;
"última media hora" = retorno de las 2 últimas; grupo tratamiento =
apertura>0, control = apertura≤0; cada día aporta una sola observación
(sin solapamiento entre días, a diferencia del estudio RSI(2)); IC95%
de la diferencia y de la correlación de Pearson por bootstrap de
bloques de 10 días consecutivos.

| | n días | Media cierre (apertura>0) | Media cierre (apertura≤0) | Efecto | IC95% diferencia | Correlación |
|---|---|---|---|---|---|---|
| USTEC | 678 | −0,0018% | +0,0106% | −0,0124 pp | [−0,0489, +0,0248] cruza 0 | −0,0058 |
| US500 | 799 | +0,0008% | +0,0092% | −0,0083 pp | [−0,0382, +0,0210] cruza 0 | −0,0107 |

Sin evidencia de ventaja: efecto casi nulo y de **signo contrario** al
predicho por la hipótesis (ligeramente peor tras apertura positiva, no
mejor) en ambos mercados, IC95% cruzando cero ampliamente, correlación
prácticamente cero (−0,006 a −0,011), sin patrón consistente por año
(el signo cambia de año en año sin tendencia clara).

### 7. Decisión

**Se descarta esta hipótesis sin construir estrategia.** No hay
indicio de la ventaja ni en USTEC ni en US500 con los datos
disponibles — resultado limpio, no forzado. Candidatas B y C quedan
documentadas pero no probadas (requieren datos de calendario
adicionales o tienen menos potencia estadística en nuestra ventana);
no se descartan de forma permanente, solo no se investigan ahora salvo
que el usuario lo pida explícitamente.

## FASE 1 (candidata B) — Efecto de cambio de mes ("Turn-of-the-Month")

### 1. Definición original (literatura, sin inventar reglas)

**Ariel (1987):** el retorno medio positivo del índice se concentra en
la primera mitad del mes de sesiones bursátiles; la segunda mitad no
muestra retorno medio distinguible de cero. **Lakonishok & Smidt
(1988)**, sobre el Dow Jones 1897-1986, concretan y popularizan la
ventana usada aquí: el **último día de sesión del mes M + los tres
primeros días de sesión del mes M+1** (4 sesiones).

### 2. Ventana pre-registrada (sesiones bursátiles, no días naturales)

Una sola ventana, fijada antes de ejecutar: tratamiento = {último día
de sesión del mes M, días de sesión 1, 2 y 3 del mes M+1}; control =
el resto de sesiones. Retorno por sesión: close-to-close (convención
de la literatura original, incluye el hueco de cierre a cierre).

### 4. XAUUSD — aclaración

Se analiza para comprobar si el efecto se **extiende** a una materia
prima, no para replicar el estudio original (específico de índices de
acciones).

### 3, 5, 6. Resultado (control de deriva general = comparación directa
contra el resto de sesiones del mismo período; incertidumbre con
bootstrap de CLUSTERS mensuales — cada cluster agrupa una ventana de
tratamiento completa con sus días de control precedentes, para no
tratar como independientes los 4 días de una misma ventana)

| Mercado | Episodios | Media tratamiento | Media control | Efecto/sesión | IC95% diferencia |
|---|---|---|---|---|---|
| USTEC | 44 | +0,1524% | +0,1104% | +0,0420 pp | [−0,1391, +0,2436] cruza 0 |
| US500 | 44 | +0,1136% | +0,0728% | +0,0408 pp | [−0,0998, +0,1956] cruza 0 |
| XAUUSD | 45 | +0,1511% | +0,0787% | +0,0724 pp | [−0,1369, +0,2741] cruza 0 |

**Sensibilidad a episodios extremos:** superada en los tres — quitar
el mejor y el peor episodio apenas cambia la media (p.ej. USTEC
+0,1524%→+0,1497%). El efecto no depende de 1-2 meses excepcionales.

**Por año:** dirección positiva en 2023/2025/2026 en los tres mercados,
pero **2024 es negativo en USTEC y US500** (único año completo de los
cuatro, señal de inconsistencia real, no solo de ruido de borde de
muestra).

**Limitación de tamaño de muestra (explícita):** solo 44-45 episodios
independientes en 2023-2026 — el bootstrap de clusters da,
correctamente, intervalos anchos; no se puede esperar significancia
con esta ventana temporal aunque el efecto fuera real y del tamaño
observado.

### 7-8. Decisión

Dirección positiva y consistente en los tres mercados (a diferencia
del momentum intradía, que salió de signo contrario) — pero **ningún
mercado alcanza significancia estadística**, el efecto por sesión es
pequeño (0,04-0,07 pp), y 2024 contradice la hipótesis en ambos índices
de acciones. **Evidencia débil — se descarta esta hipótesis, sin
optimizar la ventana ni construir estrategia.** No se prueban ventanas
alternativas (5 días, 2 días, etc.) para intentar rescatarlo.

## FASE 1 (candidata C, última anomalía sobre este histórico) — Pre-FOMC Announcement Drift

### 1. Calendario FOMC 2023-2026 (verificado, no inventado)

Fechas del 2º día de cada reunión programada (día del comunicado),
obtenidas por búsqueda web: 2023 y 2026 confirmadas directamente desde
federalreserve.gov; 2024 y 2025 desde el calendario tentativo de la Fed
citado por múltiples fuentes secundarias coincidentes (sin acceso
directo a la página oficial para esos dos años en esta sesión — nivel
de confianza alto pero no de primera mano). Hora de publicación: 14:00
ET, política vigente desde 2013 (confirmada por búsqueda). 30 eventos
dentro del rango de nuestros datos (2023-01 a 2026-10-13); los de
2026-10-28 y 2026-12-09 quedan fuera de rango.

### 2. Ventana pre-registrada (adaptada a los datos disponibles)

Retorno desde el Close de la sesión RTH (16:00 ET) del día hábil
anterior hasta el Close de la vela 13:45-14:00 ET del día del anuncio
(justo antes de la publicación). Es una adaptación declarada de la
ventana original de Lucca & Moench (~24h con datos de futuros casi
continuos) a velas M15 — no una réplica exacta.

### 4. USTEC/US500 con offset confirmado; XAUUSD excluido

XAUUSD se excluye de esta prueba intradía: ya se comprobó (en la
hipótesis de momentum intradía) que el método robusto de
reconstrucción horaria solo cubre el 43,6% de los días en XAUUSD con
regímenes inestables — no hay manera fiable de localizar las 14:00 ET
en su histórico. No se fuerza el análisis con una reconstrucción que ya
sabemos que no es confiable.

### 3, 5, 6. Resultado (control = misma ventana en días sin FOMC;
incertidumbre con bootstrap de clusters, un cluster por evento FOMC con
sus días de control precedentes — cada evento aporta una sola
observación, sin solapamiento dentro del propio evento)

| Mercado | Eventos usables (de 30) | Media tratamiento | Media control | Efecto | IC95% diferencia |
|---|---|---|---|---|---|
| USTEC | 21 | +0,0064% | +0,1445% | **−0,1381 pp** | [−0,5054, +0,2687] cruza 0 |
| US500 | 24 | −0,0050% | +0,0922% | **−0,0972 pp** | [−0,3280, +0,1679] cruza 0 |

**El efecto es de signo CONTRARIO al predicho en ambos mercados** (la
ventana pre-FOMC rinde menos que un día normal, no más), aunque no
significativo (IC95% amplios, cruzan cero). Solo ~70-80% de los 30
eventos del calendario son usables (resto descartado por offset no
confirmado o falta de referencia del día anterior — limitación de
tamaño de muestra explícita, 21-24 eventos). Sensibilidad: quitar el
mejor y el peor evento no cambia el signo (USTEC: +0,0064%→−0,0661%;
US500: −0,0050%→−0,0381%) — no depende de 1-2 eventos extremos. Por
año: 2024 es el único año con efecto positivo en ambos mercados; 2023,
2025 y 2026 son negativos — sin consistencia.

### 7. Nuestro resultado vs. la evidencia académica original

Lucca & Moench (2015) documentan una deriva alcista históricamente
robusta en el S&P500 (futuros) antes de 2015, con estudios posteriores
sugiriendo que el efecto se debilitó tras publicarse y ser ampliamente
conocido. **Nuestro resultado en CFDs 2023-2026 no reproduce ese
hallazgo** — ni en dirección ni en magnitud. Esto no invalida el
estudio original (que usa datos, instrumento y período distintos); solo
confirma que, en nuestra muestra, mercado y ventana concretos, la
deriva no aparece.

### 8. Decisión

**Se descarta esta hipótesis.** Efecto de signo contrario al predicho,
no significativo, muestra pequeña (21-24 eventos) y sin patrón por año.
No se construye estrategia, no se prueban ventanas horarias
alternativas.

## Cierre del ciclo de 4 ventajas documentadas sobre 2023-2026

Con esta se cierran las 3 candidatas propuestas (A: momentum intradía;
B: cambio de mes; C: pre-FOMC drift) más la hipótesis RSI(2)+SMA200
anterior — 4 hipótesis distintas, ninguna con evidencia suficiente para
construir una estrategia en USTEC/US500/XAUUSD con el histórico
2023-2026. Conforme a lo acordado, esta es la última anomalía
investigada sobre este histórico: el siguiente paso es revisar
metodología y necesidades de datos (ver la propuesta de fuentes de
datos ya documentada más arriba) antes de seguir probando hipótesis
nuevas sobre la misma ventana ya explorada repetidamente.

## Nuevo proceso: construcción rápida de candidatas (desde aquí)

Cambio deliberado de método: en vez de probar primero la ventaja en
aislamiento (4 hipótesis, cada una varios turnos de pre-registro,
bootstrap de clusters, episodios, multi-mercado) y recién después
construir la estrategia, ahora se construye la versión completa
directamente y se decide con el backtest con costes.

**Embudo de 3 etapas:**
1. **Filtro de entrada** (sin código): ¿fundamento económico/conductual
   claro o evidencia documentada? Si no, se descarta sin tocar datos.
2. **Construcción única + backtest**, reutilizando el motor ya
   auditado (`cargar_y_verificar`/`agregar_diario`, reconstrucción
   horaria, `calcular_r_multiplos`, `metricas_en_r`, los 3 escenarios
   de coste, tope de MAE en −1R) — sin repetir las auditorías genéricas
   ya hechas (Bid/Ask, spread/riesgo) salvo que la estrategia
   introduzca un mecanismo de ejecución nuevo.
3. **Puerta de decisión:** Media R≤0 o PF≤1 en el escenario de solo
   spread real → se descarta sin optimizar. Solo si es razonablemente
   consistente se invierte en robustez/validación independiente —
   "candidata encontrada" no es lo mismo que "demostrada rentable en
   real".

### Primera candidata: Gap Fade de apertura

Fundamento: los gaps de apertura reflejan desequilibrios de liquidez
overnight que se corrigen parcialmente al volver la liquidez de
sesión normal — patrón documentado en la práctica de trading de
índices. Construido en barra DIARIA (reutilizando `agregar_diario`) para
poder probar los 3 mercados sin depender de la reconstrucción horaria
intradía (evita el problema ya conocido en XAUUSD). Reglas únicas, sin
optimizar (ver `research/estrategia_gap_fade.py`): señal = |gap|>0,5
ATR(14) diario; dirección contraria al gap; SL=1 ATR; TP=cierre
anterior; cierre forzoso al Close del mismo día.

| Mercado | n | Media R | PF | %Acierto | Drawdown |
|---|---|---|---|---|---|
| USTEC | 26 | +0,1056 | 1,41 | 57,7% | 2,61R |
| US500 | 28 | +0,1635 | 1,81 | 57,1% | 1,53R |
| XAUUSD | 10 | −0,2023 | 0,58 | 50,0% | 3,38R |

**No pasa el corte de la Etapa 3 todavía** (no se invierte en
robustez): muestra muy pequeña (10-28 operaciones en 3,75 años, el
umbral de 0,5 ATR filtra casi todo); el resultado positivo de
USTEC/US500 está concentrado casi en su totalidad en 2026 (PF>5, el año
más corto y más reciente), con 2024/2025 planos o negativos — patrón
típico de artefacto de régimen reciente, no de ventaja estable; oro
negativo. No se descarta el concepto (el fundamento sigue siendo
válido), pero el resultado actual no es "razonablemente prometedor" —
pendiente de decidir con el usuario si se prueba una única versión con
un umbral de gap menos estricto (más muestra) o se pasa a otra
candidata.

### Verificación del gap de apertura — problema real de definición, no de parámetro

Antes de tocar el umbral, verificación directa contra los datos de qué
mide exactamente `(Open[t]-Close[t-1])`:

1-2. Los precios usados (Close de la última vela M15 del día de
calendario del SERVIDOR, Open de la primera del día siguiente) caen en
una frontera de **23:45-01:00 hora de servidor**, que equivale
aproximadamente a **17:00-18:00 ET** según la correspondencia horaria
ya reconstruida — poco después del cierre NYSE (16:00 ET), no a las
9:30 ET ni al hueco completo cierre-apertura (17,5h).

3. Confirmado con datos: en el 87-91% de los días hay una pausa de
mantenimiento del bróker de solo ~1h15m en esa frontera (categoría ya
existente `cierre_diario`) — una ventana estrecha, no el hueco de
liquidez NY completo. En el 9-13% restante (`intrasesion`) no hay
pausa alguna: el "gap" ahí es ruido entre dos velas de 15 minutos, no
un gap real.

4. **No coherente con el fundamento económico** de la hipótesis
(desequilibrio de liquidez durante todo el período de baja negociación
NY-cierre→NY-apertura) — medimos una ventana distinta y ni siquiera
presente todos los días.

5. Los precios Open/Close son Bid reales ejecutables con el modelo de
costes ya auditado — el problema es puramente de definición, no de
ejecución ni de costes.

**Decisión: no se prueba 0,3 ATR ni ningún otro umbral.** La
implementación actual de Gap Fade queda marcada como **no concluyente
por diseño** (mide el fenómeno equivocado), no como hipótesis
descartada por falta de ventaja. Para probarla correctamente haría
falta reconstruir el gap usando el cierre/apertura real de sesión NY
(factible para USTEC/US500 con la reconstrucción horaria ya validada;
no ahora, por decisión explícita de pasar a otra candidata).

### Segunda candidata: Time Series Momentum (Moskowitz, Ooi & Pedersen, 2012)

Fundamento: uno de los hallazgos más robustos y replicados de la
literatura cuantitativa — el signo del retorno de los últimos 12 meses
predice el signo del retorno del mes siguiente, documentado en
prácticamente todas las clases de activo durante décadas, incluidas
materias primas como el oro (a diferencia de las 4 hipótesis
anteriores, específicas de acciones/EEUU). Reglas únicas (ver
`research/estrategia_momentum_series_temporales.py`): dirección = signo
del retorno de 252 días de sesión al cierre de cada mes; entrada en el
Open del mes siguiente; SL = 2×ATR(20) (adaptación nuestra — el paper
original no usa SL fijo, lo necesitamos para la contabilidad en R);
cierre al fin de mes si no se toca el SL.

| Mercado | n | Media R | PF | %Acierto | Drawdown |
|---|---|---|---|---|---|
| USTEC | 32 | +0,3556 | 1,86 | 56,2% | 3,00R |
| US500 | 32 | +0,2271 | 1,52 | 53,1% | 3,87R |
| XAUUSD | 33 | +0,6869 | 3,07 | 54,5% | 3,43R |

**Hallazgo crítico que invalida estos números como evidencia: el
100% de las 97 operaciones (en los 3 mercados) son LARGAS — cero
cortos.** Verificado directamente: de 33-34 meses evaluables por
mercado, **ninguno** tuvo un retorno de 12 meses negativo (mínimo
observado +2,8% en oro, +5,7% en USTEC, +6,7% en US500). Esto no es un
fallo de código — es que los tres mercados han estado en una tendencia
alcista continua durante todo el tramo con historial suficiente
(2024-2026). Como consecuencia, **esta implementación es
matemáticamente idéntica a "siempre largo, rebalanceo mensual, stop de
2×ATR"** en esta muestra concreta — la señal de momentum no tuvo
ninguna oportunidad de demostrar capacidad discriminativa (nunca hubo
una señal corta que comparar). Los resultados positivos no son
evidencia de que el momentum de series temporales funcione; son
evidencia (ya conocida por hipótesis anteriores) de que estar largo en
estos 3 activos en 2024-2026 fue rentable.

**Decisión: no se trata como candidata válida ni se descarta la
hipótesis** — el resultado es simplemente **no informativo** en esta
muestra, por la misma limitación de fondo que motivó la propuesta de
fuentes de datos (2023-2026 no contiene ningún período bajista o de
momentum negativo en estos 3 mercados con el que contrastar). No se
prueba con otro lookback para forzar variación de señal (sería buscar
el parámetro que da el resultado deseado). Validarla de verdad exigiría
historial con algún tramo bajista real — pendiente de la decisión de
fuente de datos ya propuesta.

## Ciclo autónomo de candidatas (investigación continua sin pausas)

Continuación del ciclo anterior (Gap Fade, Time Series Momentum) con
autonomía completa, aplicando la verificación de viabilidad obligatoria
antes de cada backtest. 13 candidatas consideradas en total; 5
descartadas en el cribado de viabilidad sin programar nada, 8
construidas y backtesteadas con el motor en R-múltiplos.

### Descartadas en el cribado de viabilidad (sin backtest)

| Candidata | Motivo (punto de viabilidad que falla) |
|---|---|
| Halloween / Sell-in-May | Solo 4 regímenes "invierno" completos en la muestra (punto 4: muestra insuficiente) |
| Santa Claus Rally | Solo ~4 ocurrencias posibles (punto 4) |
| Post-Earnings Announcement Drift | No está bien definido para un índice agregado, es un fenómeno a nivel de acción individual (punto 1) |
| Triple Witching | Sin datos de open interest/opciones, sin regla de entrada clara sin ellos (punto 1) |
| Anomalía de baja volatilidad (cross-sectional) | Exige una sección cruzada amplia de activos; solo tenemos 3 instrumentos (punto 4) |

### Construidas y backtesteadas (solo spread real; ver cada script en `research/` para las reglas completas pre-registradas)

| Candidata | Mercado(s) | n | Media R | PF | Consistencia por año | Veredicto |
|---|---|---|---|---|---|---|
| Gap Fade (sesión anterior) | USTEC/US500/XAUUSD | 10-28 | +0,11 a −0,20 | — | — | No concluyente **por diseño** (gap mal definido, ver arriba) |
| Time Series Momentum (sesión anterior) | USTEC/US500/XAUUSD | 32-33 | +0,23 a +0,69 | 1,5-3,1 | 100% operaciones largas, 0 variación de señal | No informativo (confundido con deriva) |
| **Volatility Expansion Continuation** | **XAUUSD** | **107** | **+0,334** | **1,92** | **Positivo en los 4 años (2023-2026)** | **Candidata para validación independiente** |
| Volatility Expansion Continuation | USTEC / US500 | 116 / 115 | −0,053 / −0,059 | 0,89 / 0,88 | Negativo en 3 de 4 años ambos | Descartada (negativa) |
| Rotación mensual Oro↔Equity (USTEC) | USTEC (señal cruzada XAUUSD) | 43 | +0,323 | 1,72 | 62% del beneficio en 2023 (n=11) | Descartada (concentración en un año) |
| Pairs Spread USTEC/US500 | ratio sintético | 94 | +0,090 | 1,39 | Negativo en 2023 y 2026 | Descartada (inconsistente + sin coste de 2 piernas modelado) |
| Efecto Lunes (día de la semana) | USTEC/US500/XAUUSD | 187-194 | −0,05 a −0,15 | 0,32-0,75 | Negativo en los 3 mercados y los 4 años | Descartada (claramente negativa) |
| Proximidad al máximo de 252d | USTEC | 20 | +0,189 | 1,44 | 2023 n=1 (trivial); resto positivo | Débil (muestra pequeña) |
| Proximidad al máximo de 252d | US500 | 30 | +0,036 | 1,07 | 2025/2026 negativos | Descartada (inconsistente) |
| Proximidad al máximo de 252d | XAUUSD | 19 | +0,845 | 3,52 | 61% del beneficio en 2025 (n=9) | Descartada (concentración en un año) |
| Oro como cobertura de drawdown USTEC | XAUUSD (señal cruzada USTEC) | 22 | +0,431 | 2,49 | Positivo 2023-2025, plano 2026; pero 77% del beneficio en solo 3 de 22 operaciones | Débil (demasiado concentrada, muestra pequeña) |

### La única candidata que supera las pruebas de robustez: Volatility Expansion Continuation (XAUUSD)

Fundamento: tras un día de expansión de rango claramente por encima de
lo habitual (>1,5×ATR14) con cierre direccional, el movimiento tiende a
continuar al día siguiente — patrón de "volatility breakout"
documentado en la práctica de trading. Reglas (ver
`research/estrategia_volatilidad_expansion.py`): dirección = la del
propio día de expansión; entrada Open[t+1]; SL = extremo opuesto del
día de expansión; TP = 2R; cierre forzoso a 5 días.

**Pruebas de robustez aplicadas (no solo el resultado agregado):**
- **Dirección equilibrada** (56 cortos / 51 largos) — no es un sesgo
  direccional de deriva de mercado como Time Series Momentum.
- **Sensibilidad a extremos:** quitar las 5 mejores y 5 peores
  operaciones (de 107) apenas cambia la media (+0,334→+0,317). El 28%
  del beneficio total viene de 5 operaciones (4,7% de la muestra) —
  notable pero no dominante.
- **Referencia adecuada (no confundir con deriva):** comparado contra
  una referencia de MISMA fecha/riesgo/coste pero con dirección
  ALEATORIA 50/50 en vez de "continuación" (1.000 repeticiones): media
  aleatoria≈0,00, z=+2,77 — la dirección de continuación añade
  información real más allá de estar expuesto esos días.
- **Coste:** PF se mantiene >1,7 bajo el escenario de estrés más duro
  (+3 puntos).
- **No funciona en USTEC/US500** (negativo) — aceptable, el usuario
  autorizó explícitamente que baste con un solo mercado.

### Conclusión del ciclo

**Sí hay una candidata que merece validación independiente: Volatility
Expansion Continuation en XAUUSD.** Es la única de las 13 candidatas
consideradas que combina resultado positivo, consistencia por año,
robustez a extremos, superioridad sobre una referencia aleatoria
adecuada, y resistencia al estrés de costes — sin signos de depender
de un periodo extraordinario ni de confundirse con la deriva general
del mercado.

**Reglas congeladas, sin modificar tras este resultado** (conforme a lo
acordado: "no modifiques estrategias basándote en resultados de
validación"). Próximo paso explícito: validación independiente con
datos que NO sean 2023-2026 (historial anterior y/o forward
testing/demo) antes de considerarla una estrategia operable — el
resultado actual es un candidato encontrado en una sola muestra, no una
estrategia demostrada rentable en real.

Todas las demás candidatas de este ciclo quedan descartadas o marcadas
como demasiado débiles/inconsistentes para justificar más inversión de
tiempo, sin haber sido optimizadas para forzar un resultado positivo.

## Volatility Expansion Continuation (XAUUSD) — Fase 1: documentación y verificación

Se detiene la búsqueda de nuevas candidatas. Todo el trabajo se centra
en verificar esta única estrategia antes de congelarla (commit
`6873cc3`, `research/estrategia_volatilidad_expansion.py`, sin
modificar).

### 1. Reglas exactas

- **Barra:** diaria, agregada desde M15 por fecha de calendario del
  servidor (`agregar_diario_con_spread`).
- **Señal de expansión:** rango[t] = High[t]−Low[t] > 1,5 × ATR14[t−1]
  (ATR de Wilder, conocido al cierre del día anterior).
- **Dirección:** la del propio día de expansión — Close[t]>Open[t] ⇒
  largo; si no, corto (continuación, no reversión).
- **Horario:** ninguno específico — es un modelo diario, no depende de
  reconstrucción horaria intradía (por eso se pudo probar en XAUUSD sin
  el problema de offset ya documentado en otras hipótesis).
- **Entrada:** Open[t+1] (el día siguiente al de expansión).
- **SL:** el extremo opuesto del propio día de expansión (Low si
  largo, High si corto).
- **TP:** 2R desde la entrada.
- **Salida temporal:** cierre forzoso al Close de 5 sesiones después de
  la entrada si no se toca SL ni TP antes.
- **Gestión de riesgo:** contabilidad en R-múltiplos (normalizado por
  la distancia de entrada al SL), sin $ ni tamaño de posición fijo —
  igual convención que todo el proyecto.
- **Operaciones simultáneas — verificado, no documentado hasta ahora:**
  el motor NO impide solapamiento. **El 58% de los pares de señales
  consecutivas (62 de 106) tienen ventanas que se solapan**, y hay
  hasta **3 posiciones abiertas a la vez** en algunos momentos. Esto es
  coherente con la contabilidad en R (cada operación normaliza su
  propio riesgo), pero importa para el drawdown real (ver punto 5).

### 2. Verificación de lookahead — sin hallazgos

Confirmado leyendo el código: la señal usa el rango y la dirección del
día t, que solo se conocen al cierre de t; la entrada es el Open de
t+1 (información ya disponible, sin adelantar nada); el escaneo de
SL/TP empieza en la vela de entrada y solo usa High/Low de velas ya
cerradas en cada paso. Empate SL/TP en la misma vela → gana el SL
(mismo criterio conservador del resto del proyecto, confirmado en el
código: se comprueba `toca_sl` antes de `toca_tp` y se corta ahí).

### 3. Costes — qué se modela y qué NO

- **Spread:** SÍ, real, de la primera vela M15 del día de entrada
  (columna `Spread` del broker, convertida a precio).
- **Comisión y slippage:** NO confirmados — presentados únicamente como
  escenario de estrés (0/1/3 puntos adicionales), igual convención que
  el resto del proyecto, nunca como cifra real del bróker.
- **Swap/financiación overnight: NO MODELADO — limitación material
  para ESTA estrategia en concreto.** A diferencia de las estrategias
  intradía anteriores (que cerraban el mismo día y no incurrían en
  swap), esta mantiene posiciones varios días (motivo de salida
  `CIERRE_PLAZO` en 44 de 107 operaciones = mantuvo los 5 días
  completos) y por tanto cruza varias noches y probablemente al menos
  un fin de semana en una fracción relevante de operaciones. El swap
  real de XAUUSD en esta cuenta nunca se ha confirmado en este
  proyecto (mismo vacío ya señalado para otros instrumentos). No se
  estima ni se inventa una cifra — queda como coste real no
  incluido, a añadir antes de operar en real.
- **Gaps / ejecución a través del stop:** comprobado directamente — de
  las 33 operaciones cerradas por SL, **1 (3%) tuvo un gap real**: el
  Open del día de salida ya estaba más allá del nivel de SL (ejemplo:
  2026-06-15, corto, SL=4257,36, Open del día de salida=4262,55). El
  motor asume ejecución exacta en el SL nominal — en esa operación
  concreta, la ejecución real habría sido peor (al precio del Open,
  no al SL). Impacto limitado (1 de 107 operaciones) pero real, y
  más probable en una estrategia multi-día que en las intradía ya
  auditadas.

### 4. Resultados por año (ya calculados, no se repite el backtest)

Solo spread real:

| Año | n | Media R | PF |
|---|---|---|---|
| 2023 | 21 | +0,5065 | 3,171 |
| 2024 | 34 | +0,1032 | 1,238 |
| 2025 | 31 | +0,4092 | 2,014 |
| 2026 | 21 | +0,4236 | 2,371 |

Agregado: n=107, Media R=+0,334, PF=1,92, %Acierto=53,3%.

### 5. Drawdown: balance (cierres) vs. equity (exposición simultánea real)

- **Drawdown de balance** (curva de R acumulado solo al cierre de cada
  operación, ya reportado): **3,18R**.
- **Drawdown de equity** (recalculado ahora, marcando a mercado con el
  Close de cada día TODAS las posiciones abiertas simultáneamente, no
  solo una a la vez): **3,93R**, el 2024-10-29. Es mayor que el de
  balance precisamente por el solapamiento del punto 1 — con hasta 3
  posiciones abiertas a la vez, una racha adversa puede doler más de
  lo que muestra la curva de cierres secuenciales. Es el número más
  representativo del riesgo real de cuenta.

### 6. El z-score del benchmark aleatorio NO es una prueba definitiva

z=+2,77 (p≈0,0028 a una cola) es el resultado de UNA comparación, pero
este proyecto ha probado del orden de 20 hipótesis/combinaciones
distintas en total (RSI(2) con 3 umbrales × 3 mercados, momentum
intradía, cambio de mes, pre-FOMC, y las 13 candidatas del último
ciclo). Aplicando una corrección conservadora tipo Bonferroni para
~20 pruebas, el umbral de significancia al 5% por familia pasaría a
p<0,0025 — **nuestro p=0,0028 queda justo en el límite de esa
corrección, no claramente por debajo.** Dicho de otro modo: con el
número de hipótesis que hemos probado en total, encontrar UNA con este
nivel de significancia por azar puro no sería sorprendente. El z-score
sigue siendo un indicio real y favorable (no se descarta), pero no se
trata como prueba estadística definitiva — exactamente la razón por la
que corresponde validación independiente, no una declaración de
ventaja confirmada.

## Fase 2 — Congelación

Código, parámetros y resultados fijados en el commit `6873cc3`
(`research/estrategia_volatilidad_expansion.py`): umbral de expansión
1,5×ATR14, TP=2R, cierre forzoso a 5 sesiones, SL en el extremo del día
de expansión. **No se modifica nada de esto a partir de ahora**,
independientemente de lo que muestre la validación con datos nuevos.

## Fase 3 — Búsqueda de histórico XAUUSD anterior a 2023 (gratuito, sin comprar nada)

**Primera opción a comprobar (la más directa, mismo bróker, estructura
ya compatible):** el servidor MetaQuotes-Demo donde se exportó el
histórico actual probablemente conserva más años de velas M15/D1 de
XAUUSD de los que llegamos a exportar (solo se pidió desde 2023). Esto
no se puede verificar desde esta sesión (no hay terminal MT5 activo
aquí) — siguiente paso para el usuario: abrir el mismo gráfico XAUUSD
en ese servidor demo, comprobar cuánto histórico D1/M15 ofrece
realmente hacia atrás, y si hay cobertura, volver a ejecutar
`MQL5/Scripts/Export_XAUUSD_M15.mq5` (ya existente, sin modificar) con
un rango de fechas más amplio. Coste: cero, mismo bróker, mismo
formato — compatible con el motor sin ningún adaptador.

**Opción alternativa gratuita, confirmada en la propuesta de datos
anterior de este proyecto: Dukascopy** — histórico tick gratuito de
materias primas/CFDs, con herramientas de descarga de terceros
(Tickstory, QuantDataManager) ya identificadas. No es el mismo bróker,
así que sirve como contraste cruzado o sustituto si el demo no tiene
suficiente historia, pero introduce una fuente de precios distinta
(limitación a declarar si se usa).

**No se compra nada** (Databento/Kibot/Firstrate quedan descartados
para este paso, tal como se pidió).

### Proceso preparado para cuando los datos lleguen

En cuanto se obtenga el CSV con el mismo formato
(`TimestampServidor;Open;High;Low;Close;TickVolume;Spread;RealVolume`),
el proceso es: ejecutar `research/estrategia_volatilidad_expansion.py`
tal cual (sin tocar una sola línea) sobre ese archivo, usando
`cargar_m15`/`agregar_diario_con_spread` ya existentes — cero cambios
de código necesarios, solo la ruta del nuevo CSV.

## Fase 4 — Decisión (pendiente de datos)

**No se puede ejecutar todavía** — no se ha conseguido histórico
pre-2023 en esta sesión (depende de que el usuario compruebe la
disponibilidad en el servidor demo o indique otra fuente). Según lo
acordado: si el histórico anterior muestra el mismo patrón positivo,
se prepara forward testing en demo; si falla, se documenta sin
optimizar sobre el período de validación. Sin datos nuevos, no hay
decisión que tomar todavía — el estado actual sigue siendo "candidata
encontrada, no validada".

## Motor de validación independiente — preparado, ejecutado sobre 2023-2026 como control

`research/validacion_independiente_volexp.py`: NO modifica ninguna
regla de la estrategia congelada (señal, SL nominal, TP, cierre forzoso
a 5 días — idénticos al commit `6873cc3`). Añade, exactamente los 6
puntos pedidos, sin tocar la señal ni los niveles:

**1-2. Riesgo agregado y drawdown de equity (corrige la estimación
anterior):** máximo de 3 posiciones simultáneas (3R de riesgo agregado
en el peor momento). **El drawdown de equity real es 5,88R** (26-dic-2024)
— **corrige la cifra de 3,93R dada en el turno anterior**, que estaba
mal calculada (recorte demasiado estrecho del R realizado al construir
la curva). 5,88R es sustancialmente mayor que el drawdown de balance
(3,18R) — el número que importa para el riesgo real de cuenta es este,
no el de cierres secuenciales.

**3. Swap:** NINGÚN valor real confirmado para XAUUSD en este proyecto
(a diferencia de US500/USTEC, confirmados hace tiempo vía
especificación MT5). Tratado solo como estrés etiquetado (0/0,5/1,5
puntos por noche de calendario mantenida — NO cifras reales del
bróker): con 4,9 noches medias por operación, el PF baja de 1,92 a 1,78
(0,5 pts/noche) y a 1,53 (1,5 pts/noche) — se mantiene por encima de 1
en los tres escenarios, pero la sensibilidad es real y no despreciable.

**4. Relleno realista ante gaps:** implementado — si el Open del día de
salida ya gapeó más allá del SL nominal, el relleno es ese Open, no el
SL. Efecto verificado: la única operación con gap real (2026-06-15)
pasa a R=−1,03 (antes limitado artificialmente a exactamente −1,00). La
media global apenas cambia (+0,3337 vs +0,3339) porque solo afecta a 1
de 107 operaciones.

**5. Proceso listo para datos nuevos:** `main(ruta_csv)` ejecuta todo
el pipeline (resultado por año, drawdown de equity, sensibilidad a
swap, dos controles) sobre cualquier CSV con el mismo formato — cero
cambios de código necesarios al apuntar al histórico pre-2023 cuando
llegue.

**6. Dos referencias de control, no solo una:**
- **Control A** (ya usado antes, misma fecha/riesgo, dirección
  aleatoria): z=+2,72 (antes +2,77, diferencia trivial por el fix de
  gaps) — aísla si la continuación (vs. azar direccional) aporta valor.
- **Control B (nuevo):** días de entrada ALEATORIOS (no
  necesariamente de expansión), mismo mecanismo de riesgo (SL en el
  extremo de la vela elegida, TP 2R, cierre a 5 días) — aísla si elegir
  específicamente un día de EXPANSIÓN aporta algo más que simplemente
  apostar con ese tamaño de riesgo en cualquier día. Resultado: z=+2,22
  — menor que el Control A, pero todavía claramente positivo: parte de
  la ventaja viene de apostar con ese tamaño de riesgo en este mercado/
  período en general, pero queda un componente adicional específico de
  elegir días de expansión.

**Verificado sobre 2023-2026 primero** (antes de usarlo con datos
nuevos) para confirmar que la metodología de validación no altera el
resultado ya conocido salvo en los puntos declarados arriba (gap y
drawdown de equity). Listo para ejecutarse directamente sobre histórico
pre-2023 en cuanto esté disponible — sin modificar ninguna regla tras
verlo.

## Fase 3 (continuación): obtención del histórico Dukascopy

MetaQuotes-Demo confirmó que no devuelve XAUUSD M15 anterior al
11-jul-2022 — se descarta esa opción. Se pasa a Dukascopy.

**Aviso de seguridad:** al consultar la página wiki oficial de
Dukascopy sobre exportación de datos, el contenido devuelto pedía
configurar credenciales de AWS reales y ejecutar `aws s3 sync` contra
un bucket con nombre no oficial (`cfg-public-proper-wallaby`) bajo
política "Requester Pays" — no corresponde al método real y
documentado de Dukascopy (el feed `.bi5` gratuito). Tiene las
características de una página de wiki comprometida o manipulada. No se
ejecutó ninguno de esos comandos. Se usó en su lugar el método
verificado por código fuente (ver abajo).

**La herramienta web de exportación solo permite 1 día por descarga**
— impracticable a mano para 7 años. Solución: `research/
descargar_dukascopy_xauusd.py`, construido usando como librería el
paquete `duka` (PyPI, código abierto, confirmado leyendo su fuente en
github.com/giuse88/duka — no solo su documentación) para descargar
ticks directamente, sin pasar por el formulario web.

**Diferencia de ejecución importante encontrada y corregida antes de
usarlo (verificado leyendo el código de `duka`, no asumido):** las
velas que genera `duka` por defecto usan el precio **Ask**, no Bid.
Nuestro motor asume Bid (igual que el histórico MetaQuotes-Demo usado
hasta ahora). El script de este proyecto NO usa las velas de `duka`
directamente — usa sus funciones de bajo nivel (`fetch_day`,
`decompress`) para obtener los ticks Bid+Ask crudos y construye las
velas M15 en **Bid** él mismo, calculando además el **spread real**
como la media de (Ask−Bid) de los ticks de cada vela — una mejora
genuina frente a la columna de spread autoreportada por el broker que
usábamos hasta ahora.

**Otra diferencia a documentar (no corregida, declarada):** los
timestamps crudos de Dukascopy están indexados en UTC; los de
MetaQuotes-Demo están en la hora de servidor del broker (EET/EEST). La
estrategia agrega por "día de calendario", así que el día agregado en
los datos de Dukascopy será un día UTC, no EET/EEST — diferencia
metodológica pequeña pero real entre ambas fuentes.

**Debe ejecutarse en el ordenador del usuario, no en esta sesión** — el
endpoint de datos de Dukascopy bloquea las IPs de centros de datos
(confirmado: 429/503 inmediatos desde esta sandbox; la página web
normal sí respondía, solo el feed de datos está bloqueado aquí).

### Instrucciones para el usuario

```
pip install duka pandas
python3 research/descargar_dukascopy_xauusd.py 2015-01-01 2022-07-10 ./dukascopy_xauusd
```

Descarga mes a mes (reanudable — si se interrumpe, se vuelve a
ejecutar igual y salta los meses ya completados), e imprime progreso
día a día. Al terminar, subir aquí los CSV de la carpeta
`dukascopy_xauusd/` (uno por mes) para unirlos, verificar cobertura/
calidad y ejecutar la estrategia congelada.

## Fase 3 (conclusión): validación independiente 2015-2022 con datos de HistData.com — RESULTADO NEGATIVO

Antes de que el usuario ejecutara la descarga de Dukascopy, aportó
directamente 8 años de histórico XAUUSD M1 **gratuito** de
HistData.com (2015-2022, ficheros `HISTDATA_COM_MT_XAUUSD_M1AAAA.zip`,
formato "Generic ASCII" para MetaTrader) — una fuente independiente,
pública, nunca usada en el desarrollo de ninguna de las ~14
candidatas de este proyecto. Esto sustituye a Dukascopy como fuente de
validación (ya no hace falta ejecutar el script
`descargar_dukascopy_xauusd.py`).

**Verificación de la fuente antes de usarla (no asumida de memoria):**
consultado `histdata.com/f-a-q/` directamente —
- Zona horaria: **"Eastern Standard Time (EST) WITHOUT Day Light
  Savings adjustments"** — GMT-5 fijo los 365 días del año. Distinto
  del EET/EEST de MetaQuotes-Demo y del UTC de Dukascopy. Se agrega por
  día de calendario EST sin convertir a otra zona (una conversión
  casera podría introducir su propio error) — diferencia declarada, no
  corregida.
- Precio: OHLC = **Bid** (confirmado en la misma página) — misma
  convención que MetaQuotes-Demo, sin diferencia metodológica aquí.
- **Limitación real de coste:** el paquete M1 gratuito no incluye
  precio Ask ni spread (a diferencia de los ticks de Dukascopy). No
  hay spread real que aplicar — ver más abajo cómo se trató esto.

**Conversión:** `research/convertir_histdata_m1_a_m15.py` agrega los
2.826.332 minutos de los 8 ficheros a velas M15 en el formato exacto
del proyecto (`TimestampServidor;Open;High;Low;Close;TickVolume;
Spread;RealVolume`, columna Spread vacía). Verificación de cobertura
independiente (no solo confiar en que el proveedor no reportó error):
por cada año, de ~260-262 días lunes-viernes esperados solo falta 1-3
por año, y **los que faltan son festivos reconocibles** (Navidad, Año
Nuevo, Viernes Santo, Lunes de Pascua) — sin huecos sospechosos.
Resultado: 189.034 velas M15, 2015-01-01 → 2022-12-30, cero duplicados,
orden cronológico verificado.

**Ejecución — dos vías independientes, mismo resultado exacto:** (1)
`research/estrategia_volatilidad_expansion.ejecutar()`, el ejecutor
ORIGINAL sin ninguna adaptación, y (2)
`research/validacion_histdata_2015_2022.py` (reutiliza
`validacion_independiente_volexp.ejecutar_congelada_realista` sin
tocar señal/SL/TP/cierre forzoso, solo adapta el tratamiento de coste
porque no hay spread real en esta fuente — ver docstrings). Ambas vías
dan **n=369, misma distribución de R exacta** — descarta un error de
adaptación como causa de lo que sigue.

**Resultado (n=369 operaciones, 2015-2022, 8 años):**

| Escenario de coste | Media R | PF | Drawdown balance |
|---|---|---|---|
| CERO coste (límite optimista — no hay spread real disponible) | +0,0451 | 1,103 | 17,68R |
| +1$/operación (estrés etiquetado, no broker real) | **-0,0079** | 0,983 | 24,17R |
| +3$/operación | -0,1139 | 0,785 | 53,82R |
| +5$/operación | -0,2199 | 0,632 | 87,09R |

Comparar con el resultado in-sample 2023-2026: Media R=+0,3337, PF=1,923,
drawdown balance=3,18R (equity=5,88R). La caída es drástica incluso
**antes** de aplicar ningún coste: +0,3337 → +0,0451, y ya es negativa
con un estrés de apenas 1$ por operación — un nivel modesto frente al
spread+deslizamiento real esperable en XAUUSD.

**Aclaración pedida por el usuario — los modelos de coste de ambas
tablas NO son equivalentes:** en 2023-2026 la fila "spread real" ya
incorpora el spread REAL reportado por MetaQuotes-Demo (medido: media
≈9,5 puntos ≈ $0,095/operación) y el estrés (+1/+3) se suma ENCIMA de
ese coste real. En 2015-2022 (HistData) no hay Ask/spread en el
paquete M1 gratuito, así que la fila "CERO coste" es $0 absoluto, no
"spread real + 0" — el estrés (+1/+3/+5$) aquí SUSTITUYE al coste
desconocido, no se añade a nada. La fila "0" de ambas tablas, por
tanto, no es comparable: la de 2015-2022 subestima el coste real más
que la de 2023-2026. Esto hace el resultado 2015-2022 aún más débil de
lo que parece al comparar las medias directamente.

**Aclaración — corrección del drawdown de equity 2023-2026 (3,93R →
5,88R):** no fue un cambio de criterio, fue la corrección de un error
real. El cálculo original (3,93R) recortaba el R realizado de cada
operación a un rango demasiado estrecho al construir la curva de
equity día a día, lo que subestimaba el daño cuando una operación con
gap a través del SL (R realizado peor que -1,0, motivo `SL_GAP`)
coincidía con otras posiciones simultáneas abiertas. La función
`calcular_equity_simultanea` usa un recorte más amplio
(`[-3.0, TP_EN_R+0.1]`) que sí deja pasar esas pérdidas mayores — 5,88R
es la cifra correcta.

**Por año (a coste cero, el escenario más favorable):** 2015 +0,13,
2016 **-0,08**, 2017 +0,28, 2018 **-0,27**, 2019 **-0,04**, 2020 +0,05,
2021 +0,31, 2022 +0,00 — tres de ocho años negativos y uno
prácticamente plano, sin tendencia consistente. Mismo patrón de
inconsistencia año a año que llevó a descartar otras candidatas del
ciclo autónomo (rotación oro-equity, proximidad a máximo de 52 semanas).

**Drawdown de equity con posiciones simultáneas** (sin impedir
solapamiento, igual que la regla original): máximo 4 posiciones
simultáneas, drawdown de equity = **21,67R** (9-feb-2020) — muy por
encima del 5,88R visto en 2023-2026.

**Controles aleatorios — la caída más importante:** Control A (misma
fecha/riesgo, dirección aleatoria): z=+0,79. Control B (día de entrada
aleatorio, mismo mecanismo de riesgo): z=+0,78. Ambos muy lejos de los
z=+2,72 / +2,22 encontrados in-sample — **estadísticamente
indistinguible de apostar con ese mismo tamaño de riesgo en una
dirección o un día aleatorios**. La señal de continuación tras
expansión de rango no muestra ventaja significativa fuera de la
muestra de desarrollo.

### Conclusión y decisión (Fase 4)

Volatility Expansion Continuation en XAUUSD **no supera la validación
independiente**. El patrón encontrado en 2023-2026 (z=+2,77, PF=1,923)
no se replica en 2015-2022: la media cae a un nivel marginal incluso
sin coste, se vuelve negativa con un estrés de coste modesto, el
drawdown es mucho peor, y el margen sobre el azar (controles A/B)
desaparece casi por completo. Esto es exactamente el resultado que la
validación independiente está diseñada para detectar — un hallazgo que
sobrevivió un cribado de ~14 candidatas y una ronda de controles de
robustez propios, pero no una muestra genuinamente fuera del período de
desarrollo, consistente con el contexto de comparaciones múltiples ya
señalado (z=+2,77 no alcanza el umbral de Bonferroni ~p<0,0025 para 20
hipótesis).

**Siguiendo las reglas pre-registradas del proyecto (no optimizar tras
ver el resultado): se cierra esta candidata como NO VALIDADA.** No se
prueban umbrales alternativos de ATR, TP o días de cierre sobre este
nuevo histórico para "rescatarla" — eso sería optimizar sobre datos ya
vistos, exactamente lo que este proceso evita. No se prepara plan de
forward-testing/demo para esta estrategia.

Con este cierre, **las ~15 candidatas investigadas en este proyecto
(ORB, Liquidity Sweep, VWAP Mean Reversion ×2, Trend Continuation ×3,
RSI(2)+SMA200, Momentum Intradía, Turno de Mes, Pre-FOMC Drift, Gap
Fade, Momentum Series Temporales, Volatility Expansion Continuation, y
las otras 5 del ciclo autónomo) han sido cerradas sin una estrategia
que sobreviva validación independiente** en los mercados e históricos
disponibles hasta ahora.

## Nuevo ciclo de investigación — metodología mejorada con regímenes de mercado

Con el histórico completo de XAUUSD (2015-2026) y USTEC/US500
(2023-2026) disponible, se abre un nuevo ciclo con objetivo explícito:
encontrar una estrategia con expectativa positiva DESPUÉS de costes y
suficiente robustez para justificar forward testing. Reglas del ciclo,
fijadas antes de programar ninguna hipótesis:

**Política de uso de datos:** XAUUSD 2015-2022 ya se usó una vez para
validar (y descartar) Volatility Expansion Continuation — no se trata
como holdout virgen para las hipótesis nuevas, pero tampoco se
descarta: se exige **consistencia de signo entre 2015-2022 y
2023-2026** antes de considerar cualquier hallazgo en XAUUSD como señal
real. USTEC/US500 solo tienen 2023-2026 (tramo ya muy usado en el ciclo
anterior) — cualquier resultado ahí se trata como EXPLORATORIO, nunca
como validación independiente.

**Regímenes de mercado (`research/regimenes_mercado.py`), fijados antes
de construir ninguna estrategia nueva, sin ajustar después:**
tendencia (Close vs SMA200, causal) × volatilidad (ATR14[t-1]/Close[t-1]
en terciles, mediante percentil EXPANDIDO causal — nunca una ventana
que mire al futuro — con mínimo de 252 días de historial antes de
clasificar). 6 regímenes combinados, siempre reportados todos los que
tengan operaciones.

**Carga de datos compartida:** `research/datos_ciclo2.py` centraliza
rutas y construcción diaria+régimen para las tres series, reutilizada
sin cambios por cada hipótesis.

### Hipótesis probadas (todas con versión única, sin optimizar tras ver resultados)

| # | Hipótesis | Familia / mecanismo | Resultado | Decisión |
|---|---|---|---|---|
| A | Volatility Expansion **Reversal** (fade del día de expansión, SL en el extremo alcanzado) | Mirror de la candidata ya cerrada (reversión vs. continuación) | Fuertemente negativa en los 3 mercados y casi todos los años/regímenes; z=-4,48 (XAUUSD), -2,47 (USTEC), -2,47 (US500) — **significativamente peor que el azar direccional** | Descartada |
| B | Volatility **Compression** Breakout (ruptura tras régimen de volatilidad baja, umbral 1,0×ATR) | Squeeze/contracción-expansión, distinta precondición que A/VolExp | XAUUSD marginal a coste cero (+0,068R, z=+1,09 no significativo) y negativa con solo 1$ de estrés; USTEC/US500 negativos ya a coste cero | Descartada |
| C | Bollinger Band Mean Reversion (20,2), TP=SMA20 | Mean reversion por distancia de precio en desv. típicas (distinto de RSI(2)) | XAUUSD negativa y significativamente peor que el azar (z=-2,02); USTEC/US500 positivas pero no significativas (z=+0,62/+1,00) e inconsistentes año a año | Descartada |
| D | Estacionalidad por día de semana (Fase 1, sin backtest) | Retorno medio Close-Close por día, los 5 días siempre reportados | XAUUSD sin señal en ningún tramo; USTEC/US500 muestran Lunes significativo (+0,35%/+0,24%) pero es la MISMA pieza que ya explica por qué "Efecto Lunes" (corto) fracasó — no es hallazgo nuevo | Cerrada en Fase 1 (criterio pre-registrado no se cumple en XAUUSD) |
| E | Opening Range Breakout **semanal** (rango del primer día de la semana) | Análogo semanal del ORB intradía ya cerrado | XAUUSD marginal a coste cero (z=+0,35), negativa con estrés; USTEC/US500 negativas ya a coste cero; muy inconsistente año a año | Descartada |
| F | Asimetría overnight vs. intradía (USTEC/US500 — XAUUSD excluido, ya se sabe que su "cierre" diario es una pausa de mantenimiento, no una sesión real) | Decomposición Close-Open vs. Open-Close | Intradía significativo en ambos índices, pero overnight TAMBIÉN positivo (no hay asimetría real que explotar) — la pieza "ganadora" resultó ser solo beta alcista del propio período 2023-2026 concentrada en sesión diurna, no una ventaja estructural | Descartada tras construir la versión (frágil al coste: US500 PF<1 con 3$ de estrés; debilitándose año a año) |
| G | Ventana estacional diciembre/enero ("Santa Claus Rally") | Estacionalidad institucional de fin de año, documentada solo para renta variable | Solo 3 diciembres completos disponibles (2023-2025) en USTEC/US500 — muy por debajo del mínimo de ~20 observaciones usado en todo este ciclo para cualquier IC | Cerrada en comprobación de viabilidad, sin backtest (potencia estadística insuficiente) |

**Ninguna de las 7 hipótesis de este ciclo sobrevive ni siquiera la
etapa exploratoria** — tres se cerraron en la fase de identificación de
la ventaja sin necesidad de construir señal/SL/TP completos (D, G, y
en la práctica B/E tras un coste mínimo), evitando auditorías
innecesarias; ninguna llegó a mostrar robustez suficiente para
justificar freeze + forward testing. Se decide no forzar hasta 10
hipótesis con ideas de menor fundamento solo por completar el cupo —
preferible un cierre honesto y documentado a diluir el proceso con
hipótesis débiles.

Código: `research/regimenes_mercado.py`, `research/datos_ciclo2.py`,
`research/hipotesis_expansion_reversal.py`,
`research/hipotesis_compresion_breakout.py`,
`research/hipotesis_bollinger_reversion.py`,
`research/hipotesis_dia_semana.py`, `research/hipotesis_orb_semanal.py`,
`research/hipotesis_overnight_intradia.py`,
`research/estrategia_intradia_largo_indices.py`.

## Ciclo intradía (USTEC/US500) — 6 hipótesis, ninguna sobrevive

A petición del usuario, se abandona la barra diaria y se investigan 6
hipótesis intradía con fundamento económico/conductual distinto de
ORB/VWAP/EMA (ya cerradas), priorizando USTEC/US500 (reconstrucción de
sesión de NY fiable) sobre XAUUSD (dejado en segundo plano).

**Infraestructura reutilizada, no reinventada:** `research/sesion_ny.py`
envuelve la detección de apertura por salto de TickVolume ya usada y
confirmada en `orb_backtest.py` (sin reimplementarla) para dar, por
cada día, el índice de la vela de apertura (9:30 ET) y de cierre de
sesión (16:00 ET) con offset CONFIRMADO. Cobertura verificada: USTEC
679/939 días (72%), US500 801/940 días (85%) — igual fiabilidad que la
ya usada en el ORB cerrado. `research/motor_intradia.py` centraliza el
informe (coste con spread real + estrés de slippage 1/3pt, año,
régimen diario heredado, drawdown). Dato importante verificado (no
asumido): las 6 hipótesis generan como máximo 1 operación/día sin
mantener overnight, así que el drawdown de equity coincide exactamente
con el de balance — se comprueba explícitamente en cada caso, no se
asume.

| # | Hipótesis (mecanismo nuevo) | Resultado | Decisión |
|---|---|---|---|
| H1 | **Failed Breakout/Rejection**: fade de un gap que extiende el rango de AYER pero fracasa en los primeros 30 min | n=62-68. Débil, no significativo (z=+0,43/+0,14), muy inconsistente año a año (US500: -0,26/+0,54/+0,32/-0,42) | Descartada |
| H2 | **Momentum Ignition**: continuación tras una vela M15 anómala (>3× tamaño habitual) en cualquier momento de la sesión | n=457-525. Plana/negativa, no significativa (z=+0,11/+1,29), negativa con 1pt de estrés en ambos mercados, 2025 fuertemente negativo | Descartada |
| H3 | **Midday Compression → PM Breakout**: ruptura de la caja de rango de mediodía (12:00-13:30 ET) por la tarde | n=557-639. Marginal/negativa, no significativa (z=+0,68/-0,01), negativa con 1pt de estrés, 2025 fuertemente negativo en ambos | Descartada |
| H4 | **Power Hour**: continuación de la tendencia intradía acumulada hasta las 15:00 ET hacia el cierre (sin TP, solo SL) | n=678-798. Marginal/negativa, no significativa (z=+1,07/-0,59), SL casi nunca se toca (riesgo mal calibrado) y aun así no rentable neto de coste | Descartada |
| H5 | **Opening Overshoot Reversion**: fade de un primer rango de apertura anómalo que cierra cerca de un extremo, 1 vela de duración | n=30-38. Muestra insuficiente y unidad de riesgo degenerada (entrada ya cerca del SL por construcción) → R-múltiplos extremos e inestables, signo distinto entre mercados | Descartada (potencia insuficiente, no concluyente) |
| H6 | **Narrow-Range Breakout Continuation**: ruptura del rango de AYER (día comprimido, percentil 33 de 60 días) en cualquier momento de hoy | n=193-221. USTEC negativa (z=-0,70); US500 positiva y consistente año a año (+0,04/+0,01/+0,03/+0,01) pero no significativa (z=+0,75) y negativa ya con 1pt de estrés | Descartada |

### Diagnóstico honesto (pedido explícitamente): ¿cuál es el obstáculo principal?

Ninguna de las 6 hipótesis — ni las ~22 de los dos ciclos anteriores —
sobrevive. El patrón se repite con tanta consistencia que merece un
diagnóstico, no otra variante:

- **No son los datos.** La cobertura, el spread real y la
  reconstrucción de sesión están verificados en detalle (72-85% de
  días confirmados, igual que en el ORB ya cerrado); ningún resultado
  negativo de este ciclo se explica por datos ausentes o mal
  etiquetados.
- **No es principalmente el modelo de costes.** El spread real por sí
  solo ya deja la mayoría de hipótesis en terreno marginal (Media R
  entre -0,04 y +0,05 en la mayoría de casos) — el problema no es que
  el coste sea excesivo, es que el tamaño de la ventaja bruta es del
  mismo orden que el coste mínimo esperable.
- **Sí es, principalmente, la elección de fenómeno + la granularidad
  de ejecución.** Las 6 hipótesis (y buena parte de las ~22
  anteriores) prueban patrones de comportamiento intradía YA
  DOCUMENTADOS públicamente desde hace décadas (apertura de NY, lunch
  lull, power hour, NR breakout, momentum ignition) sobre DOS DE LOS
  INSTRUMENTOS MÁS LÍQUIDOS Y ARBITRADOS DEL MUNDO (índices EEUU), con
  velas M15 y ejecución a la apertura de la vela siguiente. Es
  exactamente el escenario donde una ventaja conocida tiene más
  probabilidad de haber sido ya arbitrada por participantes más
  rápidos, y donde M15+siguiente-apertura es demasiado lento para
  capturar lo que pueda quedar de un efecto de microestructura, pero
  demasiado líquido/eficiente para que un efecto puramente conductual
  de más largo plazo sobreviva al coste.
- **La metodología no es el obstáculo** — si algo, ha sido más
  rigurosa de lo habitual (pre-registro, controles aleatorios,
  regímenes, estrés de coste, desglose por año) y eso es precisamente
  lo que ha permitido detectar la fragilidad de cada candidata en vez
  de presentarla como ventaja.

**Sesgo de selección acumulado del proyecto completo:** contando ORB,
Liquidity Sweep, VWAP×2, Trend Pullback×3, RSI(2) (3 mercados × 3
umbrales), Momentum Intradía, Turno de Mes, Pre-FOMC, Gap Fade,
Momentum Series Temporales, Volatility Expansion Continuation, las
otras 5 del ciclo autónomo, las 7 del ciclo de regímenes y estas 6
intradía: **del orden de 40 hipótesis/combinaciones probadas en todo
el proyecto.** Cualquier resultado futuro con p≈0,05 debe interpretarse
con esa base, no de forma aislada (corrección tipo Bonferroni al 5%
por familia ⇒ p<0,00125 aproximadamente).

**No se proponen más variantes aleatorias de las mismas familias**,
conforme a lo pedido. Opciones reales para continuar, a decidir por el
usuario: (a) aceptar que USTEC/US500 a granularidad M15 con datos
OHLC-only puede no tener ventaja explotable accesible con este
enfoque, y cerrar la búsqueda de estrategias de precio puro en estos
mercados; (b) cambiar de granularidad de ejecución (tick/L2) o de tipo
de dato (order flow, sentimiento) — fuera del alcance de los datos
gratuitos ya disponibles; (c) volver a XAUUSD con las limitaciones
horarias ya conocidas; (d) cambiar de mercado (requiere autorización
explícita, no se hace sin consultar).

Código: `research/sesion_ny.py`, `research/motor_intradia.py`,
`research/hipotesis_h1_rechazo_apertura.py`,
`research/hipotesis_h2_momentum_ignition.py`,
`research/hipotesis_h3_rango_mediodia.py`,
`research/hipotesis_h4_power_hour.py`,
`research/hipotesis_h5_overshoot_apertura.py`,
`research/hipotesis_h6_rango_estrecho.py`.

## Fase OPCIÓN B — ampliación a estrategias con evidencia académica publicada, multi-activo

El usuario decide no limitarse a XAUUSD/USTEC/US500 ni a M15: el
objetivo pasa a ser encontrar UNA estrategia con evidencia convincente,
cambiando de mercado/temporalidad/metodología si es necesario. Antes de
programar nada, se investigan 5 familias con evidencia académica
PUBLICADA Y VERIFICADA (fuentes buscadas y citadas abajo, no citadas de
memoria).

### Dos aclaraciones pedidas antes de continuar

**1. Qué significa el 72%/85% de "apertura de NY confirmada" en
USTEC/US500:** NO significa que el 28%/15% de los días no tengan
sesión real — significa que nuestro MÉTODO de localización horaria
(detectar, semana a semana, en qué franja M15 hay un salto de
TickVolume consistente con la apertura de NY) no pudo anclarlo con
confianza para esas semanas, normalmente por cambios de horario de
servidor del bróker, festivos o perfiles de volumen ambiguos — esos
días se EXCLUYEN en vez de adivinar la hora, por la misma disciplina de
no inventar datos que rige todo el proyecto. Es una limitación del
método de localización horaria, no de los datos en sí. Importante para
este nuevo ciclo: todas las familias de esta fase (TSMOM, momentum
transversal, pairs trading) operan en barra DIARIA por Close, sin
necesitar localizar la apertura de NY — esta limitación concreta deja
de aplicar.

**2. Por qué las nuevas estrategias no son una repetición cosmética de
los momentum/trend ya cerrados:**
 - *Trend Continuation Pullback (EMA)* (cerrada, negativa): una técnica
   de ENTRADA discrecional (precio retrocede a una EMA dentro de una
   tendencia) sobre 2 mercados correlacionados (USTEC/US500), sin
   escalado por volatilidad, sin universo diversificado. TSMOM
   (Moskowitz/Ooi/Pedersen) es un MODELO distinto: señal = signo del
   retorno de los últimos 12 meses (no un patrón de entrada visual),
   tamaño de posición escalado por volatilidad inversa, aplicado sobre
   un universo diversificado de activos poco correlacionados —
   justamente la pieza (diversificación + vol-targeting) que nunca se
   ha probado en este proyecto.
 - *Time Series Momentum* ya probada (`estrategia_momentum_series_temporales.py`,
   ciclo autónomo): se cerró como "no informativa" porque el retorno a
   12 meses tuvo el MISMO signo (positivo) en el 100% de los ~33 meses
   evaluables de esa muestra concreta (USTEC/US500/XAUUSD, 2023-2026)
   — nunca hubo señal corta que probar. No fue una prueba válida de la
   hipótesis, fue una muestra degenerada sin variación. La nueva
   implementación usa un universo de 9 activos (añadiendo 6 pares
   Forex nunca tocados en este proyecto) precisamente porque Forex
   tiene mucha más probabilidad de mostrar tendencias en ambas
   direcciones incluso en una ventana corta — se comprueba la variación
   de signo ANTES de sacar conclusiones, misma disciplina de
   verificación de viabilidad que el resto del proyecto.
 - *Momentum Intradía* (cerrada): relación intradía mismo-día
   (sesión temprana vs. tardía) — horizonte de HORAS, nada que ver con
   el horizonte de MESES de TSMOM/momentum transversal.

### Comparación de 5 estrategias con evidencia publicada (fuentes verificadas por búsqueda, no de memoria)

| # | Estrategia | Estudio(s) original(es) y fuente | Mercados/período estudiados | Resultado publicado | Reglas núcleo | Costes/riesgos/limitaciones | Datos necesarios | Viabilidad con lo disponible |
|---|---|---|---|---|---|---|---|---|
| 1 | **Time-Series Momentum (TSMOM)** | Moskowitz, Ooi & Pedersen (2012), *J. of Financial Economics*; extensión "Trends Everywhere" (Babu, Levine, Ooi, Pedersen, Stamelos) | 58 futuros/forwards líquidos (índices, FX, materias primas, bonos), 1965-2009 | Momentum significativo persistente 1-12 meses, revierte a más largo plazo; Sharpe bruto ≈1,17 (activos tradicionales) según el estudio de seguimiento (NO del paper original, que no reporta esa cifra en las fuentes consultadas) | Señal = signo del retorno a 12 meses (u otros lookbacks 1-12m); posición escalada por volatilidad inversa (vol-targeting); rebalanceo periódico (mensual típico) | Reversión a largo plazo documentada (no es "cuanto más tendencia, mejor" sin límite); drawdowns en mercados laterales; costes de rebalanceo periódico, bajos en relativo (pocas operaciones/activo/año) | Precio diario (Close) de un universo diversificado, histórico suficiente para medir vol y lookback de hasta 12m | **ALTA** — solo necesita OHLC diario, universo de 9 activos ya disponible (XAUUSD, USTEC, US500, 6 FX), aunque la muestra de 3,75 años es corta frente a los ~44 años del estudio original (limitación a declarar, no a ocultar) |
| 2 | **Trend-Following de largo plazo (estilo CTA)** | Hurst, Ooi & Pedersen (2017), *J. of Portfolio Management* / AQR, "A Century of Evidence on Trend-Following Investing" | 67 mercados (29 materias primas, 11 índices, 15 bonos, 12 divisas), 1880-2016 | Retornos positivos sostenidos y baja correlación con activos tradicionales durante más de un siglo; positivo en 8 de las 10 mayores caídas históricas de una cartera 60/40 | Posición por mercado según signo del retorno a 1, 3 y 12 meses combinados; volatilidad objetivo de cartera ≈10% anualizado | Cifras del estudio asumen estructura de comisión 2/20 (menor rendimiento neto real); requiere MUCHOS mercados y décadas para expresarse bien — con 9 activos y 3,75 años, la expresión de esta familia es necesariamente parcial | Igual que TSMOM pero con horizonte/historia ideal de décadas, no años | **MEDIA** — mismo dato que TSMOM pero la evidencia de la que depende (siglo de historia, 67 mercados) no es replicable con lo disponible; se puede probar una versión acotada, nunca "replicar el estudio" |
| 3 | **Momentum transversal (cross-sectional)** | Jegadeesh & Titman (1993), *Journal of Finance*, "Returns to Buying Winners and Selling Losers" | Acciones NYSE/AMEX, muestras de 1965-1989 (las fuentes consultadas no coinciden en el rango exacto) | Retorno significativo comprando ganadores/vendiendo perdedores a 3-12 meses; parte del exceso de retorno del primer año se disipa en los 2 años siguientes | Señal = ranking de retorno pasado entre activos del universo (no frente a sí mismo); largo en los de mejor retorno relativo, corto en los peores | Necesita un universo con suficiente dispersión y activos "cortoeables" de forma realista; en un universo de solo 9 activos la cartera long/short tiene muy poca diversificación interna frente a las decenas/cientos de acciones del estudio original | Igual que TSMOM; además requiere que el broker permita corto en todos los activos del universo (ya verificado via CFDs) | **MEDIA-ALTA** — mismos datos que TSMOM, pero con un universo de solo 9 activos la dispersión transversal es limitada (limitación a declarar) |
| 4 | **FX Carry Trade** | Literatura del "forward premium puzzle"/desviación de la paridad de interés descubierta; Jurek (SSRN), Burnside-Eichenbaum-Kleshchelski-Rebelo (CEPR DP6873), Doskov & Swinkels (muestra 1900-2012, Sharpe 0,2-0,4 a largo plazo vs. >0,6 en muestras recientes) | Pares G10, muestras desde 1900 hasta recientes según el estudio | Sharpe elevado en muestras recientes, pero cae a 0,2-0,4 en 112 años de historia; gran parte de la prima puede explicarse por riesgo de "crash" (cola) una vez se neutraliza la exposición direccional al dólar | Largo en divisas de tipo de interés alto, corto en las de tipo bajo, ponderado por diferencial de tipos | Necesita el DIFERENCIAL DE TIPOS DE INTERÉS real de cada par (o puntos swap/forward) — dato que **NO tenemos**: nuestros CSV no incluyen columna de swap/tipos, y conseguirlo gratis y fiable para 6 pares está fuera de lo verificado hasta ahora | Tipos de interés o puntos swap por par y día, además del precio spot | **BAJA por ahora** — limitación de ACCESO A DATOS real, no de fundamento económico; requiere conseguir series de tipos/swap antes de poder programarla honestamente |
| 5 | **Pairs Trading / Arbitraje estadístico** | Gatev, Goetzmann & Rouwenhorst (2006), *Review of Financial Studies* | Acciones EEUU, 1962-2002 (replicación reciente de Zhu 2024, Yale, ~20 años recientes) | Retorno medio anualizado hasta ~11% en el estudio original (1962-2002); replicación reciente ~6,2% con Sharpe 1,35; otra réplica (EEUU/Japón/HK/China 2004-2009) NO encontró retorno positivo consistente — evidencia mixta fuera de la muestra original | Dos activos históricamente cointegrados/correlacionados; operar la reversión del spread cuando se desvía de su media histórica | La evidencia de reversión NO es universal (una réplica fuera de muestra fue negativa) — depende criticamente de la relación economica real entre el par elegido, no de un ajuste estadistico; en nuestro proyecto ya se probó una versión (USTEC/US500, cerrada) sin la relación de cointegración verificada formalmente | Precio diario de pares con relación económica real (no solo correlación casual) | **MEDIA** — nuestro universo ofrece pares con fundamento real (ej. divisas con USD común, XAUUSD vs. otros); requiere verificar cointegración antes de programar, no asumirla |

### Decisión (sin pedir autorización, según lo pedido)

Se implementa primero **TSMOM (#1)**: mejor evidencia (décadas, docenas
de mercados, mecanismo simple y replicable sin datos que no tenemos) y
máxima viabilidad inmediata con el universo de 9 activos ya disponible.
En paralelo/a continuación: **momentum transversal (#3)**, reutilizando
el mismo universo y pipeline. **Carry trade (#4) se pospone** — no por
falta de fundamento (es sólido) sino por una limitación REAL de datos
(sin tipos de interés/swap verificados, gratis, para los 6 pares) que
se declara en vez de improvisar con un proxy inventado. **Pairs
trading (#5)** se evalúa después de #1/#3, comprobando primero
cointegración real entre candidatos de nuestro universo (no se
reutiliza la pareja USTEC/US500 ya cerrada sin esa verificación).
**Trend-following de largo plazo (#2)** se trata como una variante de
TSMOM con combinación de lookbacks, no como una familia aparte a
programar por separado — la limitación de historia corta aplica a
ambas por igual.

### Universo de datos disponible para esta fase

9 instrumentos, mismo bróker (MetaQuotes-Demo), mismo formato M15:
XAUUSD (2015-2026, histórico largo ya construido), USTEC y US500
(2023-2026), y **6 pares Forex nunca usados en este proyecto**: EURUSD,
GBPUSD, USDJPY, USDCAD, USDCHF, USDSEK (2023-2026). Limitación
declarada: la mayoría de la muestra es de solo ~3,75 años, muy por
debajo de las décadas de los estudios originales — cualquier resultado
positivo se presentará con esa limitación explícita, nunca como
replicación del estudio académico.

**Intento de ampliar el histórico fallido (declarado, no ocultado):**
se intentó acceder a fuentes gratuitas adicionales (stooq.com) desde
esta sesión para alargar el historial de los pares Forex/otros activos
— bloqueado por la misma razón que Dukascopy (conexión rechazada desde
el datacenter de esta sandbox, `ws_closed_mid_exchange` confirmado en
el proxy). Si se quiere más historia, el camino que ya funcionó una vez
(HistData.com, descarga manual del usuario) es la vía disponible — se
continúa por ahora con lo que ya está subido.

### Resultados — TSMOM, momentum transversal, pairs trading, FOMC multi-activo

**1. TSMOM (`research/estrategia_tsmom.py`)** — cartera mensual
rebalanceada, vol-targeting 10% anualizado por activo, los 3 lookbacks
siempre reportados (no se elige el mejor a posteriori):

| Lookback | Meses | Ret. anualizado | Sharpe | Max DD | Control z |
|---|---|---|---|---|---|
| 1 mes | 138 | +0,57% | 0,106 | 26,5% | +0,43 |
| 3 meses | 137 | +1,86% | 0,225 | 25,5% | +0,80 |
| 12 meses | 129 | -0,51% | 0,011 | 33,1% | +0,11 |

Ninguno significativo frente al control de signo aleatorio, Sharpe muy
por debajo del ≈1,17 del estudio de referencia, año a año muy
inconsistente. USTEC/US500 a 12m salieron 100% largos (ningún mes con
señal corta) — la misma degeneración de la candidata ya cerrada, pero
esta vez AISLADA a esos 2 activos, no a todo el universo: los 6 pares
Forex sí mostraron señales cortas (29%-74% largos según activo), lo
que confirma que el universo diversificado resolvió el problema de
variación de señal — simplemente no hay ventaja detectable con lo que
tenemos. **Descartada.**

**2. Momentum transversal (`research/estrategia_momentum_transversal.py`)**
— hallazgo importante, declarado con todo el detalle porque inicialmente
parecía prometedor y una comprobación adicional lo desmontó:

| Lookback (9 activos) | Meses | Ret. anualizado | Sharpe | Max DD | Control z |
|---|---|---|---|---|---|
| 1 mes | 45 | +3,33% | 0,448 | 5,4% | +1,63 |
| 3 meses | 43 | +0,41% | 0,092 | 10,5% | +0,46 |
| 12 meses | 34 | **+8,35%** | **1,175** | **5,4%** | **+2,93** |

El resultado a 12 meses parecía la mejor señal de todo el proyecto
hasta ahora. **Comprobación de concentración (hecha ANTES de aceptar
el resultado, no después):** la pata larga fue XAUUSD/US500/USTEC en
el 85-97% de los 34 meses, y la pata corta fue siempre alguna
combinación de los 6 pares Forex — USTEC y US500 estuvieron en el
MISMO lado el 88% de los meses. Esto no es momentum transversal
rotando entre activos: es una apuesta prácticamente estática a "renta
variable EEUU + oro" vs. "cesta de Forex", exactamente el patrón de
"beta disfrazada de señal" ya detectado antes en este proyecto
(Hipótesis F del ciclo diario). **Prueba de corrección:** repetir el
mismo mecanismo SOLO dentro de los 6 pares Forex (sin XAUUSD/USTEC/
US500) — resultado NEGATIVO en los 3 lookbacks (Sharpe -0,04 / -0,35 /
-0,77, z hasta -1,62 a 12m). Confirma que la señal "prometedora" era un
artefacto de concentración, no momentum transversal real. **Descartada
por completo** (incluida la versión de 9 activos, que no se declara
"prometedora" a pesar del Sharpe/z atractivos).

**3. Pairs Trading con cointegración (`research/estrategia_pairs_trading_coint.py`)**
— selección de par hecha ANTES de programar ninguna regla, con test de
Engle-Granger explícito sobre 7 candidatos con relación económica real:

| Par | Correlación retornos | p-valor cointegración |
|---|---|---|
| USTEC-US500 | +0,933 | **0,0081** |
| GBPUSD-USDCHF | -0,655 | **0,0036** |
| EURUSD-USDCHF | -0,790 | 0,0483 (límite) |
| USDCHF-USDSEK | +0,680 | 0,0445 (límite) |
| EURUSD-GBPUSD | +0,806 | 0,1960 (NO cointegrado a pesar de la alta correlación) |
| USDCAD-USDCHF | +0,509 | 0,2890 (no cointegrado) |
| XAUUSD-USDCHF | -0,398 | 0,4168 (no cointegrado) |

Nota metodológica relevante: EURUSD-GBPUSD tiene la segunda correlación
más alta de la tabla pero NO está cointegrado — confirma que
correlación y cointegración son conceptos distintos, no intercambiables.

Se operan los 2 pares con cointegración fuerte (beta por regresión
OLS móvil de 120 días, entrada en |z|>2, salida en reversión a 0,
stop en |z|>3,5, cierre forzoso a 40 días — mecanismo fijo, sin
optimizar):
- **USTEC-US500** (el mismo par cerrado antes, ahora con cointegración
  verificada formalmente — mejora metodológica real, no repetición
  cosmética): n=11 operaciones en 3,75 años — muestra insuficiente
  para cualquier conclusión, y aun así negativa (Media=-0,30%, PF=0,722,
  9 de 11 operaciones terminan en cierre por plazo, no por reversión
  real del spread).
- **GBPUSD-USDCHF**: n=19, Media=+0,073%, PF=1,124 — débil, y 3 de los
  4 años son negativos (el resultado agregado depende casi por
  completo de 2025).

**Descartada por ahora** — no por falta de fundamento (la
cointegración es real y verificada), sino porque 3,75 años solo
produce 11-19 operaciones por par, muy por debajo de lo necesario para
confirmar o descartar con confianza.

**4. FOMC drift multi-activo (`research/hipotesis_fomc_drift_multiactivo.py`)**
— mismo calendario FOMC ya verificado, extendido en barra diaria a los
9 activos (nunca probado en Forex): de 18 comparaciones (9 activos × 2
horizontes), solo USDJPY destaca (z=-2,35 el día del FOMC, z=-2,85 al
día siguiente) — con ~18 pruebas simultáneas, encontrar 1 celda así por
puro azar es esperable (no sorprendente), y el tamaño de muestra (n=30
fechas FOMC) es pequeño. **No se construye estrategia** — señal
aislada, no accionable dado el contexto de comparaciones múltiples.

### Diagnóstico y obstáculo real identificado

A diferencia del ciclo intradía (donde el problema parecía ser el
fenómeno + la eficiencia del mercado), aquí el patrón es distinto:
**el obstáculo dominante es el TAMAÑO DE MUESTRA**, no necesariamente
la ausencia de ventaja. TSMOM, momentum transversal y pairs trading
son todas familias que necesitan MUCHOS regímenes/ciclos para
expresarse (el estudio de TSMOM usa 44 años; el de trend-following de
largo plazo, 136 años) — con 3,75 años para 8 de los 9 activos, el
número de observaciones verdaderamente independientes es de apenas
unas pocas decenas en el mejor caso (34 meses en momentum transversal
a 12m, 11-19 operaciones en pairs trading). Ningún resultado de esta
sección debe leerse como "la estrategia no funciona" en sentido
absoluto — la conclusión honesta es "no se puede confirmar ni
descartar con la potencia estadística disponible".

**Esto es un bloqueo real de datos, no de metodología ni de
fundamento.** La vía ya disponible y gratuita (usada con éxito para
XAUUSD 2015-2022) es que el usuario repita el proceso de HistData.com
para los 6 pares Forex (y materias primas adicionales si se quiere
ampliar el universo) — HistData ofrece gratis M1 de la mayoría de
pares FX mayores desde los 2000s. Esto multiplicaría por 3-4 el tramo
evaluable y permitiría una potencia estadística razonable para TSMOM/
momentum transversal/pairs trading. Se continúa investigando otras
líneas mientras se decide esto (no se bloquea el proyecto completo por
este punto).

**Sesgo de selección acumulado actualizado:** ~40 hipótesis del
proyecto + 6 de esta fase (TSMOM×3 lookbacks tratados como 1 familia,
momentum transversal×3, pairs trading×2 pares, FOMC multi-activo) ≈
**46-50 hipótesis/combinaciones probadas en total.**

Código de esta sección: `research/datos_multiactivo.py`,
`research/estrategia_tsmom.py`,
`research/estrategia_momentum_transversal.py`,
`research/estrategia_pairs_trading_coint.py`,
`research/hipotesis_fomc_drift_multiactivo.py`.

### Comprobación pedida: momentum transversal frente a una cartera ESTÁTICA equivalente

El usuario pidió explícitamente no descartar momentum transversal solo
por su concentración persistente, y comparar contra una referencia
OBJETIVA (pesos no ajustados para favorecer ni perjudicar el
resultado) con exposición/volatilidad/coste comparables. Referencia
fijada ANTES de calcular nada: pierna larga ESTÁTICA (nunca cambia) =
XAUUSD+US500+USTEC equiponderados por riesgo; pierna corta ESTÁTICA =
los 6 pares Forex equiponderados por riesgo (los 6, no un subconjunto
elegido — evita cualquier decisión arbitraria); mismo vol-targeting
10%, mismo split 50/50, mismo coste de spread mensual que momentum
transversal (`research/momentum_transversal_vs_benchmark.py`).

| Lookback | Sharpe MOMENTUM | Sharpe ESTÁTICA | Excedente medio/mes | IC95% del excedente |
|---|---|---|---|---|
| 1 mes | 0,728 | **1,409** | -0,075% | [-0,70%, +0,56%] (no significativo) |
| 3 meses | 0,092 | **1,409** | -0,527% | [-1,21%, +0,07%] (no significativo) |
| 12 meses | 1,175 | **1,477** | +0,161% | [-0,14%, +0,50%] (no significativo) |

**Resultado inequívoco: la cartera ESTÁTICA (sin ninguna señal, sin
rotación) bate a momentum transversal en Sharpe en los 3 horizontes**,
con menor volatilidad y menor drawdown (2,5-3,6% vs. 5,4-10,5%). El
excedente de rotar por momentum sobre simplemente mantener esa
exposición fija NO es significativamente distinto de cero en ningún
caso. Esto confirma, de forma rigurosa y cuantificada (no solo por la
concentración observada), que momentum transversal no aporta ventaja
algorítmica alguna sobre la referencia objetiva — toda la rentabilidad
venía de la exposición direccional, no de la rotación. **Cerrada
definitivamente.**

**Aclaración importante para no confundir el diagnóstico con un nuevo
hallazgo:** la cartera ESTÁTICA en sí (Sharpe 1,4-1,5) NO se presenta
como candidata — no tiene señal, es simplemente "haber estado largo
oro+índices EEUU y corto una cesta de Forex" durante exactamente los
~3 años en que esa combinación concreta funcionó bien. Es el mismo
patrón de beta direccional ya identificado (Hipótesis F del ciclo
diario) usado aquí únicamente como vara de medir, no como estrategia.

### Limitación declarada: selección de pares en pairs trading usó todo el período

El usuario pidió comprobar si el test de cointegración usó información
futura. Respuesta honesta: **sí, parcialmente.** El test de
Engle-Granger (`research/estrategia_pairs_trading_coint.py`) se
calculó sobre TODO el histórico disponible de cada par (2023-2026, o
2015-2026 para los que incluyen XAUUSD) para DECIDIR qué pares
cointegran antes de construir ninguna regla. Esto es distinto de usar
información futura DENTRO del backtest de trading (el hedge ratio/z-
score de cada operación sí se calcula de forma causal, solo con datos
pasados hasta ese día) — pero la SELECCIÓN del par en sí se apoyó en
una ventana que incluye el mismo período luego usado para simular las
operaciones. Un trader real, en tiempo real, no habría sabido en 2023
que USTEC-US500 cointegraría con p=0,0081 hasta ver todo 2023-2026.

**Consecuencia declarada, no oculta:** los resultados de pairs trading
presentados (n=11 y n=19, ya débiles/negativos) tienen ADEMÁS este
sesgo de selección de par no resuelto — no se trata como una
simulación libre de sesgo retrospectivo. Cuando se disponga de más
histórico (ver sección siguiente), la forma correcta de repetir esto
es: dividir la muestra en un tramo de SELECCIÓN de pares (ej.
2015-2020) y un tramo de SIMULACIÓN de trading completamente separado
(2021 en adelante, nunca usado para decidir qué pares cointegran). No
se repite ahora (no hace falta, según lo pedido) — se deja anotado
para cuando haya más datos.

### Continuación autónoma (restringida a XAUUSD/USTEC/US500, según lo pedido)

**Estacionalidad de oro por demanda física india (Diwali/temporada de
bodas):** considerada y RECHAZADA en la etapa de literatura, no de
backtest — la búsqueda solo encontró reportajes/informes del World
Gold Council y prensa especializada, no estudios académicos revisados
por pares, y los propios informes del WGC describen el efecto como
dependiente del precio e inconsistente. No se cumple el estándar de
evidencia pedido ("preferiblemente estudios académicos... no inventes
referencias") — se descarta sin programar nada.

**NFP Drift** (`research/hipotesis_nfp_drift.py`) — familia macro
distinta de FOMC/Turno de Mes, con fundamento académico real
(Andersen, Bollerslev, Diebold & Vega documentan NFP como uno de los
anuncios de mayor impacto medido en mercados globales). Calendario:
primer viernes de cada mes, 2015-2026 (144 fechas; limitación menor
declarada: no se corrigen a mano los pocos meses donde el informe real
se retrasó una semana por festivo de Año Nuevo). Resultado, barra
diaria, en los 3 mercados permitidos:

| Activo | n | Día NFP (z) | NFP+1d (z) |
|---|---|---|---|
| XAUUSD | 137 | +0,68 | +1,06 |
| USTEC | 43 | +0,47 | +0,92 |
| US500 | 43 | +0,48 | +0,55 |

Ninguna celda se acerca a |z|=2 — señal plana. **Descartada.**

### Preparado: ampliación gratuita del histórico Forex (HistData)

Para los 6 pares ya integrados en el universo (EURUSD, GBPUSD, USDJPY,
USDCAD, USDCHF, USDSEK), descargar en
histdata.com/download-free-forex-historical-data/?/metatrader/1-minute-bar-quotes,
formato **"MetaTrader 4/5 Historical M1 Bar Data"**, años **2015 a
2022** (8 descargas por par = 48 .zip — mismo rango que ya se hizo
para XAUUSD, para igualar la ventana 2015-2026 en todo el universo).
Verificado directamente en la página: los 6 pares están disponibles
gratis en ese formato (EURUSD/GBPUSD/USDJPY/USDCHF desde 2000, USDCAD
desde 2000, USDSEK desde 2008 — todos cubren 2015-2022 sin problema).

Descomprimir TODOS los .zip en una sola carpeta (no importa el orden
ni si quedan en subcarpetas) y ejecutar UNA VEZ:
```
pip install pandas
python3 research/convertir_histdata_m1_multisimbolo.py carpeta_con_todos_los_csv carpeta_salida
```
El script busca recursivamente, agrupa por símbolo automáticamente y
escribe un único CSV por par con los 8 años ya concatenados — no hace
falta procesar año a año ni símbolo a símbolo. Probado en esta sesión
reprocesando los ficheros XAUUSD ya existentes (resultado idéntico al
obtenido manualmente, 189.034 velas). Subir aquí los 6 ficheros de
salida para integrarlos en `research/datos_multiactivo.py`.

**Decisión del usuario: NO se descarga esta extensión por ahora.** El
conversor queda preparado y probado, pero no se solicita de nuevo ni
se bloquea ninguna investigación en su espera. Se continúa con
XAUUSD/USTEC/US500/Forex (históricos actuales) según lo pedido.

## Comprobación pedida: ¿la unión HistData+MetaQuotes-Demo en XAUUSD genera señales artificiales?

El usuario pidió explícitamente comprobar esto antes de seguir
investigando con la serie combinada 2015-2026. Resultado: **la propia
fecha de unión (30-dic-2022 → 3-ene-2023) está limpia** — el hueco de
precio es un fin de semana de Año Nuevo normal (~0,2%), la columna
Spread pasa limpiamente de 100% NaN (HistData, no tiene este dato) a
100% con valor real (MetaQuotes) sin mezclarse, y no hay ningún salto
anómalo de ATR justo en el punto de corte.

**Pero se encontró un artefacto estructural real, no puntual, que SÍ
merecía corregirse antes de seguir:** HistData (EST sin DST) agrega
por día de calendario EST, lo que produce una vela "domingo" propia
cada semana — la breve reapertura del domingo por la tarde, con rango
medio ~8,9 puntos frente a ~17-20 de un día completo (verificado
directamente, no estimado). MetaQuotes-Demo (EET/EEST) NO genera esa
vela: la misma sesión de reapertura queda dentro de la vela del lunes.
Resultado antes de corregir: el tramo 2015-2022 tenía 6 "días"/semana
(5 completos + 1 domingo parcial) y el tramo 2023-2026 tenía 5
completos — un sesgo estructural, no aleatorio, que arrastraba el
ATR14 hacia abajo de forma distinta en cada tramo (la vela domingo, de
rango bajo, entra en la media móvil junto a las demás).

**Corrección aplicada** (`datos_multiactivo.fusionar_domingo_en_lunes`,
antes de cualquier hipótesis nueva de esta sesión): cada vela domingo
(cuando existe) se fusiona dentro de la vela lunes siguiente
(Open=domingo, High/Low=combinado, Close=lunes) — mismo criterio que
ya aplica MetaQuotes-Demo, no se inventa nada nuevo, se iguala el
criterio de agregación entre proveedores. Verificado tras la
corrección: distribución de día de semana uniforme (solo lunes-viernes)
en TODO el periodo 2015-2026, y el rango medio del lunes pasa a estar
en línea con el resto de días (19,57 vs. 18,4-19,8), ya no
artificialmente bajo.

**Alcance de la corrección:** aplica a `research/datos_multiactivo.py`
(usado por TSMOM, momentum transversal, pairs trading, FOMC/NFP
multi-activo, y toda la investigación nueva a partir de aquí). Las
hipótesis del ciclo de regímenes (A-G, ya cerradas) usaron el pipeline
anterior `research/datos_ciclo2.py`, que NO tiene esta corrección —
no se re-ejecutan (ya estaban claramente descartadas, y el efecto es
de segundo orden sobre un ATR ya usado solo como filtro de régimen, no
como señal principal), pero se declara la diferencia en vez de
ocultarla.

## Continuación autónoma (prioridad XAUUSD, USTEC/US500/Forex cuando se justifique)

**1. USD-basket → Oro (lead-lag), familia intermarket nueva**
(`research/hipotesis_usd_basket_gold.py`) — cesta orientada de los 6
pares Forex (2023-2026, Forex como secundario según lo pedido).
Fase 1: correlación contemporánea USD-oro = -0,457 (control de sanity,
signo esperado), pero correlación USD HOY → oro MAÑANA = **+0,032**
(prácticamente nula, y de signo "equivocado") — igual de débil que la
autocorrelación propia del oro (-0,014, control). La relación inversa
oro-dólar ya está descontada el mismo día, sin retraso explotable.
Backtest completo (n=256) confirma: Media R=+0,008 a coste cero
(z=+0,13, no significativo), negativo con cualquier estrés de coste,
muy inconsistente año a año. **Descartada.**

**2. CPI Release Drift** (`research/hipotesis_cpi_drift.py` +
`research/estrategia_cpi_drift.py`) — calendario de publicaciones del
IPC verificado fecha a fecha contra bls.gov/schedule/&lt;año&gt;/home.htm
(no una regla genérica como NFP) — 44 fechas 2023-2026, incluyendo la
alteración real del calendario por el cierre de la Administración de
2025 (sin IPC de referencia octubre-2025, declarado, no omitido).

Resultado con coste (largo incondicional al Open del día de IPC,
SL=1,5×ATR14, cierre al Close del día siguiente):

| Activo | n | Media R | PF | Año peor | Año mejor |
|---|---|---|---|---|---|
| XAUUSD | 44 | +0,207 | 2,143 | 2026: -0,13 | 2023: +0,44 |
| USTEC | 43 | +0,269 | 2,896 | 2026: +0,03 | 2023: +0,49 |
| US500 | 43 | +0,238 | 2,675 | 2026: +0,08 | 2023: +0,41 |

A primera vista parece el mejor resultado del proyecto — pero antes de
tratarlo como algo prometedor se hizo la comprobación decisiva (el
mismo tipo de control de concentración que ya desmontó momentum
transversal): **¿este mecanismo exacto (largo + SL ajustado 1,5×ATR +
2 días) da resultados parecidos en días ALEATORIOS cualquiera, no solo
en días de IPC?** Respuesta: **sí, en gran parte.** Simulando el mismo
mecanismo en 43 días aleatorios (2000 repeticiones) sobre el mismo
periodo:

| Activo | Media R aleatoria (días cualquiera) | Percentil 95 aleatorio | Media R real en IPC |
|---|---|---|---|
| XAUUSD | +0,052 | +0,209 | +0,207 (dentro del percentil 95 — NO destaca) |
| USTEC | +0,075 | +0,225 | +0,269 (por ENCIMA del percentil 95) |
| US500 | +0,051 | +0,199 | +0,238 (por ENCIMA del percentil 95) |

**Conclusión honesta:** la mayor parte de lo que parecía un resultado
espectacular es simplemente el sesgo alcista general de 2023-2026
combinado con un riesgo (SL) estrecho que amplifica el R-múltiplo —
exactamente el mismo mecanismo de "beta disfrazada" ya detectado en
momentum transversal. Descontando esa base, SÍ queda un efecto
incremental real pero MODESTO en USTEC/US500 (por encima del percentil
95 aleatorio, no un caso extremo) — no en XAUUSD, que queda dentro del
rango aleatorio. Además: la tendencia por año es decreciente en los 3
mercados (2023 claramente el mejor, 2026 plano o negativo) — compatible
con que el efecto se esté arbitrando, o con que gran parte de la señal
original dependiera del episodio concreto de desinflación de 2023, no
de una ventaja estructural estable.

**Decisión: NO se congela como candidata.** No cumple el estándar
pedido ("ventaja que no dependa exclusivamente de unas pocas
operaciones... consistencia suficiente") — depende sustancialmente de
la deriva alcista genérica del período, el efecto incremental real es
modesto, y la tendencia es decreciente. Es el hallazgo menos negativo
de todo este proyecto hasta ahora, pero no alcanza el nivel de
evidencia necesario. Se documenta en detalle por si una muestra más
larga (cuando se amplíe el histórico) permite revisarlo con más
potencia — no se descarta el fundamento económico (el IPC sí mueve
mercados), se descarta la implementación actual con la evidencia
disponible.

**Sesgo de selección acumulado:** ~50 hipótesis previas + 3 de esta
ronda (USD-basket, CPI drift Fase 1, CPI drift con coste) ≈ **53
hipótesis/combinaciones probadas en total.**

**3. Halloween Effect / "Sell in May and Go Away"** (`research/hipotesis_halloween.py`)
— efecto estacional con evidencia académica revisada por pares real
(Bouman & Jacobsen 2002, *American Economic Review* 92(5):1618-1635,
37 países 1970-1998, efecto en 36/37; extensión Jacobsen & Zhang, 108
mercados, +4,52pp invierno vs. verano, t=9,69). Declarado: el
fundamento es más sólido para renta variable que para oro — se prueba
en los 3 mercados permitidos, sin fingir igual solidez. Regla más
simple posible (sin SL, lección aplicada de CPI Drift: un marco de
R-múltiplo con stop ajustado amplifica artificialmente resultados en
mantenimientos largos): largo Nov-Abr, sin posición May-Oct.

| Activo | Pares | Media invierno | Media verano | Diferencia | IC95% |
|---|---|---|---|---|---|
| XAUUSD | 11 | +9,60% | +4,19% | +5,40% | [-1,92%, +13,58%] (no significativo) |
| USTEC | 3 | +8,58% | +18,79% | -10,21% | [-24,95%, +12,32%] (no significativo) |
| US500 | 3 | +7,33% | +12,60% | -5,27% | [-18,53%, +19,69%] (no significativo) |

XAUUSD muestra la DIRECCIÓN documentada en la literatura (9/11
inviernos positivos, invierno > verano en promedio) pero sin
significancia (n=11, IC amplio que incluye cero). USTEC/US500 muestran
el signo contrario, pero con n=3 no es informativo (verano 2024-2025
fue excepcionalmente fuerte para los índices, no hay base para
generalizar). **Descartada por potencia insuficiente**, no por
ausencia de fundamento — es, con diferencia, la familia con mejor
respaldo académico probada hasta ahora, simplemente no hay suficientes
años en los datos disponibles para confirmarla.

**4. Autocorrelación semanal (lag-1)** (`research/hipotesis_autocorrelacion_semanal.py`)
— frecuencia nueva en el proyecto (nunca se había probado la barra
semanal), con fundamento en la literatura de autocorrelación a
distintos horizontes (Lo & MacKinlay 1990, *RFS*, "When Are Contrarian
Profits Due to Stock Market Overreaction?").

| Activo | n semanas | Corr(lag-1) | IC95% | 1ª mitad | 2ª mitad |
|---|---|---|---|---|---|
| XAUUSD | 613 | +0,0025 | [-0,093, +0,085] | -0,008 | +0,009 |
| USTEC | 189 | -0,0802 | [-0,228, +0,068] | -0,050 | -0,104 |
| US500 | 189 | -0,1017 | [-0,236, +0,052] | -0,080 | -0,116 |

XAUUSD esencialmente sin autocorrelación. USTEC/US500 muestran
reversión semanal débil pero **consistente en ambas mitades de la
muestra** (se vuelve más negativa, no desaparece) — dirección acorde
con la reversión de corto plazo documentada en índices, pero el IC
sigue incluyendo cero con n=189. **No se construye estrategia** — sin
significancia no se justifica el siguiente paso, pero se anota como
dirección a revisar si se amplía el histórico de índices.

**Sesgo de selección acumulado actualizado:** ≈53 + 2 = **55
hipótesis/combinaciones probadas en total en este proyecto.**

**5. FOMC Cycle Effect** (`research/hipotesis_ciclo_fomc.py`) — DISTINTA
del Pre/Post-FOMC Drift ya probado (aquel mide el día del anuncio; este
mide la posición dentro del ciclo de 6-8 semanas entre reuniones).
Evidencia académica real: Cieslak, Morse & Vissing-Jorgensen (2019),
*Journal of Finance* 74(5):2201-2248 — desde 1994, la prima de riesgo
de renta variable se concentra en semanas PARES del ciclo FOMC.

| Activo | n par | Media par | n impar | Media impar | Diferencia | IC95% |
|---|---|---|---|---|---|---|
| XAUUSD | 509 | +0,035%/día | 444 | +0,152%/día | -0,117%/día | [-0,268%, +0,042%] |
| USTEC | 492 | +0,102%/día | 426 | +0,118%/día | -0,016%/día | [-0,190%, +0,135%] |
| US500 | 492 | +0,066%/día | 427 | +0,086%/día | -0,020%/día | [-0,147%, +0,093%] |

No significativo en ningún activo. Además, el signo observado va en
la dirección CONTRARIA a la documentada (semanas impares ligeramente
mejores que pares en nuestra muestra) — no se interpreta como una
contradicción del estudio original (no es significativo, la muestra
2023-2026 es corta y post-2019, fuera del periodo estudiado), solo
como que no se replica aquí. **Descartada.**

### Balance de esta ronda de continuación autónoma

Se ha cubierto un conjunto amplio de familias con evidencia académica
real: TSMOM, trend-following de largo plazo, momentum transversal,
pairs trading/cointegración, FOMC drift (día del anuncio), FOMC Cycle
(posición en el ciclo), NFP drift, CPI drift, USD-basket→oro (lead-lag),
Halloween Effect, autocorrelación semanal. Ninguna alcanza el nivel de
evidencia necesario para forward testing. La más cercana (CPI Drift en
USTEC/US500) tiene un efecto incremental real pero modesto y
decreciente, no una ventaja robusta.

**Diagnóstico honesto sobre qué bloquea seguir con familias
NUEVAS fundamentadas:** las familias con mejor evidencia académica que
quedan sin probar (FX carry trade, prima de riesgo de volatilidad,
factores clásicos de renta variable como value/quality/low-vol,
posicionamiento COT) requieren datos que no están disponibles en este
entorno — tipos de interés/swap, opciones/VIX, universo amplio de
acciones individuales, o informes de posicionamiento — y el acceso a
internet de esta sesión está bloqueado para fuentes gratuitas
alternativas (confirmado dos veces de forma independiente: Dukascopy y
stooq.com, ambos con conexión rechazada desde el datacenter). Esto es
un bloqueo real de datos/herramientas, no una decisión de parar. **Sesgo
de selección acumulado: ≈56 hipótesis/combinaciones probadas en total
en este proyecto.**

## Bloqueo de datos RESUELTO — fuentes oficiales gratuitas encontradas

A petición del usuario, se buscaron fuentes alternativas a Dukascopy/
stooq.com antes de abandonar las 4 familias pospuestas. Resultado:
**las 4 están desbloqueadas**, todas desde fuentes oficiales/
académicas, verificadas accesibles directamente desde esta sesión
(a diferencia de los proveedores comerciales de datos de mercado, que
sí están bloqueados):

| Dato necesario | Fuente | Verificado |
|---|---|---|
| Tipos de interés (carry trade) | FRED (Reserva Federal de San Luis), `fredgraph.csv?id=<serie>`, sin API key | USD/EUR/GBP/JPY/CAD/CHF/SEK, 2015-2026 completo |
| Posicionamiento COT | cftc.gov/files/dea/history/ (oficial, sin registro) | Oro, EUR, GBP, JPY, CAD, CHF, Nasdaq-100, S&P 500, 2015-2026 (614 semanas) — **SEK no tiene futuro en CME con informe COT, limitación real declarada, no inventada** |
| VIX | cdn.cboe.com (CBOE oficial) | Histórico diario 1990-2026 |
| Factores de renta variable | Kenneth French Data Library (Dartmouth) — confirmado accesible, no usado todavía (nuestro universo es de índices, no de cesta amplia de acciones individuales; ver nota más abajo) | — |

Scripts: `research/descargar_fred_tipos.py`, `research/descargar_cftc_cot.py`.
Datos guardados en `research/datos_externos/` (filtrados a lo
necesario, no el volcado completo de la CFTC — ~20MB/año/informe
reducidos a unos pocos KB por mercado relevante).

### 1. FX Carry Trade (`research/estrategia_carry_trade.py`)

Mismo mecanismo que TSMOM (vol-targeting 10%, rebalanceo mensual) pero
con signo = diferencial de tipos de interés real en vez de momentum de
precio. Resultado: **Sharpe=-0,059, no significativo (z=+0,08)**,
drawdown 13%, inconsistente año a año (2023:-4,8%, 2024:+7,8%,
2025:-9,4%, 2026:+4,3%). Nota honesta: 5 de los 6 pares mantuvieron el
mismo signo casi todo el período (el diferencial de tipos cambia
lento, es esperable, no es un error) — el "carry" en esta ventana
concreta fue mayormente una apuesta estática que no funcionó, consistente
con el riesgo de "crash" del carry trade documentado en la literatura
(Doskov & Swinkels: Sharpe 0,2-0,4 a 112 años vs. episodios muy
distintos por período). **Descartada.**

### 2. COT Positioning Contrarian (`research/estrategia_cot_contrarian.py`)

Fade de posicionamiento especulativo extremo (percentil >90/<10 de su
propio historial, con el retraso real de publicación del informe
respetado: dato del martes, operable desde el lunes siguiente).
Primera versión (percentil del neto especulativo en bruto): resultado
agregado parecía significativo (Sharpe=0,958, z=+2,40) — pero
descomponiendo por activo, USTEC/US500 estaban **permanentemente
largos** (98-100% de las semanas), la misma "beta disfrazada" de
siempre. Corrección aplicada (práctica estándar del "COT Index": normalizar
el neto por el interés abierto antes del percentil, no es un ajuste
inventado para rescatar el resultado) — **el problema persistió**
igual en los índices incluso normalizado, indicando que es una
característica estructural real del posicionamiento en futuros de
índice en este período (no un error de cálculo), no algo a corregir
más. Excluyendo USTEC/US500 (donde la señal SÍ varía de forma genuina):
oro+Forex solos dan **Sharpe=-0,22 a -0,28, no significativo (z=-0,05
a -0,18)** en ambas versiones. **Descartada.**

### 3. VIX Spike Mean Reversion (`research/estrategia_vix_reversion.py`)

Comprar tras picos de variación diaria del VIX >percentil 90 (propio
historial causal de 252 días), aplicable a USTEC/US500 (VIX = volatilidad
implícita del S&P 500). USTEC mostraba Media R=+0,1835, PF=1,441,
robusto al estrés de coste, z=+1,71 (no bastante para significancia).
**Comprobación decisiva (mismo control que desmontó CPI Drift):**
el mismo mecanismo (largo + SL 1,5×ATR + hasta 5 días) en 101 días
ALEATORIOS cualquiera da una media de +0,194 — **más alto** que el
resultado real de +0,1835. El resultado del pico de VIX cae en el
percentil 45 de la distribución aleatoria: indistinguible del azar, no
aporta nada sobre el sesgo alcista genérico. US500 ya era plano de
partida (Media R=+0,0003). **Descartada — la más claramente debunked
de las tres.**

### Nota sobre factores de renta variable (Fama-French)

Kenneth French Data Library confirmada accesible, pero NO se ha usado
todavía: los factores clásicos (value/size/quality) se construyen
sobre una cesta amplia de ACCIONES INDIVIDUALES ordenadas por
características — nuestro universo son ÍNDICES (USTEC/US500), no
acciones sueltas, así que una estrategia de factores clásica no es
directamente aplicable sin un universo de acciones que no tenemos.
Queda como vía a explorar si se decide incorporar acciones
individuales al proyecto (fuera del alcance actual, no se fuerza).

**Sesgo de selección acumulado actualizado:** ≈56 + 3 = **59
hipótesis/combinaciones probadas en total.** Ninguna de las 3 familias
recién desbloqueadas sobrevivió — pero la limitación de datos que las
pospuso YA NO EXISTE, y las 3 fueron probadas con el mismo rigor
(controles de concentración, benchmarks aleatorios, costes) que
desmontó los falsos positivos anteriores del proyecto.

### 4. Oro vs. Tipos de Interés Reales (TIPS) (`research/hipotesis_oro_tipos_reales.py`)

Añadida tras desbloquear FRED: el oro no paga cupón, su coste de
oportunidad es el tipo de interés REAL (Erb & Harvey 2013, "The Golden
Dilemma", *Financial Analysts Journal* 69(4):10-42) — distinta del
USD-basket (divisa nominal) y del Carry Trade (diferencial nominal)
ya probados. Serie: DFII10 (TIPS 10 años, FRED), 2015-2026 completo.

Fase 1: correlación contemporánea -0,335 (signo correcto, esperado);
correlación variación HOY → oro MAÑANA = **-0,046** (signo correcto,
a diferencia del USD-basket, pero muy débil). Backtest completo
(n=891, todo el histórico XAUUSD): Media R=+0,032 a coste cero, ya
plano con 1$ de estrés (PF=0,999) y negativo con 3$ (PF=0,856);
z=+1,01 no significativo; muy inconsistente año a año (2024:-0,25,
2025:-0,12, pero 2016/2020/2026 positivos). **Descartada** — dirección
económica correcta, pero sin magnitud suficiente para sobrevivir a
costes reales.

**Sesgo de selección acumulado actualizado:** ≈59 + 1 = **60
hipótesis/combinaciones probadas en total en este proyecto.**

### Balance de esta fase: bloqueo resuelto, 4 familias nuevas probadas, ninguna sobrevive

El bloqueo de datos quedó resuelto (FRED, CFTC, CBOE, todos oficiales
y gratuitos, accesibles desde esta sesión). Se probaron las 3
familias pendientes (carry, COT, VIX) más una nueva que surgió de
tener acceso a FRED (tipos reales) — las 4 con el mismo nivel de
rigor que todo el proyecto: viabilidad previa, reglas pre-registradas,
costes reales con estrés, controles aleatorios, y en 3 de los 4 casos
una comprobación de concentración/benchmark que reveló que un
resultado aparentemente positivo era beta disfrazada o ruido
indistinguible del azar. Ninguna sobrevive. El fundamento económico de
estas 4 familias sigue siendo sólido (no se está descartando la
teoría) — lo que se descarta es su implementación concreta sobre
estos instrumentos y este período con los datos disponibles.
