//+------------------------------------------------------------------+
//| Check_Tick_Sync_Sample.mq5                                         |
//| Script independiente (NO es un EA). Las velas M15 pueden ocultar  |
//| que un simbolo apenas tiene ticks reales en una ventana dada --   |
//| este script comprueba, con datos de TICK reales (no agregados),  |
//| la frescura/densidad de cotizaciones de XAUUSD y los 6 pares del  |
//| DXY sintetico en una muestra de ventanas fijadas de antemano,     |
//| repartidas por todo 2023-2026 y por distintas horas del dia.      |
//|                                                                     |
//| NO rellena nada: si CopyTicksRange no devuelve ticks, se informa  |
//| explicitamente, nunca se asume que el precio "seguia vigente".    |
//+------------------------------------------------------------------+
#property script_show_inputs
#property strict

input string InpSimbolos        = "XAUUSD,EURUSD,USDJPY,GBPUSD,USDCAD,USDCHF,USDSEK";
input int    InpAnioInicio      = 2023;
input int    InpAnioFin         = 2026;
input int    InpVentanaMinutos  = 120;   // tamaño de cada ventana de muestra
input string InpNombreArchivo   = "Tick_Sync_Sample.csv";

// Horas de servidor usadas en rotacion (una por mes muestreado) para cubrir
// distintas franjas horarias, fijadas ahora, no elegidas tras ver resultados.
int HorasRotacion(const int indiceMes)
  {
   int horas[3] = {2, 10, 18};
   return horas[indiceMes % 3];
  }

void OnStart()
  {
   string simbolos[];
   StringSplit(InpSimbolos, ',', simbolos);
   for(int i = 0; i < ArraySize(simbolos); i++)
     {
      StringTrimLeft(simbolos[i]);
      StringTrimRight(simbolos[i]);
      SymbolSelect(simbolos[i], true);
     }

   int handle = FileOpen(InpNombreArchivo, FILE_WRITE | FILE_CSV | FILE_ANSI, ';');
   if(handle == INVALID_HANDLE)
     {
      Print("ERROR: no se pudo abrir ", InpNombreArchivo, ". Codigo: ", GetLastError());
      return;
     }
   FileWrite(handle, "Simbolo", "InicioVentanaServidor", "NumTicks", "PrimerTick", "UltimoTick",
             "GapMaxSeg", "GapMedianoSeg", "SinDatos");

   int totalVentanas = 0, ventanasSinDatos = 0;

   for(int anio = InpAnioInicio; anio <= InpAnioFin; anio++)
     {
      for(int mes = 1; mes <= 12; mes++)
        {
         if(anio == InpAnioFin && mes > 10) // nuestro historico de referencia llega a octubre 2026
            break;

         MqlDateTime dt;
         dt.year = anio; dt.mon = mes; dt.day = 15;
         dt.hour = HorasRotacion(mes - 1); dt.min = 0; dt.sec = 0;
         datetime inicioVentana = StructToTime(dt);
         datetime finVentana = inicioVentana + InpVentanaMinutos * 60;

         for(int s = 0; s < ArraySize(simbolos); s++)
           {
            string simbolo = simbolos[s];
            if(StringLen(simbolo) == 0)
               continue;

            MqlTick ticks[];
            int n = CopyTicksRange(simbolo, inicioVentana, finVentana, COPY_TICKS_ALL, ticks);
            totalVentanas++;

            if(n <= 0)
              {
               ventanasSinDatos++;
               FileWrite(handle, simbolo, TimeToString(inicioVentana, TIME_DATE | TIME_MINUTES),
                         0, "", "", "", "", "SIN_TICKS_O_SIN_HISTORIAL");
               continue;
              }

            datetime primerTick = ticks[0].time;
            datetime ultimoTick = ticks[n - 1].time;

            long gapMax = 0;
            long gaps[];
            ArrayResize(gaps, n > 1 ? n - 1 : 0);
            for(int j = 1; j < n; j++)
              {
               long g = (long)(ticks[j].time - ticks[j - 1].time);
               gaps[j - 1] = g;
               if(g > gapMax)
                  gapMax = g;
              }
            long gapMediano = 0;
            if(n > 1)
              {
               ArraySort(gaps);
               gapMediano = gaps[(n - 1) / 2];
              }

            FileWrite(handle, simbolo, TimeToString(inicioVentana, TIME_DATE | TIME_MINUTES),
                      n, TimeToString(primerTick, TIME_DATE | TIME_SECONDS),
                      TimeToString(ultimoTick, TIME_DATE | TIME_SECONDS),
                      (long)gapMax, (long)gapMediano, "");
           }
        }
     }

   FileClose(handle);
   Print("=== Check_Tick_Sync_Sample: fin ===");
   Print("Ventanas totales comprobadas (simbolo x fecha): ", totalVentanas);
   Print("Ventanas SIN ticks disponibles: ", ventanasSinDatos,
         " (puede ser falta de historial de ticks tan antiguo, no necesariamente mercado cerrado -- "
         "revisar caso por caso contra el calendario de sesion antes de interpretar).");
   Print("Archivo: ", InpNombreArchivo, " -> MQL5/Files");
  }
//+------------------------------------------------------------------+
