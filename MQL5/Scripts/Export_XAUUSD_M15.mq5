//+------------------------------------------------------------------+
//| Export_XAUUSD_M15.mq5                                            |
//| Script independiente de extraccion de historial (NO es un EA).   |
//| Exporta OHLC M15 crudo via CopyRates() a un CSV, sin modificar   |
//| ni depender de ningun Expert Advisor del repositorio.            |
//|                                                                    |
//| Principios:                                                       |
//|  - No rellena ni inventa velas ausentes: solo informa de huecos. |
//|  - Conserva el timestamp tal cual lo da el servidor (sin         |
//|    convertir a UTC); esa conversion se hace despues en Python.   |
//|  - Incluye Spread/TickVolume/RealVolume crudos de MqlRates, con  |
//|    aviso de que Spread es una foto puntual, no el coste real de  |
//|    ejecucion.                                                     |
//+------------------------------------------------------------------+
#property script_show_inputs
#property strict

input string   InpSimbolo       = "XAUUSD";                    // Ticker EXACTO como aparece en Market Watch
input datetime InpFechaInicio   = D'2023.01.01 00:00:00';       // Rango solicitado (hora de SERVIDOR, no UTC)
input datetime InpFechaFin      = D'2026.12.31 23:45:00';
input string   InpNombreArchivo = "XAUUSD_M15_Export.csv";       // Se guarda en MQL5/Files/
input int      InpMaxIntentos   = 10;                            // Reintentos si el historial aun no esta sincronizado
input int      InpEsperaMsEntreIntentos = 1000;

//+------------------------------------------------------------------+
void OnStart()
  {
   Print("=== Export_XAUUSD_M15: inicio ===");

   if(!SymbolSelect(InpSimbolo, true))
     {
      Print("ERROR: no se pudo seleccionar el simbolo '", InpSimbolo,
            "'. Verifica el ticker exacto en Market Watch (puede llevar sufijo del broker, ej. XAUUSD.c).");
      return;
     }

   MqlRates rates[];
   ArraySetAsSeries(rates, false);

   int copiados = 0;
   int intentos = 0;
   while(intentos < InpMaxIntentos)
     {
      copiados = CopyRates(InpSimbolo, PERIOD_M15, InpFechaInicio, InpFechaFin, rates);
      if(copiados > 0)
         break;
      intentos++;
      int err = GetLastError();
      Print("Intento ", intentos, "/", InpMaxIntentos,
            ": CopyRates devolvio ", copiados, " (error ", err, "). Esperando sincronizacion de historial...");
      ResetLastError();
      Sleep(InpEsperaMsEntreIntentos);
     }

   if(copiados <= 0)
     {
      Print("ERROR FATAL: no se pudo obtener ninguna vela tras ", InpMaxIntentos,
            " intentos. No se genera CSV. Revisa que el simbolo tenga historial M15 descargado ",
            "(Herramientas > Centro de Historial de Cotizaciones).");
      return;
     }

   int errorFinal = GetLastError();
   if(errorFinal != 0)
      Print("AVISO: CopyRates devolvio ", copiados, " velas pero reporto codigo de error ", errorFinal,
            " en el ultimo intento. Revisar con cautela.");

   int handle = FileOpen(InpNombreArchivo, FILE_WRITE | FILE_CSV | FILE_ANSI, ';');
   if(handle == INVALID_HANDLE)
     {
      Print("ERROR: no se pudo abrir '", InpNombreArchivo, "' para escritura. Codigo: ", GetLastError());
      return;
     }

   // Cabecera. TimestampServidor se exporta tal cual, SIN convertir a UTC aqui.
   FileWrite(handle, "TimestampServidor", "Open", "High", "Low", "Close",
             "TickVolume", "Spread", "RealVolume");

   int digitos = (int)SymbolInfoInteger(InpSimbolo, SYMBOL_DIGITS);

   for(int i = 0; i < copiados; i++)
     {
      FileWrite(handle,
                TimeToString(rates[i].time, TIME_DATE | TIME_SECONDS),
                DoubleToString(rates[i].open, digitos),
                DoubleToString(rates[i].high, digitos),
                DoubleToString(rates[i].low, digitos),
                DoubleToString(rates[i].close, digitos),
                (long)rates[i].tick_volume,
                (long)rates[i].spread,
                (long)rates[i].real_volume);
     }

   FileClose(handle);

   // --- Diagnostico de cobertura ---
   datetime primero = rates[0].time;
   datetime ultimo  = rates[copiados - 1].time;

   Print("=== EXPORTACION COMPLETADA ===");
   Print("Simbolo: ", InpSimbolo, "  Timeframe: M15");
   Print("Rango SOLICITADO (hora servidor): ", TimeToString(InpFechaInicio), " - ", TimeToString(InpFechaFin));
   Print("Rango DISPONIBLE (hora servidor): ", TimeToString(primero), " - ", TimeToString(ultimo));
   Print("Velas exportadas: ", copiados);

   if(primero > InpFechaInicio)
      Print("AVISO: falta historial al PRINCIPIO del rango solicitado. No hay datos entre ",
            TimeToString(InpFechaInicio), " y ", TimeToString(primero), ".");

   if(ultimo < InpFechaFin)
      Print("AVISO: falta historial al FINAL del rango solicitado. No hay datos entre ",
            TimeToString(ultimo), " y ", TimeToString(InpFechaFin), ".");

   // --- Diagnostico de huecos dentro del rango disponible ---
   int huecosInesperados = 0;
   int huecosFinDeSemana = 0;
   int ejemplosImpresos = 0;
   const int SEGUNDOS_POR_VELA = 15 * 60;

   for(int i = 1; i < copiados; i++)
     {
      long diff = (long)(rates[i].time - rates[i - 1].time);
      if(diff <= SEGUNDOS_POR_VELA)
         continue; // continuidad normal

      MqlDateTime dtPrev, dtCurr;
      TimeToStruct(rates[i - 1].time, dtPrev);
      TimeToStruct(rates[i].time, dtCurr);

      bool pareceCierreSemanal = (dtPrev.day_of_week == 5 /*viernes*/ &&
                                   (dtCurr.day_of_week == 0 /*domingo*/ || dtCurr.day_of_week == 1 /*lunes*/));

      if(pareceCierreSemanal)
         huecosFinDeSemana++;
      else
        {
         huecosInesperados++;
         if(ejemplosImpresos < 15)
           {
            Print("HUECO INESPERADO: de ", TimeToString(rates[i - 1].time),
                  " a ", TimeToString(rates[i].time),
                  " (", diff / 60, " minutos sin vela)");
            ejemplosImpresos++;
           }
        }
     }

   Print("Huecos de fin de semana/festivo detectados (esperables): ", huecosFinDeSemana);
   Print("Huecos INTRADIA inesperados detectados: ", huecosInesperados,
         (huecosInesperados > 15 ? " (se listaron solo los primeros 15 ejemplos arriba)" : ""));
   Print("NOTA: este script NO rellena ni inventa velas. Los huecos listados son para revision manual.");
   Print("NOTA: el campo 'Spread' es el valor de MqlRates.spread en el cierre de cada vela (en puntos del simbolo), ",
         "una fotografia puntual, NO el coste de ejecucion real ni un promedio durante la vela.");
   Print("Archivo generado: ", InpNombreArchivo,
         " -> buscarlo en la carpeta de datos del terminal, subcarpeta MQL5\\Files ",
         "(Archivo > Abrir carpeta de datos, NO la carpeta de instalacion).");
   Print("=== Export_XAUUSD_M15: fin ===");
  }
//+------------------------------------------------------------------+
