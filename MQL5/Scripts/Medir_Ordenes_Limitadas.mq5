//+------------------------------------------------------------------+
//| Medir_Ordenes_Limitadas.mq5                                       |
//| Con el historico de ticks de la cuenta, simula para cada entrada  |
//| del EA de CFD una orden limitada al precio medio que espera       |
//| InpSegundos y, si no se llena, entra a mercado. Mide cuanto se    |
//| ahorra (o se pierde) frente a entrar a mercado. NO opera.         |
//| Resultado: pestaña Expertos y MQL5/Files/ordenes_limitadas.csv    |
//| Limite: supone que la orden se llena en cuanto el precio la toca  |
//| (sin cola); en real puede llenarse algo menos.                    |
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
input string InpUSDJPY  = "USDJPY";
input string InpEURJPY  = "EURJPY";
input string InpGBPJPY  = "GBPJPY";
input string InpNikkei  = "JPCJPY.c";     // Upcomers; FTMO "JP225.cash"
input string InpBitcoin = "BTCUSD.nx";    // Upcomers; FTMO "BTCUSD"
input group "Ajustes"
input int    InpSegundos = 20;           // segundos de espera de la orden limitada (como InpSegundosLimitada del EA)
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

double Percentil(double &v[], double p)
  {
   int n = ArraySize(v);
   if(n == 0) return -1;
   double c[]; ArrayCopy(c, v); ArraySort(c);
   return c[(int)MathFloor(p * (n - 1))];
  }
bool Laborable(int dow) { return dow >= 1 && dow <= 5; }


// Simula una orden limitada al precio medio a la hora T: se llena si en InpSegundos el precio la toca (compra: ask <= limite;
// venta: bid >= limite); si no, se entra a mercado al final de la espera. Ahorro (pb) = frente a entrar a mercado en T
// (positivo = mejor). Incluye el coste de esperar cuando no se llena (el precio puede irse en contra).
bool Simular(string sim, int lado, datetime T_srv, double &ahorro, bool &lleno)
  {
   MqlTick a[];
   int n = CopyTicksRange(sim, a, COPY_TICKS_INFO, (ulong)(T_srv - 60) * 1000, (ulong)T_srv * 1000 - 1);
   if(n <= 0) return false;
   double bid0 = a[n - 1].bid, ask0 = a[n - 1].ask, tick = SymbolInfoDouble(sim, SYMBOL_TRADE_TICK_SIZE);
   if(bid0 <= 0 || ask0 < bid0 || tick <= 0) return false;
   double mid = (bid0 + ask0) / 2, ref = lado > 0 ? ask0 : bid0;
   double px = lado > 0 ? MathFloor(mid / tick + 1e-9) * tick : MathCeil(mid / tick - 1e-9) * tick;
   lleno = false; ahorro = 0;
   if((lado > 0 && px >= ask0) || (lado < 0 && px <= bid0)) return true;     // spread de 1 tick: igual que a mercado
   MqlTick b[];
   int m = CopyTicksRange(sim, b, COPY_TICKS_INFO, (ulong)T_srv * 1000, (ulong)(T_srv + InpSegundos) * 1000);
   double fin = ref;
   for(int i = 0; i < m; i++)
     {
      if(lado > 0 && b[i].ask > 0 && b[i].ask <= px) { lleno = true; break; }
      if(lado < 0 && b[i].bid > 0 && b[i].bid >= px) { lleno = true; break; }
      fin = lado > 0 ? b[i].ask : b[i].bid;
     }
   double entrada = lleno ? px : fin;
   ahorro = lado * (ref - entrada) / mid * 1e4;
   return true;
  }
int g_fr;
// tipoDia: 0 = lunes-viernes, 1 = solo viernes
void Medir(string nombre, string sim, int lado, int tipoDia, int h, int mi, datetime hoy)
  {
   if(sim == "") return;
   if(!SymbolSelect(sim, true)) { Print("Simbolo no encontrado: ", sim); return; }
   double v[]; int nl = 0, n = 0;
   for(int k = InpDias; k >= 1; k--)
     {
      datetime dia = hoy - k * 86400;
      MqlDateTime x; TimeToStruct(dia, x);
      if(!((tipoDia == 0 && Laborable(x.day_of_week)) || (tipoDia == 1 && x.day_of_week == 5))) continue;
      double s; bool ll;
      if(!Simular(sim, lado, AServidor(NuevaYork(dia, h, mi)), s, ll)) continue;
      ArrayResize(v, n + 1); v[n++] = s; if(ll) nl++;
     }
   if(n < 5) { PrintFormat("%-34s %-10s SIN DATOS (%d dias)", nombre, sim, n); FileWrite(g_fr, nombre, sim, lado > 0 ? "compra" : "venta", n, "", "", "", ""); return; }
   double me = 0, sd = 0; for(int i = 0; i < n; i++) me += v[i]; me /= n;
   for(int i = 0; i < n; i++) sd += (v[i] - me) * (v[i] - me); sd = MathSqrt(sd / MathMax(1, n - 1));
   double t = sd > 0 ? me / sd * MathSqrt(n) : 0;
   PrintFormat("%-34s %-10s %s | dias %3d | se llena %3.0f %% | ahorro medio %+.3f pb (t %.2f) | mediana %+.3f pb", nombre, sim, lado > 0 ? "compra" : "venta ",
               n, 100.0 * nl / n, me, t, Percentil(v, 0.5));
   FileWrite(g_fr, nombre, sim, lado > 0 ? "compra" : "venta", n, DoubleToString(100.0 * nl / n, 1), DoubleToString(me, 3), DoubleToString(t, 2), DoubleToString(Percentil(v, 0.5), 3));
  }
void OnStart()
  {
   datetime ahora = TimeGMT();
   int off = (int)MathRound((double)(TimeTradeServer() - ahora) / 3600.0);
   g_offInvierno = off - (VeranoServidor(ahora) ? 1 : 0);
   PrintFormat("Servidor: UTC%+d ahora (invierno UTC%+d). Cuenta: %s (%s). Espera %d s", off, g_offInvierno, AccountInfoString(ACCOUNT_COMPANY), AccountInfoString(ACCOUNT_SERVER), InpSegundos);
   datetime hoy = ahora - (ahora % 86400);
   g_fr = FileOpen("ordenes_limitadas.csv", FILE_WRITE | FILE_CSV | FILE_ANSI, ',');
   if(g_fr == INVALID_HANDLE) { Print("No se pudo crear el CSV"); return; }
   FileWrite(g_fr, "estrategia", "simbolo", "lado", "dias", "se_llena_pct", "ahorro_medio_pb", "t", "ahorro_mediana_pb");
   // entradas del EA (las trimestrales se miden todos los dias como aproximacion)
   Medir("E8 oro viernes entrada 16:00",     InpOro,     1, 1, 16,  0, hoy);
   Medir("E15 oro D-2 entrada 09:30",        InpOro,    -1, 0,  9, 30, hoy);
   Medir("E9 yen entrada 07:00",             InpUSDJPY,  1, 0,  7,  0, hoy);
   Medir("E11 yen entrada 00:30",            InpUSDJPY, -1, 0,  0, 30, hoy);
   Medir("E11 yen entrada 00:30",            InpEURJPY, -1, 0,  0, 30, hoy);
   Medir("E11 yen entrada 00:30",            InpGBPJPY, -1, 0,  0, 30, hoy);
   Medir("E13 Nikkei entrada 15:00",         InpNikkei,  1, 0, 15,  0, hoy);
   Medir("E16 Nikkei entrada 20:00",         InpNikkei, -1, 0, 20,  0, hoy);
   Medir("Bitcoin entrada 16:00 (invierno)", InpBitcoin, 1, 0, 16,  0, hoy);
   Medir("Bitcoin entrada 17:00 (verano)",   InpBitcoin, 1, 0, 17,  0, hoy);
   // rupturas (proxy: compra y venta a horas de su ventana; en real se entra justo tras romper, peor para la limitada)
   for(int h = 4; h <= 10; h += 3) { Medir(StringFormat("C99/C93 oro %02d:00 (proxy)", h), InpOro, 1, 0, h, 0, hoy); Medir(StringFormat("C99/C93 oro %02d:00 (proxy)", h), InpOro, -1, 0, h, 0, hoy); }
   for(int h = 4; h <= 10; h += 3) { Medir(StringFormat("C101 Nikkei %02d:00 (proxy)", h), InpNikkei, 1, 0, h, 0, hoy); Medir(StringFormat("C101 Nikkei %02d:00 (proxy)", h), InpNikkei, -1, 0, h, 0, hoy); }
   // salidas (informativo: el EA sale a mercado)
   Medir("E8 oro salida 16:55 (informativo)", InpOro,    -1, 1, 16, 55, hoy);
   Medir("E9 yen salida 08:00 (informativo)", InpUSDJPY, -1, 0,  8,  0, hoy);
   FileClose(g_fr);
   Print("Listo. Manda MQL5/Files/ordenes_limitadas.csv (y si quieres repite con InpSegundos = 60).");
  }
