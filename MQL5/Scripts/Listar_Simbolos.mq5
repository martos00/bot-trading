//+------------------------------------------------------------------+
//| Listar_Simbolos.mq5                                              |
//| Lista TODOS los simbolos del broker (activos o no) con su ruta   |
//| y descripcion, y marca los que parecen petroleo, gas o cereales. |
//| No opera. Salida: pestana Expertos y MQL5/Files/simbolos.csv     |
//+------------------------------------------------------------------+
#property script_show_inputs
input string InpBuscar = "OIL,WTI,BRENT,CRUDE,XTI,XBR,GAS,NG,XNG,CORN,SOY,WHEAT,GRAIN,ENERG,COMMOD,AGRI";

void OnStart()
  {
   string claves[];
   int nc = StringSplit(InpBuscar, ',', claves);
   int f = FileOpen("simbolos.csv", FILE_WRITE | FILE_CSV | FILE_ANSI, ';');
   if(f != INVALID_HANDLE)
      FileWrite(f, "simbolo", "ruta", "descripcion", "coincide");
   int total = SymbolsTotal(false);
   int encontrados = 0;
   PrintFormat("Total de simbolos en el broker: %d", total);
   for(int i = 0; i < total; i++)
     {
      string s = SymbolName(i, false);
      string ruta = SymbolInfoString(s, SYMBOL_PATH);
      string desc = SymbolInfoString(s, SYMBOL_DESCRIPTION);
      string todo = s + " " + ruta + " " + desc;
      StringToUpper(todo);
      bool coincide = false;
      for(int k = 0; k < nc; k++)
        {
         string c = claves[k];
         StringTrimLeft(c);
         StringTrimRight(c);
         StringToUpper(c);
         if(c != "" && StringFind(todo, c) >= 0)
           {
            coincide = true;
            break;
           }
        }
      if(f != INVALID_HANDLE)
         FileWrite(f, s, ruta, desc, coincide ? "SI" : "");
      if(coincide)
        {
         encontrados++;
         PrintFormat("CANDIDATO: %s | %s | %s", s, ruta, desc);
        }
     }
   if(f != INVALID_HANDLE)
      FileClose(f);
   PrintFormat("Candidatos: %d. Lista completa en MQL5/Files/simbolos.csv", encontrados);
  }
//+------------------------------------------------------------------+
