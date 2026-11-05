# Firmas de futuros: bots, horario y drawdown (búsqueda 29-oct-2026; fuentes de terceros, NO verificadas en las firmas)
Fuente principal: prop-memo.com (21-25 sept 2026, 28 firmas; parte final del texto llegó resumida). Secundaria: algopropfirms (mayo 2026).
- Ninguna firma de las fuentes permite claramente a la vez bots desatendidos y mantener posiciones de noche → la cartera B no es operable hoy.
- Automatización permitida (nivel A): Lucid (cierre 16:45 según revisión anterior), BluSky, FundedNext Futures, MyFundedFutures (cierre 16:10),
  FTMO Futures (cierre forzado 5:10 JST ≈ 16:10 NY; estrategia propia), Funded Futures Network (a discreción).
- Con condiciones (nivel B): Tradeify (prueba de autoría; 16:45), TradeDay (sin VPS; 16:50), Topstep (API; sin VPS), Bulenox, The Trading Pit.
- Prohíben: Apex (según la fuente más reciente), Elite Trader Funding (salvo aprobación escrita), The5ers Futures, Earn2Trade, E8, etc.
- Drawdown: casi todas EOD arrastrado ~2.000 $ en 50K; fijo solo Phidias Express (650 $; semi-automático).
- No consta en ninguna fuente qué firmas ofrecen MBT/MET, NKD o HG: hay que preguntarlo.
Para la cartera A (salida 16:45) encajan Lucid, Tradeify y TradeDay; con firmas de cierre 16:10 el oro del viernes se recorta.

## Firmas para la cartera B (29-oct-2026)
- Ninguna confirmada para la B completa (noches + bitcoin 17-19 NY + bots). Permiten noches: Elite Trader Funding Diamond Hands (bots solo
  con permiso escrito), Phidias Premium (semi-automático), Alpha Futures (solo cuenta real Prime; semi-automático), Goat (marca de
  futuros con examen EOD; política de bots desconocida).
- Con 50.000-150.000 $ la cesta E12 no se opera por capital, y lo que más aporta de B es salir a las 16:55-16:59. **Tradeify**: sus
  páginas dicen cierre a las 16:59 NY (FundedSim dice 16:45: contradicción, confirmar), sin cripto, bots propios con prueba de autoría
  (prop-memo). B sin bitcoin en 50K: Sharpe 2,22 con control de volatilidad (A: 1,85). Apex cierra a las 16:59 pero prohíbe bots.

## Respuesta de Tradeify (asistente de IA de Tradeify, 30-oct-2026; pegada por el usuario)
- Select 300K V2 (edición limitada): 349 $, KYC antes de comprar, máx. 3 de por vida (V1+V2), sin resets, fuera del límite de 15
  evaluaciones/30 días; las 300K fondeadas pueden sumarse a las demás hasta 8 fondeadas en total.
- Select 150K: 459 $ pago único, reset 299 $, consistencia en evaluación 40 % (opcional 50 %); al aprobar se elige Flex o Daily.
- Máx. 5 fondeadas activas (+ hasta 3 de 300K = 8). Plataformas: Tradovate, Rithmic, WealthCharts, TradingView (vía Tradovate).
- SIN responder: bots, hora de cierre, productos (MGC, SIL, MJY, MHG, NKD), drawdown de 150K/300K, topes de cobro.
Efecto de la consistencia del 40 % en el bot (simulación, 150K, 0,65 %): aprobar tarda ~3,2 meses en vez de 2,4 (backtest) y ~4,5 en
vez de 3,1 (al 60 %); con la opción del 50 %: 2,8 / 3,6 meses. No cambia la probabilidad de aprobar.

## Segunda respuesta de Tradeify (asistente de IA, 05-nov-2026)
- Bots: permitidos si la estrategia es propia y exclusiva, no compartida, no HFT, con prueba de autoría si la piden. Regla de
  microscalping (fondeada): > 50 % de operaciones y beneficio en operaciones de > 10 s (el bot cumple de sobra).
- Sesión 18:00 → 17:00 ET; no hay hora de cierre específica por contrato.
- Productos: MGC sí; **SIL no (solo SI grande)**; MJY, 6J, MHG, NKD **no confirmados**.
- Select 150K Flex: DD 4.500 $ EOD, sin límite diario, cobro tras 5 días ganadores ≥ 250 $, máx. 50 % del beneficio y 4.500 $.
- Select 150K Daily: DD 3.500 $ EOD, límite diario 1.750 $, cobro diario sobre colchón de 3.600 $, máx. 2.500 $.
- Select 300K Daily: DD 6.000 $ EOD, límite diario 3.000 $, colchón 6.100 $, máx. 4.000 $/día. 300K Flex: día ganador ≥ 750 $,
  máx. 50 % del beneficio y 10.000 $ por cobro (DD no indicado).
Cartera posible en Tradeify (solo MGC + SI): Sharpe 2,01 en 150K (~117 ops/año en ~63 días) y 2,00 en 300K (con C93 y C99).
Recomendación: planes Flex (sin límite diario); Daily obliga a ≤ 0,3 % (150K) o ≤ 0,2 % (300K) por el límite diario.

## Tercera respuesta de Tradeify (asistente de IA, 05-nov-2026)
- 6J ✅, HG ✅, NKD ✅; MJY y MHG ❌ (solo contratos grandes). Select 300K Flex: DD 8.000 $ EOD (aplicado en tiempo real).
- Límite diario = suspensión blanda: pausa el resto del día, no suspende la cuenta.
Cartera Tradeify: 150K oro + plata SI + yen 6J + Nikkei NKD → Sharpe 2,37 (~140 ops/año en ~72 días); 300K + oro diario → 2,38
(~555 ops/año en ~242 días). El cobre HG (10 × MHG) no cabe ni en 300K (necesitaría ~600.000 $).
Configuración del bot en Tradeify: InstPlata = SI, InstYen = 6J, InstNikkei = NKD, Operar cobre = false, bitcoin y cesta E12 = false.
