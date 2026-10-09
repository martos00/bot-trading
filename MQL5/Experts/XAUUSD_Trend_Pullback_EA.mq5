//+------------------------------------------------------------------+
//|                                   XAUUSD_Trend_Pullback_EA.mq5  |
//|   Hipótesis 3: TENDENCIA (H1) + PULLBACK + CONFIRMACIÓN (M15).  |
//|   Continuación de tendencia, sólo a favor de tendencia. No      |
//|   comparte código con ningún otro EA del repositorio: toda la  |
//|   infraestructura de riesgo/ejecución se copia aquí (no se     |
//|   modifica ningún otro archivo).                                |
//+------------------------------------------------------------------+
#property copyright "Bot Trading"
#property version   "1.00"
#property strict

#include <Trade\Trade.mqh>

//======================================================================
// PARÁMETROS DE ENTRADA
//======================================================================

input group "=== Configuración General ==="
input ulong  InpMagicNumber            = 20261009;   // Número mágico

input group "=== Tendencia H1 (EMA200 + estructura) ==="
input int    InpEMAH1Period             = 200;        // Período de la EMA de tendencia en H1
input int    InpSwingLeftH1             = 3;           // Velas a cada lado para confirmar swings H1 (fijo, primera evaluación)
input int    InpSwingRightH1            = 3;
input int    InpH1SwingsAConfirmar      = 2;           // Nº de HH/HL (o LH/LL) consecutivos exigidos
input int    InpH1HistorialBarras       = 120;         // Velas H1 escaneadas hacia atrás para localizar esos swings

input group "=== Pullback M15 ==="
input int    InpSwingLeftM15            = 2;           // Velas a cada lado para confirmar swings M15 (fijo, primera evaluación)
input int    InpSwingRightM15           = 2;
input int    InpM15HistorialBarras      = 300;         // Velas M15 escaneadas hacia atrás para localizar swings
input int    InpATRPeriodM15            = 14;          // Período del ATR en M15
input double InpImpulsoMinATR           = 1.0;         // Impulso mínimo exigido, en múltiplos de ATR(14) M15 (fijo)
input int    InpMaxVelasConfigArmada    = 48;           // Velas M15 máximas desde la confirmación del extremo relevante hasta la ruptura

input group "=== Riesgo y ejecución ==="
input double InpRiskPercent             = 0.5;         // % de riesgo del balance por operación (fijo, primera evaluación)
input double InpRiskRewardRatio         = 1.5;         // RR fijo del Take Profit (fijo, primera evaluación)
input double InpSLBufferATRMult         = 0.1;         // Buffer adicional del SL, en múltiplos de ATR(14) M15 (fijo)
input int    InpMaxDeviationPoints      = 20;          // Desviación máxima aceptada en el envío de la orden (puntos)

input group "=== Gestión de Posición (Breakeven / Trailing / Cierre Parcial) ==="
input bool   InpUsarBreakeven           = true;
input double InpBreakevenTriggerR       = 1.5;
input double InpBreakevenBufferPips     = 2.0;
input bool   InpUsarTrailingStop        = true;
input double InpCierreParcialTriggerR   = 3.0;
input double InpTrailingDistanceR       = 1.0;
input bool   InpUsarCierreParcial       = true;
input double InpCierreParcialPercent    = 50.0;
input double InpManualPipSize           = 0.0;         // 0 = automático (0.10 para oro)

input group "=== Blindaje de Riesgo Institucional ==="
input double InpMaxDailyLossPercent     = 4.0;
input double InpMaxSpreadPips           = 4.0;
input int    InpMaxPerdidasConsecutivas = 3;

input group "=== Cierre de Fin de Semana ==="
input bool   InpCerrarViernes           = true;
input int    InpFridayCloseHourNY       = 21;
input int    InpBrokerGMTOffsetHrs      = 2;

input group "=== Registro de Operaciones (CSV) ==="
input bool   InpRegistrarCSV            = true;
input string InpNombreArchivoCSV        = "TrendPullback_Log.csv";

//======================================================================
// VARIABLES GLOBALES
//======================================================================
CTrade trade;

int g_handleEMAH1    = INVALID_HANDLE;
int g_handleATRM15   = INVALID_HANDLE;

datetime g_ultimaVelaH1Procesada  = 0;
datetime g_ultimaVelaM15Procesada = 0;
datetime g_ultimaVelaIntentoCierreFDS = 0;

enum ENUM_REGIMEN { REGIMEN_INDEFINIDO = 0, REGIMEN_ALCISTA = 1, REGIMEN_BAJISTA = 2 };
ENUM_REGIMEN g_regimenH1 = REGIMEN_INDEFINIDO;

string NombreRegimen(const ENUM_REGIMEN r)
  {
   switch(r)
     {
      case REGIMEN_ALCISTA: return "ALCISTA";
      case REGIMEN_BAJISTA: return "BAJISTA";
      default:              return "INDEFINIDO";
     }
  }

//--- Kill Switch / cambio de día / circuito de pérdidas (idéntico al patrón de Baseline 1)
datetime g_diaActual              = 0;
double   g_balanceInicioDia       = 0.0;
bool     g_killSwitchActivo       = false;
int      g_perdidasConsecutivasHoy = 0;
bool     g_circuitoPerdidasActivo  = false;

//--- Estado de la posición actualmente gestionada (idéntico al patrón de Baseline 1)
double g_slOriginalPosicion    = 0.0;
bool   g_breakevenAplicado     = false;
bool   g_trailingActivado      = false;
bool   g_cierreParcialAplicado = false;

//======================================================================
// MÁQUINA DE ESTADOS DE LA SECUENCIA DE PIVOTES (una por dirección)
//======================================================================
// Secuencia COMPRA: Lo (origen) -> HiImp (impulso, >=InpImpulsoMinATR*ATR) ->
//                    LoPb (retroceso, > Lo) -> HiPb (extremo relevante,
//                    máximo decreciente < HiImp) -> cierre M15 > HiPb.
// Secuencia VENTA: espejo exacto (Hi0 -> LoImp -> HiPb -> LoPb -> cierre < LoPb).
// Los campos de la struct usan nombres genéricos válidos para ambas
// direcciones: "origen"=Lo/Hi0, "impulso"=HiImp/LoImp, "retroceso"=LoPb/HiPb
// (de donde sale el SL), "extremo"=HiPb/LoPb (el nivel de ruptura/entrada).
//----------------------------------------------------------------------
enum ENUM_ESTADO_CONFIG { CFG_BUSCANDO_IMPULSO, CFG_ESPERANDO_RETROCESO, CFG_ESPERANDO_EXTREMO, CFG_ARMADA };

struct SConfigPullback
  {
   ENUM_ESTADO_CONFIG estado;
   bool     esCompra;

   datetime origenTiempoPivote;
   double   origenPrecio;

   datetime impulsoTiempoPivote;
   datetime impulsoTiempoConfirmacion;
   double   impulsoPrecio;

   datetime retrocesoTiempoPivote;
   datetime retrocesoTiempoConfirmacion;
   double   retrocesoPrecio;

   datetime extremoTiempoPivote;
   datetime extremoTiempoConfirmacion;
   double   extremoPrecio;
  };

SConfigPullback g_cfgCompra, g_cfgVenta;

void ResetearConfig(SConfigPullback &cfg, const bool esCompra)
  {
   cfg.estado = CFG_BUSCANDO_IMPULSO;
   cfg.esCompra = esCompra;
   cfg.origenTiempoPivote = 0; cfg.origenPrecio = 0.0;
   cfg.impulsoTiempoPivote = 0; cfg.impulsoTiempoConfirmacion = 0; cfg.impulsoPrecio = 0.0;
   cfg.retrocesoTiempoPivote = 0; cfg.retrocesoTiempoConfirmacion = 0; cfg.retrocesoPrecio = 0.0;
   cfg.extremoTiempoPivote = 0; cfg.extremoTiempoConfirmacion = 0; cfg.extremoPrecio = 0.0;
  }

void CancelarConfig(SConfigPullback &cfg, const string motivo)
  {
   PrintFormat("[DIAG-CANCEL] %s: configuración %s cancelada (origen=%s impulso=%s)",
               motivo, cfg.esCompra ? "COMPRA" : "VENTA",
               TimeToString(cfg.origenTiempoPivote, TIME_DATE|TIME_MINUTES),
               TimeToString(cfg.impulsoTiempoPivote, TIME_DATE|TIME_MINUTES));
   ResetearConfig(cfg, cfg.esCompra);
  }

//======================================================================
// REGISTRO DE OPERACIONES (apertura pendiente de confirmar + CSV)
//======================================================================
struct SDatosOperacionLog
  {
   datetime tOrigen, tImpulsoPivote, tImpulsoConfirm, tRetrocesoPivote, tRetrocesoConfirm,
            tExtremoPivote, tExtremoConfirm, tRuptura;
   int      velasImpulsoARuptura;
   bool     esCompra;
   double   precioRupturaCierre;
   double   bidAntesEnvio, askAntesEnvio, precioSolicitado, precioRealEjecucion;
   double   sl, tp, buffer, volumen, perdidaPorLoteEstimada;
   double   riesgoObjetivoMonetario, riesgoEstimadoPreEjecucion, riesgoRealPostEjecucion;
   double   spreadEnEntrada;
   datetime horaApertura;
   double   equityMinimaDurante;
  };
SDatosOperacionLog g_logPendiente;      // rellenado al enviar la orden, confirmado en OnTradeTransaction (DEAL_ENTRY_IN)
bool               g_hayLogPendiente = false;
SDatosOperacionLog g_logOperacionActiva; // confirmado, esperando el cierre para escribir la fila completa
bool               g_hayLogOperacionActiva = false;

//======================================================================
// UTILIDADES
//======================================================================
double PipSize()
  {
   if(InpManualPipSize > 0.0) return InpManualPipSize;
   return 0.10;
  }

string ClaveGlobal(const string sufijo)
  {
   MqlDateTime dt;
   TimeToStruct(TimeCurrent(), dt);
   string diaStr = StringFormat("%04d%02d%02d", dt.year, dt.mon, dt.day);
   return StringFormat("EA_%s_%s_%d_%s", _Symbol, sufijo, (int)InpMagicNumber, diaStr);
  }

double ATR_M15_Cerrado()
  {
   double buf[];
   ArraySetAsSeries(buf, true);
   if(CopyBuffer(g_handleATRM15, 0, 1, 1, buf) < 1)
      return 0.0;
   return buf[0];
  }

//======================================================================
// MÓDULO 1: SWINGS DE ESTRUCTURA (idéntico a Baseline 1 -- escáner de
// pivotes genérico, confirmado sin look-ahead: un swing en "shift" sólo
// se considera confirmado cuando ya han cerrado "rightBars" velas más
// después de él; el barrido nunca lee una vela aún no formada).
//======================================================================
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

//--- Devuelve el swing CONFIRMADO más reciente (high si esHigh=true, low si
//    esHigh=false) cuyo timestamp de pivote sea estrictamente posterior a
//    "despuesDe". Usado para que la secuencia de pivotes de B siempre se
//    re-ancle al candidato más reciente disponible (evita quedarse
//    enganchada para siempre en el primer candidato si aparece uno mejor).
bool UltimoSwingDespuesDe(const bool esHigh, const ENUM_TIMEFRAMES tf, const int leftBars, const int rightBars,
                           const int barrasEscaneo, const datetime despuesDe, datetime &tiempoPivote, double &precio)
  {
   datetime t[]; double v[];
   int n = esHigh ? RecopilarSwingHighs(tf, leftBars, rightBars, barrasEscaneo, barrasEscaneo, t, v)
                  : RecopilarSwingLows(tf, leftBars, rightBars, barrasEscaneo, barrasEscaneo, t, v);
   for(int i = 0; i < n; i++)
      if(t[i] > despuesDe)
        {
         tiempoPivote = t[i];
         precio = v[i];
         return true;
        }
   return false;
  }

//======================================================================
// MÓDULO 2: TENDENCIA H1 (EMA200 + estructura) -- adaptado de Baseline 1,
// retimetrizado a H1 con swings 3/3 fijos para esta primera evaluación.
//======================================================================
void ActualizarRegimenH1()
  {
   double emaBuf[];
   ArraySetAsSeries(emaBuf, true);
   if(CopyBuffer(g_handleEMAH1, 0, 1, 1, emaBuf) < 1)
     {
      g_regimenH1 = REGIMEN_INDEFINIDO;
      return;
     }
   double cierre = iClose(_Symbol, PERIOD_H1, 1);
   bool porEncimaEMA = (cierre > emaBuf[0]);
   bool porDebajoEMA = (cierre < emaBuf[0]);

   int necesarios = InpH1SwingsAConfirmar + 1;
   datetime tH[], tL[];
   double   vH[], vL[];
   int nH = RecopilarSwingHighs(PERIOD_H1, InpSwingLeftH1, InpSwingRightH1, InpH1HistorialBarras, necesarios, tH, vH);
   int nL = RecopilarSwingLows(PERIOD_H1, InpSwingLeftH1, InpSwingRightH1, InpH1HistorialBarras, necesarios, tL, vL);

   if(nH < necesarios || nL < necesarios)
     {
      g_regimenH1 = REGIMEN_INDEFINIDO;
      return;
     }

   bool hhCrecientes = true, hlCrecientes = true;
   bool lhDecrecientes = true, llDecrecientes = true;
   for(int i = 0; i < InpH1SwingsAConfirmar; i++)
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

   if(nuevoRegimen != g_regimenH1)
      PrintFormat("[DIAG] Régimen H1 cambia de %s a %s (cierre=%.2f EMA200=%.2f)",
                  NombreRegimen(g_regimenH1), NombreRegimen(nuevoRegimen), cierre, emaBuf[0]);
   g_regimenH1 = nuevoRegimen;
  }

//======================================================================
// MÓDULO 3: SECUENCIA DE PIVOTES M15 (pullback) -- común a ambas
// direcciones mediante "esCompra"; ver mapeo de nombres en la cabecera
// de la struct SConfigPullback.
//======================================================================
void AvanzarSecuencia(SConfigPullback &cfg)
  {
   bool c = cfg.esCompra;
   datetime t; double p;
   int segundosM15 = PeriodSeconds(PERIOD_M15);

   if(cfg.estado == CFG_BUSCANDO_IMPULSO)
     {
      // Paso a: origen -- swing low (compra) / swing high (venta) más reciente, sin anclar a nada
      if(!UltimoSwingDespuesDe(!c, PERIOD_M15, InpSwingLeftM15, InpSwingRightM15, InpM15HistorialBarras, 0, t, p))
         return;
      datetime tOrigen = t; double pOrigen = p;

      // Paso b: impulso -- swing opuesto más reciente después del origen
      if(!UltimoSwingDespuesDe(c, PERIOD_M15, InpSwingLeftM15, InpSwingRightM15, InpM15HistorialBarras, tOrigen, t, p))
         return;
      datetime tImpulso = t; double pImpulso = p;

      double atr = ATR_M15_Cerrado();
      if(atr <= 0.0) return;
      double rango = c ? (pImpulso - pOrigen) : (pOrigen - pImpulso);
      if(rango < InpImpulsoMinATR * atr)
         return; // impulso insuficiente con este par; se reevalúa en la próxima vela (origen/impulso pueden actualizarse)

      cfg.origenTiempoPivote = tOrigen; cfg.origenPrecio = pOrigen;
      cfg.impulsoTiempoPivote = tImpulso; cfg.impulsoPrecio = pImpulso;
      cfg.impulsoTiempoConfirmacion = tImpulso + InpSwingRightM15 * segundosM15;
      cfg.estado = CFG_ESPERANDO_RETROCESO;
      PrintFormat("[DIAG-SEC] %s: impulso confirmado origen=%.2f@%s impulso=%.2f@%s (ATR=%.2f)",
                  c ? "COMPRA" : "VENTA", pOrigen, TimeToString(tOrigen, TIME_DATE|TIME_MINUTES),
                  pImpulso, TimeToString(tImpulso, TIME_DATE|TIME_MINUTES), atr);
      return;
     }

   if(cfg.estado == CFG_ESPERANDO_RETROCESO)
     {
      // Paso c: retroceso -- swing del mismo tipo que el origen, más reciente, después del impulso
      if(!UltimoSwingDespuesDe(!c, PERIOD_M15, InpSwingLeftM15, InpSwingRightM15, InpM15HistorialBarras,
                                cfg.impulsoTiempoPivote, t, p))
         return;

      bool invalidaOrigen = c ? (p <= cfg.origenPrecio) : (p >= cfg.origenPrecio);
      if(invalidaOrigen)
        {
         CancelarConfig(cfg, "ESTRUCTURA_INVALIDADA_EN_RETROCESO");
         return;
        }

      cfg.retrocesoTiempoPivote = t; cfg.retrocesoPrecio = p;
      cfg.retrocesoTiempoConfirmacion = t + InpSwingRightM15 * segundosM15;
      cfg.estado = CFG_ESPERANDO_EXTREMO;
      return;
     }

   if(cfg.estado == CFG_ESPERANDO_EXTREMO)
     {
      // Paso d: extremo relevante -- swing del mismo tipo que el impulso, más reciente,
      // después del retroceso, y que quede "decreciente" (compra) / "creciente" (venta)
      // respecto al impulso -- este es el nivel cuya ruptura dispara la entrada.
      if(!UltimoSwingDespuesDe(c, PERIOD_M15, InpSwingLeftM15, InpSwingRightM15, InpM15HistorialBarras,
                                cfg.retrocesoTiempoPivote, t, p))
         return;

      bool superaImpulso = c ? (p >= cfg.impulsoPrecio) : (p <= cfg.impulsoPrecio);
      if(superaImpulso)
        {
         // El rebote del retroceso ya alcanzó/superó el impulso original antes de formar
         // un máximo/mínimo cualificado por debajo/encima de él -- la secuencia a-e tal
         // como está definida no puede completarse con este par; se cancela (no se
         // inventa una regla de entrada distinta) y se vuelve a buscar un impulso nuevo.
         CancelarConfig(cfg, "RETROCESO_SUPERO_IMPULSO_SIN_EXTREMO");
         return;
        }

      cfg.extremoTiempoPivote = t; cfg.extremoPrecio = p;
      cfg.extremoTiempoConfirmacion = t + InpSwingRightM15 * segundosM15;
      cfg.estado = CFG_ARMADA;
      PrintFormat("[DIAG-SEC] %s: extremo relevante confirmado=%.2f@%s (armada, expira en %d velas desde la confirmación)",
                  c ? "COMPRA" : "VENTA", p, TimeToString(t, TIME_DATE|TIME_MINUTES), InpMaxVelasConfigArmada);
      return;
     }
   // CFG_ARMADA: nada que avanzar aquí -- se gestiona en ProcesarCancelaciones() y en
   // la comprobación de ruptura del bucle principal.
  }

//--- Cancelaciones: SIEMPRE se comprueban antes que cualquier ruptura/entrada (ver
//    OnTick) -- por construcción, el nivel de invalidación de origen y el extremo
//    relevante quedan en lados opuestos del rango (origen < retroceso < extremo en
//    compra, y al revés en venta), así que un único precio de cierre nunca puede
//    disparar ambos a la vez; el único caso real a resolver es el orden H1-antes-M15,
//    ya garantizado por el orden de llamadas en OnTick().
void ProcesarCancelaciones(SConfigPullback &cfg)
  {
   if(cfg.estado == CFG_BUSCANDO_IMPULSO)
      return;

   ENUM_REGIMEN regimenRequerido = cfg.esCompra ? REGIMEN_ALCISTA : REGIMEN_BAJISTA;
   if(g_regimenH1 != regimenRequerido)
     {
      CancelarConfig(cfg, "REGIMEN_CAMBIO");
      return;
     }

   double cierre1 = iClose(_Symbol, PERIOD_M15, 1);
   bool rompioOrigen = cfg.esCompra ? (cierre1 < cfg.origenPrecio) : (cierre1 > cfg.origenPrecio);
   if(rompioOrigen)
     {
      CancelarConfig(cfg, "ESTRUCTURA_INVALIDADA");
      return;
     }

   if(cfg.estado == CFG_ARMADA)
     {
      long velasTranscurridas = (long)((iTime(_Symbol, PERIOD_M15, 1) - cfg.extremoTiempoConfirmacion) / PeriodSeconds(PERIOD_M15));
      if(velasTranscurridas > InpMaxVelasConfigArmada)
        {
         CancelarConfig(cfg, "EXPIRADA");
         return;
        }
     }
  }

//======================================================================
// MÓDULO 4: VOLUMEN CON LÍMITE ESTRICTO DE RIESGO (sin clamp ascendente)
//======================================================================
// OrderCalcProfit() estima la pérdida entre dos precios dados usando las
// especificaciones ACTUALES del símbolo -- no incluye comisión, swap,
// deslizamiento de ejecución futuro ni gaps. El riesgo real tras la
// ejecución se recalcula por separado con el precio de ejecución
// confirmado por el bróker (ver OnTradeTransaction).
//----------------------------------------------------------------------
struct SResultadoVolumen
  {
   bool   aprobado;
   double volumen;
   double riesgoEstimado;
   double perdidaPorLoteEstimada;
   string motivoRechazo;
  };

SResultadoVolumen CalcularVolumenConLimiteRiesgo(const ENUM_ORDER_TYPE tipoOrden, const double precioEntrada,
                                                  const double precioSL, const double riesgoObjetivoMonetario)
  {
   SResultadoVolumen r;
   r.aprobado = false; r.volumen = 0.0; r.riesgoEstimado = 0.0; r.perdidaPorLoteEstimada = 0.0; r.motivoRechazo = "";

   double perdidaPorLote;
   if(!OrderCalcProfit(tipoOrden, _Symbol, 1.0, precioEntrada, precioSL, perdidaPorLote))
     {
      r.motivoRechazo = "ERROR_ORDERCALCPROFIT";
      return r;
     }
   perdidaPorLote = MathAbs(perdidaPorLote);
   if(perdidaPorLote <= 0.0)
     {
      r.motivoRechazo = "SL_INVALIDO";
      return r;
     }
   r.perdidaPorLoteEstimada = perdidaPorLote;

   double volStep = SymbolInfoDouble(_Symbol, SYMBOL_VOLUME_STEP);
   double volMin  = SymbolInfoDouble(_Symbol, SYMBOL_VOLUME_MIN);
   double volMax  = SymbolInfoDouble(_Symbol, SYMBOL_VOLUME_MAX);

   double volumenTeorico    = riesgoObjetivoMonetario / perdidaPorLote;
   double volumenRedondeado = MathFloor(volumenTeorico / volStep) * volStep; // SOLO hacia abajo

   if(volumenRedondeado < volMin)
     {
      // Nunca se sube al mínimo del bróker: si el mínimo ya excede el riesgo
      // autorizado, se rechaza la operación en vez de operar con más riesgo del previsto.
      r.motivoRechazo = "VOLUMEN_MINIMO_EXCEDE_RIESGO";
      return r;
     }

   double volumenFinal = MathMin(volumenRedondeado, volMax);
   double riesgoFinal  = volumenFinal * perdidaPorLote;

   if(riesgoFinal > riesgoObjetivoMonetario)
     {
      // Red de seguridad adicional; no debería dispararse si el floor fue correcto.
      r.motivoRechazo = "RIESGO_EXCEDIDO_POR_REDONDEO";
      return r;
     }

   r.aprobado       = true;
   r.volumen        = NormalizeDouble(volumenFinal, 2);
   r.riesgoEstimado = riesgoFinal;
   return r;
  }

//======================================================================
// MÓDULO 5: VALIDACIÓN DE SL/TP FRENTE AL BRÓKER
//======================================================================
// NormalizeDouble() por sí solo no garantiza que una orden sea aceptada --
// esto comprueba además la distancia mínima exigida por el símbolo
// (SYMBOL_TRADE_STOPS_LEVEL). SYMBOL_TRADE_FREEZE_LEVEL no aplica al envío
// inicial (sólo restringe modificar/cerrar una orden ya colocada muy cerca
// del precio -- relevante para GestionarBreakeven()/GestionarTrailingStop(),
// no para esta validación). trade.SetDeviationInPoints() tampoco es una
// garantía de ejecución exacta: sólo acota cuánto slippage se tolera antes
// de que el bróker rechace la orden; el slippage real siempre se mide
// después con el precio de ejecución confirmado.
//----------------------------------------------------------------------
bool ValidarSLTP(const double precioEntrada, double &SL, double &TP, string &motivoRechazo)
  {
   int digits = (int)SymbolInfoInteger(_Symbol, SYMBOL_DIGITS);
   SL = NormalizeDouble(SL, digits);
   TP = NormalizeDouble(TP, digits);

   long stopsLevelPuntos = SymbolInfoInteger(_Symbol, SYMBOL_TRADE_STOPS_LEVEL);
   double distSLpuntos = MathAbs(precioEntrada - SL) / _Point;
   double distTPpuntos = MathAbs(TP - precioEntrada) / _Point;

   if(distSLpuntos <= (double)stopsLevelPuntos)
     {
      motivoRechazo = "SL_DEMASIADO_CERCA";
      return false;
     }
   if(distTPpuntos <= (double)stopsLevelPuntos)
     {
      motivoRechazo = "TP_DEMASIADO_CERCA";
      return false;
     }
   return true;
  }

//======================================================================
// MÓDULO 6: FILTROS DE PROTECCIÓN (copiados sin cambios de Baseline 1)
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
   if(g_balanceInicioDia <= 0.0) return;
   if(g_killSwitchActivo) return;

   double equityActual    = AccountInfoDouble(ACCOUNT_EQUITY);
   double perdidaDiaria   = g_balanceInicioDia - equityActual;
   double perdidaDiariaPct = (perdidaDiaria / g_balanceInicioDia) * 100.0;

   if(perdidaDiariaPct >= InpMaxDailyLossPercent)
     {
      PrintFormat("KILL SWITCH ACTIVADO: pérdida diaria %.2f%% >= límite %.2f%%. Cerrando todo.",
                  perdidaDiariaPct, InpMaxDailyLossPercent);
      CerrarTodasLasPosiciones();
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
   if(!InpCerrarViernes) return false;
   datetime horaNY = ConvertirServidorANuevaYork(TimeCurrent());
   MqlDateTime dt;
   TimeToStruct(horaNY, dt);
   return (dt.day_of_week == 5 && dt.hour >= InpFridayCloseHourNY);
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

//======================================================================
// MÓDULO 7: GESTIÓN DE POSICIÓN (BREAKEVEN / TRAILING / CIERRE PARCIAL)
// -- copiado sin cambios de Baseline 1 --
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
      if(riesgo <= 0.0) return;

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
            else
               PrintFormat("[DIAG] Breakeven FALLIDO en compra #%I64u (posible FREEZE_LEVEL): %s", ticket, trade.ResultComment());
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
            else
               PrintFormat("[DIAG] Breakeven FALLIDO en venta #%I64u (posible FREEZE_LEVEL): %s", ticket, trade.ResultComment());
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
      if(riesgo <= 0.0) return;

      double slActual = PositionGetDouble(POSITION_SL);
      double tpActual = PositionGetDouble(POSITION_TP);
      ENUM_POSITION_TYPE tipo = (ENUM_POSITION_TYPE)PositionGetInteger(POSITION_TYPE);

      double precioActual = (tipo == POSITION_TYPE_BUY) ? SymbolInfoDouble(_Symbol, SYMBOL_BID)
                                                          : SymbolInfoDouble(_Symbol, SYMBOL_ASK);
      double currentR = (tipo == POSITION_TYPE_BUY) ? (precioActual - precioApertura) / riesgo
                                                      : (precioApertura - precioActual) / riesgo;

      if(currentR < InpCierreParcialTriggerR) return;

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
         else
            PrintFormat("[DIAG] Trailing FALLIDO en posición #%I64u (posible FREEZE_LEVEL): %s", ticket, trade.ResultComment());
        }
      return;
     }
  }

//======================================================================
// MÓDULO 8: INTENTO ÚNICO DE ENTRADA
//======================================================================
// Una vez detectada la ruptura (paso e), se hace EXACTAMENTE un intento.
// Si se bloquea por cualquier motivo (spread, riesgo, distancia al SL,
// margen, kill switch, circuito de pérdidas, fin de semana, rechazo del
// servidor), la configuración se consume -- no se reintenta en velas
// posteriores a un precio potencialmente peor.
//----------------------------------------------------------------------
void ConsumirConfig(SConfigPullback &cfg)
  {
   ResetearConfig(cfg, cfg.esCompra);
  }

void EscribirFilaLog(const bool ejecutada, const string motivoRechazo);

void IntentarEntradaUnica(SConfigPullback &cfg)
  {
   bool esCompra = cfg.esCompra;
   double bidAntes = SymbolInfoDouble(_Symbol, SYMBOL_BID);
   double askAntes = SymbolInfoDouble(_Symbol, SYMBOL_ASK);
   double precioEstimado = esCompra ? askAntes : bidAntes;

   double atr = ATR_M15_Cerrado();
   double spreadPrecio = askAntes - bidAntes;
   double buffer = MathMax(spreadPrecio, InpSLBufferATRMult * atr);

   double SL = esCompra ? (cfg.retrocesoPrecio - buffer) : (cfg.retrocesoPrecio + buffer);
   double TP = esCompra ? (precioEstimado + MathAbs(precioEstimado - SL) * InpRiskRewardRatio)
                         : (precioEstimado - MathAbs(precioEstimado - SL) * InpRiskRewardRatio);

   // Datos de latencia/diagnóstico comunes a cualquier resultado (ejecutada o no)
   g_logPendiente.tOrigen            = cfg.origenTiempoPivote;
   g_logPendiente.tImpulsoPivote     = cfg.impulsoTiempoPivote;
   g_logPendiente.tImpulsoConfirm    = cfg.impulsoTiempoConfirmacion;
   g_logPendiente.tRetrocesoPivote   = cfg.retrocesoTiempoPivote;
   g_logPendiente.tRetrocesoConfirm  = cfg.retrocesoTiempoConfirmacion;
   g_logPendiente.tExtremoPivote     = cfg.extremoTiempoPivote;
   g_logPendiente.tExtremoConfirm    = cfg.extremoTiempoConfirmacion;
   g_logPendiente.tRuptura           = iTime(_Symbol, PERIOD_M15, 1);
   g_logPendiente.velasImpulsoARuptura = (int)((g_logPendiente.tRuptura - cfg.impulsoTiempoConfirmacion) / PeriodSeconds(PERIOD_M15));
   g_logPendiente.esCompra           = esCompra;
   g_logPendiente.precioRupturaCierre = iClose(_Symbol, PERIOD_M15, 1);
   g_logPendiente.bidAntesEnvio      = bidAntes;
   g_logPendiente.askAntesEnvio      = askAntes;
   g_logPendiente.precioSolicitado   = precioEstimado;
   g_logPendiente.sl                = SL;
   g_logPendiente.tp                = TP;
   g_logPendiente.buffer            = buffer;
   g_logPendiente.spreadEnEntrada   = spreadPrecio;
   g_logPendiente.precioRealEjecucion = 0.0;
   g_logPendiente.volumen           = 0.0;
   g_logPendiente.riesgoObjetivoMonetario = AccountInfoDouble(ACCOUNT_BALANCE) * (InpRiskPercent / 100.0);
   g_logPendiente.riesgoEstimadoPreEjecucion = 0.0;
   g_logPendiente.riesgoRealPostEjecucion = 0.0;

   string motivo = "";
   if(!ValidarSLTP(precioEstimado, SL, TP, motivo))
     {
      g_logPendiente.sl = SL; g_logPendiente.tp = TP;
      EscribirFilaLog(false, motivo);
      ConsumirConfig(cfg);
      return;
     }

   if(!SpreadPermitido())
     { EscribirFilaLog(false, "SPREAD_ALTO"); ConsumirConfig(cfg); return; }
   if(g_killSwitchActivo)
     { EscribirFilaLog(false, "KILL_SWITCH"); ConsumirConfig(cfg); return; }
   if(g_circuitoPerdidasActivo)
     { EscribirFilaLog(false, "CIRCUITO_PERDIDAS"); ConsumirConfig(cfg); return; }
   if(DebeCerrarPorFinDeSemana())
     { EscribirFilaLog(false, "FIN_DE_SEMANA"); ConsumirConfig(cfg); return; }

   ENUM_ORDER_TYPE tipoOrden = esCompra ? ORDER_TYPE_BUY : ORDER_TYPE_SELL;
   SResultadoVolumen rv = CalcularVolumenConLimiteRiesgo(tipoOrden, precioEstimado, SL, g_logPendiente.riesgoObjetivoMonetario);
   if(!rv.aprobado)
     { EscribirFilaLog(false, rv.motivoRechazo); ConsumirConfig(cfg); return; }

   g_logPendiente.volumen = rv.volumen;
   g_logPendiente.perdidaPorLoteEstimada = rv.perdidaPorLoteEstimada;
   g_logPendiente.riesgoEstimadoPreEjecucion = rv.riesgoEstimado;

   double margenRequerido;
   if(!OrderCalcMargin(tipoOrden, _Symbol, rv.volumen, precioEstimado, margenRequerido) ||
      margenRequerido > AccountInfoDouble(ACCOUNT_MARGIN_FREE))
     { EscribirFilaLog(false, "MARGEN_INSUFICIENTE"); ConsumirConfig(cfg); return; }

   trade.SetExpertMagicNumber(InpMagicNumber);
   trade.SetDeviationInPoints(InpMaxDeviationPoints);

   // IMPORTANTE: en el Strategy Tester, OnTradeTransaction() se dispara de forma
   // SÍNCRONA durante la propia llamada a trade.Buy()/Sell() -- puede llegar antes
   // de que esta función recupere el control. Por eso g_hayLogPendiente se marca
   // ANTES de enviar la orden (no después, como en una primera versión que dejó
   // el CSV completamente vacío: OnTradeTransaction veía siempre g_hayLogPendiente
   // en false y se salía sin capturar nada, para cualquier operación).
   g_hayLogPendiente = true;

   bool enviado = esCompra ? trade.Buy(rv.volumen, _Symbol, 0.0, SL, TP, "TrendPullback_Compra")
                            : trade.Sell(rv.volumen, _Symbol, 0.0, SL, TP, "TrendPullback_Venta");

   if(!enviado)
     {
      g_hayLogPendiente = false;
      string desc = StringFormat("ORDEN_RECHAZADA_SERVIDOR:%d:%s", trade.ResultRetcode(), trade.ResultRetcodeDescription());
      EscribirFilaLog(false, desc);
      ConsumirConfig(cfg);
      return;
     }

   // La orden se envió correctamente: queda pendiente de confirmar en
   // OnTradeTransaction (DEAL_ENTRY_IN), que es la fuente autorizada del
   // precio y volumen REALMENTE ejecutados -- nunca se registra como
   // ejecutada una orden que MT5 no haya confirmado por esa vía.
   ConsumirConfig(cfg);
  }

//======================================================================
// MÓDULO 9: LOG CSV
//======================================================================
void EscribirCabeceraSiHaceFalta(const int handle)
  {
   if(FileSize(handle) == 0)
      FileWrite(handle,
                "Estado", "MotivoRechazo", "Direccion",
                "TiempoOrigen", "TiempoImpulsoPivote", "TiempoImpulsoConfirmacion",
                "TiempoRetrocesoPivote", "TiempoRetrocesoConfirmacion",
                "TiempoExtremoPivote", "TiempoExtremoConfirmacion",
                "TiempoRuptura", "VelasImpulsoARuptura",
                "PrecioRupturaCierre", "BidAntesEnvio", "AskAntesEnvio", "PrecioSolicitado", "PrecioRealEjecucion",
                "SL", "TP", "Buffer", "Volumen", "PerdidaPorLoteEstimada",
                "RiesgoObjetivoMonetario", "RiesgoEstimadoPreEjecucion", "RiesgoRealPostEjecucion",
                "SpreadEnEntrada", "RegimenH1",
                "TiempoCierre", "ResultadoMonetario", "DuracionMinutos", "DrawdownDuranteTrade");
  }

//--- Escribe una fila para un intento RECHAZADO (nunca llegó a abrir posición)
void EscribirFilaLog(const bool ejecutada, const string motivoRechazo)
  {
   if(!InpRegistrarCSV) return;
   int handle = FileOpen(InpNombreArchivoCSV, FILE_READ | FILE_WRITE | FILE_CSV | FILE_ANSI, ';');
   if(handle == INVALID_HANDLE)
     {
      PrintFormat("No se pudo abrir el archivo de log CSV '%s' (error %d).", InpNombreArchivoCSV, GetLastError());
      return;
     }
   EscribirCabeceraSiHaceFalta(handle);
   FileSeek(handle, 0, SEEK_END);

   FileWrite(handle,
             ejecutada ? "EJECUTADA" : "RECHAZADA", motivoRechazo, g_logPendiente.esCompra ? "COMPRA" : "VENTA",
             TimeToString(g_logPendiente.tOrigen, TIME_DATE|TIME_SECONDS),
             TimeToString(g_logPendiente.tImpulsoPivote, TIME_DATE|TIME_SECONDS),
             TimeToString(g_logPendiente.tImpulsoConfirm, TIME_DATE|TIME_SECONDS),
             TimeToString(g_logPendiente.tRetrocesoPivote, TIME_DATE|TIME_SECONDS),
             TimeToString(g_logPendiente.tRetrocesoConfirm, TIME_DATE|TIME_SECONDS),
             TimeToString(g_logPendiente.tExtremoPivote, TIME_DATE|TIME_SECONDS),
             TimeToString(g_logPendiente.tExtremoConfirm, TIME_DATE|TIME_SECONDS),
             TimeToString(g_logPendiente.tRuptura, TIME_DATE|TIME_SECONDS),
             g_logPendiente.velasImpulsoARuptura,
             DoubleToString(g_logPendiente.precioRupturaCierre, _Digits),
             DoubleToString(g_logPendiente.bidAntesEnvio, _Digits),
             DoubleToString(g_logPendiente.askAntesEnvio, _Digits),
             DoubleToString(g_logPendiente.precioSolicitado, _Digits),
             DoubleToString(g_logPendiente.precioRealEjecucion, _Digits),
             DoubleToString(g_logPendiente.sl, _Digits),
             DoubleToString(g_logPendiente.tp, _Digits),
             DoubleToString(g_logPendiente.buffer, _Digits),
             DoubleToString(g_logPendiente.volumen, 2),
             DoubleToString(g_logPendiente.perdidaPorLoteEstimada, 2),
             DoubleToString(g_logPendiente.riesgoObjetivoMonetario, 2),
             DoubleToString(g_logPendiente.riesgoEstimadoPreEjecucion, 2),
             DoubleToString(g_logPendiente.riesgoRealPostEjecucion, 2),
             DoubleToString(g_logPendiente.spreadEnEntrada, _Digits),
             NombreRegimen(g_regimenH1),
             "", "", "", "");
   FileClose(handle);
  }

//--- Escribe la fila completa (apertura + cierre) de una operación EJECUTADA, al cerrarla
void RegistrarOperacionEjecutadaEnCSV(const double resultadoMonetario, const datetime horaCierre)
  {
   if(!InpRegistrarCSV) return;
   int handle = FileOpen(InpNombreArchivoCSV, FILE_READ | FILE_WRITE | FILE_CSV | FILE_ANSI, ';');
   if(handle == INVALID_HANDLE)
     {
      PrintFormat("No se pudo abrir el archivo de log CSV '%s' (error %d).", InpNombreArchivoCSV, GetLastError());
      return;
     }
   EscribirCabeceraSiHaceFalta(handle);
   FileSeek(handle, 0, SEEK_END);

   double duracionMin = (double)(horaCierre - g_logOperacionActiva.horaApertura) / 60.0;
   double drawdownTrade = AccountInfoDouble(ACCOUNT_BALANCE) - g_logOperacionActiva.equityMinimaDurante;
   if(drawdownTrade < 0.0) drawdownTrade = 0.0;

   FileWrite(handle,
             "EJECUTADA", "", g_logOperacionActiva.esCompra ? "COMPRA" : "VENTA",
             TimeToString(g_logOperacionActiva.tOrigen, TIME_DATE|TIME_SECONDS),
             TimeToString(g_logOperacionActiva.tImpulsoPivote, TIME_DATE|TIME_SECONDS),
             TimeToString(g_logOperacionActiva.tImpulsoConfirm, TIME_DATE|TIME_SECONDS),
             TimeToString(g_logOperacionActiva.tRetrocesoPivote, TIME_DATE|TIME_SECONDS),
             TimeToString(g_logOperacionActiva.tRetrocesoConfirm, TIME_DATE|TIME_SECONDS),
             TimeToString(g_logOperacionActiva.tExtremoPivote, TIME_DATE|TIME_SECONDS),
             TimeToString(g_logOperacionActiva.tExtremoConfirm, TIME_DATE|TIME_SECONDS),
             TimeToString(g_logOperacionActiva.tRuptura, TIME_DATE|TIME_SECONDS),
             g_logOperacionActiva.velasImpulsoARuptura,
             DoubleToString(g_logOperacionActiva.precioRupturaCierre, _Digits),
             DoubleToString(g_logOperacionActiva.bidAntesEnvio, _Digits),
             DoubleToString(g_logOperacionActiva.askAntesEnvio, _Digits),
             DoubleToString(g_logOperacionActiva.precioSolicitado, _Digits),
             DoubleToString(g_logOperacionActiva.precioRealEjecucion, _Digits),
             DoubleToString(g_logOperacionActiva.sl, _Digits),
             DoubleToString(g_logOperacionActiva.tp, _Digits),
             DoubleToString(g_logOperacionActiva.buffer, _Digits),
             DoubleToString(g_logOperacionActiva.volumen, 2),
             DoubleToString(g_logOperacionActiva.perdidaPorLoteEstimada, 2),
             DoubleToString(g_logOperacionActiva.riesgoObjetivoMonetario, 2),
             DoubleToString(g_logOperacionActiva.riesgoEstimadoPreEjecucion, 2),
             DoubleToString(g_logOperacionActiva.riesgoRealPostEjecucion, 2),
             DoubleToString(g_logOperacionActiva.spreadEnEntrada, _Digits),
             NombreRegimen(g_regimenH1),
             TimeToString(horaCierre, TIME_DATE|TIME_SECONDS),
             DoubleToString(resultadoMonetario, 2),
             DoubleToString(duracionMin, 1),
             DoubleToString(drawdownTrade, 2));
   FileClose(handle);
  }

//======================================================================
// DETECCIÓN DE VELA NUEVA
//======================================================================
bool EsVelaNuevaH1()
  {
   datetime horaVelaActual = iTime(_Symbol, PERIOD_H1, 0);
   if(horaVelaActual != g_ultimaVelaH1Procesada)
     {
      g_ultimaVelaH1Procesada = horaVelaActual;
      return true;
     }
   return false;
  }

bool EsVelaNuevaM15()
  {
   datetime horaVelaActual = iTime(_Symbol, PERIOD_M15, 0);
   if(horaVelaActual != g_ultimaVelaM15Procesada)
     {
      g_ultimaVelaM15Procesada = horaVelaActual;
      return true;
     }
   return false;
  }

//======================================================================
// EVENTOS DEL EXPERT ADVISOR
//======================================================================
int OnInit()
  {
   g_handleEMAH1 = iMA(_Symbol, PERIOD_H1, InpEMAH1Period, 0, MODE_EMA, PRICE_CLOSE);
   if(g_handleEMAH1 == INVALID_HANDLE)
     {
      Print("Error al crear la EMA de tendencia H1.");
      return(INIT_FAILED);
     }

   g_handleATRM15 = iATR(_Symbol, PERIOD_M15, InpATRPeriodM15);
   if(g_handleATRM15 == INVALID_HANDLE)
     {
      Print("Error al crear el ATR M15.");
      return(INIT_FAILED);
     }

   trade.SetExpertMagicNumber(InpMagicNumber);

   ResetearConfig(g_cfgCompra, true);
   ResetearConfig(g_cfgVenta, false);

   g_diaActual = 0;
   GestionarCambioDeDia();
   ActualizarRegimenH1();

   g_ultimaVelaH1Procesada  = iTime(_Symbol, PERIOD_H1, 0);
   g_ultimaVelaM15Procesada = iTime(_Symbol, PERIOD_M15, 0);

   return(INIT_SUCCEEDED);
  }

void OnDeinit(const int reason)
  {
   if(g_handleEMAH1 != INVALID_HANDLE) IndicatorRelease(g_handleEMAH1);
   if(g_handleATRM15 != INVALID_HANDLE) IndicatorRelease(g_handleATRM15);
  }

void OnTradeTransaction(const MqlTradeTransaction &trans,
                         const MqlTradeRequest &request,
                         const MqlTradeResult &result)
  {
   if(trans.type != TRADE_TRANSACTION_DEAL_ADD) return;
   if(!HistoryDealSelect(trans.deal)) return;
   if(HistoryDealGetString(trans.deal, DEAL_SYMBOL) != _Symbol) return;
   if(HistoryDealGetInteger(trans.deal, DEAL_MAGIC) != (long)InpMagicNumber) return;

   ENUM_DEAL_ENTRY tipoEntrada = (ENUM_DEAL_ENTRY)HistoryDealGetInteger(trans.deal, DEAL_ENTRY);

   // --- Apertura: confirmar con los datos REALES del bróker, no con lo
   //     estimado antes de enviar la orden ---
   if(tipoEntrada == DEAL_ENTRY_IN)
     {
      if(!g_hayLogPendiente)
         return; // apertura no originada por este módulo (no debería ocurrir)

      double precioRealEjecucion = HistoryDealGetDouble(trans.deal, DEAL_PRICE);
      double volumenRealEjecutado = HistoryDealGetDouble(trans.deal, DEAL_VOLUME);

      if(volumenRealEjecutado < g_logPendiente.volumen)
         PrintFormat("[DIAG] EJECUCION_PARCIAL: solicitado=%.2f ejecutado=%.2f", g_logPendiente.volumen, volumenRealEjecutado);

      ENUM_ORDER_TYPE tipoOrdenReal = g_logPendiente.esCompra ? ORDER_TYPE_BUY : ORDER_TYPE_SELL;
      double perdidaPorLoteReal;
      double riesgoReal = 0.0;
      if(OrderCalcProfit(tipoOrdenReal, _Symbol, 1.0, precioRealEjecucion, g_logPendiente.sl, perdidaPorLoteReal))
         riesgoReal = volumenRealEjecutado * MathAbs(perdidaPorLoteReal);

      g_logPendiente.precioRealEjecucion = precioRealEjecucion;
      g_logPendiente.volumen = volumenRealEjecutado;
      g_logPendiente.riesgoRealPostEjecucion = riesgoReal;
      g_logPendiente.horaApertura = TimeCurrent();
      g_logPendiente.equityMinimaDurante = AccountInfoDouble(ACCOUNT_EQUITY);

      g_slOriginalPosicion    = g_logPendiente.sl;
      g_breakevenAplicado     = false;
      g_trailingActivado      = false;
      g_cierreParcialAplicado = false;

      g_logOperacionActiva = g_logPendiente;
      g_hayLogOperacionActiva = true;
      g_hayLogPendiente = false;

      PrintFormat("%s ejecutada: entrada=%.2f (estimado=%.2f) SL=%.2f TP=%.2f lotes=%.2f riesgoReal=%.2f (objetivo=%.2f)",
                  g_logOperacionActiva.esCompra ? "COMPRA" : "VENTA", precioRealEjecucion, g_logOperacionActiva.precioSolicitado,
                  g_logOperacionActiva.sl, g_logOperacionActiva.tp, volumenRealEjecutado, riesgoReal,
                  g_logOperacionActiva.riesgoObjetivoMonetario);
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
      RegistrarOperacionEjecutadaEnCSV(resultado, TimeCurrent());
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
      g_perdidasConsecutivasHoy = 0;
  }

void OnTick()
  {
   GestionarCambioDeDia();
   ComprobarKillSwitchDiario();
   if(g_killSwitchActivo) return;

   if(DebeCerrarPorFinDeSemana())
     {
      datetime velaActual = iTime(_Symbol, PERIOD_M15, 0);
      if(velaActual != g_ultimaVelaIntentoCierreFDS)
        {
         g_ultimaVelaIntentoCierreFDS = velaActual;
         if(HayPosicionAbierta())
           {
            Print("Cierre de fin de semana: liquidando posiciones flotantes.");
            CerrarTodasLasPosiciones();
           }
        }
      return;
     }

   if(g_hayLogOperacionActiva)
     {
      double equityActual = AccountInfoDouble(ACCOUNT_EQUITY);
      if(equityActual < g_logOperacionActiva.equityMinimaDurante)
         g_logOperacionActiva.equityMinimaDurante = equityActual;
     }

   // El régimen H1 se refresca SIEMPRE antes de cualquier comprobación de M15 --
   // incluso cuando ambas velas cierran en el mismo instante, el régimen usado
   // para cancelar/avanzar en esta misma vela ya es el actualizado.
   if(EsVelaNuevaH1())
      ActualizarRegimenH1();

   bool esVelaNuevaM15 = EsVelaNuevaM15();
   if(!esVelaNuevaM15)
      return; // toda la lógica de la secuencia opera únicamente al cierre de una vela M15

   // 1) Cancelaciones -- siempre antes que cualquier avance o entrada
   ProcesarCancelaciones(g_cfgCompra);
   ProcesarCancelaciones(g_cfgVenta);

   if(HayPosicionAbierta())
     {
      GestionarBreakeven();
      GestionarTrailingStop();
      return; // no se buscan configuraciones nuevas mientras hay una posición abierta
     }

   // 2) Avance de la secuencia, sólo en la dirección que el régimen H1 permite
   if(g_regimenH1 == REGIMEN_ALCISTA && g_cfgCompra.estado != CFG_ARMADA)
      AvanzarSecuencia(g_cfgCompra);
   if(g_regimenH1 == REGIMEN_BAJISTA && g_cfgVenta.estado != CFG_ARMADA)
      AvanzarSecuencia(g_cfgVenta);

   // 3) Ruptura (paso e) -- intento único si se cumple
   if(g_cfgCompra.estado == CFG_ARMADA && iClose(_Symbol, PERIOD_M15, 1) > g_cfgCompra.extremoPrecio)
      IntentarEntradaUnica(g_cfgCompra);
   if(g_cfgVenta.estado == CFG_ARMADA && iClose(_Symbol, PERIOD_M15, 1) < g_cfgVenta.extremoPrecio)
      IntentarEntradaUnica(g_cfgVenta);
  }
