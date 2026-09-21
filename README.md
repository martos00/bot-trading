# XAUUSD Liquidity Sweep -> MSS -> FVG Retest EA

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
