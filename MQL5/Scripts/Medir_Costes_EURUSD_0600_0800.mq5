//+------------------------------------------------------------------+
//| Medir_Costes_EURUSD_0600_0800.mq5                                 |
//| Script de diagnostico para el paso 2-3 de la ventaja certificada  |
//| C1 (research/certificacion): EURUSD corto 06:00 -> 08:00 hora de  |
//| Nueva York. Mide en la cuenta del propio broker / prop firm:      |
//|  1) Spread real a las 06:00 y a las 08:00 NY (ultimo tick en los  |
//|     60 s anteriores), dia a dia, con el historico de ticks.       |
//|     No abre ninguna operacion.                                    |
//|  2) OPCIONAL (InpProbarComision=true): abre y cierra al momento   |
//|     una operacion de prueba y lee la comision cobrada en la       |
//|     entrada y en la salida (asi se sabe si es por lado o por      |
//|     operacion completa) y el deslizamiento. SOLO en cuentas DEMO: |
//|     en cualquier otra cuenta se niega a operar.                   |
//| Resultado: diario "Expertos" y MQL5/Files/costes_eurusd_0600_0800.csv |
//|                                                                    |
//| Husos: 06:00 y 08:00 NY se calculan en UTC con el horario de      |
//| verano de EEUU. La diferencia servidor-UTC se detecta sola        |
//| (TimeTradeServer - TimeGMT) y se supone que el servidor cambia de |
//| hora con EEUU (lo habitual: UTC+2 / UTC+3). Si no es asi, pon     |
//| InpServidorConDSTdeEEUU=false.                                    |
//+------------------------------------------------------------------+
#property script_show_inputs
#property strict

#include <Trade\Trade.mqh>

input string InpSimbolo              = "EURUSD";  // nombre del simbolo en esta cuenta (p.ej. EURUSD, EURUSD.r)
input int    InpDias                 = 90;        // dias naturales hacia atras para medir el spread
input bool   InpServidorConDSTdeEEUU = true;      // el servidor suma 1 h con el horario de verano de EEUU
input bool   InpProbarComision       = false;     // abrir y cerrar UNA operacion de prueba (solo demo)
input double InpLotesPrueba          = 1.0;       // lotes de la operacion de prueba (1 lote = 100.000 EUR)

// n-esimo domingo (n>=1) de un mes, como fecha a las 00:00 UTC
datetime Domingo(int anio, int mes, int n)
  {
   MqlDateTime t = {};
   t.year = anio; t.mon = mes; t.day = 1;
   datetime d = StructToTime(t);
   MqlDateTime x; TimeToStruct(d, x);
   int primero = (7 - x.day_of_week) % 7;
   return d + (primero + 7 * (n - 1)) * 86400;
  }

bool VeranoEEUU(datetime utc)   // 2.º domingo de marzo 07:00 UTC -> 1.er domingo de noviembre 06:00 UTC
  {
   MqlDateTime x; TimeToStruct(utc, x);
   return utc >= Domingo(x.year, 3, 2) + 7 * 3600 && utc < Domingo(x.year, 11, 1) + 6 * 3600;
  }

int g_offInvierno;   // hora servidor - UTC en invierno (detectada)

datetime AServidor(datetime utc)
  {
   return utc + (g_offInvierno + ((InpServidorConDSTdeEEUU && VeranoEEUU(utc)) ? 1 : 0)) * 3600;
  }

// hh:00 de Nueva York de la fecha 'dia' (00:00 UTC) expresado en UTC
datetime HoraNY(datetime dia, int hh)
  {
   datetime t = dia + (hh + 5) * 3600;        // invierno: NY = UTC-5
   if(VeranoEEUU(t - 3600)) t -= 3600;        // verano: NY = UTC-4
   return t;
  }

// spread (en pips y en pb) del ultimo tick en [T-60 s, T) con T en hora servidor; false si no hay ticks
bool SpreadEn(datetime T_srv, double pip, double &pips, double &pb)
  {
   MqlTick ticks[];
   int n = CopyTicksRange(InpSimbolo, ticks, COPY_TICKS_INFO, (ulong)(T_srv - 60) * 1000, (ulong)T_srv * 1000 - 1);
   if(n <= 0) return false;
   double a = ticks[n - 1].ask, b = ticks[n - 1].bid;
   if(a <= 0 || b <= 0) return false;
   pips = (a - b) / pip;
   pb = (a - b) / ((a + b) / 2) * 1e4;
   return true;
  }

double Percentil(double &v[], double p)
  {
   int n = ArraySize(v);
   if(n == 0) return -1;
   double c[]; ArrayCopy(c, v); ArraySort(c);
   return c[(int)MathFloor(p * (n - 1))];
  }

void ProbarComision(double pip)
  {
   if(AccountInfoInteger(ACCOUNT_TRADE_MODE) != ACCOUNT_TRADE_MODE_DEMO)
     {
      Print("PRUEBA DE COMISION CANCELADA: la cuenta no es DEMO. Este script nunca opera en cuentas reales ni de concurso.");
      return;
     }
   CTrade trade;
   trade.SetExpertMagicNumber(60800);
   double bid0 = SymbolInfoDouble(InpSimbolo, SYMBOL_BID);
   if(!trade.Sell(InpLotesPrueba, InpSimbolo, 0, 0, 0, "medir_costes_venta"))
     { Print("No se pudo abrir la venta de prueba: ", trade.ResultRetcodeDescription()); return; }
   ulong deal_in = trade.ResultDeal();
   double px_in = trade.ResultPrice();
   Sleep(2000);
   double ask1 = SymbolInfoDouble(InpSimbolo, SYMBOL_ASK);
   if(!trade.PositionClose(InpSimbolo))
     { Print("No se pudo cerrar la venta de prueba: ", trade.ResultRetcodeDescription(), " (CIERRALA A MANO)"); return; }
   ulong deal_out = trade.ResultDeal();
   double px_out = trade.ResultPrice();
   Sleep(1000);
   HistorySelect(TimeCurrent() - 3600, TimeCurrent() + 60);
   double com_in = HistoryDealGetDouble(deal_in, DEAL_COMMISSION);
   double com_out = HistoryDealGetDouble(deal_out, DEAL_COMMISSION);
   double nocional = InpLotesPrueba * SymbolInfoDouble(InpSimbolo, SYMBOL_TRADE_CONTRACT_SIZE) * px_in;
   Print("=== Operacion de prueba (", DoubleToString(InpLotesPrueba, 2), " lotes, cuenta en ", AccountInfoString(ACCOUNT_CURRENCY), ") ===");
   Print("Comision entrada: ", DoubleToString(com_in, 2), "  comision salida: ", DoubleToString(com_out, 2),
         "  total: ", DoubleToString(com_in + com_out, 2), "  = ", DoubleToString(MathAbs(com_in + com_out) / nocional * 1e4, 3),
         " pb del nocional (", DoubleToString(MathAbs(com_in + com_out) / InpLotesPrueba, 2), " por lote ida y vuelta)");
   Print("Deslizamiento venta: ", DoubleToString((bid0 - px_in) / pip, 2), " pips  recompra: ", DoubleToString((px_out - ask1) / pip, 2), " pips");
   int fh = FileOpen("costes_eurusd_comision.csv", FILE_WRITE | FILE_CSV | FILE_ANSI, ',');
   FileWrite(fh, "lotes", "comision_entrada", "comision_salida", "nocional", "comision_pb", "desliz_venta_pips", "desliz_compra_pips");
   FileWrite(fh, InpLotesPrueba, com_in, com_out, nocional, MathAbs(com_in + com_out) / nocional * 1e4, (bid0 - px_in) / pip, (px_out - ask1) / pip);
   FileClose(fh);
  }

void OnStart()
  {
   if(!SymbolSelect(InpSimbolo, true)) { Print("Simbolo no encontrado: ", InpSimbolo, ". Pon el nombre exacto que usa esta cuenta."); return; }
   double pip = (SymbolInfoInteger(InpSimbolo, SYMBOL_DIGITS) >= 4) ? 0.0001 : 0.01;
   datetime ahora = TimeGMT();
   int off = (int)MathRound((double)(TimeTradeServer() - ahora) / 3600.0);
   g_offInvierno = off - ((InpServidorConDSTdeEEUU && VeranoEEUU(ahora)) ? 1 : 0);
   Print("Servidor: UTC", (off >= 0 ? "+" : ""), off, " ahora (invierno UTC", (g_offInvierno >= 0 ? "+" : ""), g_offInvierno, ")");

   double p6[], p8[], b6[], b8[];
   int fh = FileOpen("costes_eurusd_0600_0800.csv", FILE_WRITE | FILE_CSV | FILE_ANSI, ',');
   FileWrite(fh, "dia", "pips_0600NY", "pb_0600NY", "pips_0800NY", "pb_0800NY");
   datetime hoy = ahora - (ahora % 86400);
   for(int k = InpDias; k >= 1; k--)
     {
      datetime dia = hoy - k * 86400;
      MqlDateTime x; TimeToStruct(dia, x);
      if(x.day_of_week == 0 || x.day_of_week == 6) continue;
      double a6, c6, a8, c8;
      if(!SpreadEn(AServidor(HoraNY(dia, 6)), pip, a6, c6) || !SpreadEn(AServidor(HoraNY(dia, 8)), pip, a8, c8)) continue;
      int n = ArraySize(p6);
      ArrayResize(p6, n + 1); ArrayResize(p8, n + 1); ArrayResize(b6, n + 1); ArrayResize(b8, n + 1);
      p6[n] = a6; p8[n] = a8; b6[n] = c6; b8[n] = c8;
      FileWrite(fh, TimeToString(dia, TIME_DATE), DoubleToString(a6, 2), DoubleToString(c6, 3), DoubleToString(a8, 2), DoubleToString(c8, 3));
     }
   FileClose(fh);
   int n = ArraySize(p6);
   Print("=== Spread real de ", InpSimbolo, " en ", n, " dias laborables ===");
   if(n == 0)
      Print("Sin ticks: abre el grafico de ", InpSimbolo, " en M1, desplazate hacia atras unos meses para que se descargue el historico y vuelve a ejecutar.");
   else
     {
      Print("06:00 NY  mediana ", DoubleToString(Percentil(p6, 0.5), 2), " pips (", DoubleToString(Percentil(b6, 0.5), 3), " pb)  p90 ", DoubleToString(Percentil(p6, 0.9), 2), " pips");
      Print("08:00 NY  mediana ", DoubleToString(Percentil(p8, 0.5), 2), " pips (", DoubleToString(Percentil(b8, 0.5), 3), " pb)  p90 ", DoubleToString(Percentil(p8, 0.9), 2), " pips");
     }
   Print("Contrato: ", SymbolInfoDouble(InpSimbolo, SYMBOL_TRADE_CONTRACT_SIZE), " por lote; lote minimo ", SymbolInfoDouble(InpSimbolo, SYMBOL_VOLUME_MIN),
         "; swap corto ", SymbolInfoDouble(InpSimbolo, SYMBOL_SWAP_SHORT), " (la estrategia no cruza el rollover de las 17:00 NY)");
   if(InpProbarComision) ProbarComision(pip);
   else Print("Comision no medida (InpProbarComision=false). Activala solo en la cuenta DEMO o de prueba gratuita.");
  }
