//+------------------------------------------------------------------+
//| Cartera_6_Ventajas_EA.mq5  (version CFD, 12-nov-2026)             |
//| Cartera de ventajas certificadas en CFD (MT5: Upcomers, FTMO...). |
//| Se pone en UN grafico cualquiera y opera todos los simbolos.      |
//| Horas en Nueva York (NY) salvo bitcoin (UTC).                     |
//|                                                                    |
//| ACTIVAS por defecto (costes medidos en Upcomers el 12-nov-2026,   |
//| research/costes_cfd/upcomers_*.csv; cartera_cfd_upcomers.py):     |
//|  E8   XAUUSD largo  16:00 -> 16:55  viernes (FTMO: 16:45)         |
//|  E9   USDJPY largo  07:00 -> 08:00  antepenultimo laborable mes   |
//|  E11  USDJPY+EURJPY+GBPJPY corto 00:30 -> 02:00 ultimo laborable  |
//|       de mar/jun/sep/dic (1/3 del riesgo cada uno)                |
//|  E15  XAUUSD corto  09:30 -> 10:00  antepenultimo laborable mes   |
//|  E13  Nikkei largo  15:00 -> 16:00  2.o laborable del trimestre   |
//|  E16  Nikkei corto  20:00 -> 21:00  penultimo laborable trimestre |
//|  C93  oro, ruptura del max/min de la sesion anterior 08-15 NY,    |
//|       stop 1 ATR(14), objetivo 3 ATR, salida 16:45     (peso 0,2) |
//|  C99  oro, ruptura del rango 19:00-03:00 NY, ventana 03-11,       |
//|       stop el otro extremo, objetivo 1 anchura, salida 16:45 (0,2)|
//|  C101 Nikkei, igual que C99                              (peso 0,2)|
//|  BTC  BTCUSD largo 21:00 -> 23:00 UTC laborables (C2)    (peso 0,2)|
//|       solo si el spread al entrar <= InpMaxSpreadBTC              |
//| DESACTIVADAS: E2 euro (quitado de la cartera el 28-oct-2026),     |
//|  E10 plata y plata (spread 7-9 pb), E12 cesta, E14 FTSE,          |
//|  C113 oro Asia (C116: no pasa con costes CFD).                    |
//|                                                                    |
//| Tamano: riesgo% x peso / sigma de la franja (max de 60 y 250 dias)|
//| x escala del control de volatilidad, con tope de exposicion (el   |
//| tope se aplica despues de la escala). Stop de catastrofe a        |
//| InpStopSigmas sigmas, recortado para no perder mas de             |
//| InpPerdidaMaxOperacionPct por operacion.                          |
//| Protecciones: perdida diaria maxima, perdida total (fija o con    |
//| arrastre que se bloquea en el balance inicial), filtro de noticias|
//| de alto impacto, cierre antes de pausas de sesion, avisos.        |
//| Registro en MQL5/Files/<InpArchivoCSV>. Reglas = pre-registros.   |
//| No cambiar sin nuevo pre-registro.                                |
//+------------------------------------------------------------------+
#property strict
#include <Trade\Trade.mqh>

enum ENUM_DST_SERVIDOR
  {
   DST_EUROPA = 0,   // Europa: ultimo domingo de marzo -> ultimo domingo de octubre (Upcomers, FTMO, MetaQuotes-Demo)
   DST_EEUU   = 1,   // EEUU: 2.o domingo de marzo -> 1.er domingo de noviembre
   DST_NINGUNO = 2   // el servidor no cambia de hora
  };
enum ENUM_MODO
  {
   MODO_FONDEADO = 0, // FONDEADO: riesgo normal
   MODO_EXAMEN   = 1  // EXAMEN: riesgo x InpMultExamen
  };

input group "Riesgo"
input ENUM_MODO InpModo              = MODO_FONDEADO;
input double InpRiesgoPct            = 0.5;    // riesgo por operacion = volatilidad objetivo, % del balance
input double InpMultExamen           = 1.0;    // multiplicador de riesgo en modo EXAMEN
input double InpPesoDiarias          = 0.2;    // peso de las diarias (C93, C99, C101, bitcoin, C113) respecto al riesgo normal
input bool   InpControlVol           = true;   // control de volatilidad de la cartera (escala 0,5-2 segun los ultimos 60 dias)
input double InpVolObjetivo          = 0.35;   // volatilidad diaria objetivo en % a riesgo 0,5 (backtest de esta cartera CFD con bitcoin y oro 16:55, C116: 0,35)
input double InpStopSigmas           = 4.0;    // stop de catastrofe en sigmas
input double InpPerdidaMaxOperacionPct = 1.4;  // perdida maxima por operacion si salta el stop, % del balance (Upcomers Horizon: max 1,5 %); 0 = sin limite
input double InpTopeExposicionFX     = 10.0;   // exposicion maxima por operacion (x balance) en divisas
input double InpTopeExposicionOtros  = 6.0;    // idem en metales, indices y cripto
input double InpRedondeoMin          = 0.5;    // fraccion de lote minimo a partir de la cual se redondea hacia arriba (Nikkei: lote minimo 1)
input double InpPerdidaDiariaMaxPct  = 2.5;    // si el dia pierde esto: cierra todo y no opera mas hoy (Upcomers Horizon 3 %, Odyssey 4 %, FTMO 5 %)
input double InpPerdidaTotalMaxPct   = 5.5;    // limite de perdida total, % del balance inicial (Horizon 6 % con arrastre; Odyssey/FTMO 10 % fijo)
input bool   InpPerdidaTotalArrastre = true;   // true: el limite sigue al maximo de equity y se bloquea en el balance inicial (Horizon); false: fijo
input double InpBalanceInicial       = 0;      // 0 = el balance al arrancar el EA por primera vez

input group "Estrategias (activar / desactivar)"
input bool   InpE8_OroViernes        = true;   // E8 oro viernes
input int    InpE8_Salida            = 1655;   // hora NY de salida del oro del viernes (HHMM): 1655 = regla original (C116 la confirma en CFD; Upcomers cotiza hasta 16:59). FTMO: 1645
input bool   InpE9_YenFinMes         = true;   // E9 yen fin de mes
input bool   InpE11_YenFinTrimestre  = true;   // E11 cesta del yen fin de trimestre
input bool   InpE15_OroDmenos2       = true;   // E15 oro corto antepenultimo laborable del mes 09:30-10:00 NY
input bool   InpE13_NikkeiTrimestre  = true;   // E13 Nikkei largo 2.o laborable del trimestre 15:00-16:00 NY
input bool   InpE16_NikkeiQmenos2    = true;   // E16 Nikkei corto penultimo laborable del trimestre 20:00-21:00 NY
input bool   InpC93_OroDiaAnterior   = true;   // C93 oro ruptura del dia anterior (diaria)
input bool   InpC99_OroRangoAsia     = true;   // C99 oro ruptura del rango asiatico (diaria)
input bool   InpC101_NikkeiRangoAsia = true;   // C101 Nikkei ruptura del rango asiatico (diaria)
input bool   InpBitcoin              = true;   // bitcoin largo 21:00-23:00 UTC laborables (diaria)
input double InpMaxSpreadBTC         = 1.5;    // bitcoin: no entra si el spread supera esto (pb); mediana medida 0,36, 10 % de los dias ~4
input bool   InpC113_OroAsia         = false;  // C113 oro largo 18:00 -> 03:00 NY dom-jue (C116: NO pasa con costes CFD, +1,7 pb t 1,4)
input bool   InpE2_Euro              = false;  // E2 euro 06-08 NY (C116: empeora la cartera CFD, Sharpe -0,47)
input bool   InpE10_PlataVispera     = false;  // E10 plata vispera de festivo (spread de la plata 7-14 pb: CARO)
input bool   InpE12_MateriasVispera  = false;  // E12 cesta de materias primas (no compensa en CFD)
input bool   InpE14_FTSEantesBoE     = false;  // E14 FTSE antes del Banco de Inglaterra (candidata sin validar)

input group "Simbolos (nombre exacto en la cuenta)"
input string InpSimEURUSD            = "EURUSD";
input string InpSimUSDJPY            = "USDJPY";
input string InpSimEURJPY            = "EURJPY";
input string InpSimGBPJPY            = "GBPJPY";
input string InpSimOro               = "XAUUSD";
input string InpSimPlata             = "XAGUSD";
input string InpSimNikkei            = "JPCJPY.c";   // Nikkei 225: Upcomers "JPCJPY.c", FTMO "JP225.cash"
input string InpSimBitcoin           = "BTCUSD.nx";  // Upcomers "BTCUSD.nx", FTMO "BTCUSD"
input string InpSimUK100             = "UK100.cash"; // FTSE 100 (E14)
input string InpCestaE12             = "USOIL.cash,HEATOIL.c,NATGAS.cash,CORN.c,SOYBEAN.c,WHEAT.c"; // nombres FTMO (E12)
input int    InpNikkeiCierreViernes  = 1555;   // hora NY a la que se cierra el Nikkei los viernes (Upcomers deja de cotizar a las 16:00 NY)

input group "Calendario"
input string InpFechasBoE            = "2026.11.05,2026.12.17,2027.02.04,2027.03.18,2027.04.29,2027.06.17,2027.07.29,2027.09.16,2027.11.04,2027.12.16"; // decisiones del Banco de Inglaterra
input string InpFechasBCE            = "";     // dias de reunion del BCE "AAAA.MM.DD,..." (solo E2)
input string InpFestivosNYSE         = "2025.01.01,2025.01.09,2025.01.20,2025.02.17,2025.04.18,2025.05.26,2025.06.19,2025.07.04,2025.09.01,2025.11.27,2025.12.25,2026.01.01,2026.01.19,2026.02.16,2026.04.03,2026.05.25,2026.06.19,2026.07.03,2026.09.07,2026.11.26,2026.12.25,2027.01.01,2027.01.18,2027.02.15,2027.03.26,2027.05.31,2027.06.18,2027.07.05,2027.09.06,2027.11.25,2027.12.24"; // festivos NYSE (ampliar cada anio)
input int    InpMinNoticias          = 2;      // no abrir ni cerrar a +- estos minutos de una noticia de alto impacto
input bool   InpFiltroNoticias       = true;

input group "Sistema"
input ENUM_DST_SERVIDOR InpDSTServidor = DST_EUROPA;
input bool   InpSoloDemo             = false;  // true: negarse a operar si la cuenta no es DEMO (las cuentas de prop firm suelen ser demo)
input int    InpOffsetServidorInv    = 1;      // SOLO Probador: hora servidor - UTC en invierno (Upcomers 1; FTMO/MetaQuotes 2)
input int    InpMinAntesCierre       = 5;      // cierra lo abierto estos minutos antes de una pausa de sesion del simbolo
input double InpMaxSpreadPb          = 0;      // >0: no entrar si el spread (pb del precio) supera esto (todas las estrategias)
input bool   InpSigmaRespaldo        = true;   // si el broker no tiene historico suficiente para la sigma, usar la sigma tipica x1,3 (se registra)
input bool   InpNotificacionesMovil  = false;  // enviar tambien los avisos al movil (MetaQuotes ID en Herramientas > Opciones > Notificaciones)
input ulong  InpMagicoBase           = 61000;  // magico de cada estrategia = base + numero
input string InpArchivoCSV           = "Cartera_CFD_log.csv";
input string InpArchivoPnl           = "Cartera_CFD_pnl_diario.csv";   // resultado por sesion para el control de volatilidad (no borrar)

CTrade g_trade;
#define NV  12   // estrategias de franja horaria (numeros 0-11)
#define NR  3    // rupturas diarias (numeros 12-14)
#define NTOT 15
double g_escalaVol = 1.0;
datetime g_diaSrv = 0; double g_equityInicioDia = 0; bool g_paradoHoy = false; bool g_paradoTotal = false;

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
// hora del servidor -> UTC (para las velas y operaciones del historial)
datetime ServidorAUTC(datetime srv)
  {
   int off = OffsetInvierno();
   datetime u = srv - off * 3600;
   if(VeranoServidor(u - 3600)) u -= 3600;
   return u;
  }
// sesion de cotizacion (17:00 -> 17:00 NY) a la que pertenece una hora NY: >= 17:00 es la del dia siguiente; fin de semana -> lunes
datetime SesionDe(datetime ny)
  {
   MqlDateTime x; TimeToStruct(ny, x);
   datetime s = SoloFecha(ny) + (x.hour >= 17 ? 86400 : 0);
   while(true) { MqlDateTime y; TimeToStruct(s, y); if(y.day_of_week >= 1 && y.day_of_week <= 5) break; s += 86400; }
   return s;
  }

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
datetime SumarLaborables(datetime d, int n) { datetime s = d; for(int k = 0; k < n; k++) { s += 86400; while(!EsLaborable(s)) s += 86400; } return s; }
int LaborablesEntre(datetime a, datetime b) { int n = 0; for(datetime s = a + 86400; s <= b; s += 86400) if(EsLaborable(s)) n++; return n; }
// siguiente dia de lunes a viernes SIN saltar festivos (con HabilNYSESiguiente la vispera nunca se detectaba: fallo corregido 12-nov-2026)
datetime SiguienteLaborable(datetime d) { datetime s = d + 86400; while(!EsLaborable(s)) s += 86400; return s; }
bool EsVispera(datetime d) { return EsLaborable(d) && !FestivoNYSE(d) && FestivoNYSE(SiguienteLaborable(d)); }
bool EsDiaAntesDeVispera(datetime d)   // y la vispera es el dia siguiente (nunca se mantiene el fin de semana)
  { datetime s = SiguienteLaborable(d); return EsLaborable(d) && !FestivoNYSE(d) && s == d + 86400 && EsVispera(s); }
int LaborablesRestantesMes(datetime d)    // laborables (lun-vie) del mes posteriores a d
  {
   MqlDateTime x; TimeToStruct(d, x); int n = 0;
   for(datetime s = d + 86400; ; s += 86400) { MqlDateTime y; TimeToStruct(s, y); if(y.mon != x.mon) break; if(EsLaborable(s)) n++; }
   return n;
  }
bool EsDmenos2(datetime d) { return EsLaborable(d) && LaborablesRestantesMes(d) == 2; }
bool EsQmas2(datetime d)   // 2.o laborable (lun-vie, sin contar el 1 de enero) de enero, abril, julio y octubre
  {
   MqlDateTime x; TimeToStruct(d, x);
   if(!EsLaborable(d) || x.mon % 3 != 1 || (x.mon == 1 && x.day == 1)) return false;
   int n = 0;
   for(datetime s = d - x.day * 86400 + 86400; s <= d; s += 86400) { MqlDateTime y; TimeToStruct(s, y); if(EsLaborable(s) && !(y.mon == 1 && y.day == 1)) n++; }
   return n == 2;
  }
bool EsQmenos2(datetime d) { MqlDateTime x; TimeToStruct(d, x); return EsLaborable(d) && x.mon % 3 == 0 && LaborablesRestantesMes(d) == 1; }   // penultimo laborable del trimestre
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

//==================== registro y avisos ====================
void Registrar(string estr, string sim, string evento, double lotes, double sigma, double precio, double spreadPb, double resultado)
  {
   bool nuevo = !FileIsExist(InpArchivoCSV);
   int fh = FileOpen(InpArchivoCSV, FILE_READ | FILE_WRITE | FILE_CSV | FILE_ANSI, ',');
   if(fh != INVALID_HANDLE)
     {
      if(nuevo) FileWrite(fh, "hora_utc", "hora_ny", "estrategia", "simbolo", "evento", "lotes", "sigma_pb", "precio", "spread_pb", "resultado", "balance", "equity", "escala_vol", "modo");
      FileSeek(fh, 0, SEEK_END);
      datetime u = AhoraUTC();
      FileWrite(fh, TimeToString(u, TIME_DATE | TIME_SECONDS), TimeToString(UTCaNY(u), TIME_DATE | TIME_SECONDS), estr, sim, evento, DoubleToString(lotes, 2),
                DoubleToString(sigma * 1e4, 2), DoubleToString(precio, 5), DoubleToString(spreadPb, 2), DoubleToString(resultado, 2),
                DoubleToString(AccountInfoDouble(ACCOUNT_BALANCE), 2), DoubleToString(AccountInfoDouble(ACCOUNT_EQUITY), 2),
                DoubleToString(g_escalaVol, 2), InpModo == MODO_EXAMEN ? "examen" : "fondeado");
      FileClose(fh);
     }
   PrintFormat("%s | %s | %s | lotes %.2f | precio %s | resultado %.2f", estr, sim, evento, lotes, DoubleToString(precio, 5), resultado);
   // avisos con sonido (y al movil si se activa) de lo que hay que mirar en el momento
   if(!EnProbador() && (StringFind(evento, "error") >= 0 || StringFind(evento, "parada") == 0 || StringFind(evento, "stop_catastrofe") == 0 ||
      StringFind(evento, "simbolo_no_encontrado") == 0 || StringFind(evento, "sin_entrada_sigma") == 0 || StringFind(evento, "sigma_respaldo") >= 0 ||
      StringFind(evento, "sin_precio") == 0 || StringFind(evento, "aviso") == 0))
     {
      string m = "Cartera CFD: " + estr + " " + sim + " " + evento;
      Alert(m);
      if(InpNotificacionesMovil) SendNotification(m);
     }
  }

//==================== precios, sigma y tamano ====================
double PrecioEn(string sim, datetime T_srv)   // cierre de la vela M1 que termina en T (busca 5 minutos atras)
  {
   for(int j = 1; j <= 5; j++)
     {
      int k = iBarShift(sim, PERIOD_M1, T_srv - j * 60, true);
      if(k >= 0) return iClose(sim, PERIOD_M1, k);
     }
   return 0;
  }
datetime HoraDia(datetime dia, int hhmm, bool utc) { return utc ? dia + (hhmm / 100) * 3600 + (hhmm % 100) * 60 : NYenUTC(dia, hhmm); }
// sigma de ln(P(fin)/P(ini)) en los ultimos 'nDias' dias que cumplen el filtro (0 = laborables, 5 = viernes)
// noches: el final es 'noches' laborables despues; utc: horas en UTC en vez de NY
double Sigma(string sim, int hIni, int hFin, int filtroDia, int nDias, int noches, bool utc, int minObs, bool avisar)
  {
   datetime hoy = SoloFecha(utc ? AhoraUTC() : UTCaNY(AhoraUTC()));
   double r[]; int n = 0;
   int limite = MathMax(400, filtroDia == 5 ? nDias * 7 + 60 : nDias * 3 / 2 + 60);
   for(int k = 1; k <= limite && n < nDias; k++)
     {
      datetime d = hoy - k * 86400;
      MqlDateTime x; TimeToStruct(d, x);
      if(!EsLaborable(d)) continue;
      if(filtroDia == 5 && x.day_of_week != 5) continue;
      datetime d2 = SumarLaborables(d, noches);
      datetime t0 = UTCaServidor(HoraDia(d, hIni, utc)), t1 = UTCaServidor(HoraDia(d2, hFin, utc));
      double p0 = PrecioEn(sim, t0), p1 = PrecioEn(sim, t1);
      if(p0 <= 0) p0 = PrecioEn(sim, t0 + 120);   // tras una pausa (p. ej. el oro 17:00-18:00) no hay vela que cierre a la hora exacta
      if(p0 <= 0 || p1 <= 0) continue;
      ArrayResize(r, n + 1); r[n++] = MathLog(p1 / p0);
     }
   if(n < minObs || n < 2)
     {
      if(avisar) PrintFormat("%s: solo %d dias con datos para la sigma (%d-%d). Abre su grafico M1, retrocede para descargar historico y pon Herramientas > Opciones > Graficos > Max. barras = Unlimited.", sim, n, hIni, hFin);
      return 0;
     }
   double m = 0, v = 0;
   for(int i = 0; i < n; i++) m += r[i];
   m /= n;
   for(int i = 0; i < n; i++) v += (r[i] - m) * (r[i] - m);
   return MathSqrt(v / (n - 1));
  }
// la mayor de la sigma corta (60 dias / 52 viernes) y la larga (250 dias / 150 viernes): una racha tranquila no dispara el tamano.
// Si falta historico y InpSigmaRespaldo, la sigma tipica de la estrategia x1,3. 'respaldo' indica si se uso.
double SigmaRobusta(string sim, int hIni, int hFin, int filtroDia, int nCorta, int noches, bool utc, double sigmaRefPb, bool &respaldo)
  {
   respaldo = false;
   double s1 = Sigma(sim, hIni, hFin, filtroDia, nCorta, noches, utc, MathMin(30, nCorta * 2 / 3), true);
   if(s1 <= 0)
     {
      if(InpSigmaRespaldo && sigmaRefPb > 0) { respaldo = true; return sigmaRefPb * 1.3 / 1e4; }
      return 0;
     }
   int nLarga = filtroDia == 5 ? 150 : 250;
   double s2 = Sigma(sim, hIni, hFin, filtroDia, nLarga, noches, utc, nLarga * 3 / 5, false);
   return MathMax(s1, s2);
  }
bool EsFX(string sim) { long cm = SymbolInfoInteger(sim, SYMBOL_TRADE_CALC_MODE); return cm == SYMBOL_CALC_MODE_FOREX || cm == SYMBOL_CALC_MODE_FOREX_NO_LEVERAGE; }
// nocional de 1 lote en divisa de la cuenta = 100 x beneficio de un movimiento del 1 %
double NocionalLote(string sim, double precio)
  {
   double pr = 0;
   if(OrderCalcProfit(ORDER_TYPE_BUY, sim, 1.0, precio, precio * 1.01, pr) && pr > 0) return pr * 100.0;
   double tv = SymbolInfoDouble(sim, SYMBOL_TRADE_TICK_VALUE), ts = SymbolInfoDouble(sim, SYMBOL_TRADE_TICK_SIZE);
   if(tv <= 0 || ts <= 0) return 0;
   return precio / ts * tv;
  }
double AjustarLote(string sim, double lot)
  {
   double paso = SymbolInfoDouble(sim, SYMBOL_VOLUME_STEP); if(paso <= 0) paso = 0.01;
   double x = lot / paso; double q = MathFloor(x);
   if(x - q >= InpRedondeoMin) q += 1;
   lot = q * paso;
   if(lot < SymbolInfoDouble(sim, SYMBOL_VOLUME_MIN) - 1e-9) return 0;
   return NormalizeDouble(MathMin(lot, SymbolInfoDouble(sim, SYMBOL_VOLUME_MAX)), 2);
  }
// lotes para riesgoFrac / sigma x escala de volatilidad (tope despues de la escala); 'expos' = exposicion resultante (x balance)
double Lotes(string sim, double riesgoFrac, double sigma, double precio, double &expos)
  {
   expos = 0;
   if(sigma <= 0 || precio <= 0) return 0;
   double tope = EsFX(sim) ? InpTopeExposicionFX : InpTopeExposicionOtros;
   double e = MathMin(riesgoFrac / sigma * g_escalaVol, tope);
   double nocLote = NocionalLote(sim, precio);
   if(nocLote <= 0) return 0;
   double lot = AjustarLote(sim, e * AccountInfoDouble(ACCOUNT_BALANCE) / nocLote);
   expos = lot * nocLote / AccountInfoDouble(ACCOUNT_BALANCE);
   return lot;
  }
double SpreadPb(string sim) { double b = SymbolInfoDouble(sim, SYMBOL_BID), a = SymbolInfoDouble(sim, SYMBOL_ASK); return (a > 0 && b > 0) ? (a - b) / ((a + b) / 2) * 1e4 : 0; }

//==================== sesiones ====================
// minutos hasta el final de la sesion actual del simbolo, encadenando sesiones separadas por pausas de <= umbralMin minutos.
// 99999 = no hay cierre en los proximos dias; -1 = fuera de sesion.
int MinutosACierre(string sim, int umbralMin)
  {
   MqlDateTime t; TimeToStruct(TimeTradeServer(), t);
   int seg = t.hour * 3600 + t.min * 60 + t.sec;
   int ini[], fin[]; int n = 0;
   datetime de, a;
   for(int dd = 0; dd < 8; dd++)
      for(uint k = 0; k < 10 && SymbolInfoSessionTrade(sim, (ENUM_DAY_OF_WEEK)((t.day_of_week + dd) % 7), k, de, a); k++)
        { ArrayResize(ini, n + 1); ArrayResize(fin, n + 1); ini[n] = (int)de + dd * 86400; fin[n] = (int)a + dd * 86400; n++; }
   if(n == 0) return 99999;           // el broker no publica sesiones
   int fFin = -1;
   for(int i = 0; i < n; i++) if(seg >= ini[i] && seg < fin[i]) { fFin = fin[i]; break; }
   if(fFin < 0) return -1;
   for(int it = 0; it < 40; it++)
     {
      int prox = -1, proxFin = -1;
      for(int i = 0; i < n; i++) if(ini[i] >= fFin - 60 && fin[i] > fFin && (prox < 0 || ini[i] < prox)) { prox = ini[i]; proxFin = fin[i]; }
      if(prox < 0) return 99999;
      if(prox - fFin > umbralMin * 60) break;
      fFin = proxFin;
     }
   return MathMin(99999, (fFin - seg) / 60);
  }
bool EsNikkei(string sim) { return sim == InpSimNikkei; }
// minutos hasta el cierre forzado del Nikkei del viernes (99999 si no aplica)
int MinutosCierreNikkeiViernes(string sim, datetime ny)
  {
   if(!EsNikkei(sim)) return 99999;
   MqlDateTime x; TimeToStruct(ny, x);
   if(x.day_of_week != 5) return 99999;
   int ahora = x.hour * 60 + x.min, lim = (InpNikkeiCierreViernes / 100) * 60 + InpNikkeiCierreViernes % 100;
   return lim - ahora;
  }

//==================== estrategias ====================
// tipoDia: 0 E2, 1 viernes, 2 vispera, 3 D-2, 4 Q0, 5 dia antes de vispera, 6 Q+2, 7 BoE-3, 8 Q-2, 9 laborable (fecha UTC), 10 domingo a jueves (NY)
struct Estrategia
  {
   string nombre; bool activa; int tipoDia; int hIni; int hFin; int lado; string simbolos; string divisas; int numero; int filtroSigma; int nSigma;
   int noches; double peso; bool utc; double maxSpread; double sigmaRefPb;
  };
struct Ruptura
  {
   string nombre; bool activa; string sim; bool asiatica; int numero; double sigmaRefPb;
   datetime dia; bool lista; bool hecha; double H; double L; double atr; datetime diaEntrada;
  };
Estrategia g_E[NV];
Ruptura    g_R[NR];
int      g_diaEntrada[NV];         // id del dia (anio*1000 + dia del anio, NY o UTC) en que se entro
datetime g_fechaEntrada[NV];
double   g_sigmaUsada[NTOT];
string   g_nombre[NTOT];
int      g_avisoAlgo = -1;

bool DiaValido(const Estrategia &e, datetime d)
  {
   MqlDateTime x; TimeToStruct(d, x);
   switch(e.tipoDia)
     {
      case 0: return EsLaborable(d) && !FestivoTARGET(d) && !FestivoInglaterra(d) && !EnLista(InpFechasBCE, d);
      case 1: return x.day_of_week == 5 && !FestivoNYSE(d);
      case 2: return EsVispera(d);
      case 3: return EsDmenos2(d);
      case 4: return EsQ0(d);
      case 5: return EsDiaAntesDeVispera(d);
      case 6: return EsQmas2(d);
      case 7: return EsLaborable(d) && EnLista(InpFechasBoE, SumarLaborables(d, 3));
      case 8: return EsQmenos2(d);
      case 9: return EsLaborable(d);
      case 10: return x.day_of_week != 5 && x.day_of_week != 6;
     }
   return false;
  }
ulong Magico(int numero) { return InpMagicoBase + numero; }
bool EsMagicoNuestro(long mg) { return mg >= (long)InpMagicoBase && mg < (long)InpMagicoBase + NTOT; }
int PosicionesMagico(int numero)
  {
   int n = 0;
   for(int i = PositionsTotal() - 1; i >= 0; i--)
     {
      ulong tk = PositionGetTicket(i);
      if(tk > 0 && PositionGetInteger(POSITION_MAGIC) == (long)Magico(numero)) n++;
     }
   return n;
  }
void CerrarMagico(int numero, string motivo)
  {
   for(int i = PositionsTotal() - 1; i >= 0; i--)
     {
      ulong tk = PositionGetTicket(i);
      if(tk == 0 || PositionGetInteger(POSITION_MAGIC) != (long)Magico(numero)) continue;
      string sim = PositionGetString(POSITION_SYMBOL); double vol = PositionGetDouble(POSITION_VOLUME);
      g_trade.SetExpertMagicNumber(Magico(numero));
      if(g_trade.PositionClose(tk))
        {
         Sleep(300);
         double res = 0; ulong d = g_trade.ResultDeal();
         if(HistoryDealSelect(d)) res = HistoryDealGetDouble(d, DEAL_PROFIT) + HistoryDealGetDouble(d, DEAL_COMMISSION) + HistoryDealGetDouble(d, DEAL_SWAP);
         Registrar(g_nombre[numero], sim, "cierre_" + motivo, vol, g_sigmaUsada[numero], g_trade.ResultPrice(), SpreadPb(sim), res);
        }
      else Registrar(g_nombre[numero], sim, "error_cierre_" + IntegerToString(g_trade.ResultRetcode()), vol, 0, SymbolInfoDouble(sim, SYMBOL_BID), 0, 0);
     }
  }
// envia la orden; recorta el stop para no perder mas de InpPerdidaMaxOperacionPct (franjas) y registra
bool Abrir(int numero, string nombre, string sim, int lado, double lot, double sg, double sl, double tp, double spreadPb, string etiqueta)
  {
   g_trade.SetExpertMagicNumber(Magico(numero));
   int dig = (int)SymbolInfoInteger(sim, SYMBOL_DIGITS);
   sl = NormalizeDouble(sl, dig); if(tp > 0) tp = NormalizeDouble(tp, dig);
   bool ok = lado > 0 ? g_trade.Buy(lot, sim, 0, sl, tp, nombre) : g_trade.Sell(lot, sim, 0, sl, tp, nombre);
   double precio = lado > 0 ? SymbolInfoDouble(sim, SYMBOL_ASK) : SymbolInfoDouble(sim, SYMBOL_BID);
   Registrar(nombre, sim, ok ? etiqueta : "error_entrada_" + IntegerToString(g_trade.ResultRetcode()), lot, sg, ok ? g_trade.ResultPrice() : precio, spreadPb, 0);
   return ok;
  }
void Entrar(Estrategia &e, datetime ny, int minHastaSalida)
  {
   string sims[]; int ns = StringSplit(e.simbolos, ',', sims);
   if(ns <= 0) return;
   double riesgo = InpRiesgoPct / 100.0 * (InpModo == MODO_EXAMEN ? InpMultExamen : 1.0) * e.peso / ns;
   for(int i = 0; i < ns; i++)
     {
      string sim = sims[i]; StringTrimLeft(sim); StringTrimRight(sim);
      if(sim == "" || !SymbolSelect(sim, true)) { Registrar(e.nombre, sim, "simbolo_no_encontrado", 0, 0, 0, 0, 0); continue; }
      double bid = SymbolInfoDouble(sim, SYMBOL_BID), ask = SymbolInfoDouble(sim, SYMBOL_ASK);
      if(bid <= 0 || ask <= 0 || !SymbolInfoInteger(sim, SYMBOL_TRADE_MODE)) { Registrar(e.nombre, sim, "sin_precio_o_cerrado", 0, 0, 0, 0, 0); continue; }
      double spreadPb = SpreadPb(sim);
      // la sesion tiene que cubrir al menos el 75 % de la franja (si no llega entera, se sale antes de la pausa)
      int minCierre = MathMin(MinutosACierre(sim, e.noches > 0 ? 20 * 60 : 30), MinutosCierreNikkeiViernes(sim, ny));
      if(minCierre < 0) { Registrar(e.nombre, sim, "sin_precio_fuera_de_sesion", 0, 0, bid, spreadPb, 0); continue; }
      if(minCierre - InpMinAntesCierre < minHastaSalida * 3 / 4) { Registrar(e.nombre, sim, "sin_entrada_cierre_sesion_" + IntegerToString(minCierre) + "min", 0, 0, bid, spreadPb, 0); continue; }
      double maxSp = e.maxSpread > 0 ? e.maxSpread : InpMaxSpreadPb;
      if(maxSp > 0 && spreadPb > maxSp) { Registrar(e.nombre, sim, "sin_entrada_spread_" + DoubleToString(spreadPb, 2), 0, 0, bid, spreadPb, 0); continue; }
      bool resp = false;
      double sg = SigmaRobusta(sim, e.hIni, e.hFin, e.filtroSigma, e.nSigma, e.noches, e.utc, e.sigmaRefPb, resp);
      if(sg <= 0) { Registrar(e.nombre, sim, "sin_entrada_sigma_faltan_datos", 0, 0, bid, spreadPb, 0); continue; }
      if(resp) Registrar(e.nombre, sim, "aviso_sigma_respaldo_sin_historico", 0, sg, bid, spreadPb, 0);
      g_sigmaUsada[e.numero] = sg;
      double precio = e.lado > 0 ? ask : bid, expos = 0;
      double lot = Lotes(sim, riesgo, sg, precio, expos);
      if(lot <= 0) { Registrar(e.nombre, sim, "sin_entrada_lote_min", 0, sg, precio, spreadPb, 0); continue; }
      double dist = InpStopSigmas * sg;
      if(InpPerdidaMaxOperacionPct > 0 && expos > 0) dist = MathMin(dist, InpPerdidaMaxOperacionPct / 100.0 / expos);
      double sl = e.lado > 0 ? precio * (1 - dist) : precio * (1 + dist);
      Abrir(e.numero, e.nombre, sim, e.lado, lot, sg, sl, 0, spreadPb, e.lado > 0 ? "compra" : "venta");
     }
  }

//==================== rupturas diarias ====================
// C93: max/min de la sesion anterior (17:00->17:00 NY), ATR(14) de sesiones; ventana 08:00-15:00; stop 1 ATR, objetivo 3 ATR; salida 16:45.
// C99/C101: rango 19:00 (dia anterior) -> 03:00 NY; ventana 03:00-11:00; stop = el otro extremo; objetivo = 1 x anchura; salida 16:45.
bool PrepararNiveles(Ruptura &r, datetime dNY)
  {
   MqlRates b[];
   if(r.asiatica)
     {
      datetime a = UTCaServidor(NYenUTC(dNY - 86400, 1900)), z = UTCaServidor(NYenUTC(dNY, 300));
      int n = CopyRates(r.sim, PERIOD_M1, a, z - 60, b);
      if(n < 3) return false;
      double h = -DBL_MAX, l = DBL_MAX;
      for(int k = 0; k < n; k++) { if(b[k].time < a || b[k].time >= z) continue; h = MathMax(h, b[k].high); l = MathMin(l, b[k].low); }
      if(h <= l) return false;
      r.H = h; r.L = l; return true;
     }
   datetime desde = UTCaServidor(NYenUTC(dNY - 30 * 86400, 1700));
   int n = CopyRates(r.sim, PERIOD_M1, desde, TimeCurrent(), b);
   if(n < 100) return false;
   double sh[], sl[], sc[]; int ns = 0;
   datetime clave = 0; double h = -DBL_MAX, l = DBL_MAX, c = 0;
   for(int k = n - 1; k >= 0 && ns < 16; k--)            // de la vela mas reciente a la mas antigua
     {
      datetime ny = UTCaNY(ServidorAUTC(b[k].time));
      datetime ck = SoloFecha(ny + 7 * 3600);              // sesion 17:00->17:00: la clave es su dia de cotizacion
      if(ck >= dNY) continue;
      if(ck != clave)
        {
         if(clave != 0 && EsLaborable(clave)) { ArrayResize(sh, ns + 1); ArrayResize(sl, ns + 1); ArrayResize(sc, ns + 1); sh[ns] = h; sl[ns] = l; sc[ns] = c; ns++; }
         clave = ck; h = -DBL_MAX; l = DBL_MAX; c = b[k].close;
        }
      h = MathMax(h, b[k].high); l = MathMin(l, b[k].low);
     }
   if(ns < 15) return false;
   double tr = 0;
   for(int s = 0; s < 14; s++)
     {
      double cAnt = sc[s + 1];
      tr += MathMax(sh[s] - sl[s], MathMax(MathAbs(sh[s] - cAnt), MathAbs(sl[s] - cAnt)));
     }
   r.H = sh[0]; r.L = sl[0]; r.atr = tr / 14; return r.atr > 0;
  }
void GestionarRuptura(Ruptura &r, datetime utc, datetime ny)
  {
   datetime dNY = SoloFecha(ny);
   MqlDateTime t; TimeToStruct(ny, t);
   int hm = t.hour * 100 + t.min;
   // --- salida: 16:45 NY, otro dia, o antes de una pausa de sesion (Nikkei del viernes)
   if(PosicionesMagico(r.numero) > 0)
     {
      int mc = MathMin(MinutosACierre(r.sim, 30), MinutosCierreNikkeiViernes(r.sim, ny));
      if(mc >= 0 && mc <= InpMinAntesCierre) CerrarMagico(r.numero, "antes_cierre_sesion");
      else if(hm >= 1645 || dNY != r.diaEntrada)
        {
         if(NoticiaCerca("USD", utc) && hm < 1650 && dNY == r.diaEntrada) return;
         CerrarMagico(r.numero, "hora");
        }
      return;
     }
   if(!EsLaborable(dNY)) return;
   int hIni = r.asiatica ? 300 : 800, hFin = r.asiatica ? 1100 : 1500;
   if(r.dia != dNY) { r.dia = dNY; r.hecha = false; r.lista = false; }
   if(!r.activa || r.hecha || g_paradoHoy || g_paradoTotal || hm < hIni || hm >= hFin) return;
   if(!SymbolSelect(r.sim, true)) { r.hecha = true; Registrar(r.nombre, r.sim, "simbolo_no_encontrado", 0, 0, 0, 0, 0); return; }
   datetime iniSrv = UTCaServidor(NYenUTC(dNY, hIni));
   if(!r.lista)
     {
      r.lista = true;
      if(!PrepararNiveles(r, dNY)) { r.hecha = true; Registrar(r.nombre, r.sim, "sin_niveles_faltan_datos", 0, 0, 0, 0, 0); return; }
      Registrar(r.nombre, r.sim, "niveles_" + DoubleToString(r.H, (int)SymbolInfoInteger(r.sim, SYMBOL_DIGITS)) + "_" + DoubleToString(r.L, (int)SymbolInfoInteger(r.sim, SYMBOL_DIGITS)), 0, 0, 0, 0, 0);
      // si el EA arranca a mitad de la ventana y la ruptura ya ocurrio, no entra tarde (la regla es la PRIMERA ruptura)
      MqlRates b[]; int n = CopyRates(r.sim, PERIOD_M1, iniSrv, TimeCurrent(), b);
      for(int k = 0; k < n - 1; k++)
         if(b[k].time >= iniSrv && (b[k].high > r.H || b[k].low < r.L)) { r.hecha = true; Registrar(r.nombre, r.sim, "sin_entrada_ruptura_ya_ocurrida_al_arrancar", 0, 0, b[k].close, 0, 0); return; }
     }
   // extremos de la vela M1 en curso (y la anterior, por si el temporizador se salto un instante)
   double hi = -DBL_MAX, lo = DBL_MAX;
   for(int k = 0; k <= 1; k++)
     {
      datetime bt = iTime(r.sim, PERIOD_M1, k);
      if(bt == 0 || bt < iniSrv) continue;
      hi = MathMax(hi, iHigh(r.sim, PERIOD_M1, k)); lo = MathMin(lo, iLow(r.sim, PERIOD_M1, k));
     }
   double bid = SymbolInfoDouble(r.sim, SYMBOL_BID);
   if(bid > 0) { hi = MathMax(hi, bid); lo = MathMin(lo, bid); }
   bool arriba = hi > r.H, abajo = lo < r.L;
   if(!arriba && !abajo) return;
   r.hecha = true;
   if(arriba && abajo) { Registrar(r.nombre, r.sim, "rompe_los_dos_niveles_sin_operacion", 0, 0, bid, 0, 0); return; }
   int lado = arriba ? 1 : -1;
   if(!EnProbador() && (!TerminalInfoInteger(TERMINAL_TRADE_ALLOWED) || !MQLInfoInteger(MQL_TRADE_ALLOWED))) { Registrar(r.nombre, r.sim, "aviso_trading_algoritmico_desactivado", 0, 0, 0, 0, 0); return; }
   if(NoticiaCerca("USD", utc)) { Registrar(r.nombre, r.sim, "sin_entrada_noticia", 0, 0, bid, 0, 0); return; }
   double spreadPb = SpreadPb(r.sim);
   if(InpMaxSpreadPb > 0 && spreadPb > InpMaxSpreadPb) { Registrar(r.nombre, r.sim, "sin_entrada_spread", 0, 0, bid, spreadPb, 0); return; }
   int mc = MathMin(MinutosACierre(r.sim, 30), MinutosCierreNikkeiViernes(r.sim, ny));
   if(mc < 30 + InpMinAntesCierre) { Registrar(r.nombre, r.sim, "sin_entrada_cierre_sesion_" + IntegerToString(mc) + "min", 0, 0, bid, spreadPb, 0); return; }
   bool resp = false;
   double sg = SigmaRobusta(r.sim, hIni, 1645, 0, 60, 0, false, r.sigmaRefPb, resp);
   if(sg <= 0) { Registrar(r.nombre, r.sim, "sin_entrada_sigma_faltan_datos", 0, 0, bid, spreadPb, 0); return; }
   if(resp) Registrar(r.nombre, r.sim, "aviso_sigma_respaldo_sin_historico", 0, sg, bid, spreadPb, 0);
   g_sigmaUsada[r.numero] = sg;
   double precio = lado > 0 ? SymbolInfoDouble(r.sim, SYMBOL_ASK) : bid, expos = 0;
   double riesgo = InpRiesgoPct / 100.0 * (InpModo == MODO_EXAMEN ? InpMultExamen : 1.0) * InpPesoDiarias;
   double lot = Lotes(r.sim, riesgo, sg, precio, expos);
   if(lot <= 0) { Registrar(r.nombre, r.sim, "sin_entrada_lote_min", 0, sg, precio, spreadPb, 0); return; }
   double stop, obj;
   if(r.asiatica) { double w = r.H - r.L; stop = lado > 0 ? r.L : r.H; obj = precio + lado * w; }
   else { stop = precio - lado * r.atr; obj = precio + lado * 3 * r.atr; }
   if((lado > 0 && stop >= bid) || (lado < 0 && stop <= SymbolInfoDouble(r.sim, SYMBOL_ASK))) { Registrar(r.nombre, r.sim, "sin_entrada_stop_invalido", 0, sg, precio, spreadPb, 0); return; }
   // perdida maxima por operacion: se reducen los lotes (no se mueve el stop de la regla)
   double perdida = MathAbs(precio - stop) / precio * expos;
   if(InpPerdidaMaxOperacionPct > 0 && perdida > InpPerdidaMaxOperacionPct / 100.0)
     {
      double nocLote = NocionalLote(r.sim, precio);
      lot = AjustarLote(r.sim, InpPerdidaMaxOperacionPct / 100.0 * AccountInfoDouble(ACCOUNT_BALANCE) / (MathAbs(precio - stop) / precio * nocLote));
      if(lot <= 0) { Registrar(r.nombre, r.sim, "sin_entrada_lote_min_por_perdida_max", 0, sg, precio, spreadPb, 0); return; }
     }
   if(Abrir(r.numero, r.nombre, r.sim, lado, lot, sg, stop, obj, spreadPb, lado > 0 ? "compra_ruptura" : "venta_ruptura")) r.diaEntrada = dNY;
  }

//==================== control de volatilidad ====================
// Al terminar cada sesion (17:00 NY) se guarda su resultado (operaciones de este EA) dividido por la escala que estaba en vigor:
// asi la serie es la de la cartera SIN escalar, como en el backtest; la escala = objetivo / desviacion de los ultimos 60 dias.
datetime UltimaSesionGuardada()
  {
   if(!FileIsExist(InpArchivoPnl)) return 0;
   int fh = FileOpen(InpArchivoPnl, FILE_READ | FILE_CSV | FILE_ANSI, ',');
   if(fh == INVALID_HANDLE) return 0;
   datetime ult = 0;
   while(!FileIsEnding(fh))
     {
      string d = FileReadString(fh); if(FileIsLineEnding(fh) && d == "") continue;
      while(!FileIsLineEnding(fh) && !FileIsEnding(fh)) FileReadString(fh);
      datetime x = StringToTime(d); if(x > ult) ult = x;
     }
   FileClose(fh);
   return ult;
  }
void GuardarSesiones(datetime sesionActual)
  {
   datetime ult = UltimaSesionGuardada();
   datetime desdeSrv = ult > 0 ? UTCaServidor(NYenUTC(ult, 1700)) : TimeCurrent() - 400 * 86400;
   if(!HistorySelect(desdeSrv - 86400, TimeCurrent() + 60)) return;
   datetime ses[]; double pnl[]; int n = 0;
   for(int i = 0; i < HistoryDealsTotal(); i++)
     {
      ulong tk = HistoryDealGetTicket(i); if(tk == 0) continue;
      if(!EsMagicoNuestro(HistoryDealGetInteger(tk, DEAL_MAGIC))) continue;
      datetime s = SesionDe(UTCaNY(ServidorAUTC((datetime)HistoryDealGetInteger(tk, DEAL_TIME))));
      if(s <= ult || s >= sesionActual) continue;
      double p = HistoryDealGetDouble(tk, DEAL_PROFIT) + HistoryDealGetDouble(tk, DEAL_COMMISSION) + HistoryDealGetDouble(tk, DEAL_SWAP);
      int j = -1; for(int k = 0; k < n; k++) if(ses[k] == s) { j = k; break; }
      if(j < 0) { ArrayResize(ses, n + 1); ArrayResize(pnl, n + 1); ses[n] = s; pnl[n] = 0; j = n; n++; }
      pnl[j] += p;
     }
   datetime inicio = ult;
   if(inicio == 0)
     {
      if(n == 0) return;                                     // sin operaciones todavia: no se empieza la serie
      inicio = ses[0]; for(int k = 1; k < n; k++) if(ses[k] < inicio) inicio = ses[k];
      inicio -= 86400;
     }
   bool nuevo = !FileIsExist(InpArchivoPnl);
   int fh = FileOpen(InpArchivoPnl, FILE_READ | FILE_WRITE | FILE_CSV | FILE_ANSI, ',');
   if(fh == INVALID_HANDLE) return;
   if(nuevo) FileWrite(fh, "sesion", "pnl_frac_sin_escala", "pnl_frac", "escala_vol");
   FileSeek(fh, 0, SEEK_END);
   double bal = AccountInfoDouble(ACCOUNT_BALANCE);
   for(datetime s = inicio + 86400; s < sesionActual; s += 86400)
     {
      if(!EsLaborable(s)) continue;
      double p = 0; for(int k = 0; k < n; k++) if(ses[k] == s) p += pnl[k];
      double f = bal > 0 ? p / bal : 0;
      FileWrite(fh, TimeToString(s, TIME_DATE), DoubleToString(f / g_escalaVol, 8), DoubleToString(f, 8), DoubleToString(g_escalaVol, 3));
     }
   FileClose(fh);
  }
void ActualizarEscalaVol()
  {
   g_escalaVol = 1.0;
   if(!InpControlVol || !FileIsExist(InpArchivoPnl)) return;
   int fh = FileOpen(InpArchivoPnl, FILE_READ | FILE_CSV | FILE_ANSI, ',');
   if(fh == INVALID_HANDLE) return;
   double x[]; int n = 0; bool cab = true;
   while(!FileIsEnding(fh))
     {
      string c0 = FileReadString(fh); if(FileIsEnding(fh) && c0 == "") break;
      string c1 = FileIsLineEnding(fh) ? "" : FileReadString(fh);
      while(!FileIsLineEnding(fh) && !FileIsEnding(fh)) FileReadString(fh);
      if(cab) { cab = false; continue; }
      if(c1 == "") continue;
      ArrayResize(x, n + 1); x[n++] = StringToDouble(c1);
     }
   FileClose(fh);
   if(n < 40) return;
   int a = MathMax(0, n - 60), m = n - a; double med = 0, v = 0;
   for(int i = a; i < n; i++) med += x[i];
   med /= m;
   for(int i = a; i < n; i++) v += (x[i] - med) * (x[i] - med);
   double sd = MathSqrt(v / (m - 1));
   double objetivo = InpVolObjetivo * InpRiesgoPct * (InpModo == MODO_EXAMEN ? InpMultExamen : 1.0) / 0.5 / 100.0;
   if(sd > 0) g_escalaVol = MathMax(0.5, MathMin(2.0, objetivo / sd));
  }

//==================== protecciones ====================
string ClaveGV(string s) { return "CarteraCFD_" + s + "_" + IntegerToString(AccountInfoInteger(ACCOUNT_LOGIN)); }
double BalanceInicial()
  {
   if(InpBalanceInicial > 0) return InpBalanceInicial;
   string k = ClaveGV("BalIni");
   if(!GlobalVariableCheck(k)) GlobalVariableSet(k, AccountInfoDouble(ACCOUNT_BALANCE));
   return GlobalVariableGet(k);
  }
double NivelPerdidaTotal()
  {
   double bi = BalanceInicial();
   if(!InpPerdidaTotalArrastre) return bi * (1 - InpPerdidaTotalMaxPct / 100.0);
   string k = ClaveGV("MaxEq");
   double mx = GlobalVariableCheck(k) ? GlobalVariableGet(k) : bi;
   double eq = AccountInfoDouble(ACCOUNT_EQUITY);
   if(eq > mx) { mx = eq; GlobalVariableSet(k, mx); }
   return MathMin(mx - bi * InpPerdidaTotalMaxPct / 100.0, bi);      // sigue al maximo y se bloquea en el balance inicial
  }
void CerrarTodo(string motivo) { for(int i = 0; i < NTOT; i++) CerrarMagico(i, motivo); }
void Protecciones()
  {
   datetime srvDia = SoloFecha(TimeCurrent());
   if(srvDia != g_diaSrv) { g_diaSrv = srvDia; g_equityInicioDia = MathMax(AccountInfoDouble(ACCOUNT_BALANCE), AccountInfoDouble(ACCOUNT_EQUITY)); g_paradoHoy = false; }
   double eq = AccountInfoDouble(ACCOUNT_EQUITY);
   if(!g_paradoHoy && eq < g_equityInicioDia * (1 - InpPerdidaDiariaMaxPct / 100.0))
     { g_paradoHoy = true; CerrarTodo("perdida_diaria"); Registrar("CARTERA", "", "parada_perdida_diaria", 0, 0, 0, 0, eq - g_equityInicioDia); }
   double nivel = NivelPerdidaTotal();
   if(!g_paradoTotal && eq < nivel)
     { g_paradoTotal = true; CerrarTodo("perdida_total"); Registrar("CARTERA", "", "parada_perdida_total", 0, 0, nivel, 0, eq - BalanceInicial()); }
  }

//==================== configuracion ====================
void Poner(int k, string nombre, bool activa, int tipo, int hIni, int hFin, int lado, string sims, string divisas, int filtro, int nSigma, int noches, double peso, bool utc, double maxSp, double sigmaRef)
  {
   Estrategia e;
   e.nombre = nombre; e.activa = activa; e.tipoDia = tipo; e.hIni = hIni; e.hFin = hFin; e.lado = lado; e.simbolos = sims; e.divisas = divisas;
   e.numero = k; e.filtroSigma = filtro; e.nSigma = nSigma; e.noches = noches; e.peso = peso; e.utc = utc; e.maxSpread = maxSp; e.sigmaRefPb = sigmaRef;
   g_E[k] = e; g_nombre[k] = nombre;
  }
void PonerR(int k, string nombre, bool activa, string sim, bool asiatica, double sigmaRef)
  {
   g_R[k].nombre = nombre; g_R[k].activa = activa; g_R[k].sim = sim; g_R[k].asiatica = asiatica; g_R[k].numero = NV + k; g_R[k].sigmaRefPb = sigmaRef;
   g_R[k].dia = 0; g_R[k].lista = false; g_R[k].hecha = false; g_R[k].H = 0; g_R[k].L = 0; g_R[k].atr = 0; g_R[k].diaEntrada = 0;
   g_nombre[NV + k] = nombre;
  }
void Configurar()
  {
   //   k  nombre                  activa                   tipo hIni  hFin          lado simbolos                                             divisas             filtro nSig noches peso            utc    maxSp            sigmaRef(pb)
   Poner(0, "E2_euro",              InpE2_Euro,              0,  600,  800,          -1, InpSimEURUSD,                                        "EUR,USD",          0, 60, 0, 1.0,            false, 0,               0);
   Poner(1, "E8_oro_viernes",       InpE8_OroViernes,        1, 1600, InpE8_Salida,   1, InpSimOro,                                           "USD",              5, 52, 0, 1.0,            false, 0,               18);
   Poner(2, "E10_plata_vispera",    InpE10_PlataVispera,     2, 1600, 1645,           1, InpSimPlata,                                         "USD",              0, 60, 0, 1.0,            false, 0,               0);
   Poner(3, "E9_yen_fin_mes",       InpE9_YenFinMes,         3,  700,  800,           1, InpSimUSDJPY,                                        "USD,JPY",          0, 60, 0, 1.0,            false, 0,               10);
   Poner(4, "E11_yen_fin_trim",     InpE11_YenFinTrimestre,  4,   30,  200,          -1, InpSimUSDJPY + "," + InpSimEURJPY + "," + InpSimGBPJPY, "JPY,USD,EUR,GBP", 0, 60, 0, 1.0,            false, 0,               10);
   Poner(5, "E12_materias_vispera", InpE12_MateriasVispera,  5, 1355, 1355,           1, InpCestaE12,                                         "USD",              0, 60, 1, 1.0,            false, 0,               0);
   Poner(6, "E13_nikkei_Qmas2",     InpE13_NikkeiTrimestre,  6, 1500, 1600,           1, InpSimNikkei,                                        "JPY,USD",          0, 60, 0, 1.0,            false, 0,               40);
   Poner(7, "E14_ftse_antes_boe",   InpE14_FTSEantesBoE,     7, 1130, 1130,           1, InpSimUK100,                                         "GBP",              0, 60, 2, 1.0,            false, 0,               0);
   Poner(8, "E15_oro_Dmenos2",      InpE15_OroDmenos2,       3,  930, 1000,          -1, InpSimOro,                                           "USD",              0, 60, 0, 1.0,            false, 0,               33);
   Poner(9, "E16_nikkei_Qmenos2",   InpE16_NikkeiQmenos2,    8, 2000, 2100,          -1, InpSimNikkei,                                        "JPY,USD",          0, 60, 0, 1.0,            false, 0,               48);
   Poner(10, "bitcoin_21_23_UTC",   InpBitcoin,              9, 2100, 2300,           1, InpSimBitcoin,                                       "USD",              0, 60, 0, InpPesoDiarias, true,  InpMaxSpreadBTC, 0);
   Poner(11, "C113_oro_asia",       InpC113_OroAsia,        10, 1800,  300,           1, InpSimOro,                                           "USD",              0, 60, 1, InpPesoDiarias, false, 0,               0);
   PonerR(0, "C93_oro_dia_anterior",   InpC93_OroDiaAnterior,   InpSimOro,    false, 80);
   PonerR(1, "C99_oro_rango_asia",     InpC99_OroRangoAsia,     InpSimOro,    true,  90);
   PonerR(2, "C101_nikkei_rango_asia", InpC101_NikkeiRangoAsia, InpSimNikkei, true,  120);
  }

//==================== ciclo ====================
int OnInit()
  {
   if(InpSoloDemo && !EnProbador() && AccountInfoInteger(ACCOUNT_TRADE_MODE) != ACCOUNT_TRADE_MODE_DEMO)
     { Print("Cuenta no DEMO e InpSoloDemo=true: el EA no operara."); return INIT_FAILED; }
   if(AccountInfoInteger(ACCOUNT_MARGIN_MODE) != ACCOUNT_MARGIN_MODE_RETAIL_HEDGING)
      Alert("Cartera CFD: la cuenta NO es de cobertura (hedging). Varias estrategias usan el mismo simbolo a la vez (oro, Nikkei): pide una cuenta hedging o desactiva las que se solapen.");
   Configurar();
   for(int i = 0; i < NV; i++) { g_diaEntrada[i] = -1; g_fechaEntrada[i] = 0; }
   for(int i = 0; i < NTOT; i++) g_sigmaUsada[i] = 0;
   // si el EA se reinicia con posiciones abiertas, se reconocen (respeta su hora de salida en vez de cerrarlas)
   for(int p = PositionsTotal() - 1; p >= 0; p--)
     {
      ulong tk = PositionGetTicket(p); if(tk == 0) continue;
      long mg = PositionGetInteger(POSITION_MAGIC);
      if(!EsMagicoNuestro(mg)) continue;
      int i = (int)(mg - (long)InpMagicoBase);
      datetime tUtc = ServidorAUTC((datetime)PositionGetInteger(POSITION_TIME));
      if(i < NV)
        {
         datetime base = g_E[i].utc ? tUtc : UTCaNY(tUtc);
         MqlDateTime te; TimeToStruct(base, te);
         g_fechaEntrada[i] = SoloFecha(base); g_diaEntrada[i] = te.year * 1000 + te.day_of_year;
        }
      else { int r = i - NV; g_R[r].diaEntrada = SoloFecha(UTCaNY(tUtc)); g_R[r].dia = g_R[r].diaEntrada; g_R[r].lista = true; g_R[r].hecha = true; }
      PrintFormat("Posicion abierta reconocida: %s (%s), entrada UTC %s", g_nombre[i], PositionGetString(POSITION_SYMBOL), TimeToString(tUtc));
     }
   GuardarSesiones(SesionDe(UTCaNY(AhoraUTC())));
   ActualizarEscalaVol();
   PrintFormat("Cartera CFD iniciada%s. Modo %s (riesgo %.2f%%, diarias x%.2f). Servidor invierno UTC%+d. Balance inicial %.2f. Escala de volatilidad %.2f.",
               EnProbador() ? " en el PROBADOR" : "", InpModo == MODO_EXAMEN ? "EXAMEN" : "FONDEADO",
               InpRiesgoPct * (InpModo == MODO_EXAMEN ? InpMultExamen : 1.0), InpPesoDiarias, OffsetInvierno(), BalanceInicial(), g_escalaVol);
   if(!EnProbador() && (!TerminalInfoInteger(TERMINAL_TRADE_ALLOWED) || !MQLInfoInteger(MQL_TRADE_ALLOWED)))
      Alert("Cartera CFD: el TRADING ALGORITMICO esta desactivado. Activalo (boton verde) o el bot no puede operar.");
   EventSetTimer(1);
   return INIT_SUCCEEDED;
  }
void OnDeinit(const int reason) { EventKillTimer(); }

datetime g_sesion = 0;
void OnTimer()
  {
   Protecciones();
   datetime utc = AhoraUTC(), ny = UTCaNY(utc);
   // fin de sesion (17:00 NY): guarda el resultado y recalcula la escala de volatilidad
   datetime ses = SesionDe(ny);
   if(ses != g_sesion)
     {
      if(g_sesion != 0) { GuardarSesiones(ses); ActualizarEscalaVol(); Registrar("CARTERA", "", "nueva_sesion_escala_vol", 0, 0, g_escalaVol, 0, 0); }
      g_sesion = ses;
     }
   for(int i = 0; i < NV; i++)
     {
      Estrategia e = g_E[i];
      datetime base = e.utc ? utc : ny;
      datetime d = SoloFecha(base);
      MqlDateTime t; TimeToStruct(base, t);
      int hm = t.hour * 100 + t.min, idDia = t.year * 1000 + t.day_of_year;
      // --- salida
      if(PosicionesMagico(i) > 0)
        {
         bool cierreCerca = false;
         string ss[]; int nss = StringSplit(e.simbolos, ',', ss);
         for(int j = 0; j < nss; j++)
           {
            StringTrimLeft(ss[j]); StringTrimRight(ss[j]);
            int m = MathMin(MinutosACierre(ss[j], e.noches > 0 ? 20 * 60 : 30), MinutosCierreNikkeiViernes(ss[j], ny));
            if(m >= 0 && m <= InpMinAntesCierre) cierreCerca = true;
           }
         if(cierreCerca) { CerrarMagico(i, "antes_cierre_sesion"); continue; }
         bool tocaSalir;
         if(e.noches > 0) tocaSalir = (LaborablesEntre(g_fechaEntrada[i], d) >= e.noches && hm >= e.hFin) || (d > g_fechaEntrada[i] + (e.noches + 4) * 86400) || g_fechaEntrada[i] == 0;
         else             tocaSalir = (hm >= e.hFin) || (g_diaEntrada[i] != idDia);
         if(tocaSalir)
           {
            if(NoticiaCerca(e.divisas, utc) && hm < e.hFin + 5 && g_diaEntrada[i] == idDia) continue;    // espera fuera de la ventana de noticias (max. 5 min)
            CerrarMagico(i, "hora");
           }
         continue;
        }
      // --- entrada (ventana de 5 minutos desde la hora de entrada)
      if(!e.activa || g_paradoHoy || g_paradoTotal) continue;
      if(hm < e.hIni || hm >= e.hIni + 5 || g_diaEntrada[i] == idDia) continue;
      if(!DiaValido(e, d)) continue;
      g_diaEntrada[i] = idDia;
      if(!EnProbador() && (!TerminalInfoInteger(TERMINAL_TRADE_ALLOWED) || !MQLInfoInteger(MQL_TRADE_ALLOWED)))
        {
         if(g_avisoAlgo != idDia) { g_avisoAlgo = idDia; Registrar(e.nombre, e.simbolos, "aviso_trading_algoritmico_desactivado", 0, 0, 0, 0, 0); }
         continue;
        }
      datetime tSalida = e.noches > 0 ? HoraDia(SumarLaborables(d, e.noches), e.hFin, e.utc) : HoraDia(d, e.hFin, e.utc);
      if(NoticiaCerca(e.divisas, utc) || NoticiaCerca(e.divisas, tSalida)) { Registrar(e.nombre, e.simbolos, "sin_entrada_noticia", 0, 0, 0, 0, 0); continue; }
      g_fechaEntrada[i] = d;
      Entrar(e, ny, (int)((tSalida - utc) / 60));
     }
   for(int r = 0; r < NR; r++) GestionarRuptura(g_R[r], utc, ny);
  }

void OnTradeTransaction(const MqlTradeTransaction &tr, const MqlTradeRequest &rq, const MqlTradeResult &rs)
  {
   if(tr.type != TRADE_TRANSACTION_DEAL_ADD || !HistoryDealSelect(tr.deal)) return;
   long mg = HistoryDealGetInteger(tr.deal, DEAL_MAGIC);
   if(!EsMagicoNuestro(mg)) return;
   long razon = HistoryDealGetInteger(tr.deal, DEAL_REASON);
   if(razon != DEAL_REASON_SL && razon != DEAL_REASON_TP && razon != DEAL_REASON_SO) return;
   int i = (int)(mg - (long)InpMagicoBase);
   string ev = razon == DEAL_REASON_TP ? "cierre_objetivo" : (razon == DEAL_REASON_SO ? "aviso_stop_out_del_broker" : (i < NV ? "stop_catastrofe" : "cierre_stop_ruptura"));
   Registrar(g_nombre[i], HistoryDealGetString(tr.deal, DEAL_SYMBOL), ev, HistoryDealGetDouble(tr.deal, DEAL_VOLUME), 0,
             HistoryDealGetDouble(tr.deal, DEAL_PRICE), 0, HistoryDealGetDouble(tr.deal, DEAL_PROFIT) + HistoryDealGetDouble(tr.deal, DEAL_COMMISSION) + HistoryDealGetDouble(tr.deal, DEAL_SWAP));
  }
