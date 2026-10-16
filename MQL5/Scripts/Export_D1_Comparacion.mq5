//+------------------------------------------------------------------+
//| Export_D1_Comparacion.mq5                                        |
//| Script de DIAGNOSTICO (no opera nada). Exporta OHLC D1 crudo via |
//| CopyRates() para uno o varios simbolos, en un rango de fechas    |
//| concreto -- pensado para comparar, dia a dia, el historico D1    |
//| que sirve ESTE broker ahora mismo contra el historico que se usa |
//| en research/datos_multiactivo.py (un export M15 mas antiguo),    |
//| despues de encontrar varias operaciones del EA cuyo precio de    |
//| entrada o motivo de salida no coincide con el backtest de Python |
//| en fechas que NO se explican por tener mas historial ni por el   |
//| burn-in del EMA de N (ver README, protocolo de validacion).      |
//+------------------------------------------------------------------+
#property script_show_inputs
#property strict

input string   InpSimbolos      = "XAUUSD,USTEC,US500";
input datetime InpFechaInicio   = D'2015.01.01 00:00:00';
input datetime InpFechaFin      = D'2021.12.31 00:00:00';
input string   InpSufijoArchivo = "_D1_Comparacion.csv";
input int      InpMaxIntentos   = 10;
input int      InpEsperaMsEntreIntentos = 1000;

bool ExportarSimbolo(const string simbolo)
  {
   Print("\n=== Exportando D1 de ", simbolo, " ===");
   if(!SymbolSelect(simbolo, true))
     {
      Print("ERROR: no se pudo seleccionar '", simbolo, "'.");
      return false;
     }

   MqlRates rates[];
   ArraySetAsSeries(rates, false);

   int copiados = 0;
   int intentos = 0;
   while(intentos < InpMaxIntentos)
     {
      copiados = CopyRates(simbolo, PERIOD_D1, InpFechaInicio, InpFechaFin, rates);
      if(copiados > 0)
         break;
      intentos++;
      int err = GetLastError();
      PrintFormat("[%s] Intento %d/%d: CopyRates devolvio %d (error %d). Esperando sincronizacion de historial...",
                  simbolo, intentos, InpMaxIntentos, copiados, err);
      ResetLastError();
      Sleep(InpEsperaMsEntreIntentos);
     }

   if(copiados <= 0)
     {
      datetime primeraDisponible = (datetime)SeriesInfoInteger(simbolo, PERIOD_D1, SERIES_FIRSTDATE);
      PrintFormat("[%s] ERROR FATAL: no se pudo obtener ninguna barra tras %d intentos en el rango [%s, %s]. "
                  "Primera fecha D1 realmente disponible para este simbolo segun el terminal: %s -- "
                  "si es POSTERIOR a tu InpFechaInicio, ese es el motivo: ajusta InpFechaInicio a esa fecha "
                  "(o posterior) y vuelve a ejecutar SOLO para este simbolo.",
                  simbolo, InpMaxIntentos, TimeToString(InpFechaInicio, TIME_DATE), TimeToString(InpFechaFin, TIME_DATE),
                  primeraDisponible > 0 ? TimeToString(primeraDisponible, TIME_DATE) : "desconocida (0 barras en todo el historico)");
      return false;
     }

   string nombreArchivo = simbolo + InpSufijoArchivo;
   int handle = FileOpen(nombreArchivo, FILE_WRITE | FILE_CSV | FILE_ANSI, ';');
   if(handle == INVALID_HANDLE)
     {
      PrintFormat("[%s] ERROR al crear '%s' (error %d).", simbolo, nombreArchivo, GetLastError());
      return false;
     }
   FileWrite(handle, "Fecha", "Open", "High", "Low", "Close", "Spread", "TickVolume");
   for(int i = 0; i < copiados; i++)
      FileWrite(handle, TimeToString(rates[i].time, TIME_DATE), DoubleToString(rates[i].open, 5),
                DoubleToString(rates[i].high, 5), DoubleToString(rates[i].low, 5), DoubleToString(rates[i].close, 5),
                (long)rates[i].spread, (long)rates[i].tick_volume);
   FileClose(handle);
   PrintFormat("[%s] %d barras D1 exportadas -> MQL5/Files/%s (desde %s hasta %s)", simbolo, copiados, nombreArchivo,
               TimeToString(rates[0].time, TIME_DATE), TimeToString(rates[copiados - 1].time, TIME_DATE));
   return true;
  }

void OnStart()
  {
   string partes[];
   int n = StringSplit(InpSimbolos, ',', partes);
   for(int i = 0; i < n; i++)
     {
      string s = partes[i];
      StringTrimLeft(s);
      StringTrimRight(s);
      ExportarSimbolo(s);
     }
   Print("Export_D1_Comparacion: terminado.");
  }
