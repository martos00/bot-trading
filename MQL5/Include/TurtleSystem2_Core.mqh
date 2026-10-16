//+------------------------------------------------------------------+
//|                                       TurtleSystem2_Core.mqh     |
//|  Motor de señal del Turtle System 2 CONGELADO (ver README,       |
//|  sección "Nueva fase: estrategias documentadas de traders        |
//|  sistematicos reales" y sus actualizaciones posteriores).        |
//|                                                                    |
//|  REGLAS CONGELADAS (idénticas a research/estrategia_turtle_      |
//|  trading.py, SISTEMAS['S2'], sin piramidación):                  |
//|    - Entrada: ruptura del canal Donchian de 55 días (Close del   |
//|      día i > máximo de High[i-55..i-1], o < mínimo de            |
//|      Low[i-55..i-1]) -> entra al Open del día i+1.                |
//|    - N = EMA de span 20 (alpha=2/21, igual que                   |
//|      pandas.ewm(span=20, adjust=False)) del rango verdadero       |
//|      (True Range), con TR[0] = High[0]-Low[0] (primer dato, sin  |
//|      cierre previo -- igual que el .max(axis=1, skipna=True) de  |
//|      pandas que ignora el NaN del primer Close.shift(1)).        |
//|    - Stop = precio_entrada -/+ 2*N (N medido en la barra de la   |
//|      señal, NUNCA recalculado después de la entrada).            |
//|    - Salida: ruptura del canal Donchian de 20 días en contra      |
//|      (mismo mecanismo, shift de 1 día) -> sale al Open del día   |
//|      i+1; O bien el stop, comprobado con High/Low intradía de    |
//|      CADA día desde la entrada (si ambos se cumplen el mismo      |
//|      día, el STOP tiene prioridad -- convención "SL gana en      |
//|      empate" ya usada en el resto del proyecto).                  |
//|    - 1 sola unidad, SIN piramidación (ver freeze explícito).      |
//|                                                                    |
//|  Este archivo se incluye TANTO en el EA en vivo                  |
//|  (TurtleSystem2_EA.mq5) COMO en el script de validación           |
//|  (TurtleSystem2_ExportarSenales.mq5) para garantizar que ambos    |
//|  usan EXACTAMENTE el mismo cálculo -- cualquier diferencia entre  |
//|  EA y Python debe venir de datos (historial disponible,          |
//|  ejecución en vivo) y no de una reimplementación distinta de la  |
//|  misma regla.                                                     |
//+------------------------------------------------------------------+
#property strict

#define TURTLE_ENTRADA_DIAS   55
#define TURTLE_SALIDA_DIAS    20
#define TURTLE_PERIODO_N      20
#define TURTLE_STOP_EN_N      2.0

//--- Todas las series en estas funciones usan convención "oldest-first"
//    (índice 0 = la barra MÁS ANTIGUA), igual que el DataFrame de
//    pandas tras reset_index() en estrategia_turtle_trading.py -- OJO:
//    es la convención INVERSA a ArraySetAsSeries(true) de MQL5. Quien
//    llame a estas funciones debe copiar los arrays con
//    ArraySetAsSeries(arr, false) antes de pasarlos aquí.

//+------------------------------------------------------------------+
//| True Range clásico (Wilder), fila a fila, oldest-first.          |
//+------------------------------------------------------------------+
void TurtleCalcularTR(const double &high[], const double &low[], const double &close[], const int n, double &tr[])
  {
   ArrayResize(tr, n);
   if(n <= 0) return;
   tr[0] = high[0] - low[0];
   for(int i = 1; i < n; i++)
     {
      double a = high[i] - low[i];
      double b = MathAbs(high[i] - close[i - 1]);
      double c = MathAbs(low[i] - close[i - 1]);
      tr[i] = MathMax(a, MathMax(b, c));
     }
  }

//+------------------------------------------------------------------+
//| N = EMA(span=20, adjust=False) del TR -- recursión idéntica a    |
//| pandas: y[0]=x[0]; y[i] = (1-alpha)*y[i-1] + alpha*x[i].          |
//+------------------------------------------------------------------+
void TurtleCalcularN(const double &high[], const double &low[], const double &close[], const int n,
                      double &nOut[], const int periodo = TURTLE_PERIODO_N)
  {
   double tr[];
   TurtleCalcularTR(high, low, close, n, tr);
   ArrayResize(nOut, n);
   if(n <= 0) return;
   double alpha = 2.0 / (periodo + 1.0);
   nOut[0] = tr[0];
   for(int i = 1; i < n; i++)
      nOut[i] = (1.0 - alpha) * nOut[i - 1] + alpha * tr[i];
  }

//+------------------------------------------------------------------+
//| Canal Donchian ALTO/BAJO con shift(1): canalAlto[i] = máximo de   |
//| High[i-periodo .. i-1] (bajo[i] análogo con Low), igual que       |
//| d['High'].rolling(periodo).max().shift(1) en pandas. Para         |
//| i<periodo el canal queda sin definir (se marca con EMPTY_VALUE).  |
//+------------------------------------------------------------------+
void TurtleCalcularCanales(const double &high[], const double &low[], const int n, const int periodo,
                            double &canalAlto[], double &canalBajo[])
  {
   ArrayResize(canalAlto, n);
   ArrayResize(canalBajo, n);
   for(int i = 0; i < n; i++)
     {
      if(i < periodo)
        {
         canalAlto[i] = EMPTY_VALUE;
         canalBajo[i] = EMPTY_VALUE;
         continue;
        }
      double maxH = high[i - periodo];
      double minL = low[i - periodo];
      for(int k = i - periodo + 1; k <= i - 1; k++)
        {
         if(high[k] > maxH) maxH = high[k];
         if(low[k]  < minL) minL = low[k];
        }
      canalAlto[i] = maxH;
      canalBajo[i] = minL;
     }
  }

//+------------------------------------------------------------------+
//| Resultado de evaluar la barra "idx" ya CERRADA para una posible  |
//| entrada nueva (se usa SOLO si no hay posición abierta todavía).  |
//| direccion: 0=sin señal, +1=largo, -1=corto.                      |
//+------------------------------------------------------------------+
int TurtleEvaluarEntrada(const double &close[], const double &canalEntradaAlto[], const double &canalEntradaBajo[],
                          const int idx)
  {
   if(canalEntradaAlto[idx] == EMPTY_VALUE || canalEntradaBajo[idx] == EMPTY_VALUE)
      return 0;
   if(close[idx] > canalEntradaAlto[idx]) return 1;
   if(close[idx] < canalEntradaBajo[idx]) return -1;
   return 0;
  }

//+------------------------------------------------------------------+
//| Comprueba si la barra "idx" (ya cerrada) dispara la salida por    |
//| canal en CONTRA de la direccion dada (+1 largo / -1 corto).      |
//+------------------------------------------------------------------+
bool TurtleEvaluarSalidaCanal(const double &close[], const double &canalSalidaAlto[], const double &canalSalidaBajo[],
                               const int idx, const int direccion)
  {
   if(direccion > 0)
     {
      if(canalSalidaBajo[idx] == EMPTY_VALUE) return false;
      return close[idx] < canalSalidaBajo[idx];
     }
   else
     {
      if(canalSalidaAlto[idx] == EMPTY_VALUE) return false;
      return close[idx] > canalSalidaAlto[idx];
     }
  }

//+------------------------------------------------------------------+
//| Comprueba si el High/Low intradía de una barra toca el stop.     |
//| Convención del proyecto: en caso de empate con la salida por     |
//| canal en el mismo día, el STOP tiene prioridad (se comprueba      |
//| primero por quien llama a esta función).                          |
//+------------------------------------------------------------------+
bool TurtleEvaluarStop(const double high, const double low, const double stopPrice, const int direccion)
  {
   if(direccion > 0) return (low <= stopPrice);
   return (high >= stopPrice);
  }

//+------------------------------------------------------------------+
//| Precio de stop para una nueva entrada: entrada -/+ 2N.            |
//+------------------------------------------------------------------+
double TurtleCalcularStopInicial(const double precioEntrada, const double n, const int direccion)
  {
   return (direccion > 0) ? (precioEntrada - TURTLE_STOP_EN_N * n) : (precioEntrada + TURTLE_STOP_EN_N * n);
  }
