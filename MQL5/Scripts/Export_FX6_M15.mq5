//+------------------------------------------------------------------+
//| Export_FX6_M15.mq5                                                |
//| Script independiente (NO es un EA). Exporta OHLC M15 crudo de los |
//| 6 pares que componen el DXY sintetico (EURUSD, USDJPY, GBPUSD,   |
//| USDCAD, USDCHF, USDSEK), uno por simbolo, con la misma disciplina |
//| que Export_XAUUSD_M15.mq5: timestamp de servidor sin convertir,  |
//| Spread/TickVolume/RealVolume crudos, sin rellenar ni inventar     |
//| velas ausentes, informando de cobertura real y huecos.            |
//+------------------------------------------------------------------+
#property script_show_inputs
#property strict

input string   InpSimbolos      = "EURUSD,USDJPY,GBPUSD,USDCAD,USDCHF,USDSEK"; // separados por coma
input datetime InpFechaInicio   = D'2023.01.01 00:00:00';
input datetime InpFechaFin      = D'2026.12.31 23:45:00';
input string   InpSufijoArchivo = "_M15_Export.csv";   // se guarda en MQL5/Files/<SIMBOLO><sufijo>
input int      InpMaxIntentos   = 10;
input int      InpEsperaMsEntreIntentos = 1000;

string SplitSimbolos(const string lista, string &out[])
  {
   int n = StringSplit(lista, ',', out);
   for(int i = 0; i < n; i++)
      StringTrimLeft(out[i]);
   for(int i = 0; i < n; i++)
      StringTrimRight(out[i]);
   return out[0]; // valor de retorno no usado, solo para evitar warning
  }

bool ExportarSimbolo(const string simbolo)
  {
   Print("\n=== Exportando ", simbolo, " ===");

   if(!SymbolSelect(simbolo, true))
     {
      Print("ERROR: no se pudo seleccionar el simbolo '", simbolo, "'. ¿Esta disponible en Market Watch?");
      return false;
     }

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
            " intentos. No se genera CSV para este simbolo.");
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

   // Diagnostico rapido de huecos intradia (detalle fino se hace despues en Python)
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
   Print("=== Export_FX6_M15: inicio ===");
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

   Print("\n=== Export_FX6_M15: fin -- ", ok, " simbolos exportados correctamente, ",
         fallidos, " fallidos ===");
  }
//+------------------------------------------------------------------+
