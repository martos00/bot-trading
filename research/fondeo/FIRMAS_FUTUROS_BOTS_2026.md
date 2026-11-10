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

## Respuesta de Elite Trader Funding (Alex, soporte, 05-nov-2026)
- Bots: el equipo de riesgos revisa y aprueba cada estrategia; cuestionario de 5 puntos (respuesta preparada en
  `ETF_CUESTIONARIO_BOT_EN.md`).
- 1 paso: plano a las 16:59 ET (1 min antes del cierre en festivos cortos). DTF: permite noche y fin de semana.
- DTF: "3 minis (3 micros)" = 3 contratos en total, grandes o micro (relación 1:1). Máx. 5 DTF en total (todos los tamaños).
- 20 cuentas fondeadas en total, incluidas hasta 5 DTF (el límite de evaluaciones y la aprobación en varias cuentas, aparte).
- 150K: el arrastre incluye beneficio abierto; en fondeada deja de arrastrar al llegar a 5.100 $ de beneficio realizado (suelo 150.100 $).
- Cuota 150K: 34,70 $ el 1.er mes, 69,40 $ el 2.º y 104,10 $ desde el 3.º (BULLTOBER).
- Cobros lunes y miércoles, hasta el 100 % del beneficio elegible; límites por ciclo en las tablas de cada plan.
- DTF 100K: solo se retira el beneficio por encima de 105.100 $; 95.000 $ es el umbral de suspenso.

## FuturesElite (revisado 10-nov-2026): NO SIRVE
Su página oficial de prácticas permitidas pone en «Not allowed»: "Fully automated trading with AI or bots, and high-frequency trading."
(faq.futureselite.com, artículo 17584626). También prohíbe "buying many accounts and gambling until one hits" y exige avisar antes a
soporte si se usa VPN/VPS. Reseñas mixtas (quejas de cobros denegados por temas de IP/VPS).

## Elite Trader Funding — reputación y tope de cobros (revisado 10-nov-2026) — CAMBIA LOS CÁLCULOS
- Página de pagos de la firma (elitetraderfunding.app/payouts, «© 2026 Elite Trader Funding, LLC»): "Sim payout cap $25,000 per trader";
  "You keep requesting cycle after cycle until your cumulative payouts reach $25,000 per trader." Después pasa a LIVE ELITE (capital real,
  80/20, sin tope). Por ciclo: mínimo 100 $ y un máximo que crece con el tamaño y los ciclos; días activos 8 (1.er ciclo) y 10 (siguientes).
- Reseñas de terceros (sin verificar): ETF puede pasar a LIVE ELITE en cualquier momento (tras 1 cobro, 5 días activos o 1.000 $); al
  pasar se desactivan TODAS las cuentas sim y la cuenta real parte del saldo de la mejor. Trustpilot ~3,8/5 (~1.150 reseñas); quejas
  repetidas: 2.º cobro denegado y paso forzoso a cuenta real el día del cobro.
- CONSECUENCIA: las simulaciones de 20 cuentas ETF (plan_reinversion_etf.py, flota_20_etf*.py: ~460.000 $ en 2 años al 60 %) NO son
  realistas: el total cobrable en sim está limitado a 25.000 $ por persona; luego se depende de una cuenta real. Hay que confirmarlo por escrito.
- Tradeify: Trustpilot ~4,5/5 (~2.800 reseñas; quejas sobre todo del alta KYC con Rise). Tiene un «Tradeify Elite Program» (página no
  accesible): sus condiciones de paso a real y topes están SIN COMPROBAR.

## Topes y paso a cuenta real en otras firmas (búsqueda 10-nov-2026; fuentes de terceros, SIN VERIFICAR en las webs oficiales)
- Tradeify: «Elite Live» tras 10 cobros (elegible, no automático); el paso es obligatorio y cierra las cuentas sim; la cuenta real empieza
  en 0 $ (sin colchón), reparto 80 %; hasta 5 cuentas Elite.
- My Funded Futures: bots permitidos (según una fuente); tope sim 100.000 $ por persona; Rapid pasa a real con 10.000 $ en un día.
  Ya descartada por la hora de cierre (16:10 NY), que impide oro/plata del viernes.
- Apex y Phidias: la cuenta se cierra tras el 6.º cobro. TradeDay: pasa a real en el 5.º cobro. FTMO Futures: tope de 5.000 $.
Conclusión: ninguna firma permite cobrar sin límite de muchas cuentas simuladas; el modelo «20 cuentas para siempre» no existe.

## Firmas SIN bots pero operables A MANO (revisado 10-nov-2026; fuentes de terceros: crosstrade.io, proea.app)
### Take Profit Trader (TPT) — la más interesante
- Bots prohibidos en todas las cuentas: "all trades must be manually executed by the trader".
- Cierre automático 16:55 NY → sirve el MODO A (salida 16:45); la plata del viernes (16:57) no.
- PRO: reparto 80/20, cobros diarios desde el día 1, SIN tope por cobro ni de por vida (según las dos fuentes), sin regla de consistencia;
  hay que estar por encima del colchón (150K: saldo > 154.500 $). Hasta 5 cuentas PRO/PRO+ por persona.
- Copiador permitido solo entre cuentas propias y de su lista aprobada.
- PRO+ (cuenta real) por invitación: empieza en 0 $, congela 5.000 $ de la PRO, reparto 90/10, cobros diarios sin límite.
### Apex
- Bots prohibidos ("No Automation or Algorithm Usage allowed"). Cierre 16:59:59 → cartera B completa a mano.
- Cada cuenta fondeada se cierra tras 6 cobros (150K: 2.500-5.000 $ por cobro, ~20.500 $ en total por cuenta); hasta 20 cuentas (sin verificar).
- Para cada cobro: 5 días con ≥ 350 $ netos (150K) y ningún día con ≥ 50 % del beneficio desde el último cobro → choca con una estrategia
  que gana sobre todo los viernes. Copiar entre cuentas propias: no aclarado.

## Otras firmas «como Apex» (búsqueda 10-nov-2026; fuentes de terceros contradictorias, SIN VERIFICAR)
- Ninguna otra permite 10+ cuentas fondeadas a la vez: casi todas 5 (Tradeify, Lucid, TPT, TradeDay, Bulenox, Topstep, Goat).
- Bulenox: 5 cuentas en total entre productos; los 3 primeros cobros con tope y luego sin tope, pero tras 3 cobros pasa a cuenta
  «Funded» (si no aceptas, se cierra); consistencia 40 %; cobros semanales.
- TradeDay (2.0, mayo 2026): liquidación automática 15:50 CT = 16:50 NY → modo A; Quick Pay sin tope según una fuente; paso a real
  tras el 3.er cobro o 20.000 $ (a su criterio); 1 o 5 cuentas reales según la fuente.
- BluSky: liquidación 15 min antes del cierre → modo A (o justo); bots apoyados según una fuente; tope solo en el primer cobro; nº de cuentas no encontrado.
- Goat Funded Futures: bots (fuentes contradictorias); según una fuente permite mantener el fin de semana; cada cobro hasta el 50 % del
  beneficio; 5 cuentas.

## Firmas de CFD que aceptan EA (búsqueda 10-nov-2026; blogs de terceros, SIN VERIFICAR)
| Firma | EA | Capital máx. por persona | Notas |
|---|---|---|---|
| FTMO | Sí | 400.000 $ por estrategia (600K Prime / 1M Supreme) | sin aprobación previa |
| FundedNext | Sí (MT4/MT5, posible coste extra) | 300.000 $ por estrategia | lista de EA comerciales prohibidos |
| The5ers | Sí, código propio | Hyper Growth hasta 4 M$ escalando; High Stakes 500K | |
| FXIFY | Sí según una fuente (otras: aprobación / no en algunos planes) | 400.000 $ (escalado 4 M$ según una tabla) | |
| E8 Markets | Sí, incluso de terceros, si nadie más usa la misma | 500.000 $ (escalado 1 M$) | restringido en E8 Signature |
| Alpha Capital Group | Sí en MT5 con aprobación | 400.000 $ combinado | |
| FundingPips | Solo EA propio demostrable (fuentes contradictorias) | 400.000 $ (Prime hasta 2 M$) | política mal explicada |
| Blue Guardian | Sí | no encontrado | mínimo 2 min por operación |
| Maven | NO | — | prohíbe EA |
Capital inicial sumando FTMO, FundedNext, FXIFY, E8, Alpha y FundingPips: ~2,4 M$ (sin contar escalados ni The5ers).
