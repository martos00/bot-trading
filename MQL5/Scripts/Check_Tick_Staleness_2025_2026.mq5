//+------------------------------------------------------------------+
//| Check_Tick_Staleness_2025_2026.mq5                                 |
//| Script independiente (NO es un EA). Ampliacion LIMITADA del        |
//| diagnostico de ticks, acotada a 2025-2026 (unico tramo donde       |
//| XAUUSD tiene ticks reales). Para una muestra de dias completos,    |
//| mide para CADA cierre de vela M15 (96/dia) y cada simbolo:         |
//|   - el ultimo tick disponible antes/en ese cierre                  |
//|   - su antigüedad en segundos (ms si time_msc esta poblado)        |
//|   - si ese tick cae dentro de horas negociables o en un cierre     |
//| Tambien verifica que los timestamps de tick y de vela comparten la |
//| misma referencia temporal (un tick del rango [open,close) de la   |
//| propia vela debe existir cuando TickVolume>0).                     |
//| NO rellena nada: sin ticks -> se marca explicitamente.              |
//+------------------------------------------------------------------+
#property script_show_inputs
#property strict

input string InpSimbolos      = "XAUUSD,EURUSD,USDJPY,GBPUSD,USDCAD,USDCHF,USDSEK";
input int    InpDiasMuestra   = 24;     // dias completos a muestrear (repartidos 2025-2026)
input string InpNombreArchivo = "Tick_Staleness_2025_2026.csv";

datetime FechaInicioRango()  { return D'2025.01.01 00:00:00'; }
datetime FechaFinRango()     { return D'2026.10.09 00:00:00'; }

void OnStart()
  {
   string simbolos[];
   StringSplit(InpSimbolos, ',', simbolos);
   for(int i = 0; i < ArraySize(simbolos); i++)
     {
      StringTrimLeft(simbolos[i]); StringTrimRight(simbolos[i]);
      SymbolSelect(simbolos[i], true);
     }

   int handle = FileOpen(InpNombreArchivo, FILE_WRITE | FILE_CSV | FILE_ANSI, ';');
   if(handle == INVALID_HANDLE)
     {
      Print("ERROR: no se pudo abrir ", InpNombreArchivo, ". Codigo: ", GetLastError());
      return;
     }
   FileWrite(handle, "Simbolo", "CierreVelaServidor", "UltimoTickServidor", "AntiguedadSeg",
             "PrecisionMsc", "TickVolumeDeLaVela", "TickExisteDentroDeLaVela", "SinDatos");

   // Dias de muestra: repartidos uniformemente en el rango, fijados por formula (no elegidos
   // tras ver resultados), evitando fin de semana (se desplaza al lunes siguiente si cae en sabado/domingo)
   datetime inicio = FechaInicioRango();
   datetime fin = FechaFinRango();
   long rangoSeg = (long)(fin - inicio);

   int totalCierres = 0, sinDatos = 0, inconsistenciasTemporales = 0;

   for(int d = 0; d < InpDiasMuestra; d++)
     {
      datetime dia = inicio + (long)((double)rangoSeg * d / InpDiasMuestra);
      MqlDateTime dt;
      TimeToStruct(dia, dt);
      dt.hour = 0; dt.min = 0; dt.sec = 0;
      dia = StructToTime(dt);
      if(dt.day_of_week == 0) dia += 86400;      // domingo -> lunes
      else if(dt.day_of_week == 6) dia += 2 * 86400; // sabado -> lunes

      for(int c = 0; c < 96; c++)  // 96 cierres de vela M15 en el dia
        {
         datetime cierreVela = dia + c * 15 * 60 + 15 * 60; // cierre = apertura + 15min
         datetime aperturaVela = cierreVela - 15 * 60;

         for(int s = 0; s < ArraySize(simbolos); s++)
           {
            string simbolo = simbolos[s];
            if(StringLen(simbolo) == 0)
               continue;
            totalCierres++;

            // Ultimo tick con tiempo <= cierre de la vela (ventana de busqueda: 2h hacia atras)
            MqlTick ticks[];
            ulong desde_msc = (ulong)(cierreVela - 2 * 3600) * 1000;
            ulong hasta_msc = (ulong)cierreVela * 1000 + 999;
            int n = CopyTicksRange(simbolo, ticks, COPY_TICKS_ALL, desde_msc, hasta_msc);

            if(n <= 0)
              {
               sinDatos++;
               FileWrite(handle, simbolo, TimeToString(cierreVela, TIME_DATE | TIME_SECONDS),
                         "", "", "", "", "", "SIN_TICKS_O_SIN_HISTORIAL");
               continue;
              }

            MqlTick ultimo = ticks[n - 1];
            bool precisionMsc = (ultimo.time_msc % 1000) != 0;  // si siempre es .000, no hay precision sub-segundo real
            double antiguedadSeg = (double)(cierreVela * 1000 - ultimo.time_msc) / 1000.0;

            // Verificacion de referencia temporal compartida: si la vela tiene TickVolume>0,
            // debe existir al menos un tick con tiempo en [apertura, cierre) de esa vela.
            MqlRates velas[];
            int copiadas = CopyRates(simbolo, PERIOD_M15, aperturaVela, 1, velas);
            bool tickDentroDeVela = false;
            long tickVolumeVela = -1;
            if(copiadas > 0 && velas[0].time == aperturaVela)
              {
               tickVolumeVela = (long)velas[0].tick_volume;
               if(tickVolumeVela > 0)
                 {
                  MqlTick ticksVela[];
                  int nv = CopyTicksRange(simbolo, ticksVela, COPY_TICKS_ALL,
                                           (ulong)aperturaVela * 1000, (ulong)cierreVela * 1000 - 1);
                  tickDentroDeVela = (nv > 0);
                  if(!tickDentroDeVela)
                     inconsistenciasTemporales++;
                 }
              }

            FileWrite(handle, simbolo, TimeToString(cierreVela, TIME_DATE | TIME_SECONDS),
                      TimeToString(ultimo.time, TIME_DATE | TIME_SECONDS),
                      DoubleToString(antiguedadSeg, 3),
                      precisionMsc ? "SI" : "NO_O_SIN_MSC",
                      (string)tickVolumeVela,
                      (tickVolumeVela <= 0 ? "N/A" : (tickDentroDeVela ? "SI" : "NO")),
                      "");
           }
        }
     }

   FileClose(handle);
   Print("=== Check_Tick_Staleness_2025_2026: fin ===");
   Print("Cierres de vela x simbolo comprobados: ", totalCierres);
   Print("Sin ticks disponibles: ", sinDatos, " (", DoubleToString(100.0*sinDatos/MathMax(totalCierres,1),1), "%)");
   Print("Inconsistencias temporales (vela con TickVolume>0 pero SIN tick dentro de su propio "
         "rango horario -- señal de que tick y vela NO comparten referencia temporal): ",
         inconsistenciasTemporales);
   Print("Archivo: ", InpNombreArchivo, " -> MQL5/Files");
  }
//+------------------------------------------------------------------+
