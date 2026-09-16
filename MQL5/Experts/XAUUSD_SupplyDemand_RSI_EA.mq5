//+------------------------------------------------------------------+
//|                                XAUUSD_SupplyDemand_RSI_EA.mq5   |
//|   EA para XAUUSD basado en zonas de Oferta/Demanda (contexto)   |
//|   y rupturas de líneas de tendencia sobre el RSI (gatillo).     |
//|   Diseñado con blindaje de riesgo para cuentas de fondeo.       |
//+------------------------------------------------------------------+
#property copyright "Bot Trading"
#property version   "1.00"
#property strict

#include <Trade\Trade.mqh>

//======================================================================
// PARÁMETROS DE ENTRADA
//======================================================================

input group "=== Configuración General ==="
input ulong  InpMagicNumber         = 20250916;   // Número mágico
input ENUM_TIMEFRAMES InpTimeframe  = PERIOD_M5;   // Temporalidad de ejecución / gatillo RSI (5M)

input group "=== Indicador 1: Zonas de Oferta y Demanda (Multi-Timeframe) ==="
input ENUM_TIMEFRAMES Temporalidad_Liquidez = PERIOD_H1; // Temporalidad macro para zonas de liquidez (H1 o H4)
// NOTA: el lookback de las zonas ya NO es un input fijo: es la variable global
// "g_zonaLookbackMacro" (ver más abajo), recalibrada por el módulo de auto-optimización.

input group "=== Indicador 2: RSI Trendlines with Breakouts ==="
// NOTA: el período del RSI ya NO es un input fijo: es la variable global
// "g_rsiPeriod" (ver más abajo), recalibrada por el módulo de auto-optimización.
input int    InpRSITrendLookback    = 150;         // Velas analizadas para localizar pivotes del RSI
input int    InpPivotLeftBars       = 3;           // Barras a la izquierda para confirmar un pivote
input int    InpPivotRightBars      = 3;           // Barras a la derecha para confirmar un pivote
input int    InpSignalValidityBars  = 3;           // Nº de velas que la ruptura del RSI permanece "armada"

input group "=== Gestión de Posición (SL / TP) ==="
input double InpSLBufferPips        = 10.0;        // Colchón del Stop Loss en pips, fuera de la zona
input double InpRiskRewardRatio     = 3.0;         // Ratio Riesgo:Beneficio (1:N)
input double InpManualPipSize       = 0.0;         // Tamaño de pip manual (0 = automático)

input group "=== Blindaje de Riesgo Institucional ==="
input double InpRiskPercent         = 0.5;         // % de riesgo del balance por operación
input double InpMaxDailyLossPercent = 4.0;         // % máximo de pérdida diaria (Kill Switch)
input double InpMaxSpreadPips       = 4.0;         // Spread máximo permitido en pips

input group "=== Cierre de Fin de Semana ==="
input bool   InpCerrarViernes       = true;        // Activar cierre obligatorio de fin de semana
input int    InpFridayCloseHourNY   = 21;          // Hora de Nueva York para liquidar (21:00)
input int    InpBrokerGMTOffsetHrs  = 2;           // Offset del servidor del bróker respecto a UTC (ajustar según bróker)

input group "=== Módulo de Auto-Optimización Walk-Forward (Método 1) ==="
input bool   InpOptimizacionActiva          = true;  // Activar la recalibración semanal automática
input int    InpVelasAnalisisOptimizacion   = 500;   // Nº de velas H1 analizadas para medir volatilidad
input int    InpATRPeriodoOptimizacion      = 14;    // Período del ATR usado en el análisis de volatilidad
input int    InpZonaLookbackVolatilidadAlta = 100;   // Lookback de zonas aplicado si la volatilidad es ALTA
input int    InpRSIPeriodoVolatilidadAlta   = 21;    // Período de RSI aplicado si la volatilidad es ALTA
input int    InpZonaLookbackVolatilidadBaja = 30;    // Lookback de zonas aplicado si la volatilidad es BAJA
input int    InpRSIPeriodoVolatilidadBaja   = 10;    // Período de RSI aplicado si la volatilidad es BAJA

//======================================================================
// VARIABLES GLOBALES
//======================================================================
CTrade         trade;

int            g_handleRSI = INVALID_HANDLE;
datetime       g_ultimaVelaProcesada = 0;      // Última vela procesada en la temporalidad de ejecución (RSI)
datetime       g_ultimaVelaMacroProcesada = 0; // Última vela procesada en la temporalidad macro (zonas)
datetime       g_ultimaVelaH1Procesada = 0;    // Última vela H1 procesada por el módulo de auto-optimización

// --- Parámetros adaptativos: dejan de ser "input" fijos para que el módulo de
//     auto-optimización walk-forward pueda reconfigurarlos dinámicamente ---
int            g_zonaLookbackMacro = 100; // Lookback de las zonas de Oferta/Demanda (temporalidad macro)
int            g_rsiPeriod         = 14;  // Período del RSI

// --- Estado del módulo de auto-optimización walk-forward ---
datetime       ultimaOptimizacion = 0; // Fecha/hora de la última recalibración semanal aplicada

// --- Estructura de una zona de oferta/demanda ---
struct SZona
  {
   double superior;
   double inferior;
   bool   activa;
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

//======================================================================
// UTILIDADES
//======================================================================

//--- Calcula el tamaño de un "pip" para el símbolo actual.
//    En instrumentos de 3 ó 5 decimales, un pip equivale a 10 puntos.
//    En instrumentos de 2 ó 4 decimales, un pip equivale a 1 punto.
double PipSize()
  {
   if(InpManualPipSize > 0.0)
      return InpManualPipSize;

   int digits = (int)SymbolInfoInteger(_Symbol, SYMBOL_DIGITS);
   double point = SymbolInfoDouble(_Symbol, SYMBOL_POINT);

   if(digits == 3 || digits == 5)
      return point * 10.0;

   return point;
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
//  H4) y escanea allí las últimas "g_zonaLookbackMacro" velas (100 por
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
   if(Bars(_Symbol, Temporalidad_Liquidez) < g_zonaLookbackMacro + 1)
      return;

// iHighest/iLowest buscan, dentro de "g_zonaLookbackMacro" velas de la
// temporalidad MACRO, comenzando en la vela cerrada más reciente
// (shift = 1), el índice de la vela con el máximo/mínimo extremo.
   int shiftMax = iHighest(_Symbol, Temporalidad_Liquidez, MODE_HIGH, g_zonaLookbackMacro, 1);
   int shiftMin = iLowest(_Symbol, Temporalidad_Liquidez, MODE_LOW, g_zonaLookbackMacro, 1);

   if(shiftMax < 0 || shiftMin < 0)
      return;

   double highExtremo  = iHigh(_Symbol, Temporalidad_Liquidez, shiftMax);
   double closeDeHigh  = iClose(_Symbol, Temporalidad_Liquidez, shiftMax);

   double lowExtremo   = iLow(_Symbol, Temporalidad_Liquidez, shiftMin);
   double closeDeLow   = iClose(_Symbol, Temporalidad_Liquidez, shiftMin);

// Zona de Oferta (macro): entre el cierre (límite inferior) y el máximo (límite superior)
   g_zonaSupply.superior = highExtremo;
   g_zonaSupply.inferior = closeDeHigh;
   g_zonaSupply.activa   = true;

// Zona de Demanda (macro): entre el mínimo (límite inferior) y el cierre (límite superior)
   g_zonaDemand.inferior = lowExtremo;
   g_zonaDemand.superior = closeDeLow;
   g_zonaDemand.activa   = true;
  }

//--- Comprueba si un precio dado se encuentra dentro de una zona
bool PrecioEnZona(const double precio, const SZona &zona)
  {
   if(!zona.activa)
      return false;
   return (precio >= zona.inferior && precio <= zona.superior);
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
double CalcularLotaje(const double precioEntrada, const double precioSL)
  {
   double balance      = AccountInfoDouble(ACCOUNT_BALANCE);
   double montoRiesgo   = balance * (InpRiskPercent / 100.0);

   double tickValue = SymbolInfoDouble(_Symbol, SYMBOL_TRADE_TICK_VALUE);
   double tickSize  = SymbolInfoDouble(_Symbol, SYMBOL_TRADE_TICK_SIZE);

   if(tickSize <= 0.0 || tickValue <= 0.0)
      return 0.0;

   double distanciaSL = MathAbs(precioEntrada - precioSL);
   if(distanciaSL <= 0.0)
      return 0.0;

// Pérdida monetaria por 1 lote si el precio recorre toda la distancia del SL
   double perdidaPorLote = (distanciaSL / tickSize) * tickValue;
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

//--- Intenta ejecutar una venta cuando el precio está en zona de Oferta y hay breakout bajista del RSI
void EvaluarSenalDeVenta()
  {
   double bid = SymbolInfoDouble(_Symbol, SYMBOL_BID);

   // Condición 1: el precio actual entra en la zona de Oferta
   if(!PrecioEnZona(bid, g_zonaSupply))
      return;

   // Condición 2: ruptura bajista vigente de la línea de picos del RSI
   if(!BreakoutBajistaVigente())
      return;

   double pip = PipSize();
   double entrada = bid;
   double sl = g_zonaSupply.superior + InpSLBufferPips * pip;
   double distanciaSL = sl - entrada;
   if(distanciaSL <= 0.0)
      return;
   double tp = entrada - distanciaSL * InpRiskRewardRatio;

   double lotes = CalcularLotaje(entrada, sl);
   if(lotes <= 0.0)
     {
      Print("No se pudo calcular un lotaje válido para la venta.");
      return;
     }

   trade.SetExpertMagicNumber(InpMagicNumber);
   if(trade.Sell(lotes, _Symbol, entrada, sl, tp, "SD_RSI_Venta"))
     {
      g_breakoutBajistaArmado = false; // consumir la señal
      PrintFormat("VENTA ejecutada: lotes=%.2f entrada=%.2f SL=%.2f TP=%.2f", lotes, entrada, sl, tp);
     }
  }

//--- Intenta ejecutar una compra cuando el precio está en zona de Demanda y hay breakout alcista del RSI
void EvaluarSenalDeCompra()
  {
   double ask = SymbolInfoDouble(_Symbol, SYMBOL_ASK);

   // Condición 1: el precio actual entra en la zona de Demanda
   if(!PrecioEnZona(ask, g_zonaDemand))
      return;

   // Condición 2: ruptura alcista vigente de la línea de valles del RSI
   if(!BreakoutAlcistaVigente())
      return;

   double pip = PipSize();
   double entrada = ask;
   double sl = g_zonaDemand.inferior - InpSLBufferPips * pip;
   double distanciaSL = entrada - sl;
   if(distanciaSL <= 0.0)
      return;
   double tp = entrada + distanciaSL * InpRiskRewardRatio;

   double lotes = CalcularLotaje(entrada, sl);
   if(lotes <= 0.0)
     {
      Print("No se pudo calcular un lotaje válido para la compra.");
      return;
     }

   trade.SetExpertMagicNumber(InpMagicNumber);
   if(trade.Buy(lotes, _Symbol, entrada, sl, tp, "SD_RSI_Compra"))
     {
      g_breakoutAlcistaArmado = false; // consumir la señal
      PrintFormat("COMPRA ejecutada: lotes=%.2f entrada=%.2f SL=%.2f TP=%.2f", lotes, entrada, sl, tp);
     }
  }

//======================================================================
// MÓDULO DE AUTO-OPTIMIZACIÓN WALK-FORWARD (MÉTODO 1)
//======================================================================
// Cada semana, en la primera vela de H1 que abre en domingo o lunes (es
// decir, justo cuando el mercado reabre tras el cierre de fin de
// semana), el EA analiza las últimas "InpVelasAnalisisOptimizacion"
// velas de 1 Hora del símbolo y mide el régimen de volatilidad reciente
// mediante dos indicadores estadísticos:
//
//   1) ATR (Average True Range): se calcula el ATR de cada una de esas
//      velas y se obtienen dos promedios:
//        - "mediaATR"    -> promedio del ATR en TODO el rango analizado
//                           (línea base histórica de volatilidad).
//        - "atrReciente" -> promedio del ATR en las últimas 20 velas
//                           (fotografía de la volatilidad actual).
//   2) Desviación estándar de los precios de cierre del mismo rango,
//      como segunda medida de dispersión/volatilidad del mercado.
//
// Si "atrReciente" supera a "mediaATR", el mercado está en un régimen
// de volatilidad ALTA y el EA amplía el lookback de las zonas de Oferta/
// Demanda (más contexto, zonas más amplias) y el período del RSI (menos
// sensible al ruido). Si no, el mercado está "lento" (volatilidad BAJA)
// y el EA reduce ambos parámetros para reaccionar con mayor agilidad a
// movimientos más pequeños.
//
// Esta recalibración es puramente de PARÁMETROS DE ESTRATEGIA (lookback
// de zonas y período de RSI). NO toca ninguna regla de gestión de
// riesgo: el 0.5% de riesgo por operación, el cálculo de lotaje
// dinámico, el Kill Switch del 4% diario y el cierre de fin de semana
// siguen funcionando exactamente igual, de forma totalmente
// independiente a este módulo.
//----------------------------------------------------------------------

//--- Determina si la vela H1 recién abierta es la primera de la semana de trading
//    (apertura de domingo o lunes, justo tras el cierre del fin de semana).
bool EsPrimeraVelaDeLaSemana(const datetime horaVela)
  {
   MqlDateTime dt;
   TimeToStruct(horaVela, dt);
   return (dt.day_of_week == 0 || dt.day_of_week == 1);
  }

//--- Ejecuta, como máximo una vez por semana, la recalibración walk-forward de estrategia.
void EjecutarOptimizacionSemanal()
  {
   if(!InpOptimizacionActiva)
      return;

   datetime horaVelaH1 = iTime(_Symbol, PERIOD_H1, 0);

   // Sólo se evalúa una vez por cada vela H1 nueva (evita repetir el análisis en cada tick)
   if(horaVelaH1 == g_ultimaVelaH1Procesada)
      return;
   g_ultimaVelaH1Procesada = horaVelaH1;

   if(!EsPrimeraVelaDeLaSemana(horaVelaH1))
      return;

   // Bloqueo semanal: no recalibrar dos veces dentro de la misma semana.
   // Se agrupan las velas en "cubos" de 7 días desde una referencia fija
   // (Epoch), en vez de usar fechas de calendario, para no depender de
   // en qué día exacto abre la semana cada bróker.
   long semanaActual     = (long)(horaVelaH1 / 604800);       // 604800 s = 7 días
   long semanaOptimizada = (long)(ultimaOptimizacion / 604800);
   if(ultimaOptimizacion > 0 && semanaActual == semanaOptimizada)
      return;

   // --- Recolección de datos: últimas InpVelasAnalisisOptimizacion velas cerradas de H1 ---
   int velas = InpVelasAnalisisOptimizacion;
   if(Bars(_Symbol, PERIOD_H1) < velas + InpATRPeriodoOptimizacion + 1)
      return; // histórico insuficiente todavía

   int handleATR = iATR(_Symbol, PERIOD_H1, InpATRPeriodoOptimizacion);
   if(handleATR == INVALID_HANDLE)
      return;

   double atrBuffer[];
   ArraySetAsSeries(atrBuffer, false);
   int copiadosATR = CopyBuffer(handleATR, 0, 1, velas, atrBuffer);
   IndicatorRelease(handleATR);
   if(copiadosATR < velas)
      return;

   double closeBuffer[];
   ArraySetAsSeries(closeBuffer, false);
   if(CopyClose(_Symbol, PERIOD_H1, 1, velas, closeBuffer) < velas)
      return;

   // --- ATR: media histórica del rango completo frente al promedio reciente (últimas 20 velas) ---
   double sumaATR = 0.0;
   for(int i = 0; i < velas; i++)
      sumaATR += atrBuffer[i];
   double mediaATR = sumaATR / velas;

   int velasReciente = MathMin(20, velas);
   double sumaATRReciente = 0.0;
   for(int i = velas - velasReciente; i < velas; i++)
      sumaATRReciente += atrBuffer[i];
   double atrReciente = sumaATRReciente / velasReciente;

   // --- Desviación estándar de los precios de cierre del mismo rango analizado ---
   double sumaClose = 0.0;
   for(int i = 0; i < velas; i++)
      sumaClose += closeBuffer[i];
   double mediaClose = sumaClose / velas;

   double sumaCuadrados = 0.0;
   for(int i = 0; i < velas; i++)
      sumaCuadrados += MathPow(closeBuffer[i] - mediaClose, 2);
   double desviacionEstandar = MathSqrt(sumaCuadrados / velas);

   // --- Clasificación del régimen de volatilidad y recalibración dinámica de la estrategia ---
   bool volatilidadAlta = (atrReciente > mediaATR);

   if(volatilidadAlta)
     {
      g_zonaLookbackMacro = InpZonaLookbackVolatilidadAlta;
      g_rsiPeriod         = InpRSIPeriodoVolatilidadAlta;
     }
   else
     {
      g_zonaLookbackMacro = InpZonaLookbackVolatilidadBaja;
      g_rsiPeriod         = InpRSIPeriodoVolatilidadBaja;
     }

   // El período del RSI pudo haber cambiado: hay que recrear su handle de indicador
   if(g_handleRSI != INVALID_HANDLE)
      IndicatorRelease(g_handleRSI);
   g_handleRSI = iRSI(_Symbol, InpTimeframe, g_rsiPeriod, PRICE_CLOSE);

   ultimaOptimizacion = horaVelaH1;

   PrintFormat("AUTO-OPTIMIZACIÓN SEMANAL: volatilidad %s (ATR reciente=%.2f, ATR medio=%.2f, desv.est.=%.2f) -> Lookback zonas=%d, Período RSI=%d",
               volatilidadAlta ? "ALTA" : "BAJA", atrReciente, mediaATR, desviacionEstandar,
               g_zonaLookbackMacro, g_rsiPeriod);
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
   g_handleRSI = iRSI(_Symbol, InpTimeframe, g_rsiPeriod, PRICE_CLOSE);
   if(g_handleRSI == INVALID_HANDLE)
     {
      Print("Error al crear el indicador RSI.");
      return(INIT_FAILED);
     }

   trade.SetExpertMagicNumber(InpMagicNumber);

   g_zonaSupply.activa = false;
   g_zonaDemand.activa = false;

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
   if(g_handleRSI != INVALID_HANDLE)
      IndicatorRelease(g_handleRSI);
  }

void OnTick()
  {
   // 1) Auto-optimización walk-forward: revisa al inicio de cada vela si toca
   //    recalibrar (sólo se ejecuta de verdad una vez por semana). Es un ajuste
   //    de parámetros de estrategia, independiente de la gestión de riesgo.
   EjecutarOptimizacionSemanal();

   // 2) Gestión de cambio de día (referencia para el Kill Switch)
   GestionarCambioDeDia();

   // 3) Kill Switch diario: si ya se activó, no se hace nada más hasta el día siguiente
   ComprobarKillSwitchDiario();
   if(g_killSwitchActivo)
      return;

   // 4) Cierre obligatorio de fin de semana
   if(DebeCerrarPorFinDeSemana())
     {
      if(HayPosicionAbierta())
        {
         Print("Cierre de fin de semana: liquidando posiciones flotantes.");
         CerrarTodasLasPosiciones();
        }
      BorrarTodasLasOrdenesPendientes();
      return;
     }

   // 5a) Al cerrar una nueva vela de la temporalidad MACRO, recalcular las zonas de liquidez (contexto MTF)
   if(EsVelaNuevaMacro())
      ActualizarZonasOfertaDemanda();

   // 5b) Al cerrar una nueva vela de la temporalidad de EJECUCIÓN (5M), recalcular el gatillo RSI
   if(EsVelaNueva())
      ActualizarRSITrendlinesYBreakouts();

   // 6) Filtro de spread: prohíbe abrir operaciones si el spread es excesivo
   if(!SpreadPermitido())
      return;

   // 7) Sólo se gestiona una posición simultánea por este EA
   if(HayPosicionAbierta())
      return;

   // 8) Evaluación de señales de entrada (contexto + gatillo)
   EvaluarSenalDeVenta();
   EvaluarSenalDeCompra();
  }
//+------------------------------------------------------------------+
