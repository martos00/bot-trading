# XAUUSD Supply/Demand + RSI Trendline Breakout EA

Expert Advisor para MetaTrader 5, diseñado para operar **XAUUSD (Oro)** en
temporalidad de 5 minutos (M5), pensado para superar y operar cuentas de
fondeo (prop firms).

Archivo principal: `MQL5/Experts/XAUUSD_SupplyDemand_RSI_EA.mq5`

## Instalación

1. Copia el archivo `.mq5` dentro de `MQL5/Experts/` de tu terminal MetaTrader 5
   (`Archivo -> Abrir carpeta de datos -> MQL5 -> Experts`).
2. Compílalo con MetaEditor (F7).
3. Arrástralo sobre un gráfico de **XAUUSD en temporalidad M5**.
4. Activa "Permitir trading algorítmico".

## Arquitectura del EA

1. **Contexto — Zonas de Oferta y Demanda Multi-Timeframe (MTF)**: replica
   "Supply and Demand Visible Range" de LuxAlgo, pero haciendo "zoom
   alejado" hacia una temporalidad macro configurable en
   `Temporalidad_Liquidez` (por defecto H1, también válido H4),
   independientemente de la temporalidad del gráfico donde corre el EA.
   Las zonas se recalculan cada vez que cierra una nueva vela de esa
   temporalidad macro, usando el máximo/mínimo de las últimas
   `g_zonaLookbackMacro` velas (100 por defecto) y el cierre de la vela
   extrema, para reflejar liquidez institucional real acumulada durante
   horas/días completos en vez de ruido de velas de 5 minutos.
2. **Gatillo — RSI Trendlines with Breakouts**: RSI de `g_rsiPeriod`
   períodos (14 por defecto) sobre cierre, calculado en la temporalidad
   de ejecución `InpTimeframe` (5M por defecto). El EA detecta picos y
   valles locales del RSI (pivotes),
   traza una línea de tendencia entre los dos últimos pivotes de cada
   tipo y valida una ruptura ("breakout") cuando el RSI cruza y cierra
   por encima/debajo de dicha línea. El cálculo detallado está
   comentado en español directamente en el código, dentro de
   `ActualizarRSITrendlinesYBreakouts()` y `BuscarUltimosDosPivotes()`.
3. **Entradas**: el gatillo del RSI en 5M sólo se evalúa cuando el precio
   actual ya entró en una zona macro (MTF): venta cuando el precio está
   dentro de la zona de Oferta macro y se produce un breakout bajista de
   la línea de picos del RSI; compra cuando el precio está dentro de la
   zona de Demanda macro y se produce un breakout alcista de la línea de
   valles. Opcionalmente, ambas pueden requerir pasar el **filtro de
   tendencia macro** (`InpUsarFiltroTendencia`, **desactivado por defecto**):
   sólo se permitirían ventas si el precio está por debajo de una media
   móvil larga (`InpTrendMAPeriod`, 200 por defecto) calculada en
   `Temporalidad_Liquidez`, y compras si está por encima. Se desactivó por
   defecto porque, junto a la zona MTF y el breakout de RSI, dejaba pasar
   muy pocas señales (sin forma de medir cuántas se descartaban en el
   backtest); actívalo (`InpUsarFiltroTendencia=true`) si quieres volver a
   exigirlo. Lógica en `FiltroTendenciaPermiteVenta()` /
   `FiltroTendenciaPermiteCompra()`.
4. **Gestión de riesgo institucional**:
   - Lotaje calculado dinámicamente para arriesgar `InpRiskPercent`
     (**1.5% por defecto**, subido desde 0.5% para aumentar la
     rentabilidad total del sistema) del balance en cada operación,
     usando la función nativa `OrderCalcProfit()` para preguntarle
     directamente al bróker cuál sería la pérdida real de 1 lote entre
     el precio de entrada y el Stop Loss, en vez de derivarla
     manualmente a partir de `SYMBOL_TRADE_TICK_VALUE`/
     `SYMBOL_TRADE_TICK_SIZE` (que en algunos brokers no reflejan el
     valor real por punto en XAUUSD y podían provocar lotajes varias
     veces más grandes de lo previsto). Lógica en `CalcularLotaje()`.
     A 1.5% de riesgo, 3 pérdidas seguidas ya rondan el 4.5% de
     pérdida diaria, por lo que el Kill Switch diario (ver abajo) puede
     activarse antes o al mismo tiempo que el circuito de pérdidas
     consecutivas (`InpMaxPerdidasConsecutivas`); ambos siguen actuando
     como redes de seguridad independientes, solo que ahora se solapan
     más. Si prefieres más margen entre ambos, baja `InpRiskPercent` o
     sube `InpMaxDailyLossPercent`.
   - Kill Switch diario (`InpMaxDailyLossPercent`, 4% por defecto):
     cierra todo y bloquea el EA hasta el cambio de día del servidor.
     El estado se persiste en variables globales de la terminal por si
     se reinicia MetaTrader durante el día. Lógica detallada comentada
     en `GestionarCambioDeDia()` y `ComprobarKillSwitchDiario()`.
   - Filtro de spread máximo (`InpMaxSpreadPips`).
   - Cierre obligatorio de posiciones los viernes a las 21:00 hora de
     Nueva York (`InpFridayCloseHourNY`), calculado aplicando el
     horario de verano de EE.UU.
   - **Circuito de pérdidas consecutivas** (`InpMaxPerdidasConsecutivas`,
     3 por defecto): complementa al Kill Switch del 4%. Cuenta las
     pérdidas seguidas del día (se reinicia en cuanto una operación cierra
     en positivo) y bloquea nuevas entradas en cuanto se alcanza el
     límite, mucho antes de agotar el presupuesto diario completo del 4%.
     Detecta el resultado de cada cierre en `OnTradeTransaction()`.
5. **Auto-Optimización Walk-Forward (Método 1)**: una vez por semana,
   en la primera vela de H1 tras el cierre de fin de semana, el EA mide
   el régimen de volatilidad del oro (ATR reciente vs. ATR medio, y
   desviación estándar del cierre) sobre las últimas
   `InpVelasAnalisisOptimizacion` velas de H1 (500 por defecto) y
   recalibra dinámicamente `g_zonaLookbackMacro` y `g_rsiPeriod`:
   valores más amplios (`InpZonaLookbackVolatilidadAlta` = 100,
   `InpRSIPeriodoVolatilidadAlta` = 21) si la volatilidad reciente supera
   la media histórica, o más ajustados (`InpZonaLookbackVolatilidadBaja`
   = 30, `InpRSIPeriodoVolatilidadBaja` = 10) si el mercado está lento.
   Esta recalibración **no afecta** al riesgo por operación, el Kill
   Switch diario, el filtro de spread ni el cierre de fin de semana, que
   permanecen totalmente independientes. Lógica comentada en detalle en
   `EjecutarOptimizacionSemanal()`. Se puede desactivar con
   `InpOptimizacionActiva = false`.

## Parámetros importantes a calibrar por bróker

- **`Temporalidad_Liquidez`**: temporalidad macro usada para las zonas
  de Oferta/Demanda (H1 por defecto; H4 es una alternativa válida para
  zonas aún más amplias). Cuanto mayor sea esta temporalidad, más
  "institucionales" y menos frecuentes serán las zonas detectadas.
- **`InpBrokerGMTOffsetHrs`**: offset (en horas) del servidor de tu
  bróker respecto a UTC. Varía entre brokers (GMT+0, +2, +3, etc.) y es
  necesario para calcular correctamente las 21:00 de Nueva York. Ajusta
  este valor según la especificación de tu bróker antes de operar en real.
- **`InpManualPipSize`**: por defecto el EA usa 0.10 como tamaño de "pip"
  para el oro (la convención de mercado, independientemente de cuántos
  decimales use tu bróker para cotizar XAUUSD). La heurística de pips por
  nº de decimales típica de Forex NO aplica al oro: con brokers que cotizan
  XAUUSD a 2 decimales daba un pip de 0.01, diez veces más pequeño de lo
  previsto, lo que colocaba el Stop Loss demasiado cerca del precio y
  provocaba que saltara en segundos o minutos en el backtest. Si tu bróker
  usa una convención de pip distinta para el oro, fija aquí manualmente el
  valor correcto.

## Advertencia

Antes de usarlo en una cuenta de fondeo real, realiza pruebas exhaustivas
en el Strategy Tester (modo "Cada tick basado en datos reales") y en
cuenta demo. Verifica que `InpBrokerGMTOffsetHrs` esté correctamente
calibrado para el cierre de fin de semana y que el símbolo `XAUUSD` de tu
bróker coincide con el usado en el gráfico donde se adjunta el EA.
