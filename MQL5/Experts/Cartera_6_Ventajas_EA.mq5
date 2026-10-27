//+------------------------------------------------------------------+
//| Cartera_6_Ventajas_EA.mq5                                         |
//| Forward test en DEMO de la cartera de 6 ventajas certificadas     |
//| (research/CATALOGO_VENTAJAS.md). Se pone en UN grafico cualquiera |
//| y opera todos los simbolos indicados. Horas en Nueva York (NY).   |
//|                                                                    |
//|  E2  EURUSD  corto  06:00 -> 08:00   cada dia laborable, salvo    |
//|              festivos TARGET, festivos bancarios de Inglaterra y  |
//|              dias de reunion del BCE (lista InpFechasBCE).        |
//|  E8  XAUUSD  largo  16:00 -> 16:55   viernes                      |
//|  E10 XAGUSD  largo  16:00 -> 16:55   vispera de festivo NYSE      |
//|  E9  USDJPY  largo  07:00 -> 08:00   antepenultimo dia laborable  |
//|              del mes                                              |
//|  E11 USDJPY+EURJPY+GBPJPY corto 00:30 -> 02:00  ultimo dia        |
//|              laborable de mar/jun/sep/dic (1/3 del riesgo c/u)    |
//|  E12 cesta de materias primas largo 13:55 del dia anterior a la   |
//|              vispera -> 13:55 de la vispera de festivo NYSE       |
//|                                                                    |
//| Tamano: riesgo% / sigma de la propia franja (velas M1 del broker),|
//| con tope de exposicion. Stop de catastrofe a InpStopSigmas sigmas.|
//| Modo EXAMEN multiplica el riesgo (InpMultExamen).                 |
//| Protecciones: perdida diaria maxima propia (cierra todo y para el |
//| dia), perdida total maxima (para del todo), filtro de noticias de |
//| alto impacto a +-InpMinNoticias minutos (calendario de MT5), y    |
//| por seguridad no opera en cuentas reales con InpSoloDemo=true.    |
//| Registro de cada evento en MQL5/Files/<InpArchivoCSV>.            |
//| Reglas = pre-registros E2, E8, E9, E10, E11b(+E13), E12. No       |
//| cambiar sin nuevo pre-registro.                                   |
//+------------------------------------------------------------------+
#property strict
#include <Trade\Trade.mqh>

enum ENUM_DST_SERVIDOR
  {
   DST_EUROPA = 0,   // Europa: ultimo domingo de marzo -> ultimo domingo de octubre (MetaQuotes-Demo, FTMO)
   DST_EEUU   = 1,   // EEUU: 2.o domingo de marzo -> 1.er domingo de noviembre
   DST_NINGUNO = 2   // el servidor no cambia de hora
  };
enum ENUM_MODO
  {
   MODO_FONDEADO = 0, // FONDEADO: riesgo normal
   MODO_EXAMEN   = 1  // EXAMEN: riesgo x InpMultExamen (pasar antes la evaluacion)
  };

input group "Riesgo"
input ENUM_MODO InpModo              = MODO_FONDEADO;
input double InpRiesgoPct            = 0.5;    // riesgo por operacion = volatilidad objetivo, % del balance
input double InpMultExamen           = 1.0;    // multiplicador de riesgo en modo EXAMEN (1 = mismo riesgo que fondeada)
input double InpStopSigmas           = 4.0;    // stop de catastrofe en sigmas
input double InpTopeExposicionFX     = 10.0;   // exposicion maxima por operacion (x balance) en divisas
input double InpTopeExposicionOtros  = 6.0;    // idem en metales y materias primas
input double InpPerdidaDiariaMaxPct  = 3.5;    // si el dia pierde esto (% del inicio del dia): cierra todo y no opera mas hoy (FTMO: 5)
input double InpPerdidaTotalMaxPct   = 8.0;    // si se pierde esto desde el balance inicial: deja de operar (FTMO: 10)
input double InpBalanceInicial       = 0;      // 0 = el balance al arrancar el EA por primera vez

input group "Estrategias (activar / desactivar)"
input bool   InpE2_Euro              = true;   // E2 euro mediodia europeo
input bool   InpE8_OroViernes        = true;   // E8 oro viernes
input int    InpE8_Salida            = 1645;   // hora NY de salida del oro (HHMM): 1645 (E8b; el oro de FTMO cierra el viernes a las 16:50 NY); 1655 = regla original
input bool   InpE10_PlataVispera     = false;  // E10 plata vispera de festivo (desactivada: en FTMO el spread a esa hora ~14 pb > ventaja 9,9 pb -> CARO)
input bool   InpE9_YenFinMes         = true;   // E9 yen fin de mes
input bool   InpE11_YenFinTrimestre  = true;   // E11 cesta del yen fin de trimestre
input bool   InpE12_MateriasVispera  = true;   // E12 materias primas vispera de festivo

input group "Simbolos (nombre exacto en la cuenta)"
input string InpSimEURUSD            = "EURUSD";
input string InpSimUSDJPY            = "USDJPY";
input string InpSimEURJPY            = "EURJPY";
input string InpSimGBPJPY            = "GBPJPY";
input string InpSimOro               = "XAUUSD";
input string InpSimPlata             = "XAGUSD";
input string InpCestaE12             = "USOIL.cash,HEATOIL.c,NATGAS.cash,CORN.c,SOYBEAN.c,WHEAT.c"; // nombres FTMO; solo miembros de la cesta preregistrada (C69): CL HO NG ZC ZS ZW

input group "Calendario"
input string InpFechasBCE            = "";     // dias de reunion de politica monetaria del BCE, "AAAA.MM.DD,..." (ecb.europa.eu)
input string InpFestivosNYSE         = "2025.01.01,2025.01.09,2025.01.20,2025.02.17,2025.04.18,2025.05.26,2025.06.19,2025.07.04,2025.09.01,2025.11.27,2025.12.25,2026.01.01,2026.01.19,2026.02.16,2026.04.03,2026.05.25,2026.06.19,2026.07.03,2026.09.07,2026.11.26,2026.12.25,2027.01.01,2027.01.18,2027.02.15,2027.03.26,2027.05.31,2027.06.18,2027.07.05,2027.09.06,2027.11.25,2027.12.24"; // festivos NYSE (ampliar cada anio)
input int    InpMinNoticias          = 2;      // no abrir ni cerrar a +- estos minutos de una noticia de alto impacto
input bool   InpFiltroNoticias       = true;

input group "Sistema"
input ENUM_DST_SERVIDOR InpDSTServidor = DST_EUROPA;
input bool   InpSoloDemo             = true;   // negarse a operar si la cuenta no es DEMO (en el Probador no aplica)
input int    InpOffsetServidorInv    = 2;      // SOLO Probador: hora servidor - UTC en invierno (MetaQuotes/FTMO: 2)
input int    InpMinAntesCierre       = 5;      // cierra todo lo que siga abierto estos minutos antes de un cierre largo del simbolo (fin de semana)
input double InpMaxSpreadPb          = 0;      // >0: no entrar si el spread (pb del precio) supera esto
input ulong  InpMagicoBase           = 61000;  // magico de cada estrategia = base + numero
input string InpArchivoCSV           = "Cartera_6_Ventajas_log.csv";

CTrade g_trade;

//==================== tiempo ====================
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
bool VeranoServidor(datetime utc)
  {
   if(InpDSTServidor == DST_NINGUNO) return false;
   if(InpDSTServidor == DST_EEUU) return VeranoEEUU(utc);
   MqlDateTime x; TimeToStruct(utc, x);
   return utc >= Domingo(x.year, 4, 1) - 7 * 86400 + 3600 && utc < Domingo(x.year, 11, 1) - 7 * 86400 + 3600;
  }
bool EnProbador() { return (bool)MQLInfoInteger(MQL_TESTER); }
datetime AhoraUTC()
  {
   if(!EnProbador()) return TimeGMT();
   datetime utc = TimeCurrent() - InpOffsetServidorInv * 3600;
   if(VeranoServidor(utc - 3600)) utc -= 3600;
   return utc;
  }
int OffsetInvierno()
  {
   if(EnProbador()) return InpOffsetServidorInv;
   datetime u = TimeGMT();
   int off = (int)MathRound((double)(TimeTradeServer() - u) / 3600.0);
   return off - (VeranoServidor(u) ? 1 : 0);
  }
datetime UTCaNY(datetime utc) { return utc - (VeranoEEUU(utc) ? 4 : 5) * 3600; }
datetime UTCaServidor(datetime utc) { return utc + (OffsetInvierno() + (VeranoServidor(utc) ? 1 : 0)) * 3600; }
// hh:mm NY del dia 'dia' (fecha a las 00:00) en UTC
datetime NYenUTC(datetime dia, int hhmm)
  {
   datetime t = dia + (hhmm / 100 + 5) * 3600 + (hhmm % 100) * 60;
   if(VeranoEEUU(t - 3600)) t -= 3600;
   return t;
  }
datetime SoloFecha(datetime t) { return t - (t % 86400); }

//==================== calendario ====================
string Fecha(datetime d) { return TimeToString(d, TIME_DATE); }   // "AAAA.MM.DD"
bool EsLaborable(datetime d) { MqlDateTime x; TimeToStruct(d, x); return x.day_of_week >= 1 && x.day_of_week <= 5; }
datetime Pascua(int y)        // domingo de Pascua (algoritmo de Gauss/Butcher)
  {
   int a = y % 19, b = y / 100, c = y % 100, d = b / 4, e = b % 4, f = (b + 8) / 25, g = (b - f + 1) / 3;
   int h = (19 * a + b - d - g + 15) % 30, i = c / 4, k = c % 4, l = (32 + 2 * e + 2 * i - h - k) % 7, m = (a + 11 * h + 22 * l) / 451;
   MqlDateTime t = {}; t.year = y; t.mon = (h + l - 7 * m + 114) / 31; t.day = ((h + l - 7 * m + 114) % 31) + 1;
   return StructToTime(t);
  }
datetime DiaMes(int y, int mo, int d) { MqlDateTime t = {}; t.year = y; t.mon = mo; t.day = d; return StructToTime(t); }
datetime LunesN(int y, int mo, int n)      // n-esimo lunes del mes (n = -1: el ultimo)
  {
   if(n > 0) { datetime d = DiaMes(y, mo, 1); MqlDateTime x; TimeToStruct(d, x); return d + (((8 - x.day_of_week) % 7) + 7 * (n - 1)) * 86400; }
   datetime u = DiaMes(y, mo + 1 > 12 ? 1 : mo + 1, 1) - 86400; if(mo == 12) u = DiaMes(y, 12, 31);
   MqlDateTime x; TimeToStruct(u, x); return u - ((x.day_of_week + 6) % 7) * 86400;
  }
bool FestivoTARGET(datetime d)
  {
   MqlDateTime x; TimeToStruct(d, x); datetime p = Pascua(x.year);
   if((x.mon == 1 && x.day == 1) || (x.mon == 5 && x.day == 1) || (x.mon == 12 && (x.day == 25 || x.day == 26))) return true;
   return d == p - 2 * 86400 || d == p + 86400;
  }
datetime Observado(datetime d)  // si cae en fin de semana pasa al lunes
  {
   MqlDateTime x; TimeToStruct(d, x);
   if(x.day_of_week == 6) return d + 2 * 86400;
   if(x.day_of_week == 0) return d + 86400;
   return d;
  }
bool FestivoInglaterra(datetime d)
  {
   MqlDateTime x; TimeToStruct(d, x); int y = x.year; datetime p = Pascua(y);
   if(d == Observado(DiaMes(y, 1, 1)) || d == p - 2 * 86400 || d == p + 86400) return true;
   if(d == LunesN(y, 5, 1) || d == LunesN(y, 5, -1) || d == LunesN(y, 8, -1)) return true;
   datetime nav = DiaMes(y, 12, 25), san = DiaMes(y, 12, 26);
   MqlDateTime xn; TimeToStruct(nav, xn);
   datetime navO = nav, sanO = san;
   if(xn.day_of_week == 6) { navO = nav + 2 * 86400; sanO = san + 2 * 86400; }        // sab -> lun y mar
   else if(xn.day_of_week == 0) { navO = nav + 2 * 86400; sanO = san; }              // dom -> mar; 26 es lunes
   else if(xn.day_of_week == 5) { sanO = san + 2 * 86400; }                          // 26 sab -> lun 28
   return d == navO || d == sanO;
  }
bool EnLista(string lista, datetime d) { return StringLen(lista) > 0 && StringFind(lista, Fecha(d)) >= 0; }
bool FestivoNYSE(datetime d) { return EnLista(InpFestivosNYSE, d); }
datetime HabilNYSESiguiente(datetime d) { datetime s = d + 86400; while(!EsLaborable(s) || FestivoNYSE(s)) s += 86400; return s; }
bool EsVispera(datetime d) { return EsLaborable(d) && !FestivoNYSE(d) && FestivoNYSE(HabilNYSESiguiente(d)); }
bool EsDiaAntesDeVispera(datetime d)   // y la vispera es el dia siguiente (nunca se mantiene el fin de semana)
  { datetime s = HabilNYSESiguiente(d); return EsLaborable(d) && !FestivoNYSE(d) && s == d + 86400 && EsVispera(s); }
int LaborablesRestantesMes(datetime d)    // laborables (lun-vie) del mes posteriores a d
  {
   MqlDateTime x; TimeToStruct(d, x); int n = 0;
   for(datetime s = d + 86400; ; s += 86400) { MqlDateTime y; TimeToStruct(s, y); if(y.mon != x.mon) break; if(EsLaborable(s)) n++; }
   return n;
  }
bool EsDmenos2(datetime d) { return EsLaborable(d) && LaborablesRestantesMes(d) == 2; }
bool EsQ0(datetime d) { MqlDateTime x; TimeToStruct(d, x); return EsLaborable(d) && LaborablesRestantesMes(d) == 0 && (x.mon % 3 == 0); }

//==================== noticias ====================
bool NoticiaCerca(string divisas, datetime t_utc)
  {
   if(!InpFiltroNoticias || EnProbador()) return false;
   datetime t_srv = UTCaServidor(t_utc);
   string ds[]; int n = StringSplit(divisas, ',', ds);
   for(int i = 0; i < n; i++)
     {
      MqlCalendarValue v[];
      if(CalendarValueHistory(v, t_srv - InpMinNoticias * 60 - 60, t_srv + InpMinNoticias * 60 + 60, NULL, ds[i]) <= 0) continue;
      for(int j = 0; j < ArraySize(v); j++)
        {
         MqlCalendarEvent ev;
         if(CalendarEventById(v[j].event_id, ev) && ev.importance == CALENDAR_IMPORTANCE_HIGH &&
            MathAbs((long)(v[j].time - t_srv)) <= InpMinNoticias * 60) return true;
        }
     }
   return false;
  }

//==================== precios y tamano ====================
double PrecioEn(string sim, datetime T_srv)   // cierre de la vela M1 que termina en T (busca 5 minutos atras)
  {
   for(int j = 1; j <= 5; j++)
     {
      int k = iBarShift(sim, PERIOD_M1, T_srv - j * 60, true);
      if(k >= 0) return iClose(sim, PERIOD_M1, k);
     }
   return 0;
  }
// sigma de ln(P(fin)/P(ini)) en los ultimos 'nDias' dias que cumplen el filtro (0 = laborables, 5 = viernes)
double Sigma(string sim, int hIni, int hFin, int filtroDia, int nDias, int finDiaSiguiente = 0)
  {
   datetime hoy = SoloFecha(AhoraUTC());
   double r[]; int n = 0;
   for(int k = 1; k <= 400 && n < nDias; k++)
     {
      datetime d = hoy - k * 86400;
      MqlDateTime x; TimeToStruct(d, x);
      if(!EsLaborable(d)) continue;
      if(filtroDia == 5 && x.day_of_week != 5) continue;
      datetime d2 = d; if(finDiaSiguiente) { d2 = d + 86400; while(!EsLaborable(d2)) d2 += 86400; }
      double p0 = PrecioEn(sim, UTCaServidor(NYenUTC(d, hIni))), p1 = PrecioEn(sim, UTCaServidor(NYenUTC(d2, hFin)));
      if(p0 <= 0 || p1 <= 0) continue;
      ArrayResize(r, n + 1); r[n++] = MathLog(p1 / p0);
     }
   if(n < MathMin(30, nDias * 2 / 3)) { PrintFormat("%s: solo %d dias con datos para sigma; abre su grafico M1 y descarga historico.", sim, n); return 0; }
   double m = 0, v = 0;
   for(int i = 0; i < n; i++) m += r[i];
   m /= n;
   for(int i = 0; i < n; i++) v += (r[i] - m) * (r[i] - m);
   return MathSqrt(v / (n - 1));
  }
bool EsFX(string sim) { return StringLen(sim) >= 6 && SymbolInfoString(sim, SYMBOL_CURRENCY_BASE) != "" && (SymbolInfoInteger(sim, SYMBOL_TRADE_CALC_MODE) == SYMBOL_CALC_MODE_FOREX || SymbolInfoInteger(sim, SYMBOL_TRADE_CALC_MODE) == SYMBOL_CALC_MODE_FOREX_NO_LEVERAGE); }
double Lotes(string sim, double riesgoFrac, double sigma, double precio)
  {
   double tope = EsFX(sim) ? InpTopeExposicionFX : InpTopeExposicionOtros;
   double expos = MathMin(riesgoFrac / sigma, tope);
   double nocional = expos * AccountInfoDouble(ACCOUNT_BALANCE);          // en divisa de la cuenta
   if(precio <= 0) return 0;
   // nocional de 1 lote en divisa de la cuenta = 100 x beneficio de un movimiento del 1 % (no depende del tick value,
   // que en algunos servidores/probador no cuadra con el tamanio de contrato del oro)
   double pr = 0, nocLote = 0;
   if(OrderCalcProfit(ORDER_TYPE_BUY, sim, 1.0, precio, precio * 1.01, pr) && pr > 0) nocLote = pr * 100.0;
   else
     {
      double tv = SymbolInfoDouble(sim, SYMBOL_TRADE_TICK_VALUE), ts = SymbolInfoDouble(sim, SYMBOL_TRADE_TICK_SIZE);
      if(tv <= 0 || ts <= 0) return 0;
      nocLote = precio / ts * tv;
     }
   double lot = nocional / nocLote;
   double paso = SymbolInfoDouble(sim, SYMBOL_VOLUME_STEP);
   lot = MathFloor(lot / paso) * paso;
   if(lot < SymbolInfoDouble(sim, SYMBOL_VOLUME_MIN)) return 0;
   return MathMin(lot, SymbolInfoDouble(sim, SYMBOL_VOLUME_MAX));
  }

//==================== registro ====================
void Registrar(string estr, string sim, string evento, double lotes, double sigma, double precio, double spreadPb, double resultado)
  {
   bool nuevo = !FileIsExist(InpArchivoCSV);
   int fh = FileOpen(InpArchivoCSV, FILE_READ | FILE_WRITE | FILE_CSV | FILE_ANSI, ',');
   if(fh == INVALID_HANDLE) return;
   if(nuevo) FileWrite(fh, "hora_utc", "estrategia", "simbolo", "evento", "lotes", "sigma_pb", "precio", "spread_pb", "resultado", "balance", "equity", "modo");
   FileSeek(fh, 0, SEEK_END);
   FileWrite(fh, TimeToString(AhoraUTC(), TIME_DATE | TIME_SECONDS), estr, sim, evento, DoubleToString(lotes, 2), DoubleToString(sigma * 1e4, 2),
             DoubleToString(precio, 5), DoubleToString(spreadPb, 2), DoubleToString(resultado, 2), DoubleToString(AccountInfoDouble(ACCOUNT_BALANCE), 2),
             DoubleToString(AccountInfoDouble(ACCOUNT_EQUITY), 2), InpModo == MODO_EXAMEN ? "examen" : "fondeado");
   FileClose(fh);
  }

//==================== estrategias ====================
// tipoDia: 0 E2, 1 viernes, 2 vispera, 3 D-2, 4 Q0, 5 dia antes de vispera (sale al dia siguiente)
struct Estrategia
  {
   string nombre; bool activa; int tipoDia; int hIni; int hFin; int lado; string simbolos; string divisas; int numero; int filtroSigma; int nSigma; bool pasaNoche;
  };
Estrategia g_E[6];
int      g_diaEntrada[6];         // fecha NY (dia del anio + 1000*anio) en que se entro
datetime g_fechaEntradaNY[6];
double   g_sigmaUsada[6];

bool DiaValido(const Estrategia &e, datetime dNY)
  {
   switch(e.tipoDia)
     {
      case 0: return EsLaborable(dNY) && !FestivoTARGET(dNY) && !FestivoInglaterra(dNY) && !EnLista(InpFechasBCE, dNY);
      case 1: { MqlDateTime x; TimeToStruct(dNY, x); return x.day_of_week == 5 && !FestivoNYSE(dNY); }
      case 2: return EsVispera(dNY);
      case 3: return EsDmenos2(dNY);
      case 4: return EsQ0(dNY);
      case 5: return EsDiaAntesDeVispera(dNY);
     }
   return false;
  }
// minutos hasta el final de la sesion de trading actual del simbolo, solo si tras ella el mercado
// queda cerrado mas de 20 horas (fin de semana; los cierres nocturnos diarios no cuentan). 99999 = no hay cierre largo cerca; -1 = fuera de sesion.
int MinutosACierreLargo(string sim)
  {
   MqlDateTime t; TimeToStruct(TimeTradeServer(), t);
   int seg = t.hour * 3600 + t.min * 60 + t.sec, fin = -1;
   datetime de, a;
   for(uint k = 0; k < 10 && SymbolInfoSessionTrade(sim, (ENUM_DAY_OF_WEEK)t.day_of_week, k, de, a); k++)
      if(seg >= (int)de && seg < (int)a) { fin = (int)a; break; }
   if(fin < 0) return -1;
   int prox = -1;
   for(int dd = 0; dd < 5 && prox < 0; dd++)
      for(uint k = 0; k < 10 && SymbolInfoSessionTrade(sim, (ENUM_DAY_OF_WEEK)((t.day_of_week + dd) % 7), k, de, a); k++)
        {
         int ini = (int)de + dd * 86400;
         if(ini >= fin && (prox < 0 || ini < prox)) prox = ini;
        }
   if(prox >= 0 && prox - fin < 20 * 3600) return 99999;
   return (fin - seg) / 60;
  }
ulong Magico(const Estrategia &e) { return InpMagicoBase + e.numero; }
int PosicionesEstr(const Estrategia &e)
  {
   int n = 0;
   for(int i = PositionsTotal() - 1; i >= 0; i--)
     {
      ulong tk = PositionGetTicket(i);
      if(tk > 0 && PositionGetInteger(POSITION_MAGIC) == (long)Magico(e)) n++;
     }
   return n;
  }
void CerrarEstr(const Estrategia &e, string motivo)
  {
   for(int i = PositionsTotal() - 1; i >= 0; i--)
     {
      ulong tk = PositionGetTicket(i);
      if(tk == 0 || PositionGetInteger(POSITION_MAGIC) != (long)Magico(e)) continue;
      string sim = PositionGetString(POSITION_SYMBOL); double vol = PositionGetDouble(POSITION_VOLUME);
      double bid = SymbolInfoDouble(sim, SYMBOL_BID), ask = SymbolInfoDouble(sim, SYMBOL_ASK);
      g_trade.SetExpertMagicNumber(Magico(e));
      if(g_trade.PositionClose(tk))
        {
         Sleep(300);
         double res = 0; ulong d = g_trade.ResultDeal();
         if(HistoryDealSelect(d)) res = HistoryDealGetDouble(d, DEAL_PROFIT) + HistoryDealGetDouble(d, DEAL_COMMISSION) + HistoryDealGetDouble(d, DEAL_SWAP);
         Registrar(e.nombre, sim, "cierre_" + motivo, vol, g_sigmaUsada[e.numero], g_trade.ResultPrice(), (ask - bid) / ((ask + bid) / 2) * 1e4, res);
        }
      else Registrar(e.nombre, sim, "error_cierre_" + IntegerToString(g_trade.ResultRetcode()), vol, 0, bid, 0, 0);
     }
  }
void Entrar(Estrategia &e, datetime dNY, int minHastaSalida)
  {
   string sims[]; int ns = StringSplit(e.simbolos, ',', sims);
   if(ns <= 0) return;
   double riesgo = InpRiesgoPct / 100.0 * (InpModo == MODO_EXAMEN ? InpMultExamen : 1.0) / ns;
   g_trade.SetExpertMagicNumber(Magico(e));
   for(int i = 0; i < ns; i++)
     {
      string sim = sims[i]; StringTrimLeft(sim); StringTrimRight(sim);
      if(sim == "" || !SymbolSelect(sim, true)) { Registrar(e.nombre, sim, "simbolo_no_encontrado", 0, 0, 0, 0, 0); continue; }
      double bid = SymbolInfoDouble(sim, SYMBOL_BID), ask = SymbolInfoDouble(sim, SYMBOL_ASK);
      if(bid <= 0 || ask <= 0 || !SymbolInfoInteger(sim, SYMBOL_TRADE_MODE)) { Registrar(e.nombre, sim, "sin_precio_o_cerrado", 0, 0, 0, 0, 0); continue; }
      double spreadPb = (ask - bid) / ((ask + bid) / 2) * 1e4;
      int minCierre = MinutosACierreLargo(sim);
      if(minCierre >= 0 && minCierre < minHastaSalida + InpMinAntesCierre) { Registrar(e.nombre, sim, "sin_entrada_cierre_sesion_" + IntegerToString(minCierre) + "min", 0, 0, bid, spreadPb, 0); continue; }
      if(InpMaxSpreadPb > 0 && spreadPb > InpMaxSpreadPb) { Registrar(e.nombre, sim, "sin_entrada_spread", 0, 0, bid, spreadPb, 0); continue; }
      double sg = Sigma(sim, e.hIni, e.hFin, e.filtroSigma, e.nSigma, e.pasaNoche ? 1 : 0);
      if(sg <= 0) { Registrar(e.nombre, sim, "sin_entrada_sigma", 0, 0, bid, spreadPb, 0); continue; }
      g_sigmaUsada[e.numero] = sg;
      double precio = e.lado > 0 ? ask : bid;
      double lot = Lotes(sim, riesgo, sg, precio);
      if(lot <= 0) { Registrar(e.nombre, sim, "sin_entrada_lote_min", 0, sg, precio, spreadPb, 0); continue; }
      int dig = (int)SymbolInfoInteger(sim, SYMBOL_DIGITS);
      double sl = NormalizeDouble(e.lado > 0 ? precio * (1 - InpStopSigmas * sg) : precio * (1 + InpStopSigmas * sg), dig);
      bool ok = e.lado > 0 ? g_trade.Buy(lot, sim, 0, sl, 0, e.nombre) : g_trade.Sell(lot, sim, 0, sl, 0, e.nombre);
      Registrar(e.nombre, sim, ok ? (e.lado > 0 ? "compra" : "venta") : "error_entrada_" + IntegerToString(g_trade.ResultRetcode()), lot, sg,
                ok ? g_trade.ResultPrice() : precio, spreadPb, 0);
     }
  }

//==================== protecciones ====================
datetime g_diaSrv = 0; double g_equityInicioDia = 0; bool g_paradoHoy = false; bool g_paradoTotal = false;
double BalanceInicial()
  {
   if(InpBalanceInicial > 0) return InpBalanceInicial;
   string k = "Cartera6_BalIni_" + IntegerToString(AccountInfoInteger(ACCOUNT_LOGIN));
   if(!GlobalVariableCheck(k)) GlobalVariableSet(k, AccountInfoDouble(ACCOUNT_BALANCE));
   return GlobalVariableGet(k);
  }
void CerrarTodo(string motivo) { for(int i = 0; i < 6; i++) CerrarEstr(g_E[i], motivo); }
void Protecciones()
  {
   datetime srvDia = SoloFecha(TimeCurrent());
   if(srvDia != g_diaSrv) { g_diaSrv = srvDia; g_equityInicioDia = MathMax(AccountInfoDouble(ACCOUNT_BALANCE), AccountInfoDouble(ACCOUNT_EQUITY)); g_paradoHoy = false; }
   double eq = AccountInfoDouble(ACCOUNT_EQUITY);
   if(!g_paradoHoy && eq < g_equityInicioDia * (1 - InpPerdidaDiariaMaxPct / 100.0))
     { g_paradoHoy = true; CerrarTodo("perdida_diaria"); Registrar("CARTERA", "", "parada_perdida_diaria", 0, 0, 0, 0, eq - g_equityInicioDia); }
   if(!g_paradoTotal && eq < BalanceInicial() * (1 - InpPerdidaTotalMaxPct / 100.0))
     { g_paradoTotal = true; CerrarTodo("perdida_total"); Registrar("CARTERA", "", "parada_perdida_total", 0, 0, 0, 0, eq - BalanceInicial()); }
  }

//==================== ciclo ====================
void Configurar()
  {
   Estrategia e;
   e.nombre = "E2_euro";        e.activa = InpE2_Euro;             e.tipoDia = 0; e.hIni = 600;  e.hFin = 800;  e.lado = -1; e.simbolos = InpSimEURUSD; e.divisas = "EUR,USD"; e.numero = 0; e.filtroSigma = 0; e.nSigma = 60; e.pasaNoche = false; g_E[0] = e;
   e.nombre = "E8_oro_viernes"; e.activa = InpE8_OroViernes;       e.tipoDia = 1; e.hIni = 1600; e.hFin = InpE8_Salida; e.lado = 1;  e.simbolos = InpSimOro;    e.divisas = "USD";     e.numero = 1; e.filtroSigma = 5; e.nSigma = 52; e.pasaNoche = false; g_E[1] = e;
   e.nombre = "E10_plata_vispera"; e.activa = InpE10_PlataVispera; e.tipoDia = 2; e.hIni = 1600; e.hFin = 1655; e.lado = 1;  e.simbolos = InpSimPlata;  e.divisas = "USD";     e.numero = 2; e.filtroSigma = 0; e.nSigma = 60; e.pasaNoche = false; g_E[2] = e;
   e.nombre = "E9_yen_fin_mes"; e.activa = InpE9_YenFinMes;        e.tipoDia = 3; e.hIni = 700;  e.hFin = 800;  e.lado = 1;  e.simbolos = InpSimUSDJPY; e.divisas = "USD,JPY"; e.numero = 3; e.filtroSigma = 0; e.nSigma = 60; e.pasaNoche = false; g_E[3] = e;
   e.nombre = "E11_yen_fin_trim"; e.activa = InpE11_YenFinTrimestre; e.tipoDia = 4; e.hIni = 30; e.hFin = 200;  e.lado = -1; e.simbolos = InpSimUSDJPY + "," + InpSimEURJPY + "," + InpSimGBPJPY; e.divisas = "JPY,USD,EUR,GBP"; e.numero = 4; e.filtroSigma = 0; e.nSigma = 60; e.pasaNoche = false; g_E[4] = e;
   e.nombre = "E12_materias_vispera"; e.activa = InpE12_MateriasVispera; e.tipoDia = 5; e.hIni = 1355; e.hFin = 1355; e.lado = 1; e.simbolos = InpCestaE12; e.divisas = "USD"; e.numero = 5; e.filtroSigma = 0; e.nSigma = 60; e.pasaNoche = true; g_E[5] = e;
  }

int OnInit()
  {
   if(InpSoloDemo && !EnProbador() && AccountInfoInteger(ACCOUNT_TRADE_MODE) != ACCOUNT_TRADE_MODE_DEMO)
     { Print("Cuenta no DEMO e InpSoloDemo=true: el EA no operara."); return INIT_FAILED; }
   Configurar();
   for(int i = 0; i < 6; i++) { g_diaEntrada[i] = -1; g_fechaEntradaNY[i] = 0; g_sigmaUsada[i] = 0; }
   // si el EA se reinicia con posiciones abiertas, se reconocen (respeta su hora de salida en vez de cerrarlas)
   datetime nyAhora = UTCaNY(AhoraUTC()); MqlDateTime ta; TimeToStruct(nyAhora, ta);
   for(int p = PositionsTotal() - 1; p >= 0; p--)
     {
      ulong tk = PositionGetTicket(p); if(tk == 0) continue;
      long mg = PositionGetInteger(POSITION_MAGIC);
      if(mg < (long)InpMagicoBase || mg > (long)InpMagicoBase + 5) continue;
      int i = (int)(mg - (long)InpMagicoBase);
      datetime tSrv = (datetime)PositionGetInteger(POSITION_TIME);
      datetime tUtc = tSrv - (OffsetInvierno() + (VeranoServidor(tSrv - OffsetInvierno() * 3600) ? 1 : 0)) * 3600;
      datetime dEnt = SoloFecha(UTCaNY(tUtc)); MqlDateTime te; TimeToStruct(UTCaNY(tUtc), te);
      g_fechaEntradaNY[i] = dEnt; g_diaEntrada[i] = te.year * 1000 + te.day_of_year;
      PrintFormat("Posicion abierta reconocida: %s (%s), entrada NY %s", g_E[i].nombre, PositionGetString(POSITION_SYMBOL), TimeToString(UTCaNY(tUtc)));
     }
   if(InpFechasBCE == "") Print("AVISO: InpFechasBCE vacio: E2 no se saltara los dias de reunion del BCE (rellena las fechas de ecb.europa.eu).");
   PrintFormat("Cartera de 6 ventajas iniciada%s. Modo %s (riesgo %.2f%% por operacion). Servidor invierno UTC%+d. Balance inicial de referencia %.2f.",
               EnProbador() ? " en el PROBADOR" : "", InpModo == MODO_EXAMEN ? "EXAMEN" : "FONDEADO",
               InpRiesgoPct * (InpModo == MODO_EXAMEN ? InpMultExamen : 1.0), OffsetInvierno(), BalanceInicial());
   EventSetTimer(1);
   return INIT_SUCCEEDED;
  }
void OnDeinit(const int reason) { EventKillTimer(); }

void OnTimer()
  {
   Protecciones();
   datetime utc = AhoraUTC(), ny = UTCaNY(utc);
   datetime dNY = SoloFecha(ny);
   MqlDateTime t; TimeToStruct(ny, t);
   int hm = t.hour * 100 + t.min, idDia = t.year * 1000 + t.day_of_year;
   for(int i = 0; i < 6; i++)
     {
      Estrategia e = g_E[i];
      int abiertas = PosicionesEstr(e);
      // --- salida
      if(abiertas > 0)
        {
         bool cierreCerca = false;
         string ss[]; int nss = StringSplit(e.simbolos, ',', ss);
         for(int j = 0; j < nss; j++) { StringTrimLeft(ss[j]); StringTrimRight(ss[j]); int m = MinutosACierreLargo(ss[j]); if(m >= 0 && m <= InpMinAntesCierre) cierreCerca = true; }
         if(cierreCerca) { CerrarEstr(e, "antes_cierre_sesion"); continue; }
         bool tocaSalir;
         if(e.pasaNoche) tocaSalir = (dNY > g_fechaEntradaNY[i] && hm >= e.hFin) || (dNY > g_fechaEntradaNY[i] + 4 * 86400) || g_fechaEntradaNY[i] == 0;
         else            tocaSalir = (hm >= e.hFin) || (g_diaEntrada[i] != idDia);
         if(tocaSalir)
           {
            if(NoticiaCerca(e.divisas, utc) && hm < e.hFin + 5) continue;    // espera fuera de la ventana de noticias (max. 5 min)
            CerrarEstr(e, "hora");
           }
         continue;
        }
      // --- entrada (ventana de 5 minutos desde la hora de entrada)
      if(!e.activa || g_paradoHoy || g_paradoTotal) continue;
      if(hm < e.hIni || hm >= e.hIni + 5 || g_diaEntrada[i] == idDia) continue;
      if(!DiaValido(e, dNY)) continue;
      g_diaEntrada[i] = idDia;
      datetime tSalida = e.pasaNoche ? NYenUTC(HabilNYSESiguiente(dNY), e.hFin) : NYenUTC(dNY, e.hFin);
      if(NoticiaCerca(e.divisas, utc) || NoticiaCerca(e.divisas, tSalida)) { Registrar(e.nombre, e.simbolos, "sin_entrada_noticia", 0, 0, 0, 0, 0); continue; }
      g_fechaEntradaNY[i] = dNY;
      Entrar(e, dNY, (int)((tSalida - utc) / 60));
     }
  }

void OnTradeTransaction(const MqlTradeTransaction &tr, const MqlTradeRequest &rq, const MqlTradeResult &rs)
  {
   if(tr.type != TRADE_TRANSACTION_DEAL_ADD || !HistoryDealSelect(tr.deal)) return;
   long mg = HistoryDealGetInteger(tr.deal, DEAL_MAGIC);
   if(mg < (long)InpMagicoBase || mg > (long)InpMagicoBase + 5) return;
   if(HistoryDealGetInteger(tr.deal, DEAL_REASON) == DEAL_REASON_SL)
      Registrar(g_E[(int)(mg - (long)InpMagicoBase)].nombre, HistoryDealGetString(tr.deal, DEAL_SYMBOL), "stop_catastrofe", HistoryDealGetDouble(tr.deal, DEAL_VOLUME), 0,
                HistoryDealGetDouble(tr.deal, DEAL_PRICE), 0, HistoryDealGetDouble(tr.deal, DEAL_PROFIT) + HistoryDealGetDouble(tr.deal, DEAL_COMMISSION) + HistoryDealGetDouble(tr.deal, DEAL_SWAP));
  }
