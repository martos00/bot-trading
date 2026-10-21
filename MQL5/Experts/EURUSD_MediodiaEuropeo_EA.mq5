//+------------------------------------------------------------------+
//| EURUSD_MediodiaEuropeo_EA.mq5                                     |
//| Forward test en DEMO de la estrategia E1 (research/certificacion/ |
//| PREREGISTRO_E1_estrategia_eurusd.md) sobre la ventaja certificada |
//| C1: el EURUSD baja de media entre las 06:00 y las 08:00 de Nueva  |
//| York (mediodia europeo; Breedon-Ranaldo 2013).                    |
//|                                                                    |
//| Reglas (identicas al backtest, no cambiar sin nuevo pre-registro):|
//|  - Cada dia laborable de NY: VENTA a las 06:00:00 NY, recompra a  |
//|    las 08:00:00 NY, a mercado.                                    |
//|  - Tamano por volatilidad: sigma = desviacion tipica de la        |
//|    rentabilidad 06->08 NY de los 60 dias laborables anteriores    |
//|    (velas M1 del propio broker). Exposicion = riesgo / sigma      |
//|    (multiplo del balance), con tope.                              |
//|  - Stop de catastrofe a 4 sigma por encima del precio de venta.   |
//|  - No entra si el spread supera InpMaxSpreadPips.                 |
//| Registra cada operacion (spread, deslizamiento, comision, swap,   |
//| resultado) en MQL5/Files/<InpArchivoCSV>.                         |
//| Por seguridad, con InpSoloDemo=true no opera en cuentas reales.   |
//+------------------------------------------------------------------+
#property strict
#include <Trade\Trade.mqh>

input double InpRiesgoDiarioPct      = 0.5;    // volatilidad diaria objetivo, % del balance (pre-registro: 0.5 o 1.0)
input double InpTopeExposicion       = 10.0;   // exposicion maxima, multiplo del balance
input double InpStopSigmas           = 4.0;    // stop de catastrofe en sigmas
input int    InpDiasSigma            = 60;     // dias para estimar sigma
input double InpMaxSpreadPips        = 1.0;    // no entrar si el spread es mayor
input double InpLotesFijos           = 0.0;    // >0: usar este lotaje fijo (solo para medir costes)
input bool   InpServidorConDSTdeEEUU = true;   // el servidor cambia de hora con EEUU (lo habitual)
input bool   InpSoloDemo             = true;   // negarse a operar si la cuenta no es DEMO (en el Probador no aplica)
input int    InpOffsetServidorInv    = 2;      // SOLO Probador: hora servidor - UTC en invierno (MetaQuotes/FTMO: 2)
input ulong  InpMagico               = 60800;
input string InpArchivoCSV           = "EURUSD_MediodiaEuropeo_log.csv";

CTrade g_trade;
int    g_diaOperado = -1;          // dia del anio (NY) en que ya se abrio
double g_sigma = 0, g_bidSenal = 0, g_askSenal = 0, g_lotes = 0;
ulong  g_dealIn = 0;
datetime g_horaEntrada = 0;

//--- horario de verano de EEUU: 2.º domingo de marzo 07:00 UTC -> 1.er domingo de noviembre 06:00 UTC
datetime Domingo(int anio, int mes, int n)
  {
   MqlDateTime t = {};
   t.year = anio; t.mon = mes; t.day = 1;
   datetime d = StructToTime(t);
   MqlDateTime x; TimeToStruct(d, x);
   return d + ((7 - x.day_of_week) % 7 + 7 * (n - 1)) * 86400;
  }
bool VeranoEEUU(datetime utc)
  {
   MqlDateTime x; TimeToStruct(utc, x);
   return utc >= Domingo(x.year, 3, 2) + 7 * 3600 && utc < Domingo(x.year, 11, 1) + 6 * 3600;
  }
datetime UTCaNY(datetime utc) { return utc - (VeranoEEUU(utc) ? 4 : 5) * 3600; }

bool EnProbador() { return (bool)MQLInfoInteger(MQL_TESTER); }

// En el Probador, TimeGMT() devuelve la hora del servidor simulado (documentación de MQL5), así que el UTC se
// reconstruye con la diferencia horaria del servidor indicada por el usuario.
datetime AhoraUTC()
  {
   if(!EnProbador()) return TimeGMT();
   datetime srv = TimeCurrent();
   datetime utc = srv - InpOffsetServidorInv * 3600;
   if(InpServidorConDSTdeEEUU && VeranoEEUU(utc - 3600)) utc -= 3600;
   return utc;
  }

int OffsetInvierno()   // hora servidor - UTC en invierno, detectada ahora (en el Probador, la indicada)
  {
   if(EnProbador()) return InpOffsetServidorInv;
   datetime u = TimeGMT();
   int off = (int)MathRound((double)(TimeTradeServer() - u) / 3600.0);
   return off - ((InpServidorConDSTdeEEUU && VeranoEEUU(u)) ? 1 : 0);
  }
datetime UTCaServidor(datetime utc, int offInv)
  {
   return utc + (offInv + ((InpServidorConDSTdeEEUU && VeranoEEUU(utc)) ? 1 : 0)) * 3600;
  }
// hh:00 NY de la fecha 'dia' (00:00 UTC) en UTC
datetime HoraNYenUTC(datetime dia, int hh)
  {
   datetime t = dia + (hh + 5) * 3600;
   if(VeranoEEUU(t - 3600)) t -= 3600;
   return t;
  }
// cierre de la vela M1 que termina en T (hora servidor); 0 si no existe en los 5 minutos anteriores
double PrecioEn(datetime T_srv)
  {
   for(int j = 1; j <= 5; j++)
     {
      int k = iBarShift(_Symbol, PERIOD_M1, T_srv - j * 60, true);
      if(k >= 0) return iClose(_Symbol, PERIOD_M1, k);
     }
   return 0;
  }

double SigmaFranja()
  {
   int offInv = OffsetInvierno();
   datetime ahora = AhoraUTC();
   datetime hoy = ahora - (ahora % 86400);
   double r[]; int n = 0;
   for(int k = 1; k <= 200 && n < InpDiasSigma; k++)
     {
      datetime dia = hoy - k * 86400;
      MqlDateTime x; TimeToStruct(dia, x);
      if(x.day_of_week == 0 || x.day_of_week == 6) continue;
      double p6 = PrecioEn(UTCaServidor(HoraNYenUTC(dia, 6), offInv));
      double p8 = PrecioEn(UTCaServidor(HoraNYenUTC(dia, 8), offInv));
      if(p6 <= 0 || p8 <= 0) continue;
      ArrayResize(r, n + 1); r[n++] = -MathLog(p8 / p6);
     }
   if(n < 40) { PrintFormat("Solo %d dias con datos para sigma (minimo 40): abre M1 y descarga historico.", n); return 0; }
   double m = 0, v = 0;
   for(int i = 0; i < n; i++) m += r[i];
   m /= n;
   for(int i = 0; i < n; i++) v += (r[i] - m) * (r[i] - m);
   return MathSqrt(v / (n - 1));
  }

double Lotes(double sigma, double precio)
  {
   double lot;
   if(InpLotesFijos > 0) lot = InpLotesFijos;
   else
     {
      double expos = MathMin(InpRiesgoDiarioPct / 100.0 / sigma, InpTopeExposicion);
      double nocionalUSD = expos * AccountInfoDouble(ACCOUNT_BALANCE);
      lot = nocionalUSD / (SymbolInfoDouble(_Symbol, SYMBOL_TRADE_CONTRACT_SIZE) * precio);
     }
   double paso = SymbolInfoDouble(_Symbol, SYMBOL_VOLUME_STEP);
   lot = MathFloor(lot / paso) * paso;
   return MathMax(SymbolInfoDouble(_Symbol, SYMBOL_VOLUME_MIN), MathMin(lot, SymbolInfoDouble(_Symbol, SYMBOL_VOLUME_MAX)));
  }

void Registrar(string evento, double precio, double spreadPips, double desliz, double comision, double swap, double beneficio)
  {
   bool nuevo = !FileIsExist(InpArchivoCSV);
   int fh = FileOpen(InpArchivoCSV, FILE_READ | FILE_WRITE | FILE_CSV | FILE_ANSI, ',');
   if(fh == INVALID_HANDLE) return;
   if(nuevo) FileWrite(fh, "hora_utc", "evento", "lotes", "sigma_pb", "precio", "spread_pips", "desliz_pips", "comision", "swap", "beneficio", "balance");
   FileSeek(fh, 0, SEEK_END);
   FileWrite(fh, TimeToString(AhoraUTC(), TIME_DATE | TIME_SECONDS), evento, DoubleToString(g_lotes, 2), DoubleToString(g_sigma * 1e4, 2),
             DoubleToString(precio, 5), DoubleToString(spreadPips, 2), DoubleToString(desliz, 2), DoubleToString(comision, 2),
             DoubleToString(swap, 2), DoubleToString(beneficio, 2), DoubleToString(AccountInfoDouble(ACCOUNT_BALANCE), 2));
   FileClose(fh);
  }

bool PosicionAbierta()
  {
   for(int i = PositionsTotal() - 1; i >= 0; i--)
      if(PositionGetSymbol(i) == _Symbol && PositionGetInteger(POSITION_MAGIC) == (long)InpMagico) return true;
   return false;
  }

int OnInit()
  {
   if(_Symbol != "EURUSD" && StringFind(_Symbol, "EURUSD") < 0)
      Print("AVISO: este EA esta pensado para EURUSD; simbolo actual ", _Symbol);
   if(InpSoloDemo && !EnProbador() && AccountInfoInteger(ACCOUNT_TRADE_MODE) != ACCOUNT_TRADE_MODE_DEMO)
     { Print("Cuenta no DEMO e InpSoloDemo=true: el EA no operara."); return INIT_FAILED; }
   g_trade.SetExpertMagicNumber(InpMagico);
   EventSetTimer(1);
   PrintFormat("EA iniciado%s. Servidor invierno UTC%+d. Venta 06:00 NY, cierre 08:00 NY.",
               EnProbador() ? " en el PROBADOR" : "", OffsetInvierno());
   return INIT_SUCCEEDED;
  }

void OnDeinit(const int reason) { EventKillTimer(); }

void OnTimer()
  {
   datetime ny = UTCaNY(AhoraUTC());
   MqlDateTime t; TimeToStruct(ny, t);
   int seg = t.hour * 3600 + t.min * 60 + t.sec;
   double pip = 0.0001;

   // cierre: a partir de las 08:00:00 NY (o si quedo abierta de otro dia)
   if(PosicionAbierta() && (seg >= 8 * 3600 || t.day_of_year != g_diaOperado))
     {
      double askAntes = SymbolInfoDouble(_Symbol, SYMBOL_ASK), bidAntes = SymbolInfoDouble(_Symbol, SYMBOL_BID);
      if(g_trade.PositionClose(_Symbol))
        {
         ulong d = g_trade.ResultDeal();
         Sleep(500);
         HistorySelect(TimeCurrent() - 86400, TimeCurrent() + 60);
         double comIn = (g_dealIn > 0) ? HistoryDealGetDouble(g_dealIn, DEAL_COMMISSION) : 0;
         Registrar("cierre", g_trade.ResultPrice(), (askAntes - bidAntes) / pip, (g_trade.ResultPrice() - askAntes) / pip,
                   comIn + HistoryDealGetDouble(d, DEAL_COMMISSION), HistoryDealGetDouble(d, DEAL_SWAP), HistoryDealGetDouble(d, DEAL_PROFIT));
        }
      return;
     }

   // entrada: entre 06:00:00 y 06:05 NY, lunes-viernes, una vez al dia
   if(t.day_of_week < 1 || t.day_of_week > 5 || seg < 6 * 3600 || seg >= 6 * 3600 + 300) return;
   if(g_diaOperado == t.day_of_year || PosicionAbierta()) return;
   g_diaOperado = t.day_of_year;
   double bid = SymbolInfoDouble(_Symbol, SYMBOL_BID), ask = SymbolInfoDouble(_Symbol, SYMBOL_ASK);
   double spreadPips = (ask - bid) / pip;
   if(spreadPips > InpMaxSpreadPips) { Registrar("sin_entrada_spread", bid, spreadPips, 0, 0, 0, 0); return; }
   g_sigma = SigmaFranja();
   if(g_sigma <= 0) { Registrar("sin_entrada_sigma", bid, spreadPips, 0, 0, 0, 0); return; }
   g_lotes = Lotes(g_sigma, bid);
   double sl = NormalizeDouble(bid * (1 + InpStopSigmas * g_sigma), _Digits);
   g_bidSenal = bid; g_askSenal = ask;
   if(g_trade.Sell(g_lotes, _Symbol, 0, sl, 0, "E1_mediodia_europeo"))
     {
      g_dealIn = g_trade.ResultDeal();
      g_horaEntrada = AhoraUTC();
      Registrar("venta", g_trade.ResultPrice(), spreadPips, (bid - g_trade.ResultPrice()) / pip, 0, 0, 0);
     }
   else
      Registrar("error_venta_" + IntegerToString(g_trade.ResultRetcode()), bid, spreadPips, 0, 0, 0, 0);
  }

// registra tambien la salida por stop de catastrofe
void OnTradeTransaction(const MqlTradeTransaction &tr, const MqlTradeRequest &rq, const MqlTradeResult &rs)
  {
   if(tr.type != TRADE_TRANSACTION_DEAL_ADD) return;
   if(!HistoryDealSelect(tr.deal)) return;
   if(HistoryDealGetInteger(tr.deal, DEAL_MAGIC) != (long)InpMagico) return;
   if(HistoryDealGetInteger(tr.deal, DEAL_REASON) == DEAL_REASON_SL)
      Registrar("stop_catastrofe", HistoryDealGetDouble(tr.deal, DEAL_PRICE), 0, 0,
                HistoryDealGetDouble(tr.deal, DEAL_COMMISSION), HistoryDealGetDouble(tr.deal, DEAL_SWAP), HistoryDealGetDouble(tr.deal, DEAL_PROFIT));
  }
