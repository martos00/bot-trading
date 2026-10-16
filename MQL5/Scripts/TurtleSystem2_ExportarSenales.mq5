//+------------------------------------------------------------------+
//|                            TurtleSystem2_ExportarSenales.mq5     |
//|  Script de VALIDACIÓN (no opera, no modifica ninguna cuenta) --   |
//|  replica en MQL5, sobre todo el histórico D1 disponible en el     |
//|  terminal, el MISMO algoritmo que                                 |
//|  research/estrategia_turtle_trading.py::ejecutar_sistema() para   |
//|  System 2 (55d/20d, sin piramidación) y exporta un CSV por        |
//|  símbolo con cada operación histórica que el motor habría tomado. |
//|                                                                    |
//|  PROPÓSITO: comparar esta salida contra el backtest de Python      |
//|  ANTES de confiar en el EA en vivo (TurtleSystem2_EA.mq5) --       |
//|  usa research/comparar_turtle_ea_vs_python.py para el cotejo       |
//|  automático. Ver protocolo completo en el README.                 |
//|                                                                    |
//|  Usa el mismo include TurtleSystem2_Core.mqh que el EA en vivo     |
//|  para los cálculos de N/canales/decisión -- la única parte NO      |
//|  compartida es el bucle de control, porque aquí se reproduce el    |
//|  algoritmo de SIMULACIÓN POR LOTES de Python (que recorre toda la  |
//|  historia de una vez), mientras que el EA reacciona vela a vela    |
//|  en tiempo real. Si hay una diferencia de señales entre ambos,     |
//|  debe venir de los DATOS (historial disponible en el bróker vs.   |
//|  HistData/MetaQuotes-Demo usado en Python) o de la ejecución en    |
//|  vivo (slippage), nunca de una regla reimplementada distinta.      |
//+------------------------------------------------------------------+
#property copyright "Bot Trading"
#property version   "1.00"
#property strict
#property script_show_inputs

#include <TurtleSystem2_Core.mqh>

input string InpSimbolos          = "XAUUSD,USTEC,US500";
input int    InpHistorialBarrasD1 = 5000;

//+------------------------------------------------------------------+
//| Replica ejecutar_sistema(d, 55, 20, point, con_piramide=False)   |
//| de Python sobre todo el histórico D1 disponible de "sym", y      |
//| escribe TurtleSystem2_Validacion_<sym>.csv en MQL5/Files/.        |
//+------------------------------------------------------------------+
void ReplayTurtleSystem2(const string sym)
  {
   MqlRates rates[];
   ArraySetAsSeries(rates, false);
   int disponibles = CopyRates(sym, PERIOD_D1, 0, InpHistorialBarrasD1, rates);
   if(disponibles < TURTLE_ENTRADA_DIAS + TURTLE_PERIODO_N + 10)
     {
      PrintFormat("[%s] Histórico D1 insuficiente (%d barras disponibles) -- no se exporta nada.", sym, disponibles);
      return;
     }

   int nTotal = disponibles;
   // nFilas excluye la última barra (shift 0 = vela D1 EN FORMACIÓN si el script se corre en horario de
   // mercado) -- igual que el CSV histórico que usa Python, donde cada fila es un día YA CERRADO.
   int nFilas = nTotal - 1;

   double high[], low[], close[], open[];
   ArrayResize(high, nTotal); ArrayResize(low, nTotal); ArrayResize(close, nTotal); ArrayResize(open, nTotal);
   for(int k = 0; k < nTotal; k++)
     {
      high[k] = rates[k].high; low[k] = rates[k].low; close[k] = rates[k].close; open[k] = rates[k].open;
     }

   double N[], canalEntAlto[], canalEntBajo[], canalSalAlto[], canalSalBajo[];
   TurtleCalcularN(high, low, close, nTotal, N);
   TurtleCalcularCanales(high, low, nTotal, TURTLE_ENTRADA_DIAS, canalEntAlto, canalEntBajo);
   TurtleCalcularCanales(high, low, nTotal, TURTLE_SALIDA_DIAS, canalSalAlto, canalSalBajo);

   string nombreArchivo = StringFormat("TurtleSystem2_Validacion_%s.csv", sym);
   int handle = FileOpen(nombreArchivo, FILE_WRITE | FILE_CSV | FILE_ANSI, ';');
   if(handle == INVALID_HANDLE)
     {
      PrintFormat("[%s] No se pudo crear '%s' (error %d).", sym, nombreArchivo, GetLastError());
      return;
     }
   FileWrite(handle, "Simbolo", "FechaEntrada", "Direccion", "PrecioEntrada", "N_entrada", "RiesgoPuntos", "StopPrice",
             "FechaSalida", "PrecioSalida", "MotivoSalida", "RetBrutoPuntos");

   int nOperaciones = 0;
   int i = (int)MathMax(TURTLE_ENTRADA_DIAS, TURTLE_PERIODO_N) + 1;
   while(i < nFilas - 1)
     {
      double nActual = N[i];
      if(nActual <= 0.0 || canalEntAlto[i] == EMPTY_VALUE)
        {
         i++;
         continue;
        }

      int direccion = TurtleEvaluarEntrada(close, canalEntAlto, canalEntBajo, i);
      if(direccion == 0)
        {
         i++;
         continue;
        }

      int idxEntrada = i + 1;
      if(idxEntrada >= nFilas)
         break;

      double precioEntrada = open[idxEntrada];
      double nEntrada = nActual;
      double stop = TurtleCalcularStopInicial(precioEntrada, nEntrada, direccion);

      int idxSalida = -1;
      string motivo = "";
      double resultado = 0.0;
      int j = idxEntrada;
      while(j < nFilas)
        {
         bool tocaStop = TurtleEvaluarStop(high[j], low[j], stop, direccion);
         if(tocaStop && j > idxEntrada)
           {
            idxSalida = j; motivo = "STOP"; resultado = stop;
            break;
           }
         if(j > idxEntrada && canalSalAlto[j] != EMPTY_VALUE)
           {
            bool tocaCanal = TurtleEvaluarSalidaCanal(close, canalSalAlto, canalSalBajo, j, direccion);
            if(tocaCanal)
              {
               int idxSalidaReal = (int)MathMin(j + 1, nFilas - 1);
               idxSalida = idxSalidaReal; motivo = "CANAL_SALIDA"; resultado = open[idxSalidaReal];
               break;
              }
           }
         j++;
        }
      if(idxSalida < 0)
        {
         idxSalida = nFilas - 1; motivo = "FIN_DATOS"; resultado = close[nFilas - 1];
        }

      double riesgoPuntos = TURTLE_STOP_EN_N * nEntrada;
      double retBruto = (direccion > 0) ? (resultado - precioEntrada) : (precioEntrada - resultado);

      FileWrite(handle, sym, TimeToString(rates[idxEntrada].time, TIME_DATE), direccion > 0 ? "largo" : "corto",
                DoubleToString(precioEntrada, 5), DoubleToString(nEntrada, 5), DoubleToString(riesgoPuntos, 5),
                DoubleToString(stop, 5), TimeToString(rates[idxSalida].time, TIME_DATE), DoubleToString(resultado, 5),
                motivo, DoubleToString(retBruto, 5));
      nOperaciones++;

      i = idxSalida + 1;
     }

   FileClose(handle);
   PrintFormat("[%s] Validación exportada: %d operaciones -> MQL5/Files/%s", sym, nOperaciones, nombreArchivo);
  }

void OnStart()
  {
   string partes[];
   int nSim = StringSplit(InpSimbolos, ',', partes);
   if(nSim < 1)
     {
      Print("ERROR: InpSimbolos está vacío o mal formado.");
      return;
     }
   for(int s = 0; s < nSim; s++)
     {
      string sym = partes[s];
      StringTrimLeft(sym);
      StringTrimRight(sym);
      if(!SymbolSelect(sym, true))
        {
         PrintFormat("ERROR: no se pudo seleccionar '%s' en Market Watch -- revisa el nombre exacto del símbolo.", sym);
         continue;
        }
      ReplayTurtleSystem2(sym);
     }
   Print("TurtleSystem2_ExportarSenales: terminado. Copia los CSV de MQL5/Files/ y compáralos con "
         "research/comparar_turtle_ea_vs_python.py antes de activar el EA en vivo.");
  }
