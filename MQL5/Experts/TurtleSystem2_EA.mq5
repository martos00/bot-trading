//+------------------------------------------------------------------+
//|                                        TurtleSystem2_EA.mq5      |
//|  Turtle System 2 (Donchian 55/20, N=EMA20 del True Range,        |
//|  stop=2N, SIN piramidación, 1 unidad) -- candidata "ni descartada |
//|  ni validada" del README (ver sección "Nueva fase: estrategias   |
//|  documentadas de traders sistemáticos reales" y sus              |
//|  actualizaciones: prueba de estrés de swap, concentración        |
//|  temporal, IC95% por cluster-bootstrap). Esta es la PRIMERA       |
//|  candidata que pasa a fase de forward testing en DEMO -- NO       |
//|  se considera validada ni rentable de forma demostrada.           |
//|                                                                    |
//|  REGLAS CONGELADAS: ver MQL5/Include/TurtleSystem2_Core.mqh.      |
//|  Esas constantes (entrada 55d, salida 20d, N=EMA20, stop=2N) NO   |
//|  son parámetros de este EA a propósito -- no se puede "optimizar" |
//|  sin editar el código fuente y dejarlo documentado, cumpliendo    |
//|  el requisito explícito de no reoptimizar con los resultados de  |
//|  2023-2026.                                                       |
//|                                                                    |
//|  Un solo EA gestiona los 3 mercados (XAUUSD/USTEC/US500) desde    |
//|  UN SOLO gráfico -- así la correlación USTEC/US500 (ya            |
//|  documentada: disparan señal en fechas casi idénticas) se puede   |
//|  limitar en un único lugar con estado compartido, sin depender de |
//|  variables globales entre instancias separadas por símbolo.       |
//|                                                                    |
//|  DIFERENCIAS DELIBERADAS frente al backtest de Python             |
//|  (research/estrategia_turtle_trading.py), declaradas explícita-   |
//|  mente, no accidentales:                                          |
//|   1. Position sizing: Python mide todo en R-múltiplos (riesgo=2N  |
//|      en PUNTOS); este EA traduce ese riesgo a DINERO real         |
//|      (InpRiesgoPorOperacion_Pct % del equity si se toca el stop), |
//|      vía tick value/tick size/contract size/volumen mínimo -- el  |
//|      backtest nunca definió un tamaño de cuenta real, así que      |
//|      esto es una decisión de ejecución nueva, no una regla         |
//|      "congelada" que se esté reoptimizando.                        |
//|   2. Límite de riesgo agregado de cartera y reparto de riesgo      |
//|      USTEC/US500 cuando están en la MISMA dirección (budget        |
//|      compartido de 1,5x una unidad, no 2x) -- aplica directamente  |
//|      el hallazgo de correlación ya documentado en el README.       |
//|   3. El stop se delega en la orden SL real del bróker (ejecución   |
//|      intradía real, no una aproximación con velas diarias) --      |
//|      la salida por CANAL sigue evaluándose explícitamente al       |
//|      cierre de cada vela D1, igual que en Python.                  |
//|   4. El swap/financiación es el REAL del bróker (nunca asumido     |
//|      uniforme entre mercados) -- se registra en un log aparte.     |
//|   5. NO se añade breakeven/trailing/cierre parcial/kill-switch      |
//|      diario/cierre de viernes -- el backtest congelado no          |
//|      incluye nada de eso; añadirlo cambiaría la estrategia que se  |
//|      está poniendo a prueba.                                       |
//|                                                                    |
//|  ADVERTENCIA (pedida explícitamente): que este EA reproduzca el   |
//|  backtest de Python NO implica que la estrategia esté validada.   |
//|  Ver protocolo de validación en README antes de usar en DEMO.      |
//+------------------------------------------------------------------+
#property copyright "Bot Trading"
#property version   "1.00"
#property strict

#include <Trade\Trade.mqh>
#include <TurtleSystem2_Core.mqh>

//======================================================================
// PARÁMETROS DE ENTRADA
//======================================================================
input group "=== Universo (los 3 símbolos EXACTOS de tu bróker, separados por coma) ==="
input string InpSimbolos = "XAUUSD,USTEC,US500";

input group "=== Riesgo y position sizing (decisión de ejecución -- NO parte de la regla de señal congelada) ==="
input double InpRiesgoPorOperacion_Pct         = 1.0;  // % de equity arriesgado si se toca el stop (2N), por operación
input double InpRiesgoMaximoCartera_Pct        = 3.0;  // tope de riesgo abierto simultáneo, suma de las 3 posiciones
input double InpRiesgoCompartidoParUSTEC_US500 = 1.5;  // múltiplo de InpRiesgoPorOperacion_Pct que USTEC+US500 comparten cuando coinciden en dirección (hallazgo de correlación, ver README)

input group "=== Ejecución ==="
input ulong InpMagicNumber        = 20261016;
input int   InpMaxDeviationPoints = 50;
input int   InpHistorialBarrasD1  = 5000;   // barras D1 solicitadas para recalcular N/canales en cada evaluación

input group "=== Logs (carpeta MQL5/Files/ del terminal, o Tester/Files/ en el Strategy Tester) ==="
input bool   InpRegistrarCSV            = true;
input string InpArchivoLogOperaciones   = "TurtleSystem2_Operaciones.csv";
input string InpArchivoLogEquity        = "TurtleSystem2_Equity.csv";
input string InpArchivoLogSwaps         = "TurtleSystem2_SwapsReales.csv";
input int    InpEquitySnapshotSegundos  = 300;  // cada cuánto se registra un snapshot de equity/drawdown (timer)

//======================================================================
// ESTADO
//======================================================================
CTrade trade;

struct SEstadoSimbolo
  {
   string   simbolo;
   int      digits;
   bool     enPosicion;
   int      direccion;            // +1 largo, -1 corto, 0 sin posición
   double   nEntrada;
   double   precioEntradaReal;
   double   stopPrice;
   double   riesgoAsignadoPct;    // fijado en la apertura, no se recalcula mientras la posición está viva
   double   volumen;
   ulong    ticketPosicion;
   datetime ultimaBarraD1;
   datetime tiempoApertura;
   //--- log pendiente de confirmar en OnTradeTransaction
   bool     hayLogPendiente;
   datetime logTiempoSenal;
   double   logPrecioSolicitado;
   double   logSL;
   double   logVolumen;
   double   logRiesgoObjetivoMonetario;
   double   logRiesgoObjetivoPct;
   double   logN;
   int      logDireccion;
  };
SEstadoSimbolo g_estado[];

double   g_equityPico       = 0.0;
datetime g_ultimoLogSwaps   = 0;

//======================================================================
// UTILIDADES DE ESTADO
//======================================================================
int IndiceSimbolo(const string sym)
  {
   for(int i = 0; i < ArraySize(g_estado); i++)
      if(g_estado[i].simbolo == sym)
         return i;
   return -1;
  }

//--- Detecta si "sym" es USTEC o US500 (tolerante a sufijos del bróker) y
//    devuelve el índice del OTRO miembro del par gestionado por este EA,
//    o -1 si "sym" no es parte de ese par, o el par no está gestionado.
int IndiceParCorrelado(const int i)
  {
   string s = g_estado[i].simbolo;
   bool esUstec = (StringFind(s, "USTEC") >= 0) || (StringFind(s, "NAS100") >= 0);
   bool esUs500 = (StringFind(s, "US500") >= 0) || (StringFind(s, "SPX500") >= 0);
   if(!esUstec && !esUs500)
      return -1;
   for(int k = 0; k < ArraySize(g_estado); k++)
     {
      if(k == i) continue;
      string s2 = g_estado[k].simbolo;
      bool otroUstec = (StringFind(s2, "USTEC") >= 0) || (StringFind(s2, "NAS100") >= 0);
      bool otroUs500 = (StringFind(s2, "US500") >= 0) || (StringFind(s2, "SPX500") >= 0);
      if((esUstec && otroUs500) || (esUs500 && otroUstec))
         return k;
     }
   return -1;
  }

//--- Riesgo (% de equity) todavía disponible para una NUEVA entrada en el
//    símbolo i, con direccionNueva, respetando (a) el tope agregado de
//    cartera y (b) el presupuesto compartido USTEC/US500 cuando ambos
//    coinciden en dirección.
double RiesgoDisponiblePct(const int i, const int direccionNueva)
  {
   double riesgoComprometido = 0.0;
   for(int k = 0; k < ArraySize(g_estado); k++)
      if(g_estado[k].enPosicion)
         riesgoComprometido += g_estado[k].riesgoAsignadoPct;

   double disponibleCartera = InpRiesgoMaximoCartera_Pct - riesgoComprometido;
   if(disponibleCartera <= 0.0)
      return 0.0;

   int parIdx = IndiceParCorrelado(i);
   if(parIdx >= 0 && g_estado[parIdx].enPosicion && g_estado[parIdx].direccion == direccionNueva)
     {
      double presupuestoPar  = InpRiesgoPorOperacion_Pct * InpRiesgoCompartidoParUSTEC_US500;
      double disponiblePar   = presupuestoPar - g_estado[parIdx].riesgoAsignadoPct;
      return MathMax(0.0, MathMin(disponibleCartera, MathMin(disponiblePar, InpRiesgoPorOperacion_Pct)));
     }
   return MathMax(0.0, MathMin(disponibleCartera, InpRiesgoPorOperacion_Pct));
  }

//======================================================================
// LOGS CSV
//======================================================================
void EscribirCabeceraOperacionesSiHaceFalta(const int handle)
  {
   if(FileSize(handle) == 0)
      FileWrite(handle,
                "Evento", "Simbolo", "Motivo", "Direccion", "TiempoSenal",
                "PrecioSolicitado", "PrecioRealEjecucion", "SL", "N_senal", "Volumen",
                "RiesgoObjetivoMonetario", "RiesgoObjetivoPct", "RiesgoRealPostEjecucion",
                "TiempoCierre", "MotivoCierre", "ResultadoMonetario", "Swap", "Comision", "DuracionHoras");
  }

void EscribirFilaOperacion(const string evento, const string simbolo, const string motivo, const int direccion,
                            const datetime tiempoSenal, const double precioSolicitado, const double precioReal,
                            const double sl, const double nSenal, const double volumen,
                            const double riesgoObjetivoMon, const double riesgoObjetivoPct, const double riesgoReal,
                            const datetime tiempoCierre, const string motivoCierre, const double resultadoMonetario,
                            const double swap, const double comision, const double duracionHoras)
  {
   if(!InpRegistrarCSV) return;
   int handle = FileOpen(InpArchivoLogOperaciones, FILE_READ | FILE_WRITE | FILE_CSV | FILE_ANSI, ';');
   if(handle == INVALID_HANDLE)
     {
      PrintFormat("No se pudo abrir el log de operaciones '%s' (error %d).", InpArchivoLogOperaciones, GetLastError());
      return;
     }
   EscribirCabeceraOperacionesSiHaceFalta(handle);
   FileSeek(handle, 0, SEEK_END);
   FileWrite(handle, evento, simbolo, motivo, direccion == 1 ? "LARGO" : (direccion == -1 ? "CORTO" : ""),
             TimeToString(tiempoSenal, TIME_DATE | TIME_SECONDS),
             DoubleToString(precioSolicitado, 5), DoubleToString(precioReal, 5), DoubleToString(sl, 5),
             DoubleToString(nSenal, 5), DoubleToString(volumen, 2),
             DoubleToString(riesgoObjetivoMon, 2), DoubleToString(riesgoObjetivoPct, 4), DoubleToString(riesgoReal, 2),
             tiempoCierre > 0 ? TimeToString(tiempoCierre, TIME_DATE | TIME_SECONDS) : "", motivoCierre,
             DoubleToString(resultadoMonetario, 2), DoubleToString(swap, 2), DoubleToString(comision, 2),
             DoubleToString(duracionHoras, 1));
   FileClose(handle);
  }

void RegistrarSwapsReales()
  {
   if(!InpRegistrarCSV) return;
   int handle = FileOpen(InpArchivoLogSwaps, FILE_READ | FILE_WRITE | FILE_CSV | FILE_ANSI, ';');
   if(handle == INVALID_HANDLE) return;
   if(FileSize(handle) == 0)
      FileWrite(handle, "Tiempo", "Simbolo", "SwapLong", "SwapShort", "SwapModo", "Swap3Dias",
                "ContractSize", "TickSize", "TickValue", "VolumeMin", "VolumeStep");
   FileSeek(handle, 0, SEEK_END);
   for(int i = 0; i < ArraySize(g_estado); i++)
     {
      string s = g_estado[i].simbolo;
      FileWrite(handle, TimeToString(TimeCurrent(), TIME_DATE | TIME_SECONDS), s,
                DoubleToString(SymbolInfoDouble(s, SYMBOL_SWAP_LONG), 3),
                DoubleToString(SymbolInfoDouble(s, SYMBOL_SWAP_SHORT), 3),
                (long)SymbolInfoInteger(s, SYMBOL_SWAP_MODE), (long)SymbolInfoInteger(s, SYMBOL_SWAP_ROLLOVER3DAYS),
                DoubleToString(SymbolInfoDouble(s, SYMBOL_TRADE_CONTRACT_SIZE), 2),
                DoubleToString(SymbolInfoDouble(s, SYMBOL_TRADE_TICK_SIZE), 6),
                DoubleToString(SymbolInfoDouble(s, SYMBOL_TRADE_TICK_VALUE), 4),
                DoubleToString(SymbolInfoDouble(s, SYMBOL_VOLUME_MIN), 2),
                DoubleToString(SymbolInfoDouble(s, SYMBOL_VOLUME_STEP), 2));
     }
   FileClose(handle);
   PrintFormat("[LOG] Swaps/especificaciones reales registrados en %s", InpArchivoLogSwaps);
  }

void RegistrarEquitySnapshot()
  {
   double equity  = AccountInfoDouble(ACCOUNT_EQUITY);
   double balance = AccountInfoDouble(ACCOUNT_BALANCE);
   if(equity > g_equityPico) g_equityPico = equity;
   double ddPct = (g_equityPico > 0.0) ? (1.0 - equity / g_equityPico) * 100.0 : 0.0;

   int nAbiertas = 0;
   double riesgoAbiertoPct = 0.0;
   for(int k = 0; k < ArraySize(g_estado); k++)
      if(g_estado[k].enPosicion)
        {
         nAbiertas++;
         riesgoAbiertoPct += g_estado[k].riesgoAsignadoPct;
        }

   if(!InpRegistrarCSV) return;
   int handle = FileOpen(InpArchivoLogEquity, FILE_READ | FILE_WRITE | FILE_CSV | FILE_ANSI, ';');
   if(handle == INVALID_HANDLE) return;
   if(FileSize(handle) == 0)
      FileWrite(handle, "Tiempo", "Equity", "Balance", "EquityPico", "DrawdownPct", "PosicionesAbiertas", "RiesgoAbiertoPct");
   FileSeek(handle, 0, SEEK_END);
   FileWrite(handle, TimeToString(TimeCurrent(), TIME_DATE | TIME_SECONDS),
             DoubleToString(equity, 2), DoubleToString(balance, 2), DoubleToString(g_equityPico, 2),
             DoubleToString(ddPct, 4), nAbiertas, DoubleToString(riesgoAbiertoPct, 4));
   FileClose(handle);
  }

//--- Reconstruye g_estado a partir de posiciones YA ABIERTAS con nuestro
//    Magic Number (reinicio del terminal/EA, caída de VPS, etc. --
//    corriendo varios meses sin supervisión, un reinicio es casi
//    seguro que ocurrirá en algún momento). Sin esto, el EA perdería
//    la cuenta de una posición ya abierta y podría abrir una SEGUNDA
//    en el mismo símbolo, rompiendo la regla de "1 unidad, sin
//    piramidación". El riesgo del N original se recupera EXACTO a
//    partir de |entrada-SL|/2 (coincide con TurtleCalcularStopInicial
//    invertido); riesgoAsignadoPct solo puede aproximarse con el
//    parámetro ACTUAL (no hay forma de recuperar qué % se usó si el
//    input cambió entre reinicios -- se declara la limitación en el
//    propio log).
void SincronizarPosicionesExistentes()
  {
   for(int i = 0; i < ArraySize(g_estado); i++)
     {
      for(int p = 0; p < PositionsTotal(); p++)
        {
         ulong ticket = PositionGetTicket(p);
         if(ticket == 0) continue;
         if(PositionGetString(POSITION_SYMBOL) != g_estado[i].simbolo) continue;
         if(PositionGetInteger(POSITION_MAGIC) != (long)InpMagicNumber) continue;

         double precioApertura = PositionGetDouble(POSITION_PRICE_OPEN);
         double slActual       = PositionGetDouble(POSITION_SL);
         ENUM_POSITION_TYPE tipo = (ENUM_POSITION_TYPE)PositionGetInteger(POSITION_TYPE);
         int direccionRec = (tipo == POSITION_TYPE_BUY) ? 1 : -1;
         double nRec = (slActual > 0.0) ? MathAbs(precioApertura - slActual) / TURTLE_STOP_EN_N : 0.0;

         g_estado[i].enPosicion        = true;
         g_estado[i].direccion         = direccionRec;
         g_estado[i].nEntrada          = nRec;
         g_estado[i].precioEntradaReal = precioApertura;
         g_estado[i].stopPrice         = slActual;
         g_estado[i].riesgoAsignadoPct = InpRiesgoPorOperacion_Pct;   // aproximación -- ver comentario arriba
         g_estado[i].volumen           = PositionGetDouble(POSITION_VOLUME);
         g_estado[i].ticketPosicion    = ticket;
         g_estado[i].tiempoApertura    = (datetime)PositionGetInteger(POSITION_TIME);
         g_estado[i].logTiempoSenal    = g_estado[i].tiempoApertura;

         PrintFormat("[%s] Posición existente recuperada tras (re)inicio: ticket=%I64u %s entrada=%.5f SL=%.5f "
                     "N_reconstruido=%.5f (riesgoAsignadoPct aproximado al parámetro actual, no al histórico real).",
                     g_estado[i].simbolo, ticket, direccionRec > 0 ? "LARGO" : "CORTO", precioApertura, slActual, nRec);
         break;
        }
     }
  }

//======================================================================
// APERTURA DE POSICIÓN
//======================================================================
void AbrirPosicion(const int i, const int direccion, const double nSenal, const datetime tiempoSenal)
  {
   string sym = g_estado[i].simbolo;
   double bid = SymbolInfoDouble(sym, SYMBOL_BID);
   double ask = SymbolInfoDouble(sym, SYMBOL_ASK);
   double precioEstimado = (direccion > 0) ? ask : bid;
   double stop = TurtleCalcularStopInicial(precioEstimado, nSenal, direccion);

   EscribirFilaOperacion("SENAL", sym, direccion > 0 ? "ENTRADA_LARGO" : "ENTRADA_CORTO", direccion, tiempoSenal,
                          precioEstimado, 0.0, stop, nSenal, 0.0, 0.0, 0.0, 0.0, 0, "", 0.0, 0.0, 0.0, 0.0);

   double riesgoPct = RiesgoDisponiblePct(i, direccion);
   if(riesgoPct <= 0.0)
     {
      EscribirFilaOperacion("RECHAZADA", sym, "LIMITE_RIESGO_CARTERA_O_CORRELACION", direccion, tiempoSenal,
                             precioEstimado, 0.0, stop, nSenal, 0.0, 0.0, 0.0, 0.0, 0, "", 0.0, 0.0, 0.0, 0.0);
      return;
     }

   double equityActual = AccountInfoDouble(ACCOUNT_EQUITY);
   double riesgoMonetario = equityActual * (riesgoPct / 100.0);

   ENUM_ORDER_TYPE tipoOrden = (direccion > 0) ? ORDER_TYPE_BUY : ORDER_TYPE_SELL;
   double perdidaPorLote;
   if(!OrderCalcProfit(tipoOrden, sym, 1.0, precioEstimado, stop, perdidaPorLote))
     {
      EscribirFilaOperacion("RECHAZADA", sym, "ERROR_ORDERCALCPROFIT", direccion, tiempoSenal,
                             precioEstimado, 0.0, stop, nSenal, 0.0, riesgoMonetario, riesgoPct, 0.0, 0, "", 0.0, 0.0, 0.0, 0.0);
      return;
     }
   perdidaPorLote = MathAbs(perdidaPorLote);
   if(perdidaPorLote <= 0.0)
     {
      EscribirFilaOperacion("RECHAZADA", sym, "SL_INVALIDO", direccion, tiempoSenal,
                             precioEstimado, 0.0, stop, nSenal, 0.0, riesgoMonetario, riesgoPct, 0.0, 0, "", 0.0, 0.0, 0.0, 0.0);
      return;
     }

   double volStep = SymbolInfoDouble(sym, SYMBOL_VOLUME_STEP);
   double volMin  = SymbolInfoDouble(sym, SYMBOL_VOLUME_MIN);
   double volMax  = SymbolInfoDouble(sym, SYMBOL_VOLUME_MAX);

   double volumenTeorico = riesgoMonetario / perdidaPorLote;
   double volumen = MathFloor(volumenTeorico / volStep) * volStep;   // SOLO hacia abajo, nunca se sube al mínimo
   if(volumen < volMin)
     {
      EscribirFilaOperacion("RECHAZADA", sym, "VOLUMEN_MINIMO_EXCEDE_RIESGO", direccion, tiempoSenal,
                             precioEstimado, 0.0, stop, nSenal, 0.0, riesgoMonetario, riesgoPct, 0.0, 0, "", 0.0, 0.0, 0.0, 0.0);
      return;
     }
   volumen = MathMin(volumen, volMax);
   double riesgoFinal = volumen * perdidaPorLote;

   double margenRequerido;
   if(!OrderCalcMargin(tipoOrden, sym, volumen, precioEstimado, margenRequerido) ||
      margenRequerido > AccountInfoDouble(ACCOUNT_MARGIN_FREE))
     {
      EscribirFilaOperacion("RECHAZADA", sym, "MARGEN_INSUFICIENTE", direccion, tiempoSenal,
                             precioEstimado, 0.0, stop, nSenal, volumen, riesgoMonetario, riesgoPct, riesgoFinal, 0, "", 0.0, 0.0, 0.0, 0.0);
      return;
     }

   double stopNorm = NormalizeDouble(stop, g_estado[i].digits);

   g_estado[i].hayLogPendiente            = true;
   g_estado[i].logTiempoSenal              = tiempoSenal;
   g_estado[i].logPrecioSolicitado         = precioEstimado;
   g_estado[i].logSL                       = stopNorm;
   g_estado[i].logVolumen                  = volumen;
   g_estado[i].logRiesgoObjetivoMonetario  = riesgoMonetario;
   g_estado[i].logRiesgoObjetivoPct        = riesgoPct;
   g_estado[i].logN                        = nSenal;
   g_estado[i].logDireccion                = direccion;

   bool enviado = (direccion > 0)
                  ? trade.Buy(volumen, sym, 0.0, stopNorm, 0.0, "Turtle_S2_Largo")
                  : trade.Sell(volumen, sym, 0.0, stopNorm, 0.0, "Turtle_S2_Corto");

   if(!enviado)
     {
      g_estado[i].hayLogPendiente = false;
      string desc = StringFormat("ORDEN_RECHAZADA_SERVIDOR:%d:%s", trade.ResultRetcode(), trade.ResultRetcodeDescription());
      EscribirFilaOperacion("RECHAZADA", sym, desc, direccion, tiempoSenal,
                             precioEstimado, 0.0, stopNorm, nSenal, volumen, riesgoMonetario, riesgoPct, riesgoFinal, 0, "", 0.0, 0.0, 0.0, 0.0);
     }
  }

//======================================================================
// EVALUACIÓN POR SÍMBOLO (una vez por cada vela D1 nueva)
//======================================================================
void ProcesarSimbolo(const int i)
  {
   string sym = g_estado[i].simbolo;

   MqlRates rates[];
   ArraySetAsSeries(rates, false);
   int disponibles = CopyRates(sym, PERIOD_D1, 0, InpHistorialBarrasD1, rates);
   if(disponibles < TURTLE_ENTRADA_DIAS + TURTLE_PERIODO_N + 5)
     {
      PrintFormat("[%s] Histórico D1 insuficiente (%d barras disponibles) -- se omite esta evaluación.", sym, disponibles);
      return;
     }

   int n = disponibles;
   double high[], low[], close[];
   ArrayResize(high, n); ArrayResize(low, n); ArrayResize(close, n);
   for(int k = 0; k < n; k++)
     {
      high[k]  = rates[k].high;
      low[k]   = rates[k].low;
      close[k] = rates[k].close;
     }

   double N[], canalEntAlto[], canalEntBajo[], canalSalAlto[], canalSalBajo[];
   TurtleCalcularN(high, low, close, n, N);
   TurtleCalcularCanales(high, low, n, TURTLE_ENTRADA_DIAS, canalEntAlto, canalEntBajo);
   TurtleCalcularCanales(high, low, n, TURTLE_SALIDA_DIAS, canalSalAlto, canalSalBajo);

   int idxUltimoCerrado = n - 2;   // rates[n-1] es la vela D1 EN FORMACIÓN; n-2 es la última ya cerrada
   if(idxUltimoCerrado < TURTLE_ENTRADA_DIAS)
      return;

   if(g_estado[i].enPosicion)
     {
      bool salidaCanal = TurtleEvaluarSalidaCanal(close, canalSalAlto, canalSalBajo, idxUltimoCerrado, g_estado[i].direccion);
      if(salidaCanal)
        {
         EscribirFilaOperacion("SENAL", sym, "SALIDA_CANAL_DETECTADA", g_estado[i].direccion,
                                rates[idxUltimoCerrado].time, close[idxUltimoCerrado], 0.0, 0.0, N[idxUltimoCerrado],
                                0.0, 0.0, 0.0, 0.0, 0, "", 0.0, 0.0, 0.0, 0.0);
         ulong ticket = g_estado[i].ticketPosicion;
         if(ticket != 0 && PositionSelectByTicket(ticket))
           {
            if(!trade.PositionClose(ticket))
               PrintFormat("[%s] ERROR al cerrar por canal de salida (ticket %I64u): %s", sym, ticket, trade.ResultRetcodeDescription());
           }
        }
      return;   // con posición abierta no se buscan entradas nuevas (sin piramidación, regla congelada)
     }

   int direccion = TurtleEvaluarEntrada(close, canalEntAlto, canalEntBajo, idxUltimoCerrado);
   if(direccion == 0)
      return;

   AbrirPosicion(i, direccion, N[idxUltimoCerrado], rates[idxUltimoCerrado].time);
  }

//======================================================================
// EVENTOS DEL EXPERT ADVISOR
//======================================================================
int OnInit()
  {
   trade.SetExpertMagicNumber(InpMagicNumber);
   trade.SetDeviationInPoints(InpMaxDeviationPoints);

   string partes[];
   int nSim = StringSplit(InpSimbolos, ',', partes);
   if(nSim < 1)
     {
      Print("ERROR: InpSimbolos está vacío o mal formado.");
      return(INIT_FAILED);
     }

   ArrayResize(g_estado, nSim);
   for(int i = 0; i < nSim; i++)
     {
      string s = partes[i];
      StringTrimLeft(s);
      StringTrimRight(s);
      if(!SymbolSelect(s, true))
        {
         PrintFormat("ERROR: no se pudo seleccionar '%s' en Market Watch -- revisa el nombre exacto del símbolo en tu bróker.", s);
         return(INIT_FAILED);
        }
      g_estado[i].simbolo           = s;
      g_estado[i].digits            = (int)SymbolInfoInteger(s, SYMBOL_DIGITS);
      g_estado[i].enPosicion        = false;
      g_estado[i].direccion         = 0;
      g_estado[i].ticketPosicion    = 0;
      g_estado[i].hayLogPendiente   = false;
      g_estado[i].ultimaBarraD1     = 0;   // fuerza una evaluación inmediata en el primer OnTick de cada símbolo
     }

   SincronizarPosicionesExistentes();

   g_equityPico = AccountInfoDouble(ACCOUNT_EQUITY);
   RegistrarSwapsReales();
   g_ultimoLogSwaps = TimeCurrent();

   EventSetTimer(InpEquitySnapshotSegundos);
   PrintFormat("TurtleSystem2_EA inicializado. Símbolos gestionados: %s", InpSimbolos);
   return(INIT_SUCCEEDED);
  }

void OnDeinit(const int reason)
  {
   EventKillTimer();
  }

void OnTimer()
  {
   RegistrarEquitySnapshot();
   MqlDateTime dt;
   TimeToStruct(TimeCurrent(), dt);
   MqlDateTime dtUltimo;
   TimeToStruct(g_ultimoLogSwaps, dtUltimo);
   if(dt.day != dtUltimo.day || dt.mon != dtUltimo.mon || dt.year != dtUltimo.year)
     {
      RegistrarSwapsReales();
      g_ultimoLogSwaps = TimeCurrent();
     }
  }

void OnTradeTransaction(const MqlTradeTransaction &trans, const MqlTradeRequest &request, const MqlTradeResult &result)
  {
   if(trans.type != TRADE_TRANSACTION_DEAL_ADD) return;
   if(!HistoryDealSelect(trans.deal)) return;
   if(HistoryDealGetInteger(trans.deal, DEAL_MAGIC) != (long)InpMagicNumber) return;

   string symDeal = HistoryDealGetString(trans.deal, DEAL_SYMBOL);
   int i = IndiceSimbolo(symDeal);
   if(i < 0) return;

   ENUM_DEAL_ENTRY tipoEntrada = (ENUM_DEAL_ENTRY)HistoryDealGetInteger(trans.deal, DEAL_ENTRY);

   if(tipoEntrada == DEAL_ENTRY_IN)
     {
      if(!g_estado[i].hayLogPendiente)
         return;

      double precioReal = HistoryDealGetDouble(trans.deal, DEAL_PRICE);
      double volumenReal = HistoryDealGetDouble(trans.deal, DEAL_VOLUME);
      ulong idPosicion = (ulong)HistoryDealGetInteger(trans.deal, DEAL_POSITION_ID);

      double perdidaPorLoteReal;
      double riesgoReal = 0.0;
      ENUM_ORDER_TYPE tipoOrdenReal = (g_estado[i].logDireccion > 0) ? ORDER_TYPE_BUY : ORDER_TYPE_SELL;
      if(OrderCalcProfit(tipoOrdenReal, symDeal, 1.0, precioReal, g_estado[i].logSL, perdidaPorLoteReal))
         riesgoReal = volumenReal * MathAbs(perdidaPorLoteReal);

      g_estado[i].enPosicion         = true;
      g_estado[i].direccion          = g_estado[i].logDireccion;
      g_estado[i].nEntrada           = g_estado[i].logN;
      g_estado[i].precioEntradaReal  = precioReal;
      g_estado[i].stopPrice          = g_estado[i].logSL;
      g_estado[i].riesgoAsignadoPct  = g_estado[i].logRiesgoObjetivoPct;
      g_estado[i].volumen            = volumenReal;
      g_estado[i].ticketPosicion     = idPosicion;
      g_estado[i].tiempoApertura     = TimeCurrent();
      g_estado[i].hayLogPendiente    = false;

      EscribirFilaOperacion("EJECUTADA", symDeal, "", g_estado[i].direccion, g_estado[i].logTiempoSenal,
                             g_estado[i].logPrecioSolicitado, precioReal, g_estado[i].logSL, g_estado[i].logN,
                             volumenReal, g_estado[i].logRiesgoObjetivoMonetario, g_estado[i].logRiesgoObjetivoPct,
                             riesgoReal, 0, "", 0.0, 0.0, 0.0, 0.0);

      PrintFormat("[%s] %s EJECUTADO: entrada=%.5f (solicitado=%.5f) SL=%.5f lotes=%.2f riesgoReal=%.2f (objetivo=%.2f, %.2f%%)",
                  symDeal, g_estado[i].direccion > 0 ? "LARGO" : "CORTO", precioReal, g_estado[i].logPrecioSolicitado,
                  g_estado[i].logSL, volumenReal, riesgoReal, g_estado[i].logRiesgoObjetivoMonetario, g_estado[i].logRiesgoObjetivoPct);
      RegistrarEquitySnapshot();
      return;
     }

   if(tipoEntrada != DEAL_ENTRY_OUT && tipoEntrada != DEAL_ENTRY_OUT_BY)
      return;

   ulong idPosicion = (ulong)HistoryDealGetInteger(trans.deal, DEAL_POSITION_ID);
   if(PositionSelectByTicket(idPosicion))
      return;   // cierre parcial -- no debería ocurrir (siempre se cierra el 100%), pero por seguridad no se resetea el estado

   ENUM_DEAL_REASON razon = (ENUM_DEAL_REASON)HistoryDealGetInteger(trans.deal, DEAL_REASON);
   string motivoCierre = (razon == DEAL_REASON_SL) ? "SALIDA_STOP" : "SALIDA_CANAL";

   double resultado = 0.0, swapTotal = 0.0, comisionTotal = 0.0;
   if(HistorySelectByPosition(idPosicion))
     {
      int totalDeals = HistoryDealsTotal();
      for(int d = 0; d < totalDeals; d++)
        {
         ulong dealTicket = HistoryDealGetTicket(d);
         if(dealTicket == 0) continue;
         resultado     += HistoryDealGetDouble(dealTicket, DEAL_PROFIT);
         swapTotal     += HistoryDealGetDouble(dealTicket, DEAL_SWAP);
         comisionTotal += HistoryDealGetDouble(dealTicket, DEAL_COMMISSION);
        }
     }
   double resultadoTotal = resultado + swapTotal + comisionTotal;
   double duracionHoras = (g_estado[i].tiempoApertura > 0) ? (double)(TimeCurrent() - g_estado[i].tiempoApertura) / 3600.0 : 0.0;

   EscribirFilaOperacion("CERRADA", symDeal, "", g_estado[i].direccion, g_estado[i].logTiempoSenal,
                          g_estado[i].logPrecioSolicitado, g_estado[i].precioEntradaReal, g_estado[i].stopPrice,
                          g_estado[i].nEntrada, g_estado[i].volumen, g_estado[i].logRiesgoObjetivoMonetario,
                          g_estado[i].riesgoAsignadoPct, 0.0, TimeCurrent(), motivoCierre, resultadoTotal, swapTotal, comisionTotal, duracionHoras);

   PrintFormat("[%s] Posición cerrada (%s): resultado=%.2f (swap=%.2f, comisión=%.2f)",
               symDeal, motivoCierre, resultadoTotal, swapTotal, comisionTotal);

   g_estado[i].enPosicion      = false;
   g_estado[i].direccion       = 0;
   g_estado[i].ticketPosicion  = 0;
   RegistrarEquitySnapshot();
  }

void OnTick()
  {
   for(int i = 0; i < ArraySize(g_estado); i++)
     {
      datetime barraActual = iTime(g_estado[i].simbolo, PERIOD_D1, 0);
      if(barraActual == 0) continue;   // símbolo sin datos todavía (p.ej. justo tras SymbolSelect)
      if(barraActual != g_estado[i].ultimaBarraD1)
        {
         g_estado[i].ultimaBarraD1 = barraActual;
         ProcesarSimbolo(i);
        }
     }
  }
