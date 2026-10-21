//+------------------------------------------------------------------+
//| Medir_Costes_Sesion_Europea.mq5                                   |
//| Mide en la cuenta del broker / prop firm el spread real de varios |
//| simbolos a las dos horas de la sesion europea de C20:             |
//|   entrada 07:00 de Londres  y  salida 08:00 de Nueva York         |
//| (research/certificacion/C20_RESULTADOS.md). Para cada dia usa el  |
//| ultimo tick de los 60 s anteriores (historico de ticks). NO abre  |
//| ninguna operacion.                                                |
//| Resultado: diario "Expertos" y MQL5/Files/costes_sesion_europea.csv |
//| Coste de ida y vuelta (pb) = spread a la entrada/2 + spread a la  |
//| salida/2, en puntos basicos del precio. La comision de la cuenta  |
//| se suma aparte (FTMO: 5 $ por lote ida y vuelta).                 |
//+------------------------------------------------------------------+
#property script_show_inputs
#property strict

enum ENUM_DST_SERVIDOR
  {
   DST_EUROPA = 0,   // Europa: ultimo domingo de marzo -> ultimo domingo de octubre (MetaQuotes-Demo)
   DST_EEUU   = 1,   // EEUU: 2.o domingo de marzo -> 1.er domingo de noviembre ("cierre de Nueva York")
   DST_NINGUNO = 2   // el servidor no cambia de hora
  };

input string InpSimbolos = "USDPLN,USDHUF,EURUSD";  // simbolos separados por comas (nombre exacto en esta cuenta)
input int    InpDias     = 90;                       // dias naturales hacia atras
input ENUM_DST_SERVIDOR InpDSTServidor = DST_EUROPA; // cambio de hora del servidor (MetaQuotes-Demo: Europa; compruebalo en tu broker)

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
bool VeranoEuropa(datetime utc)                        // 01:00 UTC del ultimo domingo de marzo -> idem de octubre
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

datetime Londres07(datetime dia) { datetime t = dia + 7 * 3600; if(VeranoEuropa(t)) t -= 3600; return t; }   // en UTC
datetime NuevaYork08(datetime dia) { datetime t = dia + 13 * 3600; if(VeranoEEUU(t - 3600)) t -= 3600; return t; } // en UTC

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

double Media(double &v[])
  {
   double s = 0; int n = ArraySize(v);
   for(int i = 0; i < n; i++) s += v[i];
   return n ? s / n : 0;
  }

void OnStart()
  {
   datetime ahora = TimeGMT();
   int off = (int)MathRound((double)(TimeTradeServer() - ahora) / 3600.0);
   g_offInvierno = off - (VeranoServidor(ahora) ? 1 : 0);
   Print("Servidor: UTC", (off >= 0 ? "+" : ""), off, " ahora (invierno UTC", (g_offInvierno >= 0 ? "+" : ""), g_offInvierno, ")");

   string sims[];
   int ns = StringSplit(InpSimbolos, ',', sims);
   int fh = FileOpen("costes_sesion_europea.csv", FILE_WRITE | FILE_CSV | FILE_ANSI, ',');
   FileWrite(fh, "simbolo", "dia", "pb_0700_Londres", "pb_0800_NY", "coste_ida_vuelta_pb");
   datetime hoy = ahora - (ahora % 86400);
   for(int i = 0; i < ns; i++)
     {
      string s = sims[i];
      StringTrimLeft(s); StringTrimRight(s);
      if(!SymbolSelect(s, true)) { Print("Simbolo no encontrado: ", s, ". Pon el nombre exacto que usa esta cuenta (p. ej. USDPLN.r)."); continue; }
      double ent[], sal[], tot[];
      for(int k = InpDias; k >= 1; k--)
        {
         datetime dia = hoy - k * 86400;
         MqlDateTime x; TimeToStruct(dia, x);
         if(x.day_of_week == 0 || x.day_of_week == 6) continue;
         double a, b;
         if(!SpreadPb(s, AServidor(Londres07(dia)), a) || !SpreadPb(s, AServidor(NuevaYork08(dia)), b)) continue;
         int n = ArraySize(ent);
         ArrayResize(ent, n + 1); ArrayResize(sal, n + 1); ArrayResize(tot, n + 1);
         ent[n] = a; sal[n] = b; tot[n] = a / 2 + b / 2;
         FileWrite(fh, s, TimeToString(dia, TIME_DATE), DoubleToString(a, 3), DoubleToString(b, 3), DoubleToString(a / 2 + b / 2, 3));
        }
      int n = ArraySize(tot);
      if(n == 0)
        {
         Print(s, ": sin ticks. Abre su grafico en M1, desplazate hacia atras unos meses para descargar el historico y repite.");
         continue;
        }
      double contrato = SymbolInfoDouble(s, SYMBOL_TRADE_CONTRACT_SIZE);
      PrintFormat("%s (%d dias): spread 07:00 Londres mediana %.2f pb (p90 %.2f) | 08:00 NY mediana %.2f pb (p90 %.2f) | COSTE IDA Y VUELTA mediana %.2f pb, media %.2f pb (sin comision). Contrato %.0f",
                  s, n, Percentil(ent, 0.5), Percentil(ent, 0.9), Percentil(sal, 0.5), Percentil(sal, 0.9), Percentil(tot, 0.5), Media(tot), contrato);
     }
   FileClose(fh);
   Print("Referencia (C20, sin costes): USDPLN ≈ 3,6 pb/dia y USDHUF ≈ 4,9 pb/dia. Con un coste total (spread + comision) <= 2 pb merece la pena; >= 4 pb, no.");
  }
