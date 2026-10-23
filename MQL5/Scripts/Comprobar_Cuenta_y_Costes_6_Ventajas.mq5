//+------------------------------------------------------------------+
//| Comprobar_Cuenta_y_Costes_6_Ventajas.mq5                       |
//| Comprueba la cuenta (simbolos, contrato, apalancamiento) y mide   |
//| el spread real a las horas exactas de las cinco estrategias:      |
//|   E1/E2  EURUSD  todos los dias       06:00 -> 08:00 NY            |
//|   E9     USDJPY  antepenultimo dia habil del mes 07:00 -> 08:00 NY |
//|   E8     XAUUSD  viernes              16:00 -> 16:55 NY            |
//|   E10    XAGUSD  vispera de festivo NYSE 16:00 -> 16:55 NY          |
//|          (y todos los viernes, informativo)                        |
//|   E11    USDJPY,EURJPY,GBPJPY ultimo dia del trimestre 00:30->02:00|
//|   E12    materias primas: 13:55 dia antes de vispera -> 13:55 vispera|
//|   F1b    gas     jueves 09:00 -> 10:00 NY (informativo, no certif.)|
//| Usa el ultimo tick de los 60 s anteriores (historico de ticks).   |
//| NO abre ninguna operacion.                                         |
//| Resultado: diario "Expertos" y MQL5/Files/costes_6_ventajas.csv |
//| Coste ida y vuelta (pb) = spread entrada/2 + spread salida/2,      |
//| en puntos basicos del precio, SIN comision (sumala aparte).        |
//+------------------------------------------------------------------+
#property script_show_inputs
#property strict

enum ENUM_DST_SERVIDOR
  {
   DST_EUROPA = 0,   // Europa: ultimo domingo de marzo -> ultimo domingo de octubre (MetaQuotes-Demo, FTMO)
   DST_EEUU   = 1,   // EEUU: 2.o domingo de marzo -> 1.er domingo de noviembre ("cierre de Nueva York")
   DST_NINGUNO = 2   // el servidor no cambia de hora
  };

input string InpEUR   = "EURUSD";   // nombre exacto en esta cuenta
input string InpJPY   = "USDJPY";
input string InpOro   = "XAUUSD";
input string InpPlata = "XAGUSD";
input string InpGas   = "NATGAS";   // p. ej. NATGAS, NGAS, XNGUSD... (mira la Observacion de mercado)
input string InpEURJPY = "EURJPY";
input string InpGBPJPY = "GBPJPY";
input string InpCestaE12 = "USOIL.cash,HEATOIL.c,NATGAS.cash,CORN.c,SOYBEAN.c,WHEAT.c"; // las que existan en la cuenta
input int    InpDias  = 400;        // dias naturales hacia atras (cuanto mas, mas visperas de festivo)
input ENUM_DST_SERVIDOR InpDSTServidor = DST_EUROPA; // cambio de hora del servidor

// Festivos de la NYSE (para las visperas de E10). Ampliar cada anio.
string FESTIVOS = "2024.01.01,2024.01.15,2024.02.19,2024.03.29,2024.05.27,2024.06.19,2024.07.04,2024.09.02,2024.11.28,2024.12.25,"
                  "2025.01.01,2025.01.09,2025.01.20,2025.02.17,2025.04.18,2025.05.26,2025.06.19,2025.07.04,2025.09.01,2025.11.27,2025.12.25,"
                  "2026.01.01,2026.01.19,2026.02.16,2026.04.03,2026.05.25,2026.06.19,2026.07.03,2026.09.07,2026.11.26,2026.12.25";

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
datetime NuevaYork(datetime dia, int h, int m)          // hora local de NY de ese dia (00:00 UTC), en UTC
  {
   datetime t = dia + (h + 5) * 3600 + m * 60;
   if(VeranoEEUU(t - 3600)) t -= 3600;
   return t;
  }

bool EsFestivo(datetime dia) { return StringFind(FESTIVOS, TimeToString(dia, TIME_DATE)) >= 0; }
bool EsHabil(datetime dia) { MqlDateTime x; TimeToStruct(dia, x); return x.day_of_week >= 1 && x.day_of_week <= 5; }
bool EsVispera(datetime dia)                           // ultimo dia habil antes de un festivo NYSE
  {
   if(!EsHabil(dia) || EsFestivo(dia)) return false;
   datetime s = dia + 86400;
   while(!EsHabil(s)) s += 86400;
   return EsFestivo(s);
  }
bool EsQ0(datetime dia)                                 // ultimo dia laborable de mar/jun/sep/dic
  {
   if(!EsHabil(dia)) return false;
   MqlDateTime x; TimeToStruct(dia, x);
   if(x.mon % 3 != 0) return false;
   for(datetime s = dia + 86400; ; s += 86400) { MqlDateTime y; TimeToStruct(s, y); if(y.mon != x.mon) break; if(EsHabil(s)) return false; }
   return true;
  }
bool EsDiaAntesDeVispera(datetime dia)                  // y la vispera es el dia siguiente
  {
   if(!EsHabil(dia) || EsFestivo(dia)) return false;
   datetime s = dia + 86400; return EsHabil(s) && EsVispera(s);
  }
bool EsDmenos2(datetime dia)                           // antepenultimo dia laborable (lun-vie) del mes
  {
   if(!EsHabil(dia)) return false;
   MqlDateTime x; TimeToStruct(dia, x);
   int quedan = 0;
   for(datetime s = dia + 86400; ; s += 86400)
     {
      MqlDateTime y; TimeToStruct(s, y);
      if(y.mon != x.mon) break;
      if(EsHabil(s)) quedan++;
     }
   return quedan == 2;
  }

bool SpreadPb(string sim, datetime T_srv, double &pb)
  {
   MqlTick ticks[];
   int n = CopyTicksRange(sim, ticks, COPY_TICKS_INFO, (ulong)(T_srv - 60) * 1000, (ulong)T_srv * 1000 - 1);
   if(n <= 0) return false;
   double a = ticks[n - 1].ask, b = ticks[n - 1].bid;
   if(a <= 0 || b <= 0) return false;
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

void Cuenta(string s)
  {
   if(!SymbolSelect(s, true)) { Print("NO ENCONTRADO: ", s, " -> pon el nombre exacto (Observacion de mercado, clic derecho > Simbolos)."); return; }
   double contrato = SymbolInfoDouble(s, SYMBOL_TRADE_CONTRACT_SIZE);
   double precio = SymbolInfoDouble(s, SYMBOL_BID);
   double margen = 0;
   bool okm = OrderCalcMargin(ORDER_TYPE_BUY, s, 1.0, SymbolInfoDouble(s, SYMBOL_ASK), margen);
   double nocional = 0;
   string divisa = SymbolInfoString(s, SYMBOL_CURRENCY_PROFIT);
   // nocional de 1 lote en la divisa de la cuenta (aproximado con el valor del tick)
   double tv = SymbolInfoDouble(s, SYMBOL_TRADE_TICK_VALUE), ts = SymbolInfoDouble(s, SYMBOL_TRADE_TICK_SIZE);
   if(ts > 0) nocional = precio / ts * tv;
   double apal = (okm && margen > 0) ? nocional / margen : 0;
   PrintFormat("%s: contrato %.2f | precio %.5f | nocional 1 lote ~ %.0f %s | margen 1 lote %.2f %s | APALANCAMIENTO EFECTIVO ~ 1:%.0f | lote min %.2f paso %.2f",
               s, contrato, precio, nocional, AccountInfoString(ACCOUNT_CURRENCY), margen, AccountInfoString(ACCOUNT_CURRENCY), apal,
               SymbolInfoDouble(s, SYMBOL_VOLUME_MIN), SymbolInfoDouble(s, SYMBOL_VOLUME_STEP));
  }

// tipo: 0 todos los dias habiles, 1 D-2, 2 viernes, 3 vispera de festivo, 4 jueves, 5 Q0, 6 dia antes de vispera (sale al dia siguiente)
void Medir(string s, int tipo, int h0, int m0, int h1, int m1, string etiqueta, double refBruto, int fh, datetime hoy)
  {
   if(!SymbolSelect(s, true)) return;
   double ent[], sal[], tot[];
   for(int k = InpDias; k >= 1; k--)
     {
      datetime dia = hoy - k * 86400;
      MqlDateTime x; TimeToStruct(dia, x);
      if(!EsHabil(dia)) continue;
      if(tipo == 1 && !EsDmenos2(dia)) continue;
      if(tipo == 2 && x.day_of_week != 5) continue;
      if(tipo == 3 && !EsVispera(dia)) continue;
      if(tipo == 4 && x.day_of_week != 4) continue;
      if(tipo == 5 && !EsQ0(dia)) continue;
      if(tipo == 6 && !EsDiaAntesDeVispera(dia)) continue;
      datetime diaSal = (tipo == 6) ? dia + 86400 : dia;
      double a, b;
      if(!SpreadPb(s, AServidor(NuevaYork(dia, h0, m0)), a) || !SpreadPb(s, AServidor(NuevaYork(diaSal, h1, m1)), b)) continue;
      int n = ArraySize(ent);
      ArrayResize(ent, n + 1); ArrayResize(sal, n + 1); ArrayResize(tot, n + 1);
      ent[n] = a; sal[n] = b; tot[n] = a / 2 + b / 2;
      FileWrite(fh, s, etiqueta, TimeToString(dia, TIME_DATE), DoubleToString(a, 3), DoubleToString(b, 3), DoubleToString(a / 2 + b / 2, 3));
     }
   int n = ArraySize(tot);
   if(n == 0) { Print(s, " ", etiqueta, ": sin ticks (abre su grafico M1 y desplazate atras para descargar historico) o sin dias de ese tipo."); return; }
   double c = Percentil(tot, 0.5);
   PrintFormat("%s %s (%d dias): spread entrada mediana %.2f pb (p90 %.2f) | salida mediana %.2f pb (p90 %.2f) | COSTE mediana %.2f pb + comision | ventaja bruta historica ~ %.1f pb -> %s",
               s, etiqueta, n, Percentil(ent, 0.5), Percentil(ent, 0.9), Percentil(sal, 0.5), Percentil(sal, 0.9), c, refBruto,
               (c <= refBruto / 3 ? "OK (coste <= 1/3)" : (c <= refBruto / 2 ? "JUSTO" : "CARO")));
  }

void OnStart()
  {
   datetime ahora = TimeGMT();
   int off = (int)MathRound((double)(TimeTradeServer() - ahora) / 3600.0);
   g_offInvierno = off - (VeranoServidor(ahora) ? 1 : 0);
   PrintFormat("Cuenta %I64d (%s) | apalancamiento de la cuenta 1:%d | divisa %s | servidor UTC%+d (invierno UTC%+d)",
               AccountInfoInteger(ACCOUNT_LOGIN), AccountInfoString(ACCOUNT_SERVER), (int)AccountInfoInteger(ACCOUNT_LEVERAGE),
               AccountInfoString(ACCOUNT_CURRENCY), off, g_offInvierno);
   Print("=== Simbolos y apalancamiento ===");
   Cuenta(InpEUR); Cuenta(InpJPY); Cuenta(InpOro); Cuenta(InpPlata); Cuenta(InpGas);
   Print("Nota: el oro necesita de media ~5,4 veces el capital (vol. de 1 h muy baja). Si el apalancamiento efectivo del oro es menor, el EA limitara el tamanio.");
   int fh = FileOpen("costes_6_ventajas.csv", FILE_WRITE | FILE_CSV | FILE_ANSI, ',');
   FileWrite(fh, "simbolo", "regla", "dia", "pb_entrada", "pb_salida", "coste_ida_vuelta_pb");
   datetime hoy = ahora - (ahora % 86400);
   Print("=== Costes a las horas de cada estrategia (sin comision) ===");
   Medir(InpEUR,   0, 6, 0, 8, 0,   "E1 diario 06:00->08:00 NY",            1.7,  fh, hoy);
   Medir(InpJPY,   1, 7, 0, 8, 0,   "E9 D-2 07:00->08:00 NY",               3.4,  fh, hoy);
   Medir(InpOro,   2, 16, 0, 16, 55, "E8 viernes 16:00->16:55 NY",           3.3,  fh, hoy);
   Medir(InpPlata, 3, 16, 0, 16, 55, "E10 vispera festivo 16:00->16:55 NY",  9.9,  fh, hoy);
   Medir(InpPlata, 2, 16, 0, 16, 55, "plata viernes (informativo)",          6.3,  fh, hoy);
   Medir(InpJPY,   5, 0, 30, 2, 0,   "E11 Q0 00:30->02:00 NY (corto)",       4.4,  fh, hoy);
   Medir(InpEURJPY, 5, 0, 30, 2, 0,  "E11 Q0 00:30->02:00 NY (corto)",       4.4,  fh, hoy);
   Medir(InpGBPJPY, 5, 0, 30, 2, 0,  "E11 Q0 00:30->02:00 NY (corto)",       4.4,  fh, hoy);
   string ces[]; int nc = StringSplit(InpCestaE12, ',', ces);
   for(int i = 0; i < nc; i++) { string c = ces[i]; StringTrimLeft(c); StringTrimRight(c); Cuenta(c); Medir(c, 6, 13, 55, 13, 55, "E12 13:55 dia antes de vispera -> 13:55 vispera", 12.0, fh, hoy); }
   Medir(InpGas,   4, 9, 0, 10, 0,   "F1b jueves 09:00->10:00 NY (informativo)", 12.0, fh, hoy);
   FileClose(fh);
   Print("Envia el diario 'Expertos' y MQL5/Files/costes_6_ventajas.csv. Recuerda sumar la comision de la cuenta (FTMO divisas: 5 $ por lote ida y vuelta; metales: consulta).");
  }
