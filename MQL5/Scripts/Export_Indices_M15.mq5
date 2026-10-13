//+------------------------------------------------------------------+
//| Export_Indices_M15.mq5                                            |
//| Script independiente (NO es un EA). Exporta OHLC M15 crudo de los |
//| indices candidatos (US500, USTEC por defecto) con la misma        |
//| disciplina que Export_XAUUSD_M15.mq5 / Export_FX6_M15.mq5:        |
//| timestamp de servidor sin convertir, Spread/TickVolume/RealVolume |
//| crudos, sin rellenar huecos, informando de cobertura real.        |
//+------------------------------------------------------------------+
#property script_show_inputs
#property strict

input string   InpSimbolos      = "US500,USTEC";   // separados por coma; añade variantes mini si se quiere
input datetime InpFechaInicio   = D'2023.01.01 00:00:00';
input datetime InpFechaFin      = D'2026.12.31 23:45:00';
input string   InpSufijoArchivo = "_M15_Export.csv";
input int      InpMaxIntentos   = 10;
input int      InpEsperaMsEntreIntentos = 1000;

bool ExportarSimbolo(const string simbolo)
  {
   Print("\n=== Exportando ", simbolo, " ===");

   if(!SymbolSelect(simbolo, true))
     {
      Print("ERROR: no se pudo seleccionar el simbolo '", simbolo, "'. ¿Esta disponible en Observacion del mercado?");
      return false;
     }

   // Aviso informativo (no bloqueante): si "Operaciones" esta desactivada no impide leer
   // historial OHLC, solo impediria enviar ordenes -- se deja constancia en el log.
   long modoOperaciones = SymbolInfoInteger(simbolo, SYMBOL_TRADE_MODE);
   if(modoOperaciones == SYMBOL_TRADE_MODE_DISABLED)
      Print("  AVISO: SYMBOL_TRADE_MODE_DISABLED en este instante para ", simbolo,
            " -- normal si es fuera de horario de sesion; no afecta a la exportacion de historial.");

   MqlRates rates[];
   ArraySetAsSeries(rates, false);

   int copiados = 0;
   int intentos = 0;
   while(intentos < InpMaxIntentos)
     {
      copiados = CopyRates(simbolo, PERIOD_M15, InpFechaInicio, InpFechaFin, rates);
      if(copiados > 0)
         break;
      intentos++;
      int err = GetLastError();
      Print("  Intento ", intentos, "/", InpMaxIntentos, ": CopyRates devolvio ", copiados,
            " (error ", err, "). Esperando sincronizacion de historial...");
      ResetLastError();
      Sleep(InpEsperaMsEntreIntentos);
     }

   if(copiados <= 0)
     {
      Print("ERROR FATAL (", simbolo, "): no se pudo obtener ninguna vela tras ", InpMaxIntentos,
            " intentos. No se genera CSV para este simbolo. Si el simbolo es nuevo para este "
            "terminal, abre antes un grafico M15 suyo y espera a que sincronice el historial.");
      return false;
     }

   string nombreArchivo = simbolo + InpSufijoArchivo;
   int handle = FileOpen(nombreArchivo, FILE_WRITE | FILE_CSV | FILE_ANSI, ';');
   if(handle == INVALID_HANDLE)
     {
      Print("ERROR (", simbolo, "): no se pudo abrir '", nombreArchivo, "'. Codigo: ", GetLastError());
      return false;
     }

   FileWrite(handle, "TimestampServidor", "Open", "High", "Low", "Close",
             "TickVolume", "Spread", "RealVolume");

   int digitos = (int)SymbolInfoInteger(simbolo, SYMBOL_DIGITS);
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

   datetime primero = rates[0].time;
   datetime ultimo  = rates[copiados - 1].time;

   Print("  Velas exportadas: ", copiados);
   Print("  Rango disponible (hora servidor): ", TimeToString(primero), " - ", TimeToString(ultimo));
   if(primero > InpFechaInicio)
      Print("  AVISO: falta historial al PRINCIPIO. Sin datos entre ", TimeToString(InpFechaInicio),
            " y ", TimeToString(primero), ".");
   if(ultimo < InpFechaFin)
      Print("  AVISO: falta historial al FINAL. Sin datos entre ", TimeToString(ultimo),
            " y ", TimeToString(InpFechaFin), ".");

   int huecos = 0;
   const int SEGUNDOS_POR_VELA = 15 * 60;
   for(int i = 1; i < copiados; i++)
      if((long)(rates[i].time - rates[i - 1].time) > SEGUNDOS_POR_VELA)
         huecos++;
   Print("  Huecos (>15 min) detectados: ", huecos, " -- clasificacion detallada se hace en el analisis Python.");
   Print("  Archivo: ", nombreArchivo, " -> MQL5/Files (Archivo > Abrir carpeta de datos).");
   return true;
  }

void OnStart()
  {
   Print("=== Export_Indices_M15: inicio ===");
   string simbolos[];
   StringSplit(InpSimbolos, ',', simbolos);

   int ok = 0, fallidos = 0;
   for(int i = 0; i < ArraySize(simbolos); i++)
     {
      string s = simbolos[i];
      StringTrimLeft(s);
      StringTrimRight(s);
      if(StringLen(s) == 0)
         continue;
      if(ExportarSimbolo(s))
         ok++;
      else
         fallidos++;
     }

   Print("\n=== Export_Indices_M15: fin -- ", ok, " simbolos exportados correctamente, ",
         fallidos, " fallidos ===");
  }
//+------------------------------------------------------------------+
