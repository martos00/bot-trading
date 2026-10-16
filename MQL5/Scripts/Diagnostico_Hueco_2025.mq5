//+------------------------------------------------------------------+
//|                                  Diagnostico_Hueco_2025.mq5      |
//|  Script de DIAGNÓSTICO (no opera nada). Objetivo: distinguir si   |
//|  el hueco de 38 días hábiles en USTEC/US500 (16-jul a 9-sep-2025) |
//|  es una ausencia real en el SERVIDOR del bróker o solo una falta |
//|  de sincronización del historial LOCAL del terminal -- el        |
//|  usuario señaló correctamente que 3 exports con el mismo hueco no |
//|  descartan que los 3 vinieran del mismo caché local, nunca         |
//|  verificado contra el servidor directamente.                     |
//|                                                                    |
//|  Usa funciones MQL5 nativas para esto en vez de depender de la UI |
//|  (History Center/F2 no existe igual en todas las builds de MT5,  |
//|  según el propio usuario señaló):                                 |
//|   - SERIES_SERVER_FIRSTDATE vs SERIES_TERMINAL_FIRSTDATE: compara |
//|     lo que el SERVIDOR dice tener vs lo que el terminal ya tiene  |
//|     sincronizado localmente.                                      |
//|   - SERIES_SYNCHRONIZED: si la serie está sincronizada con el     |
//|     servidor en este momento.                                      |
//|   - CopyRates() con un rango ESTRECHO (solo la ventana del hueco)  |
//|     en vez de un rango enorme -- fuerza una sincronización        |
//|     específica de ese tramo si el terminal está conectado.        |
//|   - CopyTicksRange() para el mismo tramo -- los ticks a veces      |
//|     están disponibles por separado de las barras agregadas.       |
//|                                                                    |
//|  REQUISITO: el terminal debe estar CONECTADO en línea (no en modo  |
//|  fuera de línea/replay) para que estas peticiones puedan llegar al |
//|  servidor -- si TerminalInfoInteger(TERMINAL_CONNECTED) da false,  |
//|  el resultado de este script no es concluyente.                   |
//+------------------------------------------------------------------+
#property copyright "Bot Trading"
#property version   "1.00"
#property strict
#property script_show_inputs

input string   InpSimbolos     = "USTEC,US500";
input datetime InpVentanaDesde = D'2025.07.01 00:00:00';
input datetime InpVentanaHasta = D'2025.09.15 00:00:00';
input int      InpMaxIntentos  = 15;
input int      InpEsperaMs     = 2000;

string EstadoConexion()
  {
   bool conectado = TerminalInfoInteger(TERMINAL_CONNECTED);
   return conectado ? "CONECTADO en línea" : "**NO CONECTADO** (modo fuera de línea -- este diagnóstico NO es concluyente así)";
  }

void DiagnosticarSimbolo(const string sym)
  {
   PrintFormat("\n========== %s ==========", sym);
   PrintFormat("Estado del terminal: %s", EstadoConexion());

   if(!SymbolSelect(sym, true))
     {
      PrintFormat("[%s] ERROR: no se pudo seleccionar el símbolo.", sym);
      return;
     }

   ENUM_TIMEFRAMES temporalidades[] = {PERIOD_D1, PERIOD_H1, PERIOD_M1};
   for(int t = 0; t < ArraySize(temporalidades); t++)
     {
      ENUM_TIMEFRAMES tf = temporalidades[t];
      string nombreTf = EnumToString(tf);

      // 1) Forzar una comprobación/sincronización llamando primero a Bars() y
      //    SeriesInfoInteger -- esto por sí solo puede disparar una sincronización
      //    en segundo plano si el terminal está conectado.
      int disponibles_inicial = Bars(sym, tf);
      bool sincronizada_antes = (bool)SeriesInfoInteger(sym, tf, SERIES_SYNCHRONIZED);

      datetime servidorPrimera = (datetime)SeriesInfoInteger(sym, tf, SERIES_SERVER_FIRSTDATE);
      datetime terminalPrimera = (datetime)SeriesInfoInteger(sym, tf, SERIES_TERMINAL_FIRSTDATE);

      PrintFormat("[%s %s] Barras ya cacheadas localmente: %d | Sincronizada=%s | "
                  "Primera fecha SEGÚN SERVIDOR=%s | Primera fecha ya en TERMINAL=%s",
                  sym, nombreTf, disponibles_inicial, sincronizada_antes ? "sí" : "no",
                  servidorPrimera > 0 ? TimeToString(servidorPrimera, TIME_DATE) : "desconocida",
                  terminalPrimera > 0 ? TimeToString(terminalPrimera, TIME_DATE) : "desconocida");

      // 2) Petición ESTRECHA, dirigida solo a la ventana del hueco -- con
      //    reintentos y espera, para dar tiempo a una sincronización real con
      //    el servidor (no solo leer lo que ya hay en caché).
      MqlRates rates[];
      ArraySetAsSeries(rates, false);
      int copiados = -1;
      for(int intento = 0; intento < InpMaxIntentos; intento++)
        {
         copiados = CopyRates(sym, tf, InpVentanaDesde, InpVentanaHasta, rates);
         if(copiados > 0)
            break;
         ResetLastError();
         Sleep(InpEsperaMs);
        }
      bool sincronizada_despues = (bool)SeriesInfoInteger(sym, tf, SERIES_SYNCHRONIZED);

      if(copiados > 0)
         PrintFormat("[%s %s] Petición ESTRECHA al rango 2025-07-01/2025-09-15: %d barras devueltas "
                     "(primera=%s, última=%s) -- SÍ HAY DATOS en ese tramo para esta temporalidad.",
                     sym, nombreTf, copiados, TimeToString(rates[0].time, TIME_DATE),
                     TimeToString(rates[copiados - 1].time, TIME_DATE));
      else
         PrintFormat("[%s %s] Petición ESTRECHA al rango 2025-07-01/2025-09-15: 0 barras tras %d intentos "
                     "(sincronizada antes=%s, después=%s) -- sin datos para esta temporalidad en ese tramo.",
                     sym, nombreTf, InpMaxIntentos, sincronizada_antes ? "sí" : "no", sincronizada_despues ? "sí" : "no");
     }

   // 3) Ticks crudos para la misma ventana -- a veces disponibles aunque las
   //    barras agregadas no lo estén (o viceversa).
   MqlTick ticks[];
   ResetLastError();
   int nTicks = CopyTicksRange(sym, ticks, COPY_TICKS_ALL, (ulong)InpVentanaDesde * 1000, (ulong)InpVentanaHasta * 1000);
   if(nTicks > 0)
      PrintFormat("[%s] CopyTicksRange en el mismo rango: %d ticks devueltos -- primer tick=%s, último=%s.",
                  sym, nTicks, TimeToString(ticks[0].time, TIME_DATE | TIME_SECONDS),
                  TimeToString(ticks[nTicks - 1].time, TIME_DATE | TIME_SECONDS));
   else
      PrintFormat("[%s] CopyTicksRange en el mismo rango: 0 ticks (error %d) -- tampoco hay datos a nivel de tick.",
                  sym, GetLastError());
  }

void OnStart()
  {
   Print("=== Diagnóstico de hueco 2025-07-01/2025-09-15 -- NO opera nada, solo consulta historial ===");
   PrintFormat("Estado del terminal AL INICIO: %s", EstadoConexion());
   if(!TerminalInfoInteger(TERMINAL_CONNECTED))
      Print(">>> ADVERTENCIA: el terminal no está conectado en línea ahora mismo. "
            "Conecta la cuenta y vuelve a ejecutar este script para que el resultado sea concluyente.");

   string partes[];
   int n = StringSplit(InpSimbolos, ',', partes);
   for(int i = 0; i < n; i++)
     {
      string s = partes[i];
      StringTrimLeft(s);
      StringTrimRight(s);
      DiagnosticarSimbolo(s);
     }
   Print("\n=== Diagnóstico terminado. Copia TODO el log de la pestaña 'Expertos' y pégalo tal cual. ===");
  }
