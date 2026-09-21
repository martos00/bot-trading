//+------------------------------------------------------------------+
//|                                XAUUSD_SupplyDemand_RSI_EA.mq5   |
//|   Estrategia: LIQUIDITY SWEEP -> MARKET STRUCTURE SHIFT (MSS)   |
//|   -> FAIR VALUE GAP (FVG) RETEST, sobre XAUUSD.                 |
//|   La gestión de riesgo, ejecución y position management se     |
//|   mantienen sin cambios respecto a la versión anterior del EA. |
//+------------------------------------------------------------------+
#property copyright "Bot Trading"
#property version   "2.00"
#property strict

#include <Trade\Trade.mqh>

//======================================================================
// PARÁMETROS DE ENTRADA
//======================================================================

input group "=== Configuración General ==="
input ulong  InpMagicNumber             = 20250916;   // Número mágico
input ENUM_TIMEFRAMES InpTimeframeEntrada = PERIOD_M15; // Temporalidad de detección de liquidez/sweep/MSS/FVG/entrada
input ENUM_TIMEFRAMES InpTimeframeRegimen = PERIOD_H4;  // Temporalidad del régimen de tendencia principal

input group "=== Régimen de Mercado (H4) ==="
input int    InpEMARegimenPeriod        = 200;        // Período de la EMA de régimen en H4
input int    InpRegimenSwingBars        = 2;          // Velas a cada lado para confirmar swings de estructura en H4
input int    InpRegimenSwingsAConfirmar = 2;          // Nº de HH/HL (o LH/LL) consecutivos exigidos
input int    InpRegimenHistorialBarras  = 60;         // Velas H4 escaneadas hacia atrás para localizar esos swings

input group "=== Detección de Liquidez (M15) ==="
input int    InpSwingLeftBars           = 5;          // Velas a la izquierda para confirmar un swing
input int    InpSwingRightBars          = 5;          // Velas a la derecha para confirmar un swing
input double InpEqualToleranceATRMult   = 0.10;       // Tolerancia equal high/low, en múltiplos de ATR
input double InpZonaAgrupamientoATRMult = 0.15;       // Distancia máxima para fusionar zonas de liquidez próximas
input int    InpAsiaInicioHoraNY        = 19;         // Inicio de la sesión asiática (hora de Nueva York, día anterior)
input int    InpAsiaFinHoraNY           = 3;          // Fin de la sesión asiática (hora de Nueva York)
input int    InpSwingHistorialBarras    = 300;        // Velas M15 escaneadas hacia atrás para localizar swings

input group "=== Liquidity Sweep ==="
input int    InpATRPeriod               = 14;         // Período del ATR (en InpTimeframeEntrada)
input double InpMaxSweepDistanceATRMult = 0.5;        // Penetración máxima permitida, en múltiplos de ATR
input int    InpImportanciaMinimaZona   = 2;          // Importancia mínima de zona para considerar el sweep (2=Swing, 3=Asia, 4=Equal/PDH-PDL, 5=PWH/PWL)

input group "=== Market Structure Shift (MSS) / Timeout del Setup ==="
input int    InpSetupMaxBarras          = 48;         // Velas máximas para completar sweep -> MSS -> FVG -> retest

input group "=== Fair Value Gap (FVG) ==="
input bool   InpUsarFiltroFVGMinimo     = true;       // Ignorar FVG demasiado pequeños respecto al ATR
input double InpFVGMinSizeATRMult       = 0.10;       // Tamaño mínimo del FVG, en múltiplos de ATR

input group "=== Entrada ==="
input double InpFVGEntryPercent         = 50.0;       // % de profundidad del FVG para la entrada (25/50/75/100)

input group "=== Stop Loss ==="
input double InpSLBufferATRMult         = 0.2;        // Colchón del SL más allá del extremo del sweep, en múltiplos de ATR

input group "=== Take Profit ==="
enum ENUM_MODO_TP
  {
   MODO_TP_FIJO_RR          = 0, // MODE A: TP fijo en InpFixedRR
   MODO_TP_SIGUIENTE_LIQUIDEZ = 1 // MODE B: TP dinámico en la siguiente liquidity zone relevante
  };
input ENUM_MODO_TP InpModoTP            = MODO_TP_FIJO_RR;
input double InpFixedRR                 = 2.0;        // R:R fijo del Modo A (debe ser >= InpMinimumRR)
input double InpMinimumRR               = 2.0;        // RR mínimo exigido para aceptar la operación

input group "=== Position Sizing ==="
input double InpRiskPercent             = 0.5;        // % de riesgo del balance por operación (0.25/0.50/0.75/1.00)

input group "=== Límites de Operaciones ==="
input int    InpMaxOperacionesPorSesion = 2;          // Máximo de operaciones por sesión (sesión = día de trading del servidor)

input group "=== Gestión de Posición (Breakeven / Trailing / Cierre Parcial) ==="
input bool   InpUsarBreakeven           = true;       // Mover el SL a breakeven cuando la operación vaya a favor
input double InpBreakevenTriggerR       = 1.5;        // Múltiplo de riesgo (R) para activar el breakeven
input double InpBreakevenBufferPips     = 2.0;        // Colchón en pips sobre el precio de entrada al mover a breakeven
input bool   InpUsarTrailingStop        = true;       // Liberar el TP fijo y arrastrar el SL en tendencias fuertes
input double InpCierreParcialTriggerR   = 3.0;        // Múltiplo de riesgo (R) al que se dispara el cierre parcial
input double InpTrailingDistanceR       = 1.0;        // Distancia del trailing stop por detrás del precio, en múltiplos de R
input bool   InpUsarCierreParcial       = true;       // Cerrar parcialmente en el disparo y dejar correr sólo el resto
input double InpCierreParcialPercent    = 50.0;       // % del volumen a cerrar en el disparo del cierre parcial
input double InpManualPipSize           = 0.0;        // Tamaño de pip manual (0 = automático, 0.10 para oro)

input group "=== Blindaje de Riesgo Institucional ==="
input double InpMaxDailyLossPercent     = 4.0;        // % máximo de pérdida diaria (Kill Switch)
input double InpMaxSpreadPips           = 4.0;        // Spread máximo permitido en pips
input int    InpMaxPerdidasConsecutivas = 3;          // Nº de pérdidas seguidas en el día que bloquean nuevas entradas

input group "=== Filtro de Horario de Sesión ==="
input bool   InpUsarFiltroSesion        = true;       // Sólo buscar sweeps nuevos en la franja de mayor liquidez
input int    InpSesionInicioHoraNY      = 2;          // Hora de inicio (hora de Nueva York): killzone de Londres
input int    InpSesionFinHoraNY         = 17;         // Hora de fin (hora de Nueva York): cierre de la sesión de NY

input group "=== Cierre de Fin de Semana ==="
input bool   InpCerrarViernes           = true;       // Activar cierre obligatorio de fin de semana
input int    InpFridayCloseHourNY       = 21;         // Hora de Nueva York para liquidar (21:00)
input int    InpBrokerGMTOffsetHrs      = 2;          // Offset del servidor del bróker respecto a UTC

input group "=== Registro de Operaciones (CSV) ==="
input bool   InpRegistrarCSV            = true;       // Escribir un log CSV detallado de cada operación cerrada
input string InpNombreArchivoCSV        = "LiquiditySweepMSS_FVG_Log.csv"; // Nombre del archivo (carpeta MQL5\Files)

//======================================================================
// VARIABLES GLOBALES
//======================================================================
CTrade         trade;

int            g_handleEMARegimen = INVALID_HANDLE;
int            g_handleATR        = INVALID_HANDLE;

datetime       g_ultimaVelaEntradaProcesada = 0;
datetime       g_ultimaVelaRegimenProcesada = 0;
datetime       g_ultimaVelaIntentoCierreFDS = 0;

//--- Régimen de mercado (H4)
enum ENUM_REGIMEN { REGIMEN_INDEFINIDO = 0, REGIMEN_ALCISTA = 1, REGIMEN_BAJISTA = 2 };
ENUM_REGIMEN   g_regimenActual = REGIMEN_INDEFINIDO;

//--- Sesión asiática (recalculada una vez por día de servidor)
double         g_asiaHigh = 0.0;
double         g_asiaLow  = 0.0;
datetime       g_asiaCalculadaParaDia = 0;

//--- Kill Switch / cambio de día / circuito de pérdidas / límite de operaciones por sesión
datetime       g_diaActual         = 0;
double         g_balanceInicioDia  = 0.0;
bool           g_killSwitchActivo  = false;
int            g_perdidasConsecutivasHoy = 0;
bool           g_circuitoPerdidasActivo  = false;
int            g_operacionesHoy    = 0;

//--- Tipos y puntuación de importancia de las liquidity zones
enum ENUM_TIPO_ZONA
  {
   ZONA_PWH, ZONA_PWL, ZONA_PDH, ZONA_PDL,
   ZONA_ASIA_HIGH, ZONA_ASIA_LOW,
   ZONA_SWING_HIGH, ZONA_SWING_LOW,
   ZONA_EQUAL_HIGH, ZONA_EQUAL_LOW
  };

struct SLiquidityZone
  {
   double         nivel;
   ENUM_TIPO_ZONA tipo;
   int            importancia;
  };

SLiquidityZone g_zonasBuySide[];   // liquidez por ENCIMA del precio (highs): se barre en setups SHORT
SLiquidityZone g_zonasSellSide[];  // liquidez por DEBAJO del precio (lows):  se barre en setups LONG

//--- Máquina de estados del setup Sweep -> MSS -> FVG -> Retest (un único setup activo a la vez)
enum ENUM_ESTADO_SETUP { SETUP_NINGUNO, SETUP_SWEEP_DETECTADO, SETUP_MSS_CONFIRMADO, SETUP_FVG_LISTO };

struct SSetupActivo
  {
   ENUM_ESTADO_SETUP estado;
   bool           esLong;
   double         precioSweep;         // extremo alcanzado por el sweep (low en LONG, high en SHORT)
   double         sweepDistancia;      // penetración más allá de la zona, en precio
   ENUM_TIPO_ZONA tipoZonaSweep;
   double         nivelZonaSweep;
   int            importanciaZonaSweep;
   datetime       sweepTime;
   double         mssLevel;
   double         fvgSuperior;
   double         fvgInferior;
   double         entradaObjetivo;
   double         slPlan;
   double         tpPlan;
   double         rrPlan;
   ulong          ticketPendiente;
   ENUM_REGIMEN   regimenEnSweep;
  };
SSetupActivo   g_setup;

//--- Estado de la posición actualmente gestionada (heredado sin cambios)
double         g_slOriginalPosicion    = 0.0;
bool           g_breakevenAplicado     = false;
bool           g_trailingActivado      = false;
bool           g_cierreParcialAplicado = false;

//--- Datos del setup que originó la posición abierta, para el log CSV al cerrarla
struct SDatosOperacionLog
  {
   datetime       horaApertura;
   bool           esLong;
   ENUM_TIPO_ZONA tipoZonaSweep;
   int            importanciaZonaSweep;
   double         precioSweep;
   double         sweepDistancia;
   double         mssLevel;
   double         fvgSuperior;
   double         fvgInferior;
   double         precioEntrada;
   double         sl;
   double         tp;
   double         rrPlan;
   ENUM_REGIMEN   regimen;
   double         riesgoMonetarioPlan;
   double         equityMinimaDurante;
  };
SDatosOperacionLog g_logOperacionActiva;
bool               g_hayLogOperacionActiva = false;

//======================================================================
// UTILIDADES (heredadas sin cambios)
//======================================================================

//--- Calcula el tamaño de un "pip" para XAUUSD (convención de mercado: 0.10)
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

//--- ATR más reciente CERRADO (shift=1) en la temporalidad de entrada
double ATRActual()
  {
   double buf[];
   ArraySetAsSeries(buf, true);
   if(CopyBuffer(g_handleATR, 0, 1, 1, buf) < 1)
      return 0.0;
   return buf[0];
  }

//======================================================================
// MÓDULO 1: SWINGS DE ESTRUCTURA (genérico, reutilizado para régimen H4,
// zonas de liquidez M15 y localización del swing previo al MSS)
//======================================================================
// Un swing high en la barra "shift" sólo se considera CONFIRMADO cuando ya
// han cerrado "rightBars" velas después de él -- por eso el barrido empieza
// en shift = 1+rightBars (shift=1 es la última vela cerrada) y nunca usa
// información de velas aún no formadas. Devuelve los swings ordenados del
// más reciente al más antiguo.
//----------------------------------------------------------------------
// NOTA: "barrasEscaneo" y "maxSwings" son conceptos independientes -- el primero
// determina hasta dónde se retrocede en el historial buscando candidatos, el
// segundo cuántos swings confirmados como máximo se devuelven (puede cortar antes
// de agotar barrasEscaneo). Antes de esta corrección compartían un único parámetro,
// lo que en ActualizarRegimen() (que sólo pedía 3 swings) limitaba el escaneo a
// apenas ~4 velas en H4 -- prácticamente imposible de que aparecieran 3 swings
// confirmados ahí, dejando el régimen permanentemente INDEFINIDO.
int RecopilarSwingHighs(const ENUM_TIMEFRAMES tf, const int leftBars, const int rightBars,
                         const int barrasEscaneo, const int maxSwings, datetime &tiempos[], double &valores[])
  {
   ArrayResize(tiempos, 0);
   ArrayResize(valores, 0);

   int disponibles = Bars(_Symbol, tf);
   int limiteShift = MathMin(barrasEscaneo + leftBars + rightBars + 1, disponibles - 1);
   if(limiteShift <= leftBars + rightBars)
      return 0;

   int contador = 0;
   for(int shift = 1 + rightBars; shift <= limiteShift - leftBars && contador < maxSwings; shift++)
     {
      double centro = iHigh(_Symbol, tf, shift);
      bool esSwing = true;
      for(int k = 1; k <= leftBars && esSwing; k++)
         if(iHigh(_Symbol, tf, shift + k) > centro) esSwing = false;
      for(int k = 1; k <= rightBars && esSwing; k++)
         if(iHigh(_Symbol, tf, shift - k) > centro) esSwing = false;

      if(esSwing)
        {
         int n = ArraySize(tiempos);
         ArrayResize(tiempos, n + 1);
         ArrayResize(valores, n + 1);
         tiempos[n] = iTime(_Symbol, tf, shift);
         valores[n] = centro;
         contador++;
        }
     }
   return ArraySize(tiempos);
  }

int RecopilarSwingLows(const ENUM_TIMEFRAMES tf, const int leftBars, const int rightBars,
                        const int barrasEscaneo, const int maxSwings, datetime &tiempos[], double &valores[])
  {
   ArrayResize(tiempos, 0);
   ArrayResize(valores, 0);

   int disponibles = Bars(_Symbol, tf);
   int limiteShift = MathMin(barrasEscaneo + leftBars + rightBars + 1, disponibles - 1);
   if(limiteShift <= leftBars + rightBars)
      return 0;

   int contador = 0;
   for(int shift = 1 + rightBars; shift <= limiteShift - leftBars && contador < maxSwings; shift++)
     {
      double centro = iLow(_Symbol, tf, shift);
      bool esSwing = true;
      for(int k = 1; k <= leftBars && esSwing; k++)
         if(iLow(_Symbol, tf, shift + k) < centro) esSwing = false;
      for(int k = 1; k <= rightBars && esSwing; k++)
         if(iLow(_Symbol, tf, shift - k) < centro) esSwing = false;

      if(esSwing)
        {
         int n = ArraySize(tiempos);
         ArrayResize(tiempos, n + 1);
         ArrayResize(valores, n + 1);
         tiempos[n] = iTime(_Symbol, tf, shift);
         valores[n] = centro;
         contador++;
        }
     }
   return ArraySize(tiempos);
  }

//======================================================================
// MÓDULO 2: RÉGIMEN DE MERCADO (H4)
//======================================================================
// Alcista: cierre H4 > EMA200 H4 Y los últimos InpRegimenSwingsAConfirmar
// swing highs son crecientes (HH) Y los últimos swing lows son crecientes
// (HL). Bajista: análogo con cierre < EMA200 y swings decrecientes
// (LH/LL). Si no hay swings suficientes o la estructura es mixta, régimen
// INDEFINIDO -- y con él, no se buscan setups nuevos (regla explícita del
// punto 2 del encargo).
//----------------------------------------------------------------------
string NombreRegimen(const ENUM_REGIMEN r); // definida en el módulo de log CSV, más abajo

void ActualizarRegimen()
  {
   double emaBuf[];
   ArraySetAsSeries(emaBuf, true);
   if(CopyBuffer(g_handleEMARegimen, 0, 1, 1, emaBuf) < 1)
     {
      g_regimenActual = REGIMEN_INDEFINIDO;
      return;
     }
   double cierre = iClose(_Symbol, InpTimeframeRegimen, 1);
   bool porEncimaEMA = (cierre > emaBuf[0]);
   bool porDebajoEMA = (cierre < emaBuf[0]);

   int necesarios = InpRegimenSwingsAConfirmar + 1;
   datetime tH[], tL[];
   double   vH[], vL[];
   int nH = RecopilarSwingHighs(InpTimeframeRegimen, InpRegimenSwingBars, InpRegimenSwingBars,
                                 InpRegimenHistorialBarras, necesarios, tH, vH);
   int nL = RecopilarSwingLows(InpTimeframeRegimen, InpRegimenSwingBars, InpRegimenSwingBars,
                                InpRegimenHistorialBarras, necesarios, tL, vL);

   if(nH < necesarios || nL < necesarios)
     {
      g_regimenActual = REGIMEN_INDEFINIDO;
      return;
     }

   // vH[0]/vL[0] son los más recientes; para HH/HL cada uno debe ser mayor
   // que el siguiente más antiguo (índices crecientes = más atrás en el tiempo).
   bool hhCrecientes = true, hlCrecientes = true;
   bool lhDecrecientes = true, llDecrecientes = true;
   for(int i = 0; i < InpRegimenSwingsAConfirmar; i++)
     {
      if(!(vH[i] > vH[i + 1])) hhCrecientes = false;
      if(!(vL[i] > vL[i + 1])) hlCrecientes = false;
      if(!(vH[i] < vH[i + 1])) lhDecrecientes = false;
      if(!(vL[i] < vL[i + 1])) llDecrecientes = false;
     }

   ENUM_REGIMEN nuevoRegimen;
   if(porEncimaEMA && hhCrecientes && hlCrecientes)
      nuevoRegimen = REGIMEN_ALCISTA;
   else if(porDebajoEMA && lhDecrecientes && llDecrecientes)
      nuevoRegimen = REGIMEN_BAJISTA;
   else
      nuevoRegimen = REGIMEN_INDEFINIDO;

   if(nuevoRegimen != g_regimenActual)
      PrintFormat("[DIAG] Régimen H4 cambia de %s a %s (cierre=%.2f EMA=%.2f)",
                  NombreRegimen(g_regimenActual), NombreRegimen(nuevoRegimen), cierre, emaBuf[0]);
   g_regimenActual = nuevoRegimen;
  }

//======================================================================
// MÓDULO 3: SESIÓN ASIÁTICA (Asia High / Asia Low)
//======================================================================
// Se recalcula una vez por día de servidor, escaneando velas M15 cerradas
// hacia atrás hasta cubrir el bloque [InpAsiaInicioHoraNY, InpAsiaFinHoraNY)
// más reciente y completo (en hora de Nueva York). Tope de 200 velas
// (~50h) para evitar bucles largos si el rango horario está mal configurado.
//----------------------------------------------------------------------
datetime ConvertirServidorANuevaYork(const datetime tiempoServidor);
bool     EsHorarioDeVeranoUSA(const datetime tiempoUTC);

void ActualizarAsiaHighLow()
  {
   MqlDateTime dtHoy;
   TimeToStruct(TimeCurrent(), dtHoy);
   dtHoy.hour = 0; dtHoy.min = 0; dtHoy.sec = 0;
   datetime hoy00 = StructToTime(dtHoy);
   if(hoy00 == g_asiaCalculadaParaDia)
      return;

   double maxH = -DBL_MAX, minL = DBL_MAX;
   bool   dentroDelBloque = false, bloqueEncontrado = false;
   int    tope = 200;

   for(int shift = 1; shift <= tope; shift++)
     {
      datetime tVela = iTime(_Symbol, InpTimeframeEntrada, shift);
      if(tVela == 0) break;
      datetime horaNY = ConvertirServidorANuevaYork(tVela);
      MqlDateTime dtVela;
      TimeToStruct(horaNY, dtVela);

      bool enVentana;
      if(InpAsiaInicioHoraNY > InpAsiaFinHoraNY)
         enVentana = (dtVela.hour >= InpAsiaInicioHoraNY || dtVela.hour < InpAsiaFinHoraNY);
      else
         enVentana = (dtVela.hour >= InpAsiaInicioHoraNY && dtVela.hour < InpAsiaFinHoraNY);

      if(enVentana)
        {
         dentroDelBloque = true;
         bloqueEncontrado = true;
         double h = iHigh(_Symbol, InpTimeframeEntrada, shift);
         double l = iLow(_Symbol, InpTimeframeEntrada, shift);
         if(h > maxH) maxH = h;
         if(l < minL) minL = l;
        }
      else if(dentroDelBloque)
        {
         // ya recorrimos el bloque contiguo más reciente; al salir de la
         // ventana horaria, el bloque está completo
         break;
        }
     }

   if(bloqueEncontrado)
     {
      g_asiaHigh = maxH;
      g_asiaLow  = minL;
      g_asiaCalculadaParaDia = hoy00;
     }
  }

//======================================================================
// MÓDULO 4: CONSTRUCCIÓN DE LIQUIDITY ZONES
//======================================================================
// Reúne PWH/PWL, PDH/PDL, Asia High/Low, swing highs/lows y equal highs/
// lows de M15 en dos listas (buy-side / sell-side), con su puntuación de
// importancia, fusionando zonas del mismo lado que caigan dentro de
// InpZonaAgrupamientoATRMult*ATR entre sí (se conserva la de mayor
// importancia).
//----------------------------------------------------------------------
void AgregarZona(SLiquidityZone &lista[], const double nivel, const ENUM_TIPO_ZONA tipo,
                  const int importancia, const double distanciaAgrupamiento)
  {
   int n = ArraySize(lista);
   for(int i = 0; i < n; i++)
     {
      if(MathAbs(lista[i].nivel - nivel) <= distanciaAgrupamiento)
        {
         if(importancia > lista[i].importancia)
           {
            lista[i].nivel       = nivel;
            lista[i].tipo        = tipo;
            lista[i].importancia = importancia;
           }
         return; // fusionada con una zona existente próxima
        }
     }
   ArrayResize(lista, n + 1);
   lista[n].nivel       = nivel;
   lista[n].tipo        = tipo;
   lista[n].importancia = importancia;
  }

void ReconstruirZonasLiquidez()
  {
   ArrayResize(g_zonasBuySide, 0);
   ArrayResize(g_zonasSellSide, 0);

   double atr = ATRActual();
   if(atr <= 0.0)
      return;
   double distAgrupamiento = InpZonaAgrupamientoATRMult * atr;
   double toleranciaEqual  = InpEqualToleranceATRMult * atr;

   // --- Previous Week High/Low (semana W1 ya cerrada, shift=1) ---
   if(Bars(_Symbol, PERIOD_W1) > 1)
     {
      AgregarZona(g_zonasBuySide,  iHigh(_Symbol, PERIOD_W1, 1), ZONA_PWH, 5, distAgrupamiento);
      AgregarZona(g_zonasSellSide, iLow(_Symbol,  PERIOD_W1, 1), ZONA_PWL, 5, distAgrupamiento);
     }

   // --- Previous Day High/Low (día D1 ya cerrado, shift=1) ---
   if(Bars(_Symbol, PERIOD_D1) > 1)
     {
      AgregarZona(g_zonasBuySide,  iHigh(_Symbol, PERIOD_D1, 1), ZONA_PDH, 4, distAgrupamiento);
      AgregarZona(g_zonasSellSide, iLow(_Symbol,  PERIOD_D1, 1), ZONA_PDL, 4, distAgrupamiento);
     }

   // --- Asia High/Low ---
   if(g_asiaHigh > 0.0 && g_asiaLow > 0.0)
     {
      AgregarZona(g_zonasBuySide,  g_asiaHigh, ZONA_ASIA_HIGH, 3, distAgrupamiento);
      AgregarZona(g_zonasSellSide, g_asiaLow,  ZONA_ASIA_LOW,  3, distAgrupamiento);
     }

   // --- Swing highs/lows + Equal highs/lows (clustering por tolerancia ATR) ---
   datetime tH[], tL[];
   double   vH[], vL[];
   int nH = RecopilarSwingHighs(InpTimeframeEntrada, InpSwingLeftBars, InpSwingRightBars,
                                 InpSwingHistorialBarras, InpSwingHistorialBarras, tH, vH);
   int nL = RecopilarSwingLows(InpTimeframeEntrada, InpSwingLeftBars, InpSwingRightBars,
                                InpSwingHistorialBarras, InpSwingHistorialBarras, tL, vL);

   bool esEqualH[];
   ArrayResize(esEqualH, nH);
   for(int i = 0; i < nH; i++) esEqualH[i] = false;
   for(int i = 0; i < nH; i++)
      for(int j = i + 1; j < nH; j++)
         if(MathAbs(vH[i] - vH[j]) <= toleranciaEqual)
           { esEqualH[i] = true; esEqualH[j] = true; }

   bool esEqualL[];
   ArrayResize(esEqualL, nL);
   for(int i = 0; i < nL; i++) esEqualL[i] = false;
   for(int i = 0; i < nL; i++)
      for(int j = i + 1; j < nL; j++)
         if(MathAbs(vL[i] - vL[j]) <= toleranciaEqual)
           { esEqualL[i] = true; esEqualL[j] = true; }

   for(int i = 0; i < nH; i++)
      AgregarZona(g_zonasBuySide, vH[i], esEqualH[i] ? ZONA_EQUAL_HIGH : ZONA_SWING_HIGH,
                  esEqualH[i] ? 4 : 2, distAgrupamiento);

   for(int i = 0; i < nL; i++)
      AgregarZona(g_zonasSellSide, vL[i], esEqualL[i] ? ZONA_EQUAL_LOW : ZONA_SWING_LOW,
                  esEqualL[i] ? 4 : 2, distAgrupamiento);
  }

//======================================================================
// MÓDULO 5: LIQUIDITY SWEEP
//======================================================================
// Sweep de una sola vela CERRADA: la mecha penetra la zona una distancia
// limitada (<= InpMaxSweepDistanceATRMult*ATR) y el CIERRE de esa misma
// vela vuelve a quedar del lado seguro de la zona. Esto exige interacción
// real con una liquidity zone ya identificada (no cualquier mecha).
//----------------------------------------------------------------------
bool BuscarSweepSellSide(double &precioSweep, double &distancia, ENUM_TIPO_ZONA &tipoZona,
                          double &nivelZona, int &importanciaZona)
  {
   double atr = ATRActual();
   if(atr <= 0.0) return false;
   double maxDist = InpMaxSweepDistanceATRMult * atr;

   double low1   = iLow(_Symbol, InpTimeframeEntrada, 1);
   double close1 = iClose(_Symbol, InpTimeframeEntrada, 1);

   int n = ArraySize(g_zonasSellSide);
   for(int i = 0; i < n; i++)
     {
      if(g_zonasSellSide[i].importancia < InpImportanciaMinimaZona)
         continue;
      double nivel = g_zonasSellSide[i].nivel;
      if(low1 < nivel && close1 > nivel)
        {
         double dist = nivel - low1;
         if(dist > 0.0 && dist <= maxDist)
           {
            precioSweep     = low1;
            distancia       = dist;
            tipoZona        = g_zonasSellSide[i].tipo;
            nivelZona       = nivel;
            importanciaZona = g_zonasSellSide[i].importancia;
            return true;
           }
        }
     }
   return false;
  }

bool BuscarSweepBuySide(double &precioSweep, double &distancia, ENUM_TIPO_ZONA &tipoZona,
                         double &nivelZona, int &importanciaZona)
  {
   double atr = ATRActual();
   if(atr <= 0.0) return false;
   double maxDist = InpMaxSweepDistanceATRMult * atr;

   double high1  = iHigh(_Symbol, InpTimeframeEntrada, 1);
   double close1 = iClose(_Symbol, InpTimeframeEntrada, 1);

   int n = ArraySize(g_zonasBuySide);
   for(int i = 0; i < n; i++)
     {
      if(g_zonasBuySide[i].importancia < InpImportanciaMinimaZona)
         continue;
      double nivel = g_zonasBuySide[i].nivel;
      if(high1 > nivel && close1 < nivel)
        {
         double dist = high1 - nivel;
         if(dist > 0.0 && dist <= maxDist)
           {
            precioSweep     = high1;
            distancia       = dist;
            tipoZona        = g_zonasBuySide[i].tipo;
            nivelZona       = nivel;
            importanciaZona = g_zonasBuySide[i].importancia;
            return true;
           }
        }
     }
   return false;
  }

//======================================================================
// MÓDULO 6: MARKET STRUCTURE SHIFT (MSS)
//======================================================================
// Localiza el último swing significativo CONFIRMADO antes del sweep
// (usando únicamente velas ya cerradas) y comprueba, vela a vela tras el
// sweep, si el CIERRE lo supera (LONG) o lo pierde (SHORT).
//----------------------------------------------------------------------
bool LocalizarSwingPrevioAlSweep(const bool paraLong, const datetime antesDe, double &nivel)
  {
   datetime t[]; double v[];
   if(paraLong)
     {
      int n = RecopilarSwingHighs(InpTimeframeEntrada, InpSwingLeftBars, InpSwingRightBars,
                                   InpSwingHistorialBarras, InpSwingHistorialBarras, t, v);
      for(int i = 0; i < n; i++)
         if(t[i] < antesDe) { nivel = v[i]; return true; }
     }
   else
     {
      int n = RecopilarSwingLows(InpTimeframeEntrada, InpSwingLeftBars, InpSwingRightBars,
                                  InpSwingHistorialBarras, InpSwingHistorialBarras, t, v);
      for(int i = 0; i < n; i++)
         if(t[i] < antesDe) { nivel = v[i]; return true; }
     }
   return false;
  }

//======================================================================
// MÓDULO 7: FAIR VALUE GAP (FVG)
//======================================================================
// FVG alcista: low de la vela cerrada más reciente > high de la vela
// cerrada dos posiciones antes. FVG bajista: análogo invertido. Ambas
// comparaciones usan sólo velas ya cerradas (shift 1 y shift 3).
//----------------------------------------------------------------------
bool DetectarFVG(const bool esLong, double &superior, double &inferior)
  {
   double low1   = iLow(_Symbol, InpTimeframeEntrada, 1);
   double high1  = iHigh(_Symbol, InpTimeframeEntrada, 1);
   double high3  = iHigh(_Symbol, InpTimeframeEntrada, 3);
   double low3   = iLow(_Symbol, InpTimeframeEntrada, 3);

   if(esLong)
     {
      if(low1 > high3)
        {
         superior = low1;
         inferior = high3;
         return true;
        }
     }
   else
     {
      if(high1 < low3)
        {
         superior = low3;
         inferior = high1;
         return true;
        }
     }
   return false;
  }

//======================================================================
// MÓDULO 8: GESTIÓN DE RIESGO Y CÁLCULO DE LOTAJE (heredado sin cambios)
//======================================================================
double CalcularLotaje(const double precioEntrada, const double precioSL, const ENUM_ORDER_TYPE tipoOrden)
  {
   double balance      = AccountInfoDouble(ACCOUNT_BALANCE);
   double montoRiesgo   = balance * (InpRiskPercent / 100.0);

   double distanciaSL = MathAbs(precioEntrada - precioSL);
   if(distanciaSL <= 0.0)
      return 0.0;

   double perdidaPorLote = 0.0;
   if(!OrderCalcProfit(tipoOrden, _Symbol, 1.0, precioEntrada, precioSL, perdidaPorLote))
      return 0.0;

   perdidaPorLote = MathAbs(perdidaPorLote);
   if(perdidaPorLote <= 0.0)
      return 0.0;

   double lotes = montoRiesgo / perdidaPorLote;

   double volMin  = SymbolInfoDouble(_Symbol, SYMBOL_VOLUME_MIN);
   double volMax  = SymbolInfoDouble(_Symbol, SYMBOL_VOLUME_MAX);
   double volStep = SymbolInfoDouble(_Symbol, SYMBOL_VOLUME_STEP);

   lotes = MathFloor(lotes / volStep) * volStep;
   lotes = MathMax(volMin, MathMin(volMax, lotes));

   return NormalizeDouble(lotes, 2);
  }

//======================================================================
// MÓDULO 9: FILTROS DE PROTECCIÓN (SPREAD, KILL SWITCH, FIN DE SEMANA,
// SESIÓN) -- heredados sin cambios
//======================================================================
bool SpreadPermitido()
  {
   double spreadPuntos = (double)SymbolInfoInteger(_Symbol, SYMBOL_SPREAD);
   double spreadPips   = (spreadPuntos * SymbolInfoDouble(_Symbol, SYMBOL_POINT)) / PipSize();
   return (spreadPips <= InpMaxSpreadPips);
  }

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

void GestionarCambioDeDia()
  {
   MqlDateTime dt;
   TimeToStruct(TimeCurrent(), dt);
   dt.hour = 0; dt.min = 0; dt.sec = 0;
   datetime inicioDeHoy = StructToTime(dt);

   if(inicioDeHoy != g_diaActual)
     {
      g_diaActual = inicioDeHoy;
      g_perdidasConsecutivasHoy = 0;
      g_circuitoPerdidasActivo  = false;
      g_operacionesHoy          = 0;

      string claveBal = ClaveGlobal("BalanceInicioDia");
      string claveKS  = ClaveGlobal("KillSwitch");

      if(GlobalVariableCheck(claveBal))
        {
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
      return;

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

bool EsHorarioDeVeranoUSA(const datetime tiempoUTC)
  {
   MqlDateTime dt;
   TimeToStruct(tiempoUTC, dt);
   int year = dt.year;

   MqlDateTime tmp;
   ZeroMemory(tmp);
   tmp.year = year; tmp.mon = 3; tmp.day = 1;
   datetime primerDiaMarzo = StructToTime(tmp);
   TimeToStruct(primerDiaMarzo, tmp);
   int diaSemana1Marzo = tmp.day_of_week;
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
   int offsetNY = EsHorarioDeVeranoUSA(tiempoUTC) ? -4 : -5;
   return tiempoUTC + offsetNY * 3600;
  }

bool DebeCerrarPorFinDeSemana()
  {
   if(!InpCerrarViernes)
      return false;
   datetime horaNY = ConvertirServidorANuevaYork(TimeCurrent());
   MqlDateTime dt;
   TimeToStruct(horaNY, dt);
   if(dt.day_of_week == 5 && dt.hour >= InpFridayCloseHourNY)
      return true;
   return false;
  }

bool SesionPermiteOperar()
  {
   if(!InpUsarFiltroSesion)
      return true;
   datetime horaNY = ConvertirServidorANuevaYork(TimeCurrent());
   MqlDateTime dt;
   TimeToStruct(horaNY, dt);
   if(InpSesionInicioHoraNY <= InpSesionFinHoraNY)
      return (dt.hour >= InpSesionInicioHoraNY && dt.hour < InpSesionFinHoraNY);
   return (dt.hour >= InpSesionInicioHoraNY || dt.hour < InpSesionFinHoraNY);
  }

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

bool HayOrdenPendiente(const ulong ticket)
  {
   for(int i = 0; i < OrdersTotal(); i++)
      if(OrderGetTicket(i) == ticket)
         return true;
   return false;
  }

//======================================================================
// MÓDULO 10: TAKE PROFIT Y VALIDACIÓN DE RR
//======================================================================
// MODE A: TP fijo a InpFixedRR. MODE B: TP en la siguiente liquidity zone
// relevante en dirección del trade (la más cercana cuyo RR implícito ya
// cumpla InpMinimumRR; si la más cercana no lo cumple se prueba con la
// siguiente más lejana). Si ningún TP lógico alcanza InpMinimumRR, no hay
// operación (se descarta el setup).
//----------------------------------------------------------------------
bool CalcularTP(const bool esLong, const double entrada, const double sl, double &tp, double &rr)
  {
   double riesgo = MathAbs(entrada - sl);
   if(riesgo <= 0.0)
      return false;

   if(InpModoTP == MODO_TP_FIJO_RR)
     {
      tp = esLong ? entrada + InpFixedRR * riesgo : entrada - InpFixedRR * riesgo;
      rr = InpFixedRR;
      return (rr >= InpMinimumRR);
     }

   // MODE B: siguiente liquidity zone relevante en la dirección del trade,
   // ordenada por proximidad; se prueba cada una hasta encontrar la
   // primera que cumpla el RR mínimo.
   SLiquidityZone candidatas[];
   ArrayResize(candidatas, 0);
   if(esLong)
     {
      int n = ArraySize(g_zonasBuySide);
      for(int i = 0; i < n; i++)
         if(g_zonasBuySide[i].nivel > entrada)
           {
            int k = ArraySize(candidatas);
            ArrayResize(candidatas, k + 1);
            candidatas[k] = g_zonasBuySide[i];
           }
     }
   else
     {
      int n = ArraySize(g_zonasSellSide);
      for(int i = 0; i < n; i++)
         if(g_zonasSellSide[i].nivel < entrada)
           {
            int k = ArraySize(candidatas);
            ArrayResize(candidatas, k + 1);
            candidatas[k] = g_zonasSellSide[i];
           }
     }

   // Ordenar por proximidad a la entrada (selection sort simple; listas pequeñas)
   int total = ArraySize(candidatas);
   for(int i = 0; i < total - 1; i++)
     {
      int mejor = i;
      for(int j = i + 1; j < total; j++)
        {
         double distJ = MathAbs(candidatas[j].nivel - entrada);
         double distMejor = MathAbs(candidatas[mejor].nivel - entrada);
         if(distJ < distMejor) mejor = j;
        }
      if(mejor != i)
        {
         SLiquidityZone tmp = candidatas[i];
         candidatas[i] = candidatas[mejor];
         candidatas[mejor] = tmp;
        }
     }

   for(int i = 0; i < total; i++)
     {
      double rrCandidato = MathAbs(candidatas[i].nivel - entrada) / riesgo;
      if(rrCandidato >= InpMinimumRR)
        {
         tp = candidatas[i].nivel;
         rr = rrCandidato;
         return true;
        }
     }
   return false; // ninguna liquidity zone ofrece un RR suficiente: no hay operación
  }

//======================================================================
// MÓDULO 11: MÁQUINA DE ESTADOS DEL SETUP (Sweep -> MSS -> FVG -> Retest)
//======================================================================
void ResetearSetup()
  {
   g_setup.estado = SETUP_NINGUNO;
   g_setup.ticketPendiente = 0;
  }

string NombreZona(const ENUM_TIPO_ZONA t); // definida en el módulo de log CSV, más abajo

//--- Paso 1: buscar un sweep nuevo (sólo si no hay setup ni posición/orden en curso)
void BuscarNuevoSweep()
  {
   if(g_regimenActual == REGIMEN_INDEFINIDO)
      return;
   if(!SesionPermiteOperar())
      return;
   if(g_operacionesHoy >= InpMaxOperacionesPorSesion)
      return;

   double precioSweep, distancia, nivelZona;
   ENUM_TIPO_ZONA tipoZona;
   int importanciaZona;

   if(g_regimenActual == REGIMEN_ALCISTA &&
      BuscarSweepSellSide(precioSweep, distancia, tipoZona, nivelZona, importanciaZona))
     {
      g_setup.estado               = SETUP_SWEEP_DETECTADO;
      g_setup.esLong                = true;
      g_setup.precioSweep           = precioSweep;
      g_setup.sweepDistancia        = distancia;
      g_setup.tipoZonaSweep         = tipoZona;
      g_setup.nivelZonaSweep        = nivelZona;
      g_setup.importanciaZonaSweep  = importanciaZona;
      g_setup.sweepTime             = iTime(_Symbol, InpTimeframeEntrada, 1);
      g_setup.regimenEnSweep        = g_regimenActual;
      PrintFormat("[DIAG] Sweep LONG detectado: zona=%s(imp.%d) nivel=%.2f sweep=%.2f dist=%.2f",
                  NombreZona(tipoZona), importanciaZona, nivelZona, precioSweep, distancia);
      return;
     }

   if(g_regimenActual == REGIMEN_BAJISTA &&
      BuscarSweepBuySide(precioSweep, distancia, tipoZona, nivelZona, importanciaZona))
     {
      g_setup.estado               = SETUP_SWEEP_DETECTADO;
      g_setup.esLong                = false;
      g_setup.precioSweep           = precioSweep;
      g_setup.sweepDistancia        = distancia;
      g_setup.tipoZonaSweep         = tipoZona;
      g_setup.nivelZonaSweep        = nivelZona;
      g_setup.importanciaZonaSweep  = importanciaZona;
      g_setup.sweepTime             = iTime(_Symbol, InpTimeframeEntrada, 1);
      g_setup.regimenEnSweep        = g_regimenActual;
      PrintFormat("[DIAG] Sweep SHORT detectado: zona=%s(imp.%d) nivel=%.2f sweep=%.2f dist=%.2f",
                  NombreZona(tipoZona), importanciaZona, nivelZona, precioSweep, distancia);
     }
  }

//--- Paso 2: tras el sweep, esperar el Market Structure Shift
void ComprobarMSS()
  {
   double nivel;
   if(!LocalizarSwingPrevioAlSweep(g_setup.esLong, g_setup.sweepTime, nivel))
     {
      Print("[DIAG] Setup descartado: no hay swing previo utilizable para el MSS.");
      ResetearSetup(); // no hay swing previo utilizable: setup inviable
      return;
     }

   double close1 = iClose(_Symbol, InpTimeframeEntrada, 1);
   if(g_setup.esLong && close1 > nivel)
     {
      g_setup.mssLevel = nivel;
      g_setup.estado   = SETUP_MSS_CONFIRMADO;
      PrintFormat("[DIAG] MSS alcista confirmado: swing=%.2f cierre=%.2f", nivel, close1);
     }
   else if(!g_setup.esLong && close1 < nivel)
     {
      g_setup.mssLevel = nivel;
      g_setup.estado   = SETUP_MSS_CONFIRMADO;
      PrintFormat("[DIAG] MSS bajista confirmado: swing=%.2f cierre=%.2f", nivel, close1);
     }
  }

//--- Paso 3: tras el MSS, buscar el primer FVG en la dirección del movimiento
void BuscarFVG()
  {
   double sup, inf;
   if(!DetectarFVG(g_setup.esLong, sup, inf))
      return;

   double atr = ATRActual();
   if(InpUsarFiltroFVGMinimo && atr > 0.0 && (sup - inf) < InpFVGMinSizeATRMult * atr)
     {
      PrintFormat("[DIAG] FVG encontrado pero descartado por tamaño mínimo: tamaño=%.2f mínimo=%.2f",
                  sup - inf, InpFVGMinSizeATRMult * atr);
      return; // FVG demasiado pequeño: se ignora, se sigue esperando otro
     }

   PrintFormat("[DIAG] FVG %s válido: superior=%.2f inferior=%.2f", g_setup.esLong ? "alcista" : "bajista", sup, inf);
   g_setup.fvgSuperior = sup;
   g_setup.fvgInferior = inf;

   double pct = InpFVGEntryPercent / 100.0;
   g_setup.entradaObjetivo = g_setup.esLong ? inf + pct * (sup - inf)
                                              : sup - pct * (sup - inf);

   // Stop Loss: invalida la hipótesis del liquidity sweep
   if(atr <= 0.0) { ResetearSetup(); return; }
   g_setup.slPlan = g_setup.esLong ? g_setup.precioSweep - InpSLBufferATRMult * atr
                                     : g_setup.precioSweep + InpSLBufferATRMult * atr;

   double tp, rr;
   if(!CalcularTP(g_setup.esLong, g_setup.entradaObjetivo, g_setup.slPlan, tp, rr))
     {
      Print("[DIAG] Setup descartado: ningún TP lógico alcanza el RR mínimo (InpMinimumRR).");
      ResetearSetup(); // ningún TP lógico alcanza el RR mínimo: no hay operación
      return;
     }
   g_setup.tpPlan = tp;
   g_setup.rrPlan = rr;
   g_setup.estado = SETUP_FVG_LISTO;

   // Colocar la orden límite de retest al nivel objetivo del FVG, con
   // expiración = InpSetupMaxBarras velas (si no se rellena, expira sola).
   double lotes = CalcularLotaje(g_setup.entradaObjetivo, g_setup.slPlan,
                                  g_setup.esLong ? ORDER_TYPE_BUY : ORDER_TYPE_SELL);
   if(lotes <= 0.0)
     {
      Print("No se pudo calcular un lotaje válido para el retest del FVG.");
      ResetearSetup();
      return;
     }

   // Comprobación de margen: cuando el SL está anormalmente cerca del entry (ATR
   // momentáneamente muy bajo), CalcularLotaje() puede devolver un lotaje que el
   // % de riesgo justifica matemáticamente pero que la cuenta no puede permitirse
   // (margen requerido > margen libre). Se descarta el setup aquí en vez de dejar
   // que el bróker rechace la orden en OnTradeTransaction, que además consumía
   // igualmente el hueco de la sesión sin dejar ninguna operación real.
   double margenRequerido;
   ENUM_ORDER_TYPE tipoOrdenMargen = g_setup.esLong ? ORDER_TYPE_BUY : ORDER_TYPE_SELL;
   if(!OrderCalcMargin(tipoOrdenMargen, _Symbol, lotes, g_setup.entradaObjetivo, margenRequerido))
     {
      Print("[DIAG] Setup descartado: no se pudo calcular el margen requerido para la orden.");
      ResetearSetup();
      return;
     }
   double margenLibre = AccountInfoDouble(ACCOUNT_FREEMARGIN);
   if(margenRequerido > margenLibre)
     {
      PrintFormat("[DIAG] Setup descartado: margen insuficiente para el lotaje calculado (lotes=%.2f, margen requerido=%.2f, margen libre=%.2f). SL demasiado cercano al entry para el %% de riesgo configurado.",
                  lotes, margenRequerido, margenLibre);
      ResetearSetup();
      return;
     }

   datetime expiracion = TimeCurrent() + InpSetupMaxBarras * PeriodSeconds(InpTimeframeEntrada);
   trade.SetExpertMagicNumber(InpMagicNumber);
   bool enviado;
   if(g_setup.esLong)
      enviado = trade.BuyLimit(lotes, g_setup.entradaObjetivo, _Symbol, g_setup.slPlan, g_setup.tpPlan,
                                ORDER_TIME_SPECIFIED, expiracion, "SweepMSSFVG_Long");
   else
      enviado = trade.SellLimit(lotes, g_setup.entradaObjetivo, _Symbol, g_setup.slPlan, g_setup.tpPlan,
                                 ORDER_TIME_SPECIFIED, expiracion, "SweepMSSFVG_Short");

   if(enviado)
     {
      g_setup.ticketPendiente = trade.ResultOrder();
      PrintFormat("Orden límite de retest FVG colocada (%s): entrada=%.2f SL=%.2f TP=%.2f RR=%.2f",
                  g_setup.esLong ? "LONG" : "SHORT", g_setup.entradaObjetivo, g_setup.slPlan, g_setup.tpPlan, g_setup.rrPlan);
     }
   else
     {
      Print("Fallo al colocar la orden límite de retest del FVG.");
      ResetearSetup();
     }
  }

//--- Timeout general: si desde el sweep han pasado más de InpSetupMaxBarras velas sin
//    completar la secuencia sweep->MSS->FVG->retest, se descarta el setup (cubre las
//    fases SWEEP_DETECTADO y MSS_CONFIRMADO; la fase FVG_LISTO expira sola vía la
//    fecha de expiración de la orden límite, ver BuscarFVG()).
bool SetupExpiradoPorTiempo()
  {
   if(g_setup.estado == SETUP_NINGUNO)
      return false;
   datetime ahora = iTime(_Symbol, InpTimeframeEntrada, 1);
   long barrasTranscurridas = (long)((ahora - g_setup.sweepTime) / PeriodSeconds(InpTimeframeEntrada));
   return (barrasTranscurridas > InpSetupMaxBarras);
  }

//--- Comprueba invalidación (rotura de estructura en contra) o expiración de la orden pendiente
void SupervisarSetupPendiente()
  {
   if(g_setup.estado != SETUP_MSS_CONFIRMADO && g_setup.estado != SETUP_FVG_LISTO)
      return;

   double close1 = iClose(_Symbol, InpTimeframeEntrada, 1);
   bool estructuraInvalidada = g_setup.esLong ? (close1 < g_setup.mssLevel)
                                                : (close1 > g_setup.mssLevel);
   if(estructuraInvalidada)
     {
      Print("[DIAG] Setup invalidado: el precio cerró de nuevo más allá del nivel del MSS.");
      if(g_setup.estado == SETUP_FVG_LISTO && g_setup.ticketPendiente != 0 && HayOrdenPendiente(g_setup.ticketPendiente))
         trade.OrderDelete(g_setup.ticketPendiente);
      ResetearSetup();
      return;
     }

   if(g_setup.estado == SETUP_FVG_LISTO && g_setup.ticketPendiente != 0 && !HayOrdenPendiente(g_setup.ticketPendiente))
     {
      // la orden ya no existe (se rellenó -> gestionado en OnTradeTransaction,
      // o expiró/fue cancelada por el bróker): si no hay posición nuestra
      // abierta, fue una expiración -- se libera el setup.
      if(!HayPosicionAbierta())
        {
         Print("[DIAG] Orden límite de retest expirada sin rellenarse.");
         ResetearSetup();
        }
     }
  }

//======================================================================
// MÓDULO 12: GESTIÓN DE POSICIÓN (BREAKEVEN / TRAILING / CIERRE PARCIAL)
// -- heredado sin cambios de la versión anterior del EA --
//======================================================================
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
      return;
     }
  }

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

      if(InpUsarCierreParcial && !g_cierreParcialAplicado)
        {
         double volumenActual  = PositionGetDouble(POSITION_VOLUME);
         double volStep        = SymbolInfoDouble(_Symbol, SYMBOL_VOLUME_STEP);
         double volMin         = SymbolInfoDouble(_Symbol, SYMBOL_VOLUME_MIN);
         double volumenCerrar  = MathFloor((volumenActual * InpCierreParcialPercent / 100.0) / volStep) * volStep;

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
            g_cierreParcialAplicado = true;
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
      return;
     }
  }

//======================================================================
// MÓDULO 13: LOG CSV DE OPERACIONES
//======================================================================
void EscribirCabeceraSiHaceFalta(const int handle)
  {
   if(FileSize(handle) == 0)
      FileWrite(handle, "FechaHoraApertura", "FechaHoraCierre", "Direccion", "TipoZonaLiquidez",
                "ImportanciaZona", "PrecioSweep", "SweepDistancia", "MSSLevel", "FVGSuperior",
                "FVGInferior", "PrecioEntrada", "StopLoss", "TakeProfit", "RRPlan", "ResultadoR",
                "ResultadoMonetario", "DuracionMinutos", "DrawdownDuranteTrade", "Regimen4H");
  }

string NombreZona(const ENUM_TIPO_ZONA t)
  {
   switch(t)
     {
      case ZONA_PWH:        return "PWH";
      case ZONA_PWL:        return "PWL";
      case ZONA_PDH:        return "PDH";
      case ZONA_PDL:        return "PDL";
      case ZONA_ASIA_HIGH:  return "AsiaHigh";
      case ZONA_ASIA_LOW:   return "AsiaLow";
      case ZONA_SWING_HIGH: return "SwingHigh";
      case ZONA_SWING_LOW:  return "SwingLow";
      case ZONA_EQUAL_HIGH: return "EqualHigh";
      case ZONA_EQUAL_LOW:  return "EqualLow";
     }
   return "?";
  }

string NombreRegimen(const ENUM_REGIMEN r)
  {
   if(r == REGIMEN_ALCISTA) return "ALCISTA";
   if(r == REGIMEN_BAJISTA) return "BAJISTA";
   return "INDEFINIDO";
  }

void RegistrarOperacionEnCSV(const double resultadoMonetario, const datetime horaCierre)
  {
   if(!InpRegistrarCSV)
      return;

   int handle = FileOpen(InpNombreArchivoCSV, FILE_READ | FILE_WRITE | FILE_CSV | FILE_ANSI, ';');
   if(handle == INVALID_HANDLE)
     {
      PrintFormat("No se pudo abrir el archivo de log CSV '%s' (error %d).", InpNombreArchivoCSV, GetLastError());
      return;
     }
   EscribirCabeceraSiHaceFalta(handle);
   FileSeek(handle, 0, SEEK_END);

   double resultadoR = (g_logOperacionActiva.riesgoMonetarioPlan > 0.0)
                        ? resultadoMonetario / g_logOperacionActiva.riesgoMonetarioPlan : 0.0;
   double duracionMin = (double)(horaCierre - g_logOperacionActiva.horaApertura) / 60.0;
   double drawdownTrade = (AccountInfoDouble(ACCOUNT_BALANCE) - g_logOperacionActiva.equityMinimaDurante);
   if(drawdownTrade < 0.0) drawdownTrade = 0.0;

   FileWrite(handle,
             TimeToString(g_logOperacionActiva.horaApertura, TIME_DATE | TIME_SECONDS),
             TimeToString(horaCierre, TIME_DATE | TIME_SECONDS),
             g_logOperacionActiva.esLong ? "LONG" : "SHORT",
             NombreZona(g_logOperacionActiva.tipoZonaSweep),
             g_logOperacionActiva.importanciaZonaSweep,
             DoubleToString(g_logOperacionActiva.precioSweep, _Digits),
             DoubleToString(g_logOperacionActiva.sweepDistancia, _Digits),
             DoubleToString(g_logOperacionActiva.mssLevel, _Digits),
             DoubleToString(g_logOperacionActiva.fvgSuperior, _Digits),
             DoubleToString(g_logOperacionActiva.fvgInferior, _Digits),
             DoubleToString(g_logOperacionActiva.precioEntrada, _Digits),
             DoubleToString(g_logOperacionActiva.sl, _Digits),
             DoubleToString(g_logOperacionActiva.tp, _Digits),
             DoubleToString(g_logOperacionActiva.rrPlan, 2),
             DoubleToString(resultadoR, 3),
             DoubleToString(resultadoMonetario, 2),
             DoubleToString(duracionMin, 1),
             DoubleToString(drawdownTrade, 2),
             NombreRegimen(g_logOperacionActiva.regimen));

   FileClose(handle);
  }

//======================================================================
// EVENTOS DEL EXPERT ADVISOR
//======================================================================
int OnInit()
  {
   g_handleEMARegimen = iMA(_Symbol, InpTimeframeRegimen, InpEMARegimenPeriod, 0, MODE_EMA, PRICE_CLOSE);
   if(g_handleEMARegimen == INVALID_HANDLE)
     {
      Print("Error al crear la EMA de régimen.");
      return(INIT_FAILED);
     }

   g_handleATR = iATR(_Symbol, InpTimeframeEntrada, InpATRPeriod);
   if(g_handleATR == INVALID_HANDLE)
     {
      Print("Error al crear el ATR.");
      return(INIT_FAILED);
     }

   if(InpFixedRR < InpMinimumRR)
      Print("AVISO: InpFixedRR es menor que InpMinimumRR; en Modo A ninguna operación pasará el filtro de RR mínimo.");

   trade.SetExpertMagicNumber(InpMagicNumber);

   ResetearSetup();
   g_diaActual = 0;
   GestionarCambioDeDia();

   ActualizarAsiaHighLow();
   ActualizarRegimen();
   ReconstruirZonasLiquidez();
   g_ultimaVelaEntradaProcesada = iTime(_Symbol, InpTimeframeEntrada, 0);
   g_ultimaVelaRegimenProcesada = iTime(_Symbol, InpTimeframeRegimen, 0);

   return(INIT_SUCCEEDED);
  }

void OnDeinit(const int reason)
  {
   if(g_handleEMARegimen != INVALID_HANDLE)
      IndicatorRelease(g_handleEMARegimen);
   if(g_handleATR != INVALID_HANDLE)
      IndicatorRelease(g_handleATR);
  }

//======================================================================
// CIRCUITO DE PÉRDIDAS CONSECUTIVAS (heredado sin cambios) + FILL/CIERRE
// DE ÓRDENES DEL SETUP SWEEP->MSS->FVG
//======================================================================
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

   // --- Apertura (fill de la orden límite de retest del FVG) ---
   if(tipoEntrada == DEAL_ENTRY_IN)
     {
      double precioEntradaReal = HistoryDealGetDouble(trans.deal, DEAL_PRICE);
      g_slOriginalPosicion    = g_setup.slPlan;
      g_breakevenAplicado     = false;
      g_trailingActivado      = false;
      g_cierreParcialAplicado = false;
      g_operacionesHoy++;

      g_logOperacionActiva.horaApertura          = TimeCurrent();
      g_logOperacionActiva.esLong                = g_setup.esLong;
      g_logOperacionActiva.tipoZonaSweep         = g_setup.tipoZonaSweep;
      g_logOperacionActiva.importanciaZonaSweep  = g_setup.importanciaZonaSweep;
      g_logOperacionActiva.precioSweep           = g_setup.precioSweep;
      g_logOperacionActiva.sweepDistancia        = g_setup.sweepDistancia;
      g_logOperacionActiva.mssLevel              = g_setup.mssLevel;
      g_logOperacionActiva.fvgSuperior           = g_setup.fvgSuperior;
      g_logOperacionActiva.fvgInferior           = g_setup.fvgInferior;
      g_logOperacionActiva.precioEntrada         = precioEntradaReal;
      g_logOperacionActiva.sl                    = g_setup.slPlan;
      g_logOperacionActiva.tp                    = g_setup.tpPlan;
      g_logOperacionActiva.rrPlan                = g_setup.rrPlan;
      g_logOperacionActiva.regimen               = g_setup.regimenEnSweep;
      g_logOperacionActiva.riesgoMonetarioPlan   = AccountInfoDouble(ACCOUNT_BALANCE) * (InpRiskPercent / 100.0);
      g_logOperacionActiva.equityMinimaDurante   = AccountInfoDouble(ACCOUNT_EQUITY);
      g_hayLogOperacionActiva = true;

      PrintFormat("%s ejecutada (retest FVG): entrada=%.2f SL=%.2f TP=%.2f RR=%.2f",
                  g_setup.esLong ? "COMPRA" : "VENTA", precioEntradaReal, g_setup.slPlan, g_setup.tpPlan, g_setup.rrPlan);

      ResetearSetup(); // el sweep que originó esta operación queda consumido
      return;
     }

   if(tipoEntrada != DEAL_ENTRY_OUT && tipoEntrada != DEAL_ENTRY_OUT_BY)
      return;

   ulong idPosicion = (ulong)HistoryDealGetInteger(trans.deal, DEAL_POSITION_ID);
   if(PositionSelectByTicket(idPosicion))
      return; // cierre parcial: la posición sigue viva, no se resetea su estado

   g_slOriginalPosicion    = 0.0;
   g_breakevenAplicado     = false;
   g_trailingActivado      = false;
   g_cierreParcialAplicado = false;

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

   if(g_hayLogOperacionActiva)
     {
      RegistrarOperacionEnCSV(resultado, TimeCurrent());
      g_hayLogOperacionActiva = false;
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

//======================================================================
// DETECCIÓN DE VELA NUEVA
//======================================================================
bool EsVelaNuevaEntrada()
  {
   datetime horaVelaActual = iTime(_Symbol, InpTimeframeEntrada, 0);
   if(horaVelaActual != g_ultimaVelaEntradaProcesada)
     {
      g_ultimaVelaEntradaProcesada = horaVelaActual;
      return true;
     }
   return false;
  }

bool EsVelaNuevaRegimen()
  {
   datetime horaVelaActual = iTime(_Symbol, InpTimeframeRegimen, 0);
   if(horaVelaActual != g_ultimaVelaRegimenProcesada)
     {
      g_ultimaVelaRegimenProcesada = horaVelaActual;
      return true;
     }
   return false;
  }

void OnTick()
  {
   // 1) Gestión de cambio de día (referencia para el Kill Switch y el límite de operaciones por sesión)
   GestionarCambioDeDia();

   // 2) Kill Switch diario
   ComprobarKillSwitchDiario();
   if(g_killSwitchActivo)
      return;

   // 3) Cierre obligatorio de fin de semana
   if(DebeCerrarPorFinDeSemana())
     {
      datetime velaActual = iTime(_Symbol, InpTimeframeEntrada, 0);
      if(velaActual != g_ultimaVelaIntentoCierreFDS)
        {
         g_ultimaVelaIntentoCierreFDS = velaActual;
         if(HayPosicionAbierta())
           {
            Print("Cierre de fin de semana: liquidando posiciones flotantes.");
            CerrarTodasLasPosiciones();
           }
         BorrarTodasLasOrdenesPendientes();
         ResetearSetup();
        }
      return;
     }

   // 4) Actualizar equity mínima de la operación activa (para el drawdown por trade del log CSV)
   if(g_hayLogOperacionActiva)
     {
      double equityActual = AccountInfoDouble(ACCOUNT_EQUITY);
      if(equityActual < g_logOperacionActiva.equityMinimaDurante)
         g_logOperacionActiva.equityMinimaDurante = equityActual;
     }

   // 5) Régimen 4H: sólo se recalcula al cerrar una nueva vela H4
   if(EsVelaNuevaRegimen())
      ActualizarRegimen();

   // 6) Sesión asiática y liquidity zones: se recalculan al cerrar una nueva vela M15
   //    NOTA: EsVelaNuevaEntrada() tiene efecto colateral (consume el flag de "vela
   //    nueva" al devolver true una única vez por vela) -- se llama UNA SOLA VEZ por
   //    tick y se reutiliza el resultado en todo OnTick(). Llamarla varias veces por
   //    tick (bug anterior) hacía que sólo el primer "if" viera vela nueva y el resto,
   //    incluida la búsqueda de sweeps, la viera siempre como false: la máquina de
   //    estados nunca llegaba a ejecutarse pese al régimen estar activo.
   bool esVelaNuevaEntrada = EsVelaNuevaEntrada();
   if(esVelaNuevaEntrada)
     {
      ActualizarAsiaHighLow();
      ReconstruirZonasLiquidez();
     }

   // 7) Si ya hay una posición abierta, sólo se gestiona (breakeven/trailing); no se buscan setups nuevos
   if(HayPosicionAbierta())
     {
      GestionarBreakeven();
      GestionarTrailingStop();
      return;
     }

   // 8) Supervisión del setup en curso (invalidación de estructura / expiración de la
   //    orden pendiente): se hace siempre, incluso si el spread está momentáneamente
   //    alto o el circuito de pérdidas está activo, para no dejar huérfana una orden
   //    límite ya colocada en el mercado.
   if(esVelaNuevaEntrada)
     {
      if(SetupExpiradoPorTiempo() &&
         (g_setup.estado == SETUP_SWEEP_DETECTADO || g_setup.estado == SETUP_MSS_CONFIRMADO))
        {
         PrintFormat("[DIAG] Setup descartado por timeout (InpSetupMaxBarras) en estado %d.", g_setup.estado);
         ResetearSetup();
        }
      if(g_setup.estado == SETUP_MSS_CONFIRMADO || g_setup.estado == SETUP_FVG_LISTO)
         SupervisarSetupPendiente();
     }
   else if(g_setup.estado == SETUP_FVG_LISTO)
     {
      // entre velas, sólo se supervisa la orden pendiente (expiración/invalidación);
      // el propio relleno de la orden llega por OnTradeTransaction
      SupervisarSetupPendiente();
     }

   // 9) Filtro de spread: sólo bloquea la búsqueda/activación de setups NUEVOS
   if(!SpreadPermitido())
      return;

   // 10) Circuito de pérdidas consecutivas: idem, sólo bloquea aperturas nuevas
   if(g_circuitoPerdidasActivo)
      return;

   // 11) Progresión de la máquina de estados (buscar un sweep nuevo, comprobar el MSS
   //     o, tras un MSS ya supervisado, buscar el FVG), sólo al cerrar una vela M15 nueva
   //     (todas las reglas -sweep, MSS, FVG- se evalúan sobre velas ya cerradas)
   if(esVelaNuevaEntrada)
     {
      if(g_setup.estado == SETUP_NINGUNO)
         BuscarNuevoSweep();
      else if(g_setup.estado == SETUP_SWEEP_DETECTADO)
         ComprobarMSS();
      else if(g_setup.estado == SETUP_MSS_CONFIRMADO)
         BuscarFVG();
     }
  }
//+------------------------------------------------------------------+
