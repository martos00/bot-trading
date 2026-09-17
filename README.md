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
   valles. Ambas requieren además pasar el **filtro de zona fresca**
   (`InpUsarFiltroZonaFresca`, **activado por defecto**): una zona de
   Oferta/Demanda pierde fuerza institucional cada vez que el precio la
   revisita, así que sólo se permite operar durante la primera visita del
   precio a la zona; en cuanto el precio sale de ella tras haber entrado,
   la zona queda marcada como "puesta a prueba" (`tocada`) y no vuelve a
   generar señales hasta que se forme una zona nueva en el siguiente
   cierre de vela macro. Desactívalo (`InpUsarFiltroZonaFresca=false`) si
   prefieres operar también los retests de una misma zona. Lógica en
   `ActualizarEstadoDeZona()` / `MarcarZonasTocadas()`. Y el **filtro de
   tendencia macro** (`InpUsarFiltroTendencia`, **activado por defecto**): sólo se permiten
   ventas si el precio está por debajo de una media móvil larga
   (`InpTrendMAPeriod`, 200 por defecto) calculada en
   `Temporalidad_Liquidez`, y compras si está por encima. Desactívalo
   (`InpUsarFiltroTendencia=false`) si prefieres dejar pasar más señales a
   cambio de operar también contra la tendencia de fondo. Lógica en
   `FiltroTendenciaPermiteVenta()` / `FiltroTendenciaPermiteCompra()`.
4. **Breakeven automático** (`InpUsarBreakeven`, activado por defecto):
   en cuanto el precio se mueve a favor `InpBreakevenTriggerR` veces
   (**1.5 por defecto**) la distancia de riesgo original de la operación
   (entrada-SL), el EA mueve el Stop Loss al precio de entrada más un
   pequeño colchón (`InpBreakevenBufferPips`, 2 pips por defecto), de
   forma que la operación ya no puede cerrarse en pérdida aunque el
   precio revierta antes de llegar al Take Profit. Con `InpRiskRewardRatio`
   en 3.0 por defecto, un disparo demasiado pronto (p.ej. 1.0R) capa parte
   de las ganancias grandes: la operación llega a 1R, se protege a
   breakeven, el precio revierte y cierra en 0 en vez de seguir hasta el
   TP completo (+3R). Subirlo a 1.5R le da más recorrido a la operación
   antes de proteger, preservando más del upside del ratio 1:3 sin perder
   la protección contra reversiones fuertes. Lógica en
   `GestionarBreakeven()`.
5. **Cierre parcial en el TP original + trailing stop en el resto**
   (`InpUsarTrailingStop` y `InpUsarCierreParcial`, ambos activados por
   defecto): con un TP fijo en 1:3, cualquier tendencia que se moviera
   más allá de 3R cerraba igualmente en el TP, dejando sobre la mesa todo
   el recorrido adicional. En cuanto el precio se mueve a favor
   `InpCierreParcialTriggerR` veces (**3.0 por defecto, el mismo nivel
   que el TP original**) la distancia de riesgo, el EA:
   1. Cierra `InpCierreParcialPercent` % del volumen (**50% por
      defecto**) para asegurar la ganancia del ratio 1:3 original, igual
      que si hubiera cerrado en el TP fijo.
   2. Libera el TP fijo del volumen restante (lo quita) y empieza a
      arrastrar su Stop Loss a `InpTrailingDistanceR` (**1.0 por
      defecto**) de distancia por detrás del precio, siempre en la
      dirección favorable.
   Así, la mitad de la ganancia queda asegurada en el objetivo original y
   la otra mitad puede seguir corriendo mucho más allá de +3R en
   tendencias fuertes, sin aumentar el riesgo inicial de la operación. Si
   se desactiva `InpUsarCierreParcial`, el EA simplemente libera el TP
   del 100% del volumen en ese mismo nivel y deja correr toda la
   posición con trailing (comportamiento anterior). Se activa después del
   breakeven (`InpBreakevenTriggerR` en 1.5R) y sólo mejora el SL, nunca
   lo empeora. Lógica en `GestionarTrailingStop()`.
6. **Filtro de horario de sesión** (`InpUsarFiltroSesion`, activado por
   defecto): el oro se mueve con volumen y tendencias limpias durante el
   solapamiento Londres-Nueva York y la sesión de Nueva York; fuera de
   esa franja (sesión asiática, madrugada europea) el volumen es más bajo
   y las rupturas del RSI tienden a ser ruido. El EA sólo abre
   operaciones **nuevas** entre `InpSesionInicioHoraNY` y
   `InpSesionFinHoraNY` (**08:00–17:00 hora de Nueva York por defecto**);
   una posición ya abierta se sigue gestionando con normalidad
   (breakeven, trailing, Kill Switch, cierre de fin de semana) a
   cualquier hora, y el filtro no restringe el símbolo con el que se
   opera (el EA siempre opera únicamente XAUUSD), sólo la franja horaria
   dentro de ese único mercado. Lógica en `SesionPermiteOperar()`.
7. **Gestión de riesgo institucional**:
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
8. **Auto-Optimización Walk-Forward (Método 1)**: una vez por semana,
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
