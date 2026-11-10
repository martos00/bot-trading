//+------------------------------------------------------------------+
//| Medir_Costes_Cartera.mq5                                          |
//| Mide en la cuenta (demo de FTMO u otra firma de CFD) el spread    |
//| real a las horas de CADA estrategia de la cartera, con el         |
//| historico de ticks de los ultimos InpDias dias. NO abre ninguna   |
//| operacion.                                                        |
//| Para cada hora usa el ultimo tick de los 60 s anteriores.         |
//| Coste de ida y vuelta (pb) = spread entrada/2 + spread salida/2   |
//| (sin comision: la comision hay que sumarla aparte).               |
//| Resultados:                                                       |
//|   - pestaña "Expertos": resumen por estrategia                    |
//|   - MQL5/Files/costes_cartera_resumen.csv  (lo que hay que mandar)|
//|   - MQL5/Files/costes_cartera_detalle.csv  (dia a dia)            |
//|   - MQL5/Files/costes_cartera_simbolos.csv (datos de cada simbolo)|
//+------------------------------------------------------------------+
#property script_show_inputs
#property strict

enum ENUM_DST_SERVIDOR
  {
   DST_EUROPA  = 0,  // Europa: ultimo domingo de marzo -> ultimo domingo de octubre (FTMO, MetaQuotes)
   DST_EEUU    = 1,  // EEUU: 2.o domingo de marzo -> 1.er domingo de noviembre
   DST_NINGUNO = 2   // el servidor no cambia de hora
  };

input group "Simbolos (nombre EXACTO en esta cuenta; vacio = no medir)"
input string InpOro     = "XAUUSD";
input string InpPlata   = "XAGUSD";
input string InpUSDJPY  = "USDJPY";
input string InpEURJPY  = "EURJPY";
input string InpGBPJPY  = "GBPJPY";
input string InpEURUSD  = "EURUSD";
input string InpNikkei  = "JP225.cash";   // nombre FTMO del Nikkei
input string InpBitcoin = "BTCUSD";
input group "Ajustes"
input int    InpDias    = 180;            // dias naturales hacia atras (si faltan ticks, abre el grafico M1 del simbolo y desplazate atras)
input ENUM_DST_SERVIDOR InpDSTServidor = DST_EUROPA;

// ---------------- horas ----------------
datetime Domingo(int anio, int mes, int n)            // n-esimo domingo del mes, 00:00 UTC
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
bool VeranoEuropa(datetime utc)
  {
   MqlDateTime x; TimeToStruct(utc, x);
   return utc >= Domingo(x.year, 4, 1) - 7 * 86400 + 3600 && utc < Domingo(x.year, 11, 1) - 7 * 86400 + 3600;
  }
bool VeranoServidor(datetime utc)
  {
   if(InpDSTServidor == DST_NINGUNO) return false;
   if(InpDSTServidor == DST_EEUU) return VeranoEEUU(utc);
   return VeranoEuropa(utc);
  }
int g_offInvierno;
datetime AServidor(datetime utc) { return utc + (g_offInvierno + (VeranoServidor(utc) ? 1 : 0)) * 3600; }
datetime NuevaYork(datetime dia, int h, int m)         // hora local de NY de ese dia (dia = 00:00 UTC), devuelta en UTC
  {
   datetime t = dia + (h + 5) * 3600 + m * 60;
   if(VeranoEEUU(t - 3600)) t -= 3600;
   return t;
  }

// spread (pb) del ultimo tick de los 60 s anteriores a T (hora del servidor)
bool SpreadPb(string sim, datetime T_srv, double &pb)
  {
   MqlTick ticks[];
   int n = CopyTicksRange(sim, ticks, COPY_TICKS_INFO, (ulong)(T_srv - 60) * 1000, (ulong)T_srv * 1000 - 1);
   if(n <= 0) return false;
   double a = ticks[n - 1].ask, b = ticks[n - 1].bid;
   if(a <= 0 || b <= 0 || a < b) return false;
   pb = (a - b) / ((a + b) / 2) * 1e4;
   return true;
  }
double Percentil(double &v[], double p)
  {
   int n = ArraySize(v);
   if(n == 0) return -1;
   double c[]; ArrayCopy(c, v); ArraySort(c);
   return c[(int)MathFloor(p * (n - 1))];
  }
bool Laborable(int dow) { return dow >= 1 && dow <= 5; }

int g_fr, g_fd;

// tipoDia: 0 = lunes-viernes, 1 = solo viernes, 2 = domingo-jueves (C113)
// diasSalida: la salida es N dias naturales despues de la entrada
void Medir(string nombre, string sim, int tipoDia, int h0, int m0, int h1, int m1, int diasSalida, datetime hoy)
  {
   if(sim == "") return;
   if(!SymbolSelect(sim, true)) { Print("Simbolo no encontrado: ", sim, " (", nombre, "). Pon el nombre exacto de esta cuenta."); return; }
   double ent[], sal[], tot[];
   int intentos = 0;
   for(int k = InpDias; k >= 1; k--)
     {
      datetime dia = hoy - k * 86400;
      MqlDateTime x; TimeToStruct(dia, x);
      bool ok = (tipoDia == 0 && Laborable(x.day_of_week)) || (tipoDia == 1 && x.day_of_week == 5) ||
                (tipoDia == 2 && x.day_of_week != 5 && x.day_of_week != 6);
      if(!ok) continue;
      intentos++;
      double a, b;
      if(!SpreadPb(sim, AServidor(NuevaYork(dia, h0, m0)), a)) continue;
      if(!SpreadPb(sim, AServidor(NuevaYork(dia + diasSalida * 86400, h1, m1)), b)) continue;
      int n = ArraySize(ent);
      ArrayResize(ent, n + 1); ArrayResize(sal, n + 1); ArrayResize(tot, n + 1);
      ent[n] = a; sal[n] = b; tot[n] = a / 2 + b / 2;
      FileWrite(g_fd, nombre, sim, TimeToString(dia, TIME_DATE), DoubleToString(a, 3), DoubleToString(b, 3), DoubleToString(a / 2 + b / 2, 3));
     }
   int n = ArraySize(tot);
   string franja = StringFormat("%02d:%02d -> %02d:%02d%s NY", h0, m0, h1, m1, diasSalida > 0 ? " (dia sig.)" : "");
   if(n == 0)
     {
      PrintFormat("%-26s %-12s %s: SIN DATOS (%d dias probados). Mercado cerrado a esa hora o faltan ticks.", nombre, sim, franja, intentos);
      FileWrite(g_fr, nombre, sim, franja, intentos, 0, "", "", "", "", "", "");
      return;
     }
   PrintFormat("%-26s %-12s %s | dias %d/%d | entrada med %.2f p90 %.2f | salida med %.2f p90 %.2f | IDA Y VUELTA med %.2f p75 %.2f pb",
               nombre, sim, franja, n, intentos, Percentil(ent, 0.5), Percentil(ent, 0.9), Percentil(sal, 0.5), Percentil(sal, 0.9),
               Percentil(tot, 0.5), Percentil(tot, 0.75));
   FileWrite(g_fr, nombre, sim, franja, intentos, n, DoubleToString(Percentil(ent, 0.5), 3), DoubleToString(Percentil(ent, 0.9), 3),
             DoubleToString(Percentil(sal, 0.5), 3), DoubleToString(Percentil(sal, 0.9), 3), DoubleToString(Percentil(tot, 0.5), 3),
             DoubleToString(Percentil(tot, 0.75), 3));
  }

// hora (NY) del ultimo tick de cada viernes: para saber hasta cuando se puede operar el viernes
void UltimoTickViernes(string sim, datetime hoy)
  {
   if(sim == "" || !SymbolSelect(sim, true)) return;
   int mins[];
   for(int k = InpDias; k >= 1; k--)
     {
      datetime dia = hoy - k * 86400;
      MqlDateTime x; TimeToStruct(dia, x);
      if(x.day_of_week != 5) continue;
      datetime t0 = AServidor(NuevaYork(dia, 15, 0)), t1 = AServidor(NuevaYork(dia, 18, 0));
      MqlTick ticks[];
      int n = CopyTicksRange(sim, ticks, COPY_TICKS_INFO, (ulong)t0 * 1000, (ulong)t1 * 1000);
      if(n <= 0) continue;
      int seg = (int)((datetime)(ticks[n - 1].time) - t0);      // segundos desde las 15:00 NY
      int m = ArraySize(mins); ArrayResize(mins, m + 1); mins[m] = seg;
     }
   int m = ArraySize(mins);
   if(m == 0) { Print(sim, ": sin ticks de viernes."); return; }
   ArraySort(mins);
   int med = mins[m / 2];
   PrintFormat("%-12s ultimo tick del viernes (mediana de %d viernes): %02d:%02d:%02d NY", sim, m, 15 + med / 3600, (med % 3600) / 60, med % 60);
   FileWrite(g_fr, "ULTIMO_TICK_VIERNES", sim, StringFormat("%02d:%02d:%02d NY", 15 + med / 3600, (med % 3600) / 60, med % 60), m, m, "", "", "", "", "", "");
  }

void DatosSimbolo(int fh, string sim)
  {
   if(sim == "" || !SymbolSelect(sim, true)) return;
   FileWrite(fh, sim, SymbolInfoDouble(sim, SYMBOL_TRADE_CONTRACT_SIZE), SymbolInfoDouble(sim, SYMBOL_VOLUME_MIN),
             SymbolInfoDouble(sim, SYMBOL_VOLUME_STEP), SymbolInfoDouble(sim, SYMBOL_VOLUME_MAX), SymbolInfoDouble(sim, SYMBOL_TRADE_TICK_SIZE),
             SymbolInfoDouble(sim, SYMBOL_TRADE_TICK_VALUE), SymbolInfoInteger(sim, SYMBOL_DIGITS), SymbolInfoString(sim, SYMBOL_CURRENCY_PROFIT),
             SymbolInfoDouble(sim, SYMBOL_SWAP_LONG), SymbolInfoDouble(sim, SYMBOL_SWAP_SHORT));
  }

void OnStart()
  {
   datetime ahora = TimeGMT();
   int off = (int)MathRound((double)(TimeTradeServer() - ahora) / 3600.0);
   g_offInvierno = off - (VeranoServidor(ahora) ? 1 : 0);
   PrintFormat("Servidor: UTC%+d ahora (invierno UTC%+d). Cuenta: %s (%s)", off, g_offInvierno, AccountInfoString(ACCOUNT_COMPANY), AccountInfoString(ACCOUNT_SERVER));
   datetime hoy = ahora - (ahora % 86400);

   g_fr = FileOpen("costes_cartera_resumen.csv", FILE_WRITE | FILE_CSV | FILE_ANSI, ',');
   g_fd = FileOpen("costes_cartera_detalle.csv", FILE_WRITE | FILE_CSV | FILE_ANSI, ',');
   if(g_fr == INVALID_HANDLE || g_fd == INVALID_HANDLE) { Print("No se pudieron crear los CSV en MQL5/Files."); return; }
   FileWrite(g_fr, "estrategia", "simbolo", "franja", "dias_probados", "dias_con_datos", "entrada_med_pb", "entrada_p90_pb", "salida_med_pb", "salida_p90_pb", "ida_vuelta_med_pb", "ida_vuelta_p75_pb");
   FileWrite(g_fd, "estrategia", "simbolo", "dia", "pb_entrada", "pb_salida", "ida_vuelta_pb");

   // --- estrategias de franja ---
   Medir("E8 oro viernes",           InpOro,    1, 16,  0, 16, 45, 0, hoy);
   Medir("E8 oro viernes (16:55)",   InpOro,    1, 16,  0, 16, 55, 0, hoy);
   Medir("Plata viernes (16:45)",    InpPlata,  1, 16, 30, 16, 45, 0, hoy);
   Medir("Plata viernes (16:57)",    InpPlata,  1, 16, 30, 16, 57, 0, hoy);
   Medir("E10 plata vispera (proxy)",InpPlata,  0, 16,  0, 16, 45, 0, hoy);   // todos los laborables como aproximacion
   Medir("E15 oro D-2 (proxy)",      InpOro,    0,  9, 30, 10,  0, 0, hoy);
   Medir("E9 yen D-2 (proxy)",       InpUSDJPY, 0,  7,  0,  8,  0, 0, hoy);
   Medir("E11 yen Q0 (proxy)",       InpUSDJPY, 0,  0, 30,  2,  0, 0, hoy);
   Medir("E11 yen Q0 (proxy)",       InpEURJPY, 0,  0, 30,  2,  0, 0, hoy);
   Medir("E11 yen Q0 (proxy)",       InpGBPJPY, 0,  0, 30,  2,  0, 0, hoy);
   Medir("E13 Nikkei Q+2 (proxy)",   InpNikkei, 0, 15,  0, 16,  0, 0, hoy);
   Medir("E16 Nikkei Q-2 (proxy)",   InpNikkei, 0, 20,  0, 21,  0, 0, hoy);
   Medir("E2 euro manana",           InpEURUSD, 0,  6,  0,  8,  0, 0, hoy);
   // --- C113 oro en Asia: entrada justo tras la reapertura ---
   Medir("C113 oro Asia 18:01",      InpOro,    2, 18,  1,  3,  0, 1, hoy);
   Medir("C113 oro Asia 18:02",      InpOro,    2, 18,  2,  3,  0, 1, hoy);
   Medir("C113 oro Asia 18:05",      InpOro,    2, 18,  5,  3,  0, 1, hoy);
   Medir("C113 oro Asia 18:15",      InpOro,    2, 18, 15,  3,  0, 1, hoy);
   // --- rupturas diarias: entrada a distintas horas de su ventana, salida 16:45 ---
   for(int h = 3; h <= 10; h++) Medir(StringFormat("C99 oro rango asia %02d:00", h), InpOro, 0, h, 0, 16, 45, 0, hoy);
   for(int h = 8; h <= 14; h++) Medir(StringFormat("C93 oro dia anterior %02d:00", h), InpOro, 0, h, 0, 16, 45, 0, hoy);
   for(int h = 3; h <= 10; h++) Medir(StringFormat("C101 Nikkei rango asia %02d:00", h), InpNikkei, 0, h, 0, 16, 45, 0, hoy);
   // --- bitcoin 21-23 UTC (en NY: 16-18 en invierno, 17-19 en verano; se mide en invierno y en verano por separado) ---
   Medir("Bitcoin 16:00-18:00 NY",   InpBitcoin, 0, 16, 0, 18, 0, 0, hoy);
   Medir("Bitcoin 17:00-19:00 NY",   InpBitcoin, 0, 17, 0, 19, 0, 0, hoy);

   // --- hasta cuando hay precio los viernes ---
   UltimoTickViernes(InpOro, hoy); UltimoTickViernes(InpPlata, hoy); UltimoTickViernes(InpNikkei, hoy); UltimoTickViernes(InpUSDJPY, hoy);
   FileClose(g_fr); FileClose(g_fd);

   int fs = FileOpen("costes_cartera_simbolos.csv", FILE_WRITE | FILE_CSV | FILE_ANSI, ',');
   FileWrite(fs, "simbolo", "tamano_contrato", "lote_min", "paso_lote", "lote_max", "tick", "valor_tick", "decimales", "divisa_beneficio", "swap_largo", "swap_corto");
   DatosSimbolo(fs, InpOro); DatosSimbolo(fs, InpPlata); DatosSimbolo(fs, InpUSDJPY); DatosSimbolo(fs, InpEURJPY); DatosSimbolo(fs, InpGBPJPY);
   DatosSimbolo(fs, InpEURUSD); DatosSimbolo(fs, InpNikkei); DatosSimbolo(fs, InpBitcoin);
   FileClose(fs);
   Print("Listo. Manda los 3 CSV de MQL5/Files (costes_cartera_resumen.csv, costes_cartera_detalle.csv, costes_cartera_simbolos.csv) y la COMISION por lote de cada simbolo de tu firma.");
  }
