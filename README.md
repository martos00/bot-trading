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

1. **Contexto — Zonas de Oferta y Demanda**: replica "Supply and Demand
   Visible Range" de LuxAlgo. Se recalculan en cada vela cerrada de M5,
   usando el máximo/mínimo de las últimas `InpZonaLookback` velas y el
   cierre de la vela extrema.
2. **Gatillo — RSI Trendlines with Breakouts**: RSI de 14 períodos sobre
   cierre. El EA detecta picos y valles locales del RSI (pivotes),
   traza una línea de tendencia entre los dos últimos pivotes de cada
   tipo y valida una ruptura ("breakout") cuando el RSI cruza y cierra
   por encima/debajo de dicha línea. El cálculo detallado está
   comentado en español directamente en el código, dentro de
   `ActualizarRSITrendlinesYBreakouts()` y `BuscarUltimosDosPivotes()`.
3. **Entradas**: venta cuando el precio está dentro de la zona de Oferta
   y se produce un breakout bajista de la línea de picos del RSI; compra
   cuando el precio está dentro de la zona de Demanda y se produce un
   breakout alcista de la línea de valles.
4. **Gestión de riesgo institucional**:
   - Lotaje calculado dinámicamente para arriesgar `InpRiskPercent`
     (0.5% por defecto) del balance en cada operación.
   - Kill Switch diario (`InpMaxDailyLossPercent`, 4% por defecto):
     cierra todo y bloquea el EA hasta el cambio de día del servidor.
     El estado se persiste en variables globales de la terminal por si
     se reinicia MetaTrader durante el día. Lógica detallada comentada
     en `GestionarCambioDeDia()` y `ComprobarKillSwitchDiario()`.
   - Filtro de spread máximo (`InpMaxSpreadPips`).
   - Cierre obligatorio de posiciones los viernes a las 21:00 hora de
     Nueva York (`InpFridayCloseHourNY`), calculado aplicando el
     horario de verano de EE.UU.

## Parámetros importantes a calibrar por bróker

- **`InpBrokerGMTOffsetHrs`**: offset (en horas) del servidor de tu
  bróker respecto a UTC. Varía entre brokers (GMT+0, +2, +3, etc.) y es
  necesario para calcular correctamente las 21:00 de Nueva York. Ajusta
  este valor según la especificación de tu bróker antes de operar en real.
- **`InpManualPipSize`**: por defecto el EA detecta automáticamente el
  tamaño de "pip" según los decimales del símbolo (10 puntos si tiene 3
  o 5 decimales, 1 punto si tiene 2 o 4). Si tu bróker cotiza XAUUSD de
  forma distinta, fija aquí manualmente el valor del pip.

## Advertencia

Antes de usarlo en una cuenta de fondeo real, realiza pruebas exhaustivas
en el Strategy Tester (modo "Cada tick basado en datos reales") y en
cuenta demo. Verifica que `InpBrokerGMTOffsetHrs` esté correctamente
calibrado para el cierre de fin de semana y que el símbolo `XAUUSD` de tu
bróker coincide con el usado en el gráfico donde se adjunta el EA.
