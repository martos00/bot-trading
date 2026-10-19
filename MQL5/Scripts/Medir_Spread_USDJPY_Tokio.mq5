//+------------------------------------------------------------------+
//| Medir_Spread_USDJPY_Tokio.mq5                                     |
//| Script de diagnostico (NO es un EA, no abre operaciones). Mide en |
//| el historico de ticks del PROPIO broker el spread real de USDJPY  |
//| en los 3 instantes de la estrategia H73 (research/fase69):        |
//|   - 17:05 Nueva York (entrada tramo 1, justo tras el rollover)    |
//|   - 09:55 Tokio (fixing: cierre tramo 1 / apertura tramo 2)       |
//|   - 08:00 Frankfurt (cierre tramo 2)                              |
//| Spread = ask - bid del ultimo tick en los 5 minutos anteriores.   |
//| Resultado: mediana y percentil 90 en pips, en el diario "Expertos"|
//| y en MQL5/Files/spread_usdjpy_tokio.csv.                          |
//|                                                                    |
//| Husos: los instantes se calculan en UTC con las reglas de horario |
//| de verano de EEUU y de la UE; Tokio no tiene horario de verano.   |
//| La hora del servidor se obtiene como UTC + offset, con el offset  |
//| de invierno indicado y +1 h en verano de EEUU si el servidor lo   |
//| sigue (lo habitual: UTC+2 invierno / UTC+3 verano). Compruebalo   |
//| antes con Check_Server_Offset.mq5.                                 |
//+------------------------------------------------------------------+
#property script_show_inputs
#property strict

input string InpSimbolo              = "USDJPY";
input int    InpDias                 = 120;   // dias naturales hacia atras
input int    InpOffsetInviernoHoras  = 2;     // hora servidor - UTC en invierno
input bool   InpServidorConDSTdeEEUU = true;  // el servidor suma 1 h con el horario de verano de EEUU

// n-esimo domingo (n>=1) de un mes, o el ultimo si n==0, como fecha a las 00:00 UTC
datetime Domingo(int anio, int mes, int n)
  {
   MqlDateTime t = {};
   t.year = anio; t.mon = mes; t.day = 1;
   datetime d = StructToTime(t);
   if(n == 0)
     {
      t.mon = mes + 1; if(t.mon == 13) { t.mon = 1; t.year++; }
      d = StructToTime(t) - 86400;
      MqlDateTime x; TimeToStruct(d, x);
      return d - x.day_of_week * 86400;
     }
   MqlDateTime x; TimeToStruct(d, x);
   int primero = (7 - x.day_of_week) % 7;
   return d + (primero + 7 * (n - 1)) * 86400;
  }

bool VeranoEEUU(datetime utc)   // 2.º domingo de marzo 07:00 UTC -> 1.er domingo de noviembre 06:00 UTC
  {
   MqlDateTime x; TimeToStruct(utc, x);
   return utc >= Domingo(x.year, 3, 2) + 7 * 3600 && utc < Domingo(x.year, 11, 1) + 6 * 3600;
  }

bool VeranoUE(datetime utc)     // ultimo domingo de marzo 01:00 UTC -> ultimo domingo de octubre 01:00 UTC
  {
   MqlDateTime x; TimeToStruct(utc, x);
   return utc >= Domingo(x.year, 3, 0) + 3600 && utc < Domingo(x.year, 10, 0) + 3600;
  }

datetime AServidor(datetime utc)
  {
   int off = InpOffsetInviernoHoras + ((InpServidorConDSTdeEEUU && VeranoEEUU(utc)) ? 1 : 0);
   return utc + off * 3600;
  }

// spread (pips) del ultimo tick en [T-5min, T) con T en hora servidor; -1 si no hay ticks
double SpreadEn(datetime T_srv, double pip)
  {
   MqlTick ticks[];
   int n = CopyTicksRange(InpSimbolo, ticks, COPY_TICKS_INFO, (ulong)(T_srv - 300) * 1000, (ulong)T_srv * 1000 - 1);
   if(n <= 0) return -1;
   return (ticks[n - 1].ask - ticks[n - 1].bid) / pip;
  }

double Percentil(double &v[], double p)
  {
   int n = ArraySize(v);
   if(n == 0) return -1;
   ArraySort(v);
   int k = (int)MathFloor(p * (n - 1));
   return v[k];
  }

void OnStart()
  {
   if(!SymbolSelect(InpSimbolo, true)) { Print("Simbolo no encontrado: ", InpSimbolo); return; }
   double pip = (SymbolInfoInteger(InpSimbolo, SYMBOL_DIGITS) >= 3) ? 0.01 : 0.0001;
   double s1705[], s0955[], s0800[];
   int fh = FileOpen("spread_usdjpy_tokio.csv", FILE_WRITE | FILE_CSV | FILE_ANSI, ',');
   FileWrite(fh, "dia_tokio_utc", "pips_1705NY", "pips_0955TOK", "pips_0800FRA");
   datetime hoy = TimeGMT() - (TimeGMT() % 86400);
   for(int k = InpDias; k >= 1; k--)
     {
      datetime dia = hoy - k * 86400;          // 00:00 UTC de la fecha de Tokio
      MqlDateTime x; TimeToStruct(dia, x);
      if(x.day_of_week == 0 || x.day_of_week == 6) continue;
      // 09:55 Tokio = 00:55 UTC del mismo dia
      datetime t0955 = dia + 55 * 60;
      // 17:05 NY del dia anterior: 21:05 UTC (verano EEUU) o 22:05 UTC (invierno)
      datetime t1705 = dia - 86400 + 22 * 3600 + 5 * 60;
      if(VeranoEEUU(t1705 - 3600)) t1705 -= 3600;
      // 08:00 Frankfurt: 06:00 UTC (verano UE) o 07:00 UTC (invierno)
      datetime t0800 = dia + 7 * 3600;
      if(VeranoUE(t0800)) t0800 -= 3600;
      double a = SpreadEn(AServidor(t1705), pip), b = SpreadEn(AServidor(t0955), pip), c = SpreadEn(AServidor(t0800), pip);
      if(a < 0 || b < 0 || c < 0) continue;
      int n = ArraySize(s1705);
      ArrayResize(s1705, n + 1); ArrayResize(s0955, n + 1); ArrayResize(s0800, n + 1);
      s1705[n] = a; s0955[n] = b; s0800[n] = c;
      FileWrite(fh, TimeToString(dia, TIME_DATE), DoubleToString(a, 2), DoubleToString(b, 2), DoubleToString(c, 2));
     }
   FileClose(fh);
   int n = ArraySize(s1705);
   Print("=== Spread real de ", InpSimbolo, " en ", n, " dias (pips) ===");
   Print("17:05 NY      mediana ", DoubleToString(Percentil(s1705, 0.5), 2), "  p90 ", DoubleToString(Percentil(s1705, 0.9), 2));
   Print("09:55 Tokio   mediana ", DoubleToString(Percentil(s0955, 0.5), 2), "  p90 ", DoubleToString(Percentil(s0955, 0.9), 2));
   Print("08:00 Frankf. mediana ", DoubleToString(Percentil(s0800, 0.5), 2), "  p90 ", DoubleToString(Percentil(s0800, 0.9), 2));
   Print("Swap largo: ", SymbolInfoDouble(InpSimbolo, SYMBOL_SWAP_LONG), "  swap corto: ", SymbolInfoDouble(InpSimbolo, SYMBOL_SWAP_SHORT),
         "  (la estrategia no cruza el rollover de las 17:00 NY)");
   Print("La comision por lote NO es accesible por la API: consultala en la especificacion de la cuenta.");
   if(n == 0) Print("Sin ticks: abre el grafico de ", InpSimbolo, " en M1 y desplazate hacia atras para que el terminal descargue el historico de ticks.");
  }
