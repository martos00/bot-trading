//+------------------------------------------------------------------+
//|                                   XAUUSD_RSI_Trendline_EA.mq5   |
//|   EA para XAUUSD basado en zonas de Oferta/Demanda (contexto)   |
//|   y rupturas de líneas de tendencia sobre el RSI (gatillo).     |
//|   Diseñado con blindaje de riesgo para cuentas de fondeo.       |
//|   Hipótesis 2: recuperada de la versión previa a Baseline 1,    |
//|   sin el módulo de auto-optimización semanal (parámetros fijos |
//|   para poder validar con el mismo protocolo train/val/OOS).    |
//+------------------------------------------------------------------+
#property copyright "Bot Trading"
#property version   "1.00"
#property strict

#include <Trade\Trade.mqh>

//======================================================================
// PARÁMETROS DE ENTRADA
//======================================================================

input group "=== Configuración General ==="
input ulong  InpMagicNumber         = 20260101;   // Número mágico
input ENUM_TIMEFRAMES InpTimeframe  = PERIOD_M5;   // Temporalidad de ejecución / gatillo RSI (5M)

input group "=== Indicador 1: Zonas de Oferta y Demanda (Multi-Timeframe) ==="
input ENUM_TIMEFRAMES Temporalidad_Liquidez = PERIOD_H1; // Temporalidad macro para zonas de liquidez (H1 o H4)
input int    InpZonaLookbackMacro   = 100;         // Velas analizadas (temporalidad macro) para las zonas de Oferta/Demanda

input group "=== Filtro de Zona Fresca ==="
input bool   InpUsarFiltroZonaFresca = true;       // Sólo operar el primer toque de cada zona (bloquea retests)

input group "=== Filtro de Tendencia Macro ==="
input bool   InpUsarFiltroTendencia = true;        // Activar filtro de tendencia (evita operar contra la tendencia de fondo)
input int    InpTrendMAPeriod       = 200;         // Período de la media móvil de tendencia (en Temporalidad_Liquidez)
input ENUM_MA_METHOD InpTrendMAMethod = MODE_SMA;  // Método de la media móvil de tendencia

input group "=== Indicador 2: RSI Trendlines with Breakouts ==="
input int    InpRSIPeriod           = 14;          // Período del RSI
input int    InpRSITrendLookback    = 150;         // Velas analizadas para localizar pivotes del RSI
input int    InpPivotLeftBars       = 3;           // Barras a la izquierda para confirmar un pivote
input int    InpPivotRightBars      = 3;           // Barras a la derecha para confirmar un pivote
input int    InpSignalValidityBars  = 3;           // Nº de velas que la ruptura del RSI permanece "armada"

input group "=== Gestión de Posición (SL / TP) ==="
input double InpSLBufferPips        = 10.0;        // Colchón del Stop Loss en pips, fuera de la zona
input double InpRiskRewardRatio     = 3.0;         // Ratio Riesgo:Beneficio (1:N)
input double InpManualPipSize       = 0.0;         // Tamaño de pip manual (0 = automático)
input bool   InpUsarBreakeven       = true;        // Mover el SL a breakeven cuando la operación vaya a favor
input double InpBreakevenTriggerR   = 1.5;         // Múltiplo de riesgo (R) de beneficio flotante para activar el breakeven
input double InpBreakevenBufferPips = 2.0;         // Colchón en pips sobre el precio de entrada al mover a breakeven
input bool   InpUsarTrailingStop      = true;       // Liberar el TP fijo y arrastrar el SL en tendencias fuertes
input double InpCierreParcialTriggerR = 3.0;        // Múltiplo de riesgo (R) al que se dispara el cierre parcial y se libera el TP
input double InpTrailingDistanceR     = 1.0;        // Distancia del trailing stop por detrás del precio, en múltiplos de R
input bool   InpUsarCierreParcial     = true;       // Cerrar parcialmente en el disparo y dejar correr sólo el resto
input double InpCierreParcialPercent  = 50.0;       // % del volumen a cerrar en el disparo del cierre parcial

input group "=== Blindaje de Riesgo Institucional ==="
input double InpRiskPercent          = 1.5;        // % de riesgo del balance por operación
input double InpMaxDailyLossPercent  = 4.0;        // % máximo de pérdida diaria (Kill Switch)
input double InpMaxSpreadPips        = 4.0;        // Spread máximo permitido en pips
input int    InpMaxPerdidasConsecutivas = 3;       // Nº de pérdidas seguidas en el día que bloquean nuevas entradas

input group "=== Filtro de Horario de Sesión ==="
input bool   InpUsarFiltroSesion    = true;        // Sólo abrir operaciones en la franja de mayor liquidez del oro
input int    InpSesionInicioHoraNY  = 8;           // Hora de inicio (hora de Nueva York): solapamiento Londres-NY
input int    InpSesionFinHoraNY     = 17;          // Hora de fin (hora de Nueva York): cierre de la sesión de NY

input group "=== Cierre de Fin de Semana ==="
input bool   InpCerrarViernes       = true;        // Activar cierre obligatorio de fin de semana
input int    InpFridayCloseHourNY   = 21;          // Hora de Nueva York para liquidar (21:00)
input int    InpBrokerGMTOffsetHrs  = 2;           // Offset del servidor del bróker respecto a UTC (ajustar según bróker)

//======================================================================
// VARIABLES GLOBALES
//======================================================================
CTrade         trade;

int            g_handleRSI = INVALID_HANDLE;
int            g_handleTendenciaMA = INVALID_HANDLE;
datetime       g_ultimaVelaProcesada = 0;      // Última vela procesada en la temporalidad de ejecución (RSI)
datetime       g_ultimaVelaMacroProcesada = 0; // Última vela procesada en la temporalidad macro (zonas)
datetime       g_ultimaVelaIntentoCierreFDS = 0; // Última vela en la que se intentó el cierre de fin de semana
datetime       g_ultimaVelaIntentoVenta = 0;    // Última vela en la que se intentó abrir una venta
datetime       g_ultimaVelaIntentoCompra = 0;   // Última vela en la que se intentó abrir una compra

// --- Estructura de una zona de oferta/demanda ---
struct SZona
  {
   double superior;
   double inferior;
   bool   activa;
   bool   huboEntrada; // el precio ya entró en esta zona alguna vez desde que se formó
   bool   tocada;      // el precio entró y ya volvió a salir: la zona quedó "puesta a prueba"
  };

SZona          g_zonaSupply;
SZona          g_zonaDemand;

// --- Estado de las líneas de tendencia del RSI ---
bool           g_lineaPicosValida  = false;   // Línea sobre picos (máximos locales) del RSI
double         g_picosPendiente    = 0.0;
double         g_picosValorBase    = 0.0;
int            g_picosBarraBase    = 0;

bool           g_lineaVallesValida = false;   // Línea sobre valles (mínimos locales) del RSI
double         g_vallesPendiente   = 0.0;
double         g_vallesValorBase   = 0.0;
int            g_vallesBarraBase   = 0;

// --- Señales de ruptura (breakout) del RSI, con "armado" temporal ---
bool           g_breakoutBajistaArmado = false;
datetime       g_breakoutBajistaTime   = 0;

bool           g_breakoutAlcistaArmado = false;
datetime       g_breakoutAlcistaTime   = 0;

// --- Kill Switch diario ---
datetime       g_diaActual          = 0;
double         g_balanceInicioDia   = 0.0;
bool           g_killSwitchActivo   = false;

// --- Circuito de pérdidas consecutivas (independiente del Kill Switch del 4%) ---
int            g_perdidasConsecutivasHoy = 0;
bool           g_circuitoPerdidasActivo  = false;

// --- Breakeven de la posición actualmente abierta (sólo se gestiona una a la vez) ---
double         g_slOriginalPosicion   = 0.0; // SL con el que se abrió la posición (antes de cualquier breakeven)
bool           g_breakevenAplicado    = false;
bool           g_trailingActivado     = false; // true en cuanto se libera el TP fijo y empieza el trailing
bool           g_cierreParcialAplicado = false; // true en cuanto se ejecuta el cierre parcial de la posición

//======================================================================
// DIAGNÓSTICO (instrumentación pura: no afecta a ninguna regla de trading,
// sólo cuenta cuántas veces se cumple cada condición del embudo de entrada
// para poder medir, con datos, qué filtro elimina más oportunidades).
//======================================================================
bool   g_diagDentroSupplyAnterior = false; // estado anterior de PrecioEnZona(bid, Supply), para detectar el flanco de entrada ("toque")
bool   g_diagDentroDemandAnterior = false; // estado anterior de PrecioEnZona(ask, Demand)
bool   g_diagCoincideVentaAnterior  = false; // estado anterior de (dentro de Supply) AND (breakout bajista vigente)
bool   g_diagCoincideCompraAnterior = false; // estado anterior de (dentro de Demand) AND (breakout alcista vigente)

int    g_diagBreakoutBajistaDetectado = 0; // nº de veces que se confirmó un breakout bajista del RSI (línea de picos)
int    g_diagBreakoutAlcistaDetectado = 0; // nº de veces que se confirmó un breakout alcista del RSI (línea de valles)

int    g_diagContactosSupply            = 0; // nº de "toques" distintos de la zona de Oferta (flanco de entrada)
int    g_diagContactosSupplyEnSesion     = 0; // de esos toques, cuántos ocurrieron dentro del horario de sesión permitido
int    g_diagContactosSupplyConBreakout  = 0; // de esos toques, cuántos ocurrieron con un breakout bajista ya vigente

int    g_diagContactosDemand             = 0; // nº de "toques" distintos de la zona de Demanda (flanco de entrada)
int    g_diagContactosDemandEnSesion     = 0;
int    g_diagContactosDemandConBreakout  = 0;

int    g_diagCoincidenciasVenta               = 0; // nº de veces que (dentro de zona) y (breakout vigente) coincidieron a la vez (flanco)
int    g_diagCoincidenciasVentaBloqTendencia   = 0; // de esas coincidencias, cuántas fueron bloqueadas por el filtro de tendencia
int    g_diagCoincidenciasVentaBloqSesion      = 0; // ... por el filtro de horario de sesión
int    g_diagCoincidenciasVentaBloqZonaFresca  = 0; // ... por el filtro de zona fresca

int    g_diagCoincidenciasCompra               = 0;
int    g_diagCoincidenciasCompraBloqTendencia   = 0;
int    g_diagCoincidenciasCompraBloqSesion      = 0;
int    g_diagCoincidenciasCompraBloqZonaFresca  = 0;

// --- Desglose MUTUAMENTE EXCLUYENTE de las coincidencias (zona+breakout) según
//     tendencia/zona fresca, para separar el solapamiento del desglose anterior.
//     Por construcción: sobrevivenAmbos + bloqSoloTendencia + bloqSoloZonaFresca
//     + bloqAmbos == g_diagCoincidenciasVenta (o Compra) ---
int    g_diagVentaSobrevivenAmbosFiltros   = 0; // tendencia OK y zona fresca OK
int    g_diagVentaBloqSoloTendencia        = 0; // sólo bloqueada por tendencia
int    g_diagVentaBloqSoloZonaFresca       = 0; // sólo bloqueada por zona fresca
int    g_diagVentaBloqAmbosFiltros         = 0; // bloqueada por los dos a la vez
int    g_diagVentaCoincideConPosAbierta    = 0; // de las coincidencias, cuántas ocurrieron con una posición ya abierta

int    g_diagCompraSobrevivenAmbosFiltros  = 0;
int    g_diagCompraBloqSoloTendencia       = 0;
int    g_diagCompraBloqSoloZonaFresca      = 0;
int    g_diagCompraBloqAmbosFiltros        = 0;
int    g_diagCompraCoincideConPosAbierta   = 0;

int    g_diagVentasEjecutadas  = 0; // nº de ventas que finalmente se enviaron (mismo evento que el Print "VENTA ejecutada")
int    g_diagComprasEjecutadas = 0; // nº de compras que finalmente se enviaron (mismo evento que el Print "COMPRA ejecutada")

double g_diagAnchosZonaSupply[]; // tamaño en $ (superior - inferior) de cada zona de Oferta calculada, para media/mediana
double g_diagAnchosZonaDemand[]; // ídem para la zona de Demanda

// --- Seguimiento de cierre de posición para el estudio "qué selecciona el filtro de tendencia" ---
bool  g_diagHabiaPosicionAbiertaAnterior = false; // estado anterior de TicketPosicionPropiaActual() != 0
ulong g_diagTicketPosicionAnterior       = 0;     // ticket de la posición que se venía trackeando

//======================================================================
// UTILIDADES
//======================================================================

//--- Calcula el tamaño de un "pip" para XAUUSD.
//    La heurística de pips por nº de decimales (estándar en pares de Forex)
//    NO aplica al oro: muchos brokers cotizan XAUUSD con 2 decimales (ej.
//    4212.45), lo que esa heurística clasificaría como "1 punto = 1 pip"
//    (0.01), cuando la convención real de mercado para el oro es que un pip
//    equivale a 0.10 (10 centavos). Usar 0.01 hacía que InpSLBufferPips=10
//    colocara el SL a solo $0.10 del borde de la zona -- diez veces más
//    ajustado de lo previsto, y explicaba stops saltando en segundos/minutos
//    detectados en el backtest. Por eso el valor por defecto para el oro es
//    fijo (0.10) salvo que el usuario indique InpManualPipSize explícitamente.
double PipSize()
  {
   if(InpManualPipSize > 0.0)
      return InpManualPipSize;

   return 0.10;
  }

//--- Clave única (por símbolo/magic/día) para variables globales persistentes
string ClaveGlobal(const string sufijo)
  {
   MqlDateTime dt;
   TimeToStruct(TimeCurrent(), dt);
   string diaStr = StringFormat("%04d%02d%02d", dt.year, dt.mon, dt.day);
   return StringFormat("EA_%s_%s_%d_%s", _Symbol, sufijo, (int)InpMagicNumber, diaStr);
  }

//======================================================================
// MÓDULO 1A: ZONAS DE OFERTA Y DEMANDA MULTI-TIMEFRAME (CONTEXTO MACRO)
//======================================================================
//  Replica la lógica de "Supply and Demand Visible Range", pero en modo
//  Multi-Timeframe (MTF): en lugar de mirar las velas de la temporalidad
//  de ejecución (5M), el bot "hace zoom" hacia la temporalidad macro
//  configurada en "Temporalidad_Liquidez" (por defecto H1, también válido
//  H4) y escanea allí las últimas "InpZonaLookbackMacro" velas (100 por
//  defecto). Esto asegura que las zonas representan liquidez institucional
//  real acumulada durante horas/días completos, y no simple ruido de
//  velas de 5 minutos.
//
//  - Zona de OFERTA (Supply): rango entre el máximo más alto de las
//    últimas N velas MACRO y el precio de cierre de esa misma vela.
//  - Zona de DEMANDA (Demand): rango entre el mínimo más bajo de las
//    últimas N velas MACRO y el precio de cierre de esa misma vela.
//
//  El escaneo se repite de forma constante cada vez que cierra una
//  nueva vela en la temporalidad macro (ver EsVelaNuevaMacro()), sin
//  importar que el EA esté corriendo sobre un gráfico de 5 minutos: el
//  historial de la temporalidad macro se solicita directamente al
//  terminal mediante iHighest/iLowest/iHigh/iLow/iClose indicando
//  "Temporalidad_Liquidez" como parámetro de timeframe.
//----------------------------------------------------------------------
void ActualizarZonasOfertaDemanda()
  {
// Verifica que exista histórico suficiente de la temporalidad macro
   if(Bars(_Symbol, Temporalidad_Liquidez) < InpZonaLookbackMacro + 1)
      return;

// iHighest/iLowest buscan, dentro de "InpZonaLookbackMacro" velas de la
// temporalidad MACRO, comenzando en la vela cerrada más reciente
// (shift = 1), el índice de la vela con el máximo/mínimo extremo.
   int shiftMax = iHighest(_Symbol, Temporalidad_Liquidez, MODE_HIGH, InpZonaLookbackMacro, 1);
   int shiftMin = iLowest(_Symbol, Temporalidad_Liquidez, MODE_LOW, InpZonaLookbackMacro, 1);

   if(shiftMax < 0 || shiftMin < 0)
      return;

   double highExtremo  = iHigh(_Symbol, Temporalidad_Liquidez, shiftMax);
   double closeDeHigh  = iClose(_Symbol, Temporalidad_Liquidez, shiftMax);

   double lowExtremo   = iLow(_Symbol, Temporalidad_Liquidez, shiftMin);
   double closeDeLow   = iClose(_Symbol, Temporalidad_Liquidez, shiftMin);

// Zona de Oferta (macro): entre el cierre (límite inferior) y el máximo (límite superior)
   g_zonaSupply.superior    = highExtremo;
   g_zonaSupply.inferior    = closeDeHigh;
   g_zonaSupply.activa      = true;
   g_zonaSupply.huboEntrada = false;
   g_zonaSupply.tocada      = false;

// Zona de Demanda (macro): entre el mínimo (límite inferior) y el cierre (límite superior)
   g_zonaDemand.inferior    = lowExtremo;
   g_zonaDemand.superior    = closeDeLow;
   g_zonaDemand.activa      = true;
   g_zonaDemand.huboEntrada = false;
   g_zonaDemand.tocada      = false;

   // --- Diagnóstico: registrar el ancho en $ de cada zona recién calculada,
   //     para poder sacar media/mediana al final del backtest (no afecta al trading) ---
   int nSupply = ArraySize(g_diagAnchosZonaSupply);
   ArrayResize(g_diagAnchosZonaSupply, nSupply + 1);
   g_diagAnchosZonaSupply[nSupply] = g_zonaSupply.superior - g_zonaSupply.inferior;

   int nDemand = ArraySize(g_diagAnchosZonaDemand);
   ArrayResize(g_diagAnchosZonaDemand, nDemand + 1);
   g_diagAnchosZonaDemand[nDemand] = g_zonaDemand.superior - g_zonaDemand.inferior;
  }

//--- Comprueba si un precio dado se encuentra dentro de una zona
bool PrecioEnZona(const double precio, const SZona &zona)
  {
   if(!zona.activa)
      return false;
   return (precio >= zona.inferior && precio <= zona.superior);
  }

//--- Filtro de zona fresca: las zonas institucionales pierden fuerza cada vez que el
//    precio las revisita. Se considera que una zona ha sido "puesta a prueba" (tocada)
//    sólo cuando el precio entró en ella y DESPUÉS volvió a salir -- mientras el precio
//    permanece dentro de forma continua (su primera visita), la zona sigue "fresca" y
//    puede seguir generando señales; sólo se bloquean los retests posteriores a esa
//    primera visita, hasta que se forme una zona nueva en el siguiente cierre de vela
//    macro (ver el reseteo de huboEntrada/tocada en ActualizarZonasOfertaDemanda()).
void ActualizarEstadoDeZona(SZona &zona, const double precio)
  {
   if(PrecioEnZona(precio, zona))
      zona.huboEntrada = true;
   else if(zona.huboEntrada)
      zona.tocada = true;
  }

void MarcarZonasTocadas()
  {
   double bid = SymbolInfoDouble(_Symbol, SYMBOL_BID);
   double ask = SymbolInfoDouble(_Symbol, SYMBOL_ASK);

   ActualizarEstadoDeZona(g_zonaSupply, bid);
   ActualizarEstadoDeZona(g_zonaDemand, ask);
  }

//======================================================================
// MÓDULO 1B: RSI TRENDLINES WITH BREAKOUTS (GATILLO)
//======================================================================
// Cómo se calculan las líneas de tendencia dentro del RSI:
//
// 1) Se copian los últimos "InpRSITrendLookback" valores CERRADOS del
//    RSI (se excluye la vela en formación, por eso se copia con shift=1).
//
// 2) Se buscan "pivotes" del RSI:
//      - Un PICO (máximo local) en la barra i se confirma si su valor
//        es mayor que el de todas las barras dentro de una ventana de
//        "InpPivotLeftBars" barras a la izquierda y "InpPivotRightBars"
//        a la derecha.
//      - Un VALLE (mínimo local) se confirma de forma análoga pero
//        buscando el valor mínimo dentro de esa misma ventana.
//
// 3) Se toman los DOS pivotes más recientes de cada tipo (picos y
//    valles) y se traza una recta que los une, igual que si se
//    dibujaran manualmente las trendlines sobre el indicador RSI en el
//    gráfico:
//
//        pendiente = (valor2 - valor1) / (indice2 - indice1)
//        valorLinea(i) = valor1 + pendiente * (i - indice1)
//
//    Esta recta se proyecta hacia adelante en el tiempo (extrapolación),
//    de modo que en cada nueva vela se puede calcular el valor teórico
//    que tendría la línea de tendencia en ese punto, exactamente igual
//    a como LuxAlgo extiende sus trendlines hasta la vela actual.
//
// 4) Un "Breakout" (ruptura) se valida cuando el RSI CIERRA cruzando la
//    línea proyectada:
//      - Breakout BAJISTA (línea de picos): el RSI de la vela anterior
//        estaba en o por encima de la línea, y el RSI de la vela recién
//        cerrada terminó por DEBAJO de la línea -> señal de VENTA.
//      - Breakout ALCISTA (línea de valles): el RSI de la vela anterior
//        estaba en o por debajo de la línea, y el RSI de la vela recién
//        cerrada terminó por ENCIMA de la línea -> señal de COMPRA.
//----------------------------------------------------------------------

//--- Busca los dos pivotes (picos o valles) más recientes dentro del buffer del RSI.
//    rsi[] debe estar indexado como serie NO temporal (0 = valor más antiguo).
bool BuscarUltimosDosPivotes(const double &rsi[], const int total, const int pivLeft, const int pivRight,
                              const bool buscarPicos, int &idx1, double &val1, int &idx2, double &val2)
  {
   int encontrados[]; // índices de pivotes encontrados, del más reciente al más antiguo
   double valores[];
   int total_piv = 0;
   ArrayResize(encontrados, 0);
   ArrayResize(valores, 0);

// Se recorre el buffer de más reciente a más antiguo. Un pivote en la
// posición "i" sólo puede confirmarse si existen "pivRight" barras más
// nuevas que ya cerraron después de él (para poder compararlas).
   for(int i = total - 1 - pivRight; i >= pivLeft; i--)
     {
      bool esPivote = true;
      double centro = rsi[i];

      for(int k = 1; k <= pivLeft && esPivote; k++)
        {
         if(buscarPicos)
           {
            if(rsi[i - k] > centro) esPivote = false;
           }
         else
           {
            if(rsi[i - k] < centro) esPivote = false;
           }
        }

      for(int k = 1; k <= pivRight && esPivote; k++)
        {
         if(buscarPicos)
           {
            if(rsi[i + k] > centro) esPivote = false;
           }
         else
           {
            if(rsi[i + k] < centro) esPivote = false;
           }
        }

      if(esPivote)
        {
         total_piv++;
         ArrayResize(encontrados, total_piv);
         ArrayResize(valores, total_piv);
         encontrados[total_piv - 1] = i;
         valores[total_piv - 1]     = centro;

         if(total_piv >= 2)
            break; // ya tenemos los dos pivotes más recientes
        }
     }

   if(total_piv < 2)
      return false;

// encontrados[0] es el pivote más reciente, encontrados[1] el anterior
   idx2 = encontrados[0];
   val2 = valores[0];
   idx1 = encontrados[1];
   val1 = valores[1];

   return true;
  }

//--- Recalcula ambas líneas de tendencia (picos y valles) del RSI y determina
//    si se ha producido una ruptura (breakout) confirmada en la última vela cerrada.
void ActualizarRSITrendlinesYBreakouts()
  {
   int velasNecesarias = InpRSITrendLookback + InpPivotRightBars + 2;
   double rsiBuffer[];
   ArraySetAsSeries(rsiBuffer, false);

// Se copia desde shift=1 para trabajar únicamente con velas ya cerradas
   int copiados = CopyBuffer(g_handleRSI, 0, 1, velasNecesarias, rsiBuffer);
   if(copiados < velasNecesarias)
      return; // aún no hay histórico suficiente

   int total = ArraySize(rsiBuffer);

// --- Línea de tendencia sobre PICOS (para detectar breakout bajista / venta) ---
   int idx1p, idx2p;
   double val1p, val2p;
   g_lineaPicosValida = BuscarUltimosDosPivotes(rsiBuffer, total, InpPivotLeftBars, InpPivotRightBars,
                                                 true, idx1p, val1p, idx2p, val2p);
   if(g_lineaPicosValida)
     {
      g_picosPendiente = (val2p - val1p) / (double)(idx2p - idx1p);
      g_picosValorBase = val1p;
      g_picosBarraBase = idx1p;
     }

// --- Línea de tendencia sobre VALLES (para detectar breakout alcista / compra) ---
   int idx1v, idx2v;
   double val1v, val2v;
   g_lineaVallesValida = BuscarUltimosDosPivotes(rsiBuffer, total, InpPivotLeftBars, InpPivotRightBars,
                                                  false, idx1v, val1v, idx2v, val2v);
   if(g_lineaVallesValida)
     {
      g_vallesPendiente = (val2v - val1v) / (double)(idx2v - idx1v);
      g_vallesValorBase = val1v;
      g_vallesBarraBase = idx1v;
     }

// Índices de la última vela cerrada (total-1) y la anterior a esa (total-2)
   int iActual   = total - 1;
   int iAnterior = total - 2;
   double rsiActual   = rsiBuffer[iActual];
   double rsiAnterior = rsiBuffer[iAnterior];

// --- Comprobar breakout BAJISTA sobre la línea de picos ---
   if(g_lineaPicosValida)
     {
      double lineaActual   = g_picosValorBase + g_picosPendiente * (iActual   - g_picosBarraBase);
      double lineaAnterior = g_picosValorBase + g_picosPendiente * (iAnterior - g_picosBarraBase);

      bool cruceBajista = (rsiAnterior >= lineaAnterior) && (rsiActual < lineaActual);
      if(cruceBajista)
        {
         g_breakoutBajistaArmado = true;
         g_breakoutBajistaTime   = TimeCurrent();
         g_diagBreakoutBajistaDetectado++; // diagnóstico: no afecta al trading
        }
     }

// --- Comprobar breakout ALCISTA sobre la línea de valles ---
   if(g_lineaVallesValida)
     {
      double lineaActual   = g_vallesValorBase + g_vallesPendiente * (iActual   - g_vallesBarraBase);
      double lineaAnterior = g_vallesValorBase + g_vallesPendiente * (iAnterior - g_vallesBarraBase);

      bool cruceAlcista = (rsiAnterior <= lineaAnterior) && (rsiActual > lineaActual);
      if(cruceAlcista)
        {
         g_breakoutAlcistaArmado = true;
         g_breakoutAlcistaTime   = TimeCurrent();
         g_diagBreakoutAlcistaDetectado++; // diagnóstico: no afecta al trading
        }
     }
  }

//--- Un breakout permanece "armado" (válido) durante InpSignalValidityBars velas,
//    tiempo en el que se espera a que el precio también entre en su zona.
bool BreakoutBajistaVigente()
  {
   if(!g_breakoutBajistaArmado)
      return false;
   long segundosVela = PeriodSeconds(InpTimeframe);
   long limite = segundosVela * InpSignalValidityBars;
   return ((TimeCurrent() - g_breakoutBajistaTime) <= limite);
  }

bool BreakoutAlcistaVigente()
  {
   if(!g_breakoutAlcistaArmado)
      return false;
   long segundosVela = PeriodSeconds(InpTimeframe);
   long limite = segundosVela * InpSignalValidityBars;
   return ((TimeCurrent() - g_breakoutAlcistaTime) <= limite);
  }

//======================================================================
// MÓDULO 2: GESTIÓN DE RIESGO Y CÁLCULO DE LOTAJE
//======================================================================

//--- Calcula el volumen (lotaje) exacto para que, si el precio toca el
//    Stop Loss, la pérdida sea igual a InpRiskPercent % del balance.
//    Usa OrderCalcProfit() en vez de derivar el valor manualmente a partir
//    de SYMBOL_TRADE_TICK_VALUE/SYMBOL_TRADE_TICK_SIZE: para algunos
//    brokers/símbolos (como ciertas cotizaciones de XAUUSD) esos valores no
//    reflejan el $ real por punto y por lote, lo que provocaba lotajes hasta
//    10 veces mayores de lo previsto. OrderCalcProfit() le pregunta
//    directamente al bróker cuál sería el resultado monetario de la
//    operación, sin asumir nada sobre el tick.
double CalcularLotaje(const double precioEntrada, const double precioSL, const ENUM_ORDER_TYPE tipoOrden)
  {
   double balance      = AccountInfoDouble(ACCOUNT_BALANCE);
   double montoRiesgo   = balance * (InpRiskPercent / 100.0);

   double distanciaSL = MathAbs(precioEntrada - precioSL);
   if(distanciaSL <= 0.0)
      return 0.0;

// Pérdida monetaria real que reportaría el bróker para 1.0 lote si el
// precio recorriera toda la distancia del SL.
   double perdidaPorLote = 0.0;
   if(!OrderCalcProfit(tipoOrden, _Symbol, 1.0, precioEntrada, precioSL, perdidaPorLote))
      return 0.0;

   perdidaPorLote = MathAbs(perdidaPorLote);
   if(perdidaPorLote <= 0.0)
      return 0.0;

   double lotes = montoRiesgo / perdidaPorLote;

// Ajustar a los límites y al paso de volumen permitidos por el bróker
   double volMin  = SymbolInfoDouble(_Symbol, SYMBOL_VOLUME_MIN);
   double volMax  = SymbolInfoDouble(_Symbol, SYMBOL_VOLUME_MAX);
   double volStep = SymbolInfoDouble(_Symbol, SYMBOL_VOLUME_STEP);

   lotes = MathFloor(lotes / volStep) * volStep;
   lotes = MathMax(volMin, MathMin(volMax, lotes));

   return NormalizeDouble(lotes, 2);
  }

//======================================================================
// MÓDULO 3: FILTROS DE PROTECCIÓN (SPREAD, KILL SWITCH, FIN DE SEMANA)
//======================================================================

//--- Filtro de Spread: bloquea nuevas operaciones si el spread actual supera el máximo permitido.
bool SpreadPermitido()
  {
   double spreadPuntos = (double)SymbolInfoInteger(_Symbol, SYMBOL_SPREAD);
   double spreadPips   = (spreadPuntos * SymbolInfoDouble(_Symbol, SYMBOL_POINT)) / PipSize();
   return (spreadPips <= InpMaxSpreadPips);
  }

//--- Cierra todas las posiciones abiertas por este EA en este símbolo
void CerrarTodasLasPosiciones()
  {
   for(int i = PositionsTotal() - 1; i >= 0; i--)
     {
      ulong ticket = PositionGetTicket(i);
      if(ticket == 0) continue;
      if(PositionGetString(POSITION_SYMBOL) != _Symbol) continue;
      if(PositionGetInteger(POSITION_MAGIC) != (long)InpMagicNumber) continue;

      trade.PositionClose(ticket);
     }
  }

//--- Elimina todas las órdenes pendientes de este EA en este símbolo
void BorrarTodasLasOrdenesPendientes()
  {
   for(int i = OrdersTotal() - 1; i >= 0; i--)
     {
      ulong ticket = OrderGetTicket(i);
      if(ticket == 0) continue;
      if(OrderGetString(ORDER_SYMBOL) != _Symbol) continue;
      if(OrderGetInteger(ORDER_MAGIC) != (long)InpMagicNumber) continue;

      trade.OrderDelete(ticket);
     }
  }

//----------------------------------------------------------------------
// KILL SWITCH DIARIO
//
// Funcionamiento:
//   1) Al iniciar cada nuevo día de servidor se guarda el balance de
//      referencia ("g_balanceInicioDia").
//   2) En cada tick se calcula la pérdida diaria total SUMANDO el
//      resultado ya cerrado en el día (implícito en el Balance actual,
//      que ya refleja las operaciones cerradas) más el flotante en
//      tiempo real de las posiciones abiertas. Esa suma es exactamente
//      el Equity actual de la cuenta:
//
//         PérdidaDiaria(%) = (BalanceInicioDia - EquityActual) / BalanceInicioDia * 100
//
//   3) Si esa pérdida alcanza o supera "InpMaxDailyLossPercent":
//        - Se cierran TODAS las posiciones a mercado.
//        - Se eliminan TODAS las órdenes pendientes.
//        - Se activa una bandera "g_killSwitchActivo" que bloquea
//          cualquier nueva operación.
//   4) La bandera sólo se libera cuando el servidor cambia de día
//      (nueva fecha en TimeCurrent()), momento en el que se reinicia
//      también el balance de referencia.
//   5) El estado se guarda además en variables globales de la
//      terminal (GlobalVariableSet) para que, si la plataforma se
//      reinicia en pleno día, el bloqueo del Kill Switch no se pierda.
//----------------------------------------------------------------------
void GestionarCambioDeDia()
  {
   MqlDateTime dt;
   TimeToStruct(TimeCurrent(), dt);
   dt.hour = 0; dt.min = 0; dt.sec = 0;
   datetime inicioDeHoy = StructToTime(dt);

   if(inicioDeHoy != g_diaActual)
     {
      g_diaActual        = inicioDeHoy;

      // Reinicio diario del circuito de pérdidas consecutivas
      g_perdidasConsecutivasHoy = 0;
      g_circuitoPerdidasActivo  = false;

      string claveBal = ClaveGlobal("BalanceInicioDia");
      string claveKS  = ClaveGlobal("KillSwitch");

      if(GlobalVariableCheck(claveBal))
        {
         // Ya existía un registro para hoy (ej. reinicio de la terminal)
         g_balanceInicioDia = GlobalVariableGet(claveBal);
         g_killSwitchActivo = GlobalVariableCheck(claveKS) && (GlobalVariableGet(claveKS) > 0.5);
        }
      else
        {
         g_balanceInicioDia = AccountInfoDouble(ACCOUNT_BALANCE);
         g_killSwitchActivo = false;
         GlobalVariableSet(claveBal, g_balanceInicioDia);
         GlobalVariableSet(claveKS, 0.0);
        }

      PrintFormat("Nuevo día de trading. Balance de referencia: %.2f", g_balanceInicioDia);
     }
  }

void ComprobarKillSwitchDiario()
  {
   if(g_balanceInicioDia <= 0.0)
      return;

   if(g_killSwitchActivo)
      return; // ya activado hoy, no hay nada más que comprobar

   double equityActual   = AccountInfoDouble(ACCOUNT_EQUITY);
   double perdidaDiaria   = g_balanceInicioDia - equityActual;
   double perdidaDiariaPct = (perdidaDiaria / g_balanceInicioDia) * 100.0;

   if(perdidaDiariaPct >= InpMaxDailyLossPercent)
     {
      PrintFormat("KILL SWITCH ACTIVADO: pérdida diaria %.2f%% >= límite %.2f%%. Cerrando todo.",
                  perdidaDiariaPct, InpMaxDailyLossPercent);

      CerrarTodasLasPosiciones();
      BorrarTodasLasOrdenesPendientes();

      g_killSwitchActivo = true;
      GlobalVariableSet(ClaveGlobal("KillSwitch"), 1.0);
     }
  }

//----------------------------------------------------------------------
// CIERRE DE FIN DE SEMANA
// Convierte la hora del servidor a hora de Nueva York (aplicando el
// horario de verano de EE.UU.) y liquida toda posición flotante los
// viernes a partir de las InpFridayCloseHourNY (21:00 por defecto).
//----------------------------------------------------------------------
bool EsHorarioDeVeranoUSA(const datetime tiempoUTC)
  {
   MqlDateTime dt;
   TimeToStruct(tiempoUTC, dt);

// DST en EE.UU.: comienza el 2º domingo de marzo y termina el 1er domingo de noviembre
   int year = dt.year;

   MqlDateTime tmp;
   ZeroMemory(tmp);
   tmp.year = year; tmp.mon = 3; tmp.day = 1;
   datetime primerDiaMarzo = StructToTime(tmp);
   TimeToStruct(primerDiaMarzo, tmp);
   int diaSemana1Marzo = tmp.day_of_week; // 0=domingo
   int diaSegundoDomingoMarzo = 1 + ((7 - diaSemana1Marzo) % 7) + 7;

   ZeroMemory(tmp);
   tmp.year = year; tmp.mon = 11; tmp.day = 1;
   datetime primerDiaNoviembre = StructToTime(tmp);
   TimeToStruct(primerDiaNoviembre, tmp);
   int diaSemana1Noviembre = tmp.day_of_week;
   int diaPrimerDomingoNoviembre = 1 + ((7 - diaSemana1Noviembre) % 7);

   ZeroMemory(tmp);
   tmp.year = year; tmp.mon = 3; tmp.day = diaSegundoDomingoMarzo; tmp.hour = 2;
   datetime inicioDST = StructToTime(tmp);

   ZeroMemory(tmp);
   tmp.year = year; tmp.mon = 11; tmp.day = diaPrimerDomingoNoviembre; tmp.hour = 2;
   datetime finDST = StructToTime(tmp);

   return (tiempoUTC >= inicioDST && tiempoUTC < finDST);
  }

datetime ConvertirServidorANuevaYork(const datetime tiempoServidor)
  {
   datetime tiempoUTC = tiempoServidor - InpBrokerGMTOffsetHrs * 3600;
   int offsetNY = EsHorarioDeVeranoUSA(tiempoUTC) ? -4 : -5; // EDT / EST
   return tiempoUTC + offsetNY * 3600;
  }

bool DebeCerrarPorFinDeSemana()
  {
   if(!InpCerrarViernes)
      return false;

   datetime horaNY = ConvertirServidorANuevaYork(TimeCurrent());
   MqlDateTime dt;
   TimeToStruct(horaNY, dt);

// day_of_week: 0=domingo,...,5=viernes,6=sábado
   if(dt.day_of_week == 5 && dt.hour >= InpFridayCloseHourNY)
      return true;

   return false;
  }

//----------------------------------------------------------------------
// FILTRO DE HORARIO DE SESIÓN
// El oro se mueve con volumen y tendencias limpias durante el solapamiento
// Londres-Nueva York y la sesión de Nueva York; fuera de esa franja (sesión
// asiática, madrugada europea) el volumen es más bajo y las rupturas del RSI
// tienden a ser ruido. Este filtro sólo bloquea la APERTURA de operaciones
// nuevas fuera de [InpSesionInicioHoraNY, InpSesionFinHoraNY) en hora de
// Nueva York; una posición ya abierta sigue gestionándose (breakeven,
// trailing, Kill Switch, cierre de fin de semana) a cualquier hora.
//----------------------------------------------------------------------
bool SesionPermiteOperar()
  {
   if(!InpUsarFiltroSesion)
      return true;

   datetime horaNY = ConvertirServidorANuevaYork(TimeCurrent());
   MqlDateTime dt;
   TimeToStruct(horaNY, dt);

   if(InpSesionInicioHoraNY <= InpSesionFinHoraNY)
      return (dt.hour >= InpSesionInicioHoraNY && dt.hour < InpSesionFinHoraNY);

// Rango que cruza la medianoche (por si se configura así)
   return (dt.hour >= InpSesionInicioHoraNY || dt.hour < InpSesionFinHoraNY);
  }

//======================================================================
// FILTRO DE TENDENCIA MACRO
//======================================================================
// Reduce las rachas de pérdidas seguidas en mercado lateral: sólo deja
// operar a favor de la tendencia de fondo, medida con una media móvil
// larga (InpTrendMAPeriod) calculada en la misma temporalidad macro que
// las zonas de Oferta/Demanda (Temporalidad_Liquidez). Si el cierre de
// la última vela macro cerrada está por encima de la media, se considera
// tendencia alcista (sólo se permiten compras); si está por debajo,
// tendencia bajista (sólo se permiten ventas). Con InpUsarFiltroTendencia
// en false, el filtro queda desactivado y ambos lados quedan permitidos.
//----------------------------------------------------------------------
bool FiltroTendenciaPermiteVenta()
  {
   if(!InpUsarFiltroTendencia)
      return true;

   double maBuffer[];
   ArraySetAsSeries(maBuffer, true);
   if(CopyBuffer(g_handleTendenciaMA, 0, 1, 1, maBuffer) < 1)
      return false; // sin datos suficientes todavía: no arriesgar

   double cierreMacro = iClose(_Symbol, Temporalidad_Liquidez, 1);
   return (cierreMacro < maBuffer[0]); // tendencia bajista
  }

bool FiltroTendenciaPermiteCompra()
  {
   if(!InpUsarFiltroTendencia)
      return true;

   double maBuffer[];
   ArraySetAsSeries(maBuffer, true);
   if(CopyBuffer(g_handleTendenciaMA, 0, 1, 1, maBuffer) < 1)
      return false;

   double cierreMacro = iClose(_Symbol, Temporalidad_Liquidez, 1);
   return (cierreMacro > maBuffer[0]); // tendencia alcista
  }

//======================================================================
// DIAGNÓSTICO: EMBUDO DE CONDICIONES DE ENTRADA
//======================================================================
// Mide, sin tocar ninguna regla de trading, cuántas veces se cumple cada
// condición de EvaluarSenalDeVenta()/EvaluarSenalDeCompra() por separado,
// para poder saber qué filtro elimina más oportunidades en vez de
// adivinarlo. Todo lo que hace esta función es LEER estado y contar
// "flancos" (la primera vez que una condición pasa a ser verdadera, no
// cada tick mientras se mantiene verdadera) -- no abre, cierra ni
// modifica ninguna operación, ni cambia ninguna variable que use la
// lógica de entrada/salida real.
void ActualizarContadoresDiagnostico()
  {
   double bid = SymbolInfoDouble(_Symbol, SYMBOL_BID);
   double ask = SymbolInfoDouble(_Symbol, SYMBOL_ASK);

   bool dentroSupplyAhora = PrecioEnZona(bid, g_zonaSupply);
   bool dentroDemandAhora = PrecioEnZona(ask, g_zonaDemand);
   bool breakoutBajistaVigenteAhora = BreakoutBajistaVigente();
   bool breakoutAlcistaVigenteAhora = BreakoutAlcistaVigente();
   bool sesionOkAhora    = SesionPermiteOperar();
   bool tendenciaOkVenta  = FiltroTendenciaPermiteVenta();
   bool tendenciaOkCompra = FiltroTendenciaPermiteCompra();

   // --- Toques de zona (flanco: primera vez que entra, no cada tick dentro) ---
   if(dentroSupplyAhora && !g_diagDentroSupplyAnterior)
     {
      g_diagContactosSupply++;
      if(sesionOkAhora)
         g_diagContactosSupplyEnSesion++;
      if(breakoutBajistaVigenteAhora)
         g_diagContactosSupplyConBreakout++;
     }
   if(dentroDemandAhora && !g_diagDentroDemandAnterior)
     {
      g_diagContactosDemand++;
      if(sesionOkAhora)
         g_diagContactosDemandEnSesion++;
      if(breakoutAlcistaVigenteAhora)
         g_diagContactosDemandConBreakout++;
     }

   // --- Coincidencia zona + breakout (flanco), y por qué se perdería si se perdiera ---
   bool coincideVentaAhora  = dentroSupplyAhora && breakoutBajistaVigenteAhora;
   if(coincideVentaAhora && !g_diagCoincideVentaAnterior)
     {
      g_diagCoincidenciasVenta++;
      if(!tendenciaOkVenta)
         g_diagCoincidenciasVentaBloqTendencia++;
      if(!sesionOkAhora)
         g_diagCoincidenciasVentaBloqSesion++;
      if(InpUsarFiltroZonaFresca && g_zonaSupply.tocada)
         g_diagCoincidenciasVentaBloqZonaFresca++;

      // Desglose MUTUAMENTE EXCLUYENTE tendencia vs zona fresca (sin solape)
      bool bloqTendencia  = !tendenciaOkVenta;
      bool bloqZonaFresca = (InpUsarFiltroZonaFresca && g_zonaSupply.tocada);
      if(bloqTendencia && bloqZonaFresca)
         g_diagVentaBloqAmbosFiltros++;
      else if(bloqTendencia)
         g_diagVentaBloqSoloTendencia++;
      else if(bloqZonaFresca)
         g_diagVentaBloqSoloZonaFresca++;
      else
         g_diagVentaSobrevivenAmbosFiltros++;

      // Posible cuello de botella oculto: ¿ya había una posición abierta en ese instante?
      if(HayPosicionAbierta())
         g_diagVentaCoincideConPosAbierta++;
     }

   bool coincideCompraAhora = dentroDemandAhora && breakoutAlcistaVigenteAhora;
   if(coincideCompraAhora && !g_diagCoincideCompraAnterior)
     {
      g_diagCoincidenciasCompra++;
      if(!tendenciaOkCompra)
         g_diagCoincidenciasCompraBloqTendencia++;
      if(!sesionOkAhora)
         g_diagCoincidenciasCompraBloqSesion++;
      if(InpUsarFiltroZonaFresca && g_zonaDemand.tocada)
         g_diagCoincidenciasCompraBloqZonaFresca++;

      bool bloqTendencia  = !tendenciaOkCompra;
      bool bloqZonaFresca = (InpUsarFiltroZonaFresca && g_zonaDemand.tocada);
      if(bloqTendencia && bloqZonaFresca)
         g_diagCompraBloqAmbosFiltros++;
      else if(bloqTendencia)
         g_diagCompraBloqSoloTendencia++;
      else if(bloqZonaFresca)
         g_diagCompraBloqSoloZonaFresca++;
      else
         g_diagCompraSobrevivenAmbosFiltros++;

      if(HayPosicionAbierta())
         g_diagCompraCoincideConPosAbierta++;
     }

   g_diagDentroSupplyAnterior  = dentroSupplyAhora;
   g_diagDentroDemandAnterior  = dentroDemandAhora;
   g_diagCoincideVentaAnterior  = coincideVentaAhora;
   g_diagCoincideCompraAnterior = coincideCompraAhora;
  }

//--- Calcula media y mediana de un array de doubles (usado sólo para el resumen de diagnóstico)
void CalcularMediaYMediana(double &valores[], double &media, double &mediana)
  {
   int n = ArraySize(valores);
   media = 0.0;
   mediana = 0.0;
   if(n == 0)
      return;

   double suma = 0.0;
   for(int i = 0; i < n; i++)
      suma += valores[i];
   media = suma / n;

   double ordenado[];
   ArrayResize(ordenado, n);
   ArrayCopy(ordenado, valores);
   ArraySort(ordenado);
   if(n % 2 == 1)
      mediana = ordenado[n / 2];
   else
      mediana = (ordenado[n / 2 - 1] + ordenado[n / 2]) / 2.0;
  }

//--- Imprime el resumen completo del embudo de diagnóstico (se llama una vez, en OnDeinit)
void ImprimirResumenDiagnostico()
  {
   double mediaSupply, medianaSupply, mediaDemand, medianaDemand;
   CalcularMediaYMediana(g_diagAnchosZonaSupply, mediaSupply, medianaSupply);
   CalcularMediaYMediana(g_diagAnchosZonaDemand, mediaDemand, medianaDemand);

   Print("================ DIAGNÓSTICO: EMBUDO DE ENTRADA (no afecta al trading) ================");
   PrintFormat("Ancho de zona Oferta  ($): media=%.2f  mediana=%.2f  (muestras=%d)", mediaSupply, medianaSupply, ArraySize(g_diagAnchosZonaSupply));
   PrintFormat("Ancho de zona Demanda ($): media=%.2f  mediana=%.2f  (muestras=%d)", mediaDemand, medianaDemand, ArraySize(g_diagAnchosZonaDemand));
   Print("--- Lado VENTA (zona Oferta / breakout bajista) ---");
   PrintFormat("  Breakouts bajistas detectados:                 %d", g_diagBreakoutBajistaDetectado);
   PrintFormat("  Toques de zona Oferta:                         %d", g_diagContactosSupply);
   PrintFormat("    - de esos, en horario de sesión válido:      %d", g_diagContactosSupplyEnSesion);
   PrintFormat("    - de esos, con breakout bajista ya vigente:  %d", g_diagContactosSupplyConBreakout);
   PrintFormat("  Zona + breakout coinciden a la vez:            %d", g_diagCoincidenciasVenta);
   PrintFormat("    - de esas coincidencias, bloqueadas por tendencia:   %d", g_diagCoincidenciasVentaBloqTendencia);
   PrintFormat("    - de esas coincidencias, bloqueadas por sesión:      %d", g_diagCoincidenciasVentaBloqSesion);
   PrintFormat("    - de esas coincidencias, bloqueadas por zona fresca: %d", g_diagCoincidenciasVentaBloqZonaFresca);
   PrintFormat("  [desglose excluyente tendencia/zona fresca sobre %d coincidencias, sin solape]", g_diagCoincidenciasVenta);
   PrintFormat("    - sobreviven tendencia (bloq. o no por zona fresca): %d", g_diagVentaSobrevivenAmbosFiltros + g_diagVentaBloqSoloZonaFresca);
   PrintFormat("    - sobreviven zona fresca (bloq. o no por tendencia): %d", g_diagVentaSobrevivenAmbosFiltros + g_diagVentaBloqSoloTendencia);
   PrintFormat("    - bloqueadas SOLO por tendencia:                     %d", g_diagVentaBloqSoloTendencia);
   PrintFormat("    - bloqueadas SOLO por zona fresca:                   %d", g_diagVentaBloqSoloZonaFresca);
   PrintFormat("    - bloqueadas por AMBOS filtros a la vez:             %d", g_diagVentaBloqAmbosFiltros);
   PrintFormat("    - sobreviven AMBOS filtros:                          %d", g_diagVentaSobrevivenAmbosFiltros);
   PrintFormat("    - [check suma = coincidencias]: %d", g_diagVentaSobrevivenAmbosFiltros + g_diagVentaBloqSoloTendencia + g_diagVentaBloqSoloZonaFresca + g_diagVentaBloqAmbosFiltros);
   PrintFormat("  Coincidencias con una posición ya abierta:           %d", g_diagVentaCoincideConPosAbierta);
   PrintFormat("  Ventas finalmente ejecutadas:                  %d", g_diagVentasEjecutadas);
   Print("--- Lado COMPRA (zona Demanda / breakout alcista) ---");
   PrintFormat("  Breakouts alcistas detectados:                 %d", g_diagBreakoutAlcistaDetectado);
   PrintFormat("  Toques de zona Demanda:                        %d", g_diagContactosDemand);
   PrintFormat("    - de esos, en horario de sesión válido:      %d", g_diagContactosDemandEnSesion);
   PrintFormat("    - de esos, con breakout alcista ya vigente:  %d", g_diagContactosDemandConBreakout);
   PrintFormat("  Zona + breakout coinciden a la vez:            %d", g_diagCoincidenciasCompra);
   PrintFormat("    - de esas coincidencias, bloqueadas por tendencia:   %d", g_diagCoincidenciasCompraBloqTendencia);
   PrintFormat("    - de esas coincidencias, bloqueadas por sesión:      %d", g_diagCoincidenciasCompraBloqSesion);
   PrintFormat("    - de esas coincidencias, bloqueadas por zona fresca: %d", g_diagCoincidenciasCompraBloqZonaFresca);
   PrintFormat("  [desglose excluyente tendencia/zona fresca sobre %d coincidencias, sin solape]", g_diagCoincidenciasCompra);
   PrintFormat("    - sobreviven tendencia (bloq. o no por zona fresca): %d", g_diagCompraSobrevivenAmbosFiltros + g_diagCompraBloqSoloZonaFresca);
   PrintFormat("    - sobreviven zona fresca (bloq. o no por tendencia): %d", g_diagCompraSobrevivenAmbosFiltros + g_diagCompraBloqSoloTendencia);
   PrintFormat("    - bloqueadas SOLO por tendencia:                     %d", g_diagCompraBloqSoloTendencia);
   PrintFormat("    - bloqueadas SOLO por zona fresca:                   %d", g_diagCompraBloqSoloZonaFresca);
   PrintFormat("    - bloqueadas por AMBOS filtros a la vez:             %d", g_diagCompraBloqAmbosFiltros);
   PrintFormat("    - sobreviven AMBOS filtros:                          %d", g_diagCompraSobrevivenAmbosFiltros);
   PrintFormat("    - [check suma = coincidencias]: %d", g_diagCompraSobrevivenAmbosFiltros + g_diagCompraBloqSoloTendencia + g_diagCompraBloqSoloZonaFresca + g_diagCompraBloqAmbosFiltros);
   PrintFormat("  Coincidencias con una posición ya abierta:           %d", g_diagCompraCoincideConPosAbierta);
   PrintFormat("  Compras finalmente ejecutadas:                 %d", g_diagComprasEjecutadas);
   Print("=========================================================================================");
  }

//======================================================================
// MÓDULO 4: LÓGICA DE ENTRADA Y SALIDA
//======================================================================

bool HayPosicionAbierta()
  {
   for(int i = 0; i < PositionsTotal(); i++)
     {
      ulong ticket = PositionGetTicket(i);
      if(ticket == 0) continue;
      if(PositionGetString(POSITION_SYMBOL) != _Symbol) continue;
      if(PositionGetInteger(POSITION_MAGIC) != (long)InpMagicNumber) continue;
      return true;
     }
   return false;
  }

//--- Diagnóstico: devuelve el ticket de la posición propia actualmente abierta (0 si no hay ninguna)
ulong TicketPosicionPropiaActual()
  {
   for(int i = 0; i < PositionsTotal(); i++)
     {
      ulong ticket = PositionGetTicket(i);
      if(ticket == 0) continue;
      if(PositionGetString(POSITION_SYMBOL) != _Symbol) continue;
      if(PositionGetInteger(POSITION_MAGIC) != (long)InpMagicNumber) continue;
      return ticket;
     }
   return 0;
  }

//--- Diagnóstico: detecta cuándo se cierra la posición que se venía trackeando y
//    busca su resultado neto real (profit + swap + comisión) en el histórico, para
//    poder cruzarlo más tarde con el estado de tendencia registrado al abrirla.
//    Sólo lee el histórico de operaciones -- no modifica ninguna posición ni orden.
void ActualizarDiagnosticoCierrePosicion()
  {
   ulong ticketAhora = TicketPosicionPropiaActual();
   bool  hayAhora    = (ticketAhora != 0);

   if(g_diagHabiaPosicionAbiertaAnterior && !hayAhora)
     {
      if(HistorySelectByPosition(g_diagTicketPosicionAnterior))
        {
         double resultadoNeto = 0.0;
         int totalDeals = HistoryDealsTotal();
         for(int i = 0; i < totalDeals; i++)
           {
            ulong dealTicket = HistoryDealGetTicket(i);
            resultadoNeto += HistoryDealGetDouble(dealTicket, DEAL_PROFIT)
                           + HistoryDealGetDouble(dealTicket, DEAL_SWAP)
                           + HistoryDealGetDouble(dealTicket, DEAL_COMMISSION);
           }
         PrintFormat("[DIAG-RESULTADO] ticket=%I64u resultado_neto=%.2f", g_diagTicketPosicionAnterior, resultadoNeto);
        }
     }

   g_diagHabiaPosicionAbiertaAnterior = hayAhora;
   g_diagTicketPosicionAnterior       = ticketAhora;
  }

//--- Intenta ejecutar una venta cuando el precio está en zona de Oferta y hay breakout bajista del RSI
void EvaluarSenalDeVenta()
  {
   double bid = SymbolInfoDouble(_Symbol, SYMBOL_BID);

   // Condición 1: el precio actual entra en la zona de Oferta
   if(!PrecioEnZona(bid, g_zonaSupply))
      return;

   // Condición 1b: filtro de zona fresca -- evita operar zonas ya puestas a prueba antes
   if(InpUsarFiltroZonaFresca && g_zonaSupply.tocada)
      return;

   // Condición 2: ruptura bajista vigente de la línea de picos del RSI
   if(!BreakoutBajistaVigente())
      return;

   // Condición 3: filtro de tendencia macro (evita vender en tendencia alcista de fondo)
   if(!FiltroTendenciaPermiteVenta())
      return;

   // Como máximo un intento de apertura por vela: si trade.Sell() falla (p.ej.
   // "mercado cerrado" fuera de horario), la señal seguía armada y el EA
   // reintentaba en cada tick sin parar hasta que la señal expiraba -- se
   // detectaron cientos de órdenes de venta fallidas seguidas en el backtest.
   datetime velaIntento = iTime(_Symbol, InpTimeframe, 0);
   if(velaIntento == g_ultimaVelaIntentoVenta)
      return;
   g_ultimaVelaIntentoVenta = velaIntento;

   double pip = PipSize();
   double entrada = bid;
   double sl = g_zonaSupply.superior + InpSLBufferPips * pip;
   double distanciaSL = sl - entrada;
   if(distanciaSL <= 0.0)
      return;
   double tp = entrada - distanciaSL * InpRiskRewardRatio;

   double lotes = CalcularLotaje(entrada, sl, ORDER_TYPE_SELL);
   if(lotes <= 0.0)
     {
      Print("No se pudo calcular un lotaje válido para la venta.");
      return;
     }

   // Comprobación de margen antes de enviar la orden: un SL anormalmente
   // cercano al entry puede disparar el lotaje por riesgo% muy por encima
   // de lo que la cuenta puede soportar (bug ya visto en Baseline 1).
   double margenRequeridoVenta;
   if(!OrderCalcMargin(ORDER_TYPE_SELL, _Symbol, lotes, entrada, margenRequeridoVenta))
     {
      Print("No se pudo calcular el margen requerido para la venta.");
      return;
     }
   double margenLibreVenta = AccountInfoDouble(ACCOUNT_MARGIN_FREE);
   if(margenRequeridoVenta > margenLibreVenta)
     {
      PrintFormat("Venta descartada: margen insuficiente para el lotaje calculado (lotes=%.2f, margen requerido=%.2f, margen libre=%.2f).",
                  lotes, margenRequeridoVenta, margenLibreVenta);
      return;
     }

   trade.SetExpertMagicNumber(InpMagicNumber);
   if(trade.Sell(lotes, _Symbol, entrada, sl, tp, "SD_RSI_Venta"))
     {
      g_breakoutBajistaArmado = false; // consumir la señal
      g_slOriginalPosicion = sl;
      g_breakevenAplicado = false;
      g_trailingActivado = false;
      g_cierreParcialAplicado = false;
      g_diagVentasEjecutadas++; // diagnóstico: no afecta al trading
      PrintFormat("VENTA ejecutada: lotes=%.2f entrada=%.2f SL=%.2f TP=%.2f", lotes, entrada, sl, tp);

      // --- Diagnóstico: registrar el estado de tendencia en el momento exacto de la
      //     entrada (independientemente de si InpUsarFiltroTendencia está activo o no),
      //     para poder clasificar después cada operación como a favor/en contra de
      //     tendencia y cruzarlo con su resultado real ---
      double maBufferDiag[];
      ArraySetAsSeries(maBufferDiag, true);
      if(CopyBuffer(g_handleTendenciaMA, 0, 1, 1, maBufferDiag) >= 1)
        {
         double maValorDiag       = maBufferDiag[0];
         double cierreMacroDiag   = iClose(_Symbol, Temporalidad_Liquidez, 1);
         double distanciaDiag     = cierreMacroDiag - maValorDiag; // >0 = precio sobre la MA (régimen alcista)
         bool   favorableTendenciaDiag = (cierreMacroDiag < maValorDiag); // lo que exige FiltroTendenciaPermiteVenta()
         ulong  ticketDiag = TicketPosicionPropiaActual();
         PrintFormat("[DIAG-TENDENCIA] ticket=%I64u lado=VENTA cierreMacro=%.2f MA200=%.2f distancia=%.2f favorable_tendencia=%s",
                     ticketDiag, cierreMacroDiag, maValorDiag, distanciaDiag, favorableTendenciaDiag ? "SI" : "NO");
        }
     }
  }

//--- Intenta ejecutar una compra cuando el precio está en zona de Demanda y hay breakout alcista del RSI
void EvaluarSenalDeCompra()
  {
   double ask = SymbolInfoDouble(_Symbol, SYMBOL_ASK);

   // Condición 1: el precio actual entra en la zona de Demanda
   if(!PrecioEnZona(ask, g_zonaDemand))
      return;

   // Condición 1b: filtro de zona fresca -- evita operar zonas ya puestas a prueba antes
   if(InpUsarFiltroZonaFresca && g_zonaDemand.tocada)
      return;

   // Condición 2: ruptura alcista vigente de la línea de valles del RSI
   if(!BreakoutAlcistaVigente())
      return;

   // Condición 3: filtro de tendencia macro (evita comprar en tendencia bajista de fondo)
   if(!FiltroTendenciaPermiteCompra())
      return;

   // Como máximo un intento de apertura por vela (ver misma nota en EvaluarSenalDeVenta()).
   datetime velaIntento = iTime(_Symbol, InpTimeframe, 0);
   if(velaIntento == g_ultimaVelaIntentoCompra)
      return;
   g_ultimaVelaIntentoCompra = velaIntento;

   double pip = PipSize();
   double entrada = ask;
   double sl = g_zonaDemand.inferior - InpSLBufferPips * pip;
   double distanciaSL = entrada - sl;
   if(distanciaSL <= 0.0)
      return;
   double tp = entrada + distanciaSL * InpRiskRewardRatio;

   double lotes = CalcularLotaje(entrada, sl, ORDER_TYPE_BUY);
   if(lotes <= 0.0)
     {
      Print("No se pudo calcular un lotaje válido para la compra.");
      return;
     }

   // Comprobación de margen antes de enviar la orden (ver misma nota en EvaluarSenalDeVenta()).
   double margenRequeridoCompra;
   if(!OrderCalcMargin(ORDER_TYPE_BUY, _Symbol, lotes, entrada, margenRequeridoCompra))
     {
      Print("No se pudo calcular el margen requerido para la compra.");
      return;
     }
   double margenLibreCompra = AccountInfoDouble(ACCOUNT_MARGIN_FREE);
   if(margenRequeridoCompra > margenLibreCompra)
     {
      PrintFormat("Compra descartada: margen insuficiente para el lotaje calculado (lotes=%.2f, margen requerido=%.2f, margen libre=%.2f).",
                  lotes, margenRequeridoCompra, margenLibreCompra);
      return;
     }

   trade.SetExpertMagicNumber(InpMagicNumber);
   if(trade.Buy(lotes, _Symbol, entrada, sl, tp, "SD_RSI_Compra"))
     {
      g_breakoutAlcistaArmado = false; // consumir la señal
      g_slOriginalPosicion = sl;
      g_breakevenAplicado = false;
      g_trailingActivado = false;
      g_cierreParcialAplicado = false;
      g_diagComprasEjecutadas++; // diagnóstico: no afecta al trading
      PrintFormat("COMPRA ejecutada: lotes=%.2f entrada=%.2f SL=%.2f TP=%.2f", lotes, entrada, sl, tp);

      // --- Diagnóstico: mismo registro de tendencia que en EvaluarSenalDeVenta() ---
      double maBufferDiag[];
      ArraySetAsSeries(maBufferDiag, true);
      if(CopyBuffer(g_handleTendenciaMA, 0, 1, 1, maBufferDiag) >= 1)
        {
         double maValorDiag       = maBufferDiag[0];
         double cierreMacroDiag   = iClose(_Symbol, Temporalidad_Liquidez, 1);
         double distanciaDiag     = cierreMacroDiag - maValorDiag;
         bool   favorableTendenciaDiag = (cierreMacroDiag > maValorDiag); // lo que exige FiltroTendenciaPermiteCompra()
         ulong  ticketDiag = TicketPosicionPropiaActual();
         PrintFormat("[DIAG-TENDENCIA] ticket=%I64u lado=COMPRA cierreMacro=%.2f MA200=%.2f distancia=%.2f favorable_tendencia=%s",
                     ticketDiag, cierreMacroDiag, maValorDiag, distanciaDiag, favorableTendenciaDiag ? "SI" : "NO");
        }
     }
  }

//--- Una vez el precio se ha movido a favor InpBreakevenTriggerR veces la distancia
//    de riesgo original (entrada-SL), mueve el SL al precio de entrada (+/- un
//    pequeño colchón) para que la operación ya no pueda cerrar en pérdida. Usa
//    g_slOriginalPosicion (el SL con el que se abrió) en vez del SL actual, porque
//    tras aplicar el breakeven el SL actual ya no refleja el riesgo original.
void GestionarBreakeven()
  {
   if(!InpUsarBreakeven || g_breakevenAplicado || g_slOriginalPosicion <= 0.0)
      return;

   for(int i = 0; i < PositionsTotal(); i++)
     {
      ulong ticket = PositionGetTicket(i);
      if(ticket == 0) continue;
      if(PositionGetString(POSITION_SYMBOL) != _Symbol) continue;
      if(PositionGetInteger(POSITION_MAGIC) != (long)InpMagicNumber) continue;

      double precioApertura = PositionGetDouble(POSITION_PRICE_OPEN);
      double riesgo = MathAbs(precioApertura - g_slOriginalPosicion);
      if(riesgo <= 0.0)
         return;

      double pip = PipSize();
      double slActual = PositionGetDouble(POSITION_SL);
      double tpActual = PositionGetDouble(POSITION_TP);
      ENUM_POSITION_TYPE tipo = (ENUM_POSITION_TYPE)PositionGetInteger(POSITION_TYPE);

      if(tipo == POSITION_TYPE_BUY)
        {
         double bid = SymbolInfoDouble(_Symbol, SYMBOL_BID);
         double disparo = precioApertura + riesgo * InpBreakevenTriggerR;
         double nuevoSL = precioApertura + InpBreakevenBufferPips * pip;
         if(bid >= disparo && nuevoSL > slActual)
           {
            if(trade.PositionModify(ticket, nuevoSL, tpActual))
              {
               g_breakevenAplicado = true;
               PrintFormat("Breakeven aplicado a la compra #%I64u: SL movido a %.2f", ticket, nuevoSL);
              }
           }
        }
      else if(tipo == POSITION_TYPE_SELL)
        {
         double ask = SymbolInfoDouble(_Symbol, SYMBOL_ASK);
         double disparo = precioApertura - riesgo * InpBreakevenTriggerR;
         double nuevoSL = precioApertura - InpBreakevenBufferPips * pip;
         if(ask <= disparo && (slActual <= 0.0 || nuevoSL < slActual))
           {
            if(trade.PositionModify(ticket, nuevoSL, tpActual))
              {
               g_breakevenAplicado = true;
               PrintFormat("Breakeven aplicado a la venta #%I64u: SL movido a %.2f", ticket, nuevoSL);
              }
           }
        }
      return; // sólo hay una posición gestionada por este EA
     }
  }

//--- Una vez el precio se ha movido a favor InpCierreParcialTriggerR veces el riesgo
//    original (3R por defecto, el mismo nivel que el TP fijo), esta función:
//      1) Si InpUsarCierreParcial está activo, cierra InpCierreParcialPercent% del
//         volumen (50% por defecto) para asegurar la ganancia del ratio 1:3 original.
//      2) Libera el Take Profit fijo del volumen restante (lo pone a 0) y empieza a
//         arrastrar su Stop Loss a una distancia de InpTrailingDistanceR por detrás del
//         precio.
//    Sin esto, toda operación que llegase a superar el TP fijo cerraría siempre en el
//    mismo múltiplo de riesgo por muy fuerte que fuese la tendencia; con el cierre
//    parcial + trailing, la mitad de la ganancia queda asegurada en el objetivo
//    original y la otra mitad puede seguir corriendo mucho más allá de 3R en
//    tendencias fuertes de XAUUSD, sin aumentar el riesgo inicial de la operación.
//    Usa g_slOriginalPosicion (no el SL actual) para medir el múltiplo de riesgo real,
//    igual que GestionarBreakeven().
void GestionarTrailingStop()
  {
   if(!InpUsarTrailingStop || g_slOriginalPosicion <= 0.0)
      return;

   for(int i = 0; i < PositionsTotal(); i++)
     {
      ulong ticket = PositionGetTicket(i);
      if(ticket == 0) continue;
      if(PositionGetString(POSITION_SYMBOL) != _Symbol) continue;
      if(PositionGetInteger(POSITION_MAGIC) != (long)InpMagicNumber) continue;

      double precioApertura = PositionGetDouble(POSITION_PRICE_OPEN);
      double riesgo = MathAbs(precioApertura - g_slOriginalPosicion);
      if(riesgo <= 0.0)
         return;

      double slActual = PositionGetDouble(POSITION_SL);
      double tpActual = PositionGetDouble(POSITION_TP);
      ENUM_POSITION_TYPE tipo = (ENUM_POSITION_TYPE)PositionGetInteger(POSITION_TYPE);

      double precioActual = (tipo == POSITION_TYPE_BUY) ? SymbolInfoDouble(_Symbol, SYMBOL_BID)
                                                          : SymbolInfoDouble(_Symbol, SYMBOL_ASK);
      double currentR = (tipo == POSITION_TYPE_BUY) ? (precioActual - precioApertura) / riesgo
                                                      : (precioApertura - precioActual) / riesgo;

      if(currentR < InpCierreParcialTriggerR)
         return;

      // --- Cierre parcial: se ejecuta una única vez por posición, en cuanto se alcanza
      //     el múltiplo de riesgo objetivo, para asegurar parte de la ganancia al nivel
      //     del TP original antes de liberar el TP y dejar correr el resto con trailing.
      if(InpUsarCierreParcial && !g_cierreParcialAplicado)
        {
         double volumenActual  = PositionGetDouble(POSITION_VOLUME);
         double volStep        = SymbolInfoDouble(_Symbol, SYMBOL_VOLUME_STEP);
         double volMin         = SymbolInfoDouble(_Symbol, SYMBOL_VOLUME_MIN);
         double volumenCerrar  = MathFloor((volumenActual * InpCierreParcialPercent / 100.0) / volStep) * volStep;

         // Sólo cierra parcialmente si queda volumen suficiente a ambos lados (el
         // cerrado y el que sigue abierto) para respetar el mínimo del bróker; si no,
         // se deja correr toda la posición sin cierre parcial.
         if(volumenCerrar >= volMin && (volumenActual - volumenCerrar) >= volMin)
           {
            if(trade.PositionClosePartial(ticket, NormalizeDouble(volumenCerrar, 2)))
              {
               g_cierreParcialAplicado = true;
               PrintFormat("Cierre parcial ejecutado en posición #%I64u: %.2f lotes cerrados en R=%.2f",
                           ticket, volumenCerrar, currentR);
              }
           }
         else
            g_cierreParcialAplicado = true; // volumen insuficiente: no reintentar cada tick
        }

      double nuevoSL = (tipo == POSITION_TYPE_BUY)
                        ? precioApertura + (currentR - InpTrailingDistanceR) * riesgo
                        : precioApertura - (currentR - InpTrailingDistanceR) * riesgo;

      bool liberarTP = !g_trailingActivado && tpActual != 0.0;
      bool mejoraSL  = (tipo == POSITION_TYPE_BUY) ? (nuevoSL > slActual)
                                                     : (slActual <= 0.0 || nuevoSL < slActual);

      if(liberarTP || mejoraSL)
        {
         double slFinal = mejoraSL ? nuevoSL : slActual;
         if(trade.PositionModify(ticket, slFinal, 0.0))
           {
            g_trailingActivado = true;
            PrintFormat("Trailing stop en %s #%I64u: SL=%.2f (R actual=%.2f, TP fijo liberado)",
                        (tipo == POSITION_TYPE_BUY ? "compra" : "venta"), ticket, slFinal, currentR);
           }
        }

      return; // sólo hay una posición gestionada por este EA
     }
  }

//======================================================================
// DETECCIÓN DE VELA NUEVA
//======================================================================

//--- Nueva vela en la temporalidad de EJECUCIÓN (5M): dispara el recálculo del gatillo RSI
bool EsVelaNueva()
  {
   datetime horaVelaActual = iTime(_Symbol, InpTimeframe, 0);
   if(horaVelaActual != g_ultimaVelaProcesada)
     {
      g_ultimaVelaProcesada = horaVelaActual;
      return true;
     }
   return false;
  }

//--- Nueva vela en la temporalidad MACRO (H1/H4): dispara el recálculo de las zonas de liquidez.
//    Se comprueba de forma independiente al timeframe de ejecución, de modo que el escaneo
//    Multi-Timeframe se mantiene "constante" aunque el gráfico donde corre el EA sea de 5 minutos.
bool EsVelaNuevaMacro()
  {
   datetime horaVelaMacroActual = iTime(_Symbol, Temporalidad_Liquidez, 0);
   if(horaVelaMacroActual != g_ultimaVelaMacroProcesada)
     {
      g_ultimaVelaMacroProcesada = horaVelaMacroActual;
      return true;
     }
   return false;
  }

//======================================================================
// EVENTOS DEL EXPERT ADVISOR
//======================================================================
int OnInit()
  {
   g_handleRSI = iRSI(_Symbol, InpTimeframe, InpRSIPeriod, PRICE_CLOSE);
   if(g_handleRSI == INVALID_HANDLE)
     {
      Print("Error al crear el indicador RSI.");
      return(INIT_FAILED);
     }

   g_handleTendenciaMA = iMA(_Symbol, Temporalidad_Liquidez, InpTrendMAPeriod, 0, InpTrendMAMethod, PRICE_CLOSE);
   if(g_handleTendenciaMA == INVALID_HANDLE)
     {
      Print("Error al crear la media móvil del filtro de tendencia.");
      return(INIT_FAILED);
     }

   trade.SetExpertMagicNumber(InpMagicNumber);

   g_zonaSupply.activa      = false;
   g_zonaSupply.huboEntrada = false;
   g_zonaSupply.tocada      = false;
   g_zonaDemand.activa      = false;
   g_zonaDemand.huboEntrada = false;
   g_zonaDemand.tocada      = false;

   g_diaActual = 0; // fuerza la inicialización del día en el primer tick
   GestionarCambioDeDia();

   // Siembra inicial de las zonas macro para no operar sin contexto mientras
   // se espera al cierre de la primera vela de "Temporalidad_Liquidez"
   ActualizarZonasOfertaDemanda();
   g_ultimaVelaMacroProcesada = iTime(_Symbol, Temporalidad_Liquidez, 0);

   return(INIT_SUCCEEDED);
  }

void OnDeinit(const int reason)
  {
   ImprimirResumenDiagnostico();

   if(g_handleRSI != INVALID_HANDLE)
      IndicatorRelease(g_handleRSI);
   if(g_handleTendenciaMA != INVALID_HANDLE)
      IndicatorRelease(g_handleTendenciaMA);
  }

//======================================================================
// CIRCUITO DE PÉRDIDAS CONSECUTIVAS
//======================================================================
// Complementa al Kill Switch del 4%: en vez de esperar a que se acumule
// toda la pérdida diaria permitida, cuenta las pérdidas SEGUIDAS del día
// (se reinicia a 0 en cuanto una operación cierra en positivo) y bloquea
// nuevas entradas en cuanto se alcanza "InpMaxPerdidasConsecutivas",
// mucho antes de llegar al límite diario. No fuerza el cierre de nada
// (cuando se evalúa ya se está plano, tras el cierre que disparó la
// cuenta), simplemente impide abrir la siguiente operación hasta el
// día siguiente.
//
// Se detecta el resultado de cada operación cerrada en OnTradeTransaction,
// el evento nativo de MQL5 para cambios en el historial de trading: cuando
// MetaTrader añade un nuevo deal de cierre (TRADE_TRANSACTION_DEAL_ADD con
// ENTRY_OUT/ENTRY_OUT_BY) de este símbolo y con nuestro número mágico, se
// suma su beneficio/pérdida real (incluyendo swap y comisión) para saber
// si fue ganadora o perdedora.
//----------------------------------------------------------------------
void OnTradeTransaction(const MqlTradeTransaction &trans,
                         const MqlTradeRequest &request,
                         const MqlTradeResult &result)
  {
   if(trans.type != TRADE_TRANSACTION_DEAL_ADD)
      return;

   if(!HistoryDealSelect(trans.deal))
      return;

   if(HistoryDealGetString(trans.deal, DEAL_SYMBOL) != _Symbol)
      return;
   if(HistoryDealGetInteger(trans.deal, DEAL_MAGIC) != (long)InpMagicNumber)
      return;

   ENUM_DEAL_ENTRY tipoEntrada = (ENUM_DEAL_ENTRY)HistoryDealGetInteger(trans.deal, DEAL_ENTRY);
   if(tipoEntrada != DEAL_ENTRY_OUT && tipoEntrada != DEAL_ENTRY_OUT_BY)
      return; // sólo interesan los cierres, no las aperturas

   // Si la posición sigue abierta tras este cierre, fue un cierre PARCIAL (el cierre
   // parcial en el TP original): la posición sigue viva con el resto del volumen, así
   // que no se resetea su estado (SL original, breakeven, trailing) ni cuenta todavía
   // para el circuito de pérdidas consecutivas, que sólo evalúa el resultado final de
   // la operación completa.
   ulong idPosicion = (ulong)HistoryDealGetInteger(trans.deal, DEAL_POSITION_ID);
   if(PositionSelectByTicket(idPosicion))
      return;

   // La posición se cerró por completo: el SL original ya no aplica a ninguna posición viva
   g_slOriginalPosicion = 0.0;
   g_breakevenAplicado = false;
   g_trailingActivado = false;
   g_cierreParcialAplicado = false;

   // Se suma el resultado de TODOS los cierres de esta posición (el cierre parcial en
   // el TP original, si lo hubo, más el cierre final) para clasificar correctamente la
   // operación completa como ganadora o perdedora en el circuito de pérdidas consecutivas.
   double resultado = 0.0;
   if(HistorySelectByPosition(idPosicion))
     {
      int totalDeals = HistoryDealsTotal();
      for(int d = 0; d < totalDeals; d++)
        {
         ulong dealTicket = HistoryDealGetTicket(d);
         if(dealTicket == 0) continue;
         ENUM_DEAL_ENTRY entradaDeal = (ENUM_DEAL_ENTRY)HistoryDealGetInteger(dealTicket, DEAL_ENTRY);
         if(entradaDeal != DEAL_ENTRY_OUT && entradaDeal != DEAL_ENTRY_OUT_BY)
            continue;

         resultado += HistoryDealGetDouble(dealTicket, DEAL_PROFIT)
                    + HistoryDealGetDouble(dealTicket, DEAL_SWAP)
                    + HistoryDealGetDouble(dealTicket, DEAL_COMMISSION);
        }
     }

   if(resultado < 0.0)
     {
      g_perdidasConsecutivasHoy++;
      if(g_perdidasConsecutivasHoy >= InpMaxPerdidasConsecutivas && !g_circuitoPerdidasActivo)
        {
         g_circuitoPerdidasActivo = true;
         PrintFormat("CIRCUITO DE PÉRDIDAS CONSECUTIVAS ACTIVADO: %d pérdidas seguidas hoy (límite %d). Sin nuevas entradas hasta el día siguiente.",
                     g_perdidasConsecutivasHoy, InpMaxPerdidasConsecutivas);
        }
     }
   else
     {
      g_perdidasConsecutivasHoy = 0;
     }
  }

void OnTick()
  {
   // 1) Gestión de cambio de día (referencia para el Kill Switch)
   GestionarCambioDeDia();

   // 2) Kill Switch diario: si ya se activó, no se hace nada más hasta el día siguiente
   ComprobarKillSwitchDiario();
   if(g_killSwitchActivo)
      return;

   // 3) Cierre obligatorio de fin de semana.
   //    Se intenta como máximo una vez por cada vela nueva (no en cada tick):
   //    si el mercado ya cerró para el símbolo, CerrarTodasLasPosiciones()
   //    falla y, sin este límite, el EA reintentaba en cada tick -- se
   //    detectaron cientos de órdenes fallidas seguidas ("Market closed") en
   //    el backtest, sin ningún beneficio, hasta que dejaban de llegar ticks
   //    por el fin de semana.
   if(DebeCerrarPorFinDeSemana())
     {
      datetime velaActual = iTime(_Symbol, InpTimeframe, 0);
      if(velaActual != g_ultimaVelaIntentoCierreFDS)
        {
         g_ultimaVelaIntentoCierreFDS = velaActual;
         if(HayPosicionAbierta())
           {
            Print("Cierre de fin de semana: liquidando posiciones flotantes.");
            CerrarTodasLasPosiciones();
           }
         BorrarTodasLasOrdenesPendientes();
        }
      return;
     }

   // 4a) Al cerrar una nueva vela de la temporalidad MACRO, recalcular las zonas de liquidez (contexto MTF)
   if(EsVelaNuevaMacro())
      ActualizarZonasOfertaDemanda();

   // 4b) Al cerrar una nueva vela de la temporalidad de EJECUCIÓN (5M), recalcular el gatillo RSI
   if(EsVelaNueva())
      ActualizarRSITrendlinesYBreakouts();

   // 4c) Registrar si el precio ha entrado/salido de alguna zona, para el filtro de zona fresca
   MarcarZonasTocadas();

   // 4d) Diagnóstico: solo cuenta condiciones del embudo de entrada, no decide nada
   ActualizarContadoresDiagnostico();
   ActualizarDiagnosticoCierrePosicion();

   // 5) Filtro de spread: prohíbe abrir operaciones si el spread es excesivo
   if(!SpreadPermitido())
      return;

   // 6) Sólo se gestiona una posición simultánea por este EA. Si ya hay una
   //    abierta, no se evalúan nuevas entradas, pero sí se gestiona su breakeven.
   if(HayPosicionAbierta())
     {
      GestionarBreakeven();
      GestionarTrailingStop();
      return;
     }

   // 7) Circuito de pérdidas consecutivas: bloquea nuevas entradas el resto
   //    del día tras InpMaxPerdidasConsecutivas pérdidas seguidas
   if(g_circuitoPerdidasActivo)
      return;

   // 8) Filtro de horario de sesión: sólo abre operaciones nuevas en la franja de
   //    mayor liquidez del oro (una posición ya abierta se sigue gestionando siempre)
   if(!SesionPermiteOperar())
      return;

   // 9) Evaluación de señales de entrada (contexto + gatillo)
   EvaluarSenalDeVenta();
   EvaluarSenalDeCompra();
  }
//+------------------------------------------------------------------+
