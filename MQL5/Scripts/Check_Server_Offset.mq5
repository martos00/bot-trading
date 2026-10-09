//+------------------------------------------------------------------+
//| Check_Server_Offset.mq5                                           |
//| Script de diagnostico (NO es un EA). Mide el offset ACTUAL entre |
//| la hora de servidor del broker y UTC real, por metodo DIRECTO    |
//| (TimeTradeServer vs TimeGMT), sin inferir nada a partir de precio|
//| ni de picos de volatilidad en torno a noticias.                  |
//|                                                                    |
//| TimeGMT() se calcula a partir de la configuracion de zona horaria|
//| del PC local -- fiable si el reloj/zona horaria del sistema esta |
//| correctamente sincronizado (NTP), que es el caso habitual. Se    |
//| imprime tambien TimeLocal() para poder contrastar manualmente    |
//| contra un reloj de referencia externo (ej. time.gov) si se quiere|
//| una segunda verificacion independiente.                           |
//+------------------------------------------------------------------+
#property script_show_inputs
#property strict

input string InpSimboloOro = "XAUUSD";   // Ticker exacto como en Market Watch
input string InpSimboloDXY = "";         // Ticker del indice dolar si existe (dejar vacio si no se conoce aun)

void OnStart()
  {
   datetime tServidor = TimeTradeServer();
   datetime tGMT       = TimeGMT();
   datetime tLocal      = TimeLocal();
   datetime tCurrent    = TimeCurrent();  // hora de la ultima cotizacion (puede retrasarse si el mercado esta cerrado)

   long offsetServidorGMT = (long)(tServidor - tGMT);

   Print("=== Check_Server_Offset: medicion DIRECTA, metodo MT5 nativo ===");
   Print("TimeTradeServer() [hora servidor, SIEMPRE actualizada]: ", TimeToString(tServidor, TIME_DATE|TIME_SECONDS));
   Print("TimeGMT()         [UTC segun reloj/zona horaria del PC local]: ", TimeToString(tGMT, TIME_DATE|TIME_SECONDS));
   Print("TimeLocal()       [hora local del PC, para contraste manual]: ", TimeToString(tLocal, TIME_DATE|TIME_SECONDS));
   Print("TimeCurrent()     [hora del ultimo tick recibido, puede no ser 'ahora' si el mercado esta cerrado]: ",
         TimeToString(tCurrent, TIME_DATE|TIME_SECONDS));
   Print("OFFSET ACTUAL servidor - UTC = ", offsetServidorGMT, " segundos = ",
         DoubleToString(offsetServidorGMT / 3600.0, 2), " horas");
   Print("");
   Print("VERIFICACION MANUAL RECOMENDADA: compara TimeLocal() arriba contra un reloj UTC/local "
         "independiente (ej. time.gov o el reloj del sistema operativo) para confirmar que el PC "
         "esta bien sincronizado -- si no lo esta, TimeGMT() tampoco sera fiable.");
   Print("");
   Print("=== Informacion de simbolos (para distinguir indice/futuro/CFD de DXY) ===");

   string simbolos[];
   int total = 2;
   ArrayResize(simbolos, total);
   simbolos[0] = InpSimboloOro;
   simbolos[1] = InpSimboloDXY;

   for(int i = 0; i < total; i++)
     {
      string s = simbolos[i];
      if(StringLen(s) == 0)
         continue;
      if(!SymbolSelect(s, true))
        {
         Print("Simbolo '", s, "' no encontrado en Market Watch / Observacion de mercado.");
         continue;
        }
      Print("--- ", s, " ---");
      Print("  Descripcion: ", SymbolInfoString(s, SYMBOL_DESCRIPTION));
      Print("  Path (categoria en el arbol de simbolos): ", SymbolInfoString(s, SYMBOL_PATH));
      Print("  Divisa base/cotizacion: ", SymbolInfoString(s, SYMBOL_CURRENCY_BASE), " / ",
            SymbolInfoString(s, SYMBOL_CURRENCY_PROFIT));
      Print("  Digitos: ", SymbolInfoInteger(s, SYMBOL_DIGITS),
            "  Tick size: ", DoubleToString(SymbolInfoDouble(s, SYMBOL_TRADE_TICK_SIZE), 8));
      Print("  Fecha de inicio/fin de contrato (0 = sin vencimiento, >0 = futuro/CFD con rollover): "
            "start=", (long)SymbolInfoInteger(s, SYMBOL_START_TIME),
            "  expiration=", (long)SymbolInfoInteger(s, SYMBOL_EXPIRATION_TIME));
     }

   if(StringLen(InpSimboloDXY) == 0)
      Print("\nAVISO: no se indico InpSimboloDXY -- revisa manualmente en Market Watch que simbolo "
            "representa el dolar (puede llamarse 'USDX', 'DXY', 'USDOLLAR', etc. segun el broker) y "
            "vuelve a ejecutar este script con ese nombre para ver su especificacion.");

   Print("=== Fin ===");
  }
//+------------------------------------------------------------------+
