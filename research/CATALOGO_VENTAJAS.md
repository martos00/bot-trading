# Catálogo de ventajas: probadas y pendientes (21-oct-2026)

Objetivo: no repetir pruebas y ordenar las que quedan por mecanismo y fecha de publicación (las recientes han tenido menos
tiempo de desaparecer). Cada prueba nueva se pre-registra antes de calcular. Contador acumulado de pruebas ≈ 1.168.

**27-oct-2026: auditoría de la hora de HistData** (`research/certificacion/AUDITORIA_HORA_HISTDATA.md`): las confirmaciones con HistData medían una hora antes en verano. Corregido: todas las ventajas certificadas siguen confirmadas (casi todas más fuertes); dos descartadas pasan a candidatas (EURUSD Q+1 15-16 NY; Nikkei Q+2 15-16 NY), pendientes de otra fuente.

## A. Ya probadas
| Familia | Pruebas | Resultado |
|---|---|---|
| **Divisa local débil en su horario (Breedon-Ranaldo)** | C1, C3, R1, E1 | **EUR/USD mañana europea: CERTIFICADA (única operable)**; GBP certificada pero repite la del euro |
| Dólar débil en horario de EE. UU. | C3, C4 | No supera corrección por pruebas |
| Asia invertida (yen/AUD en su horario) | C5, P3 | Yen: existe sin costes, no operable con costes |
| Cripto 21-23 UTC (Quantpedia) | C2, H78 | Certificada; costes de fondeo > ventaja |
| Fixings FX diarios (Krohn-Mueller-Whelan) | H71, H73 | Desaparece tras 2019; Tokio era artefacto del BID |
| Fixing de fin de mes con cobertura de RV (Melvin-Prins) | C6 | No certificada |
| Gotobi USD/JPY (Bessho et al.) | C10 | Real 2003-2022; no rentable desde su publicación (2023) |
| Prima del dólar en días FOMC (Mueller et al.) | C10 | No certificada |
| Días FOMC / pre-FOMC en bolsa | N2, hipótesis FOMC | Decae después de 2010 |
| Cambio de mes y víspera de festivo | C7, turno de mes | No certificadas |
| Dash for Cash (Etula et al.) | C13 | La presión vendedora desaparece tras 2013 |
| Ciclo de subastas del Tesoro (Lou-Yan-Zhang) | C8 | Desaparece tras 2013 con el futuro real |
| Fin de mes en bonos (Hartley-Schwarz) | C12 | ZN no; ZF sí 2019-2023, se apaga desde 2024 |
| Rebalanceo 60/40 (Harvey et al.) | H72 | No confirmada fuera de muestra |
| Impulso intradía última media hora (Gao; Baltussen; con GEX) | H69, C11 | No supera costes |
| Overnight drift (Boyarchenko et al.) | documental | Los autores informan de que es ≈ 0 desde 2021 |
| Noise Area / ORB (Zarattini et al.) | H74, H76, ORB | Débil o desaparecida tras publicación |
| Connors / RSI(2) / IBS / Bollinger / VWAP / reversión asiática | H75, P1, G1, varios | Negativas o rompen la pérdida diaria |
| Perfil de mercado: regla del 80% y setups de zona de valor | C9, C14 | Regla del 80%: candidata débil (solo S&P 2018-26); resto negativo |
| SMC / ICT (barrido, MSS, FVG, oferta-demanda; modelo TJR de NY) | H2, Sweep-MSS-FVG MT5, C74 | Sobreajuste; negativas (C74: bruto negativo en ES, EURUSD y oro) |
| Trend following, TSMOM, carry, value, momentum, COT, REER | H70, varias, AQR | Sin ventaja desde 2012 |
| VIX (estructura de plazos, reversión), oro y tipos reales, materias primas → FX | N1, N3, varias | Negativas |
| Barridos de franjas horarias en 17+ mercados | B1, H80 | Solo artefactos del BID |
| Oro en Tokio (Donati-Jung) | H77 | Desaparece fuera de muestra |
| Optimización MT5 Supply-Demand/RSI | Validación | Sobreajuste |
| Base del VIX (Simon-Campasano) | C35 | No certificada (t 0,19; colas de −12 pt) |
| Basis-momentum en materias primas (Boons-Prado 2019) | C34 | Fuerte hasta 2014 (t 2,8), muerto después (t 0,18) |
| Adelantarse al Goldman roll (Mou 2011) | C36 | Desaparecido en ambas ventanas |
| Hueco de apertura del ES ("los huecos se cierran"; Berkman et al.) | C37 | Bruto 0 pb: sin ventaja |
| MOM-TOM: tendencia en cambio de mes (Van Hemert 2014) | C38 | Días TOM negativos |
| Día de la semana en 27 futuros | B3 | Las 2 seleccionadas desaparecen |
| Rebote tras el fixing del BCE (14:15 Frankfurt) | C39 | Existe (+0,34 pb) pero < coste (0,84 pb) |
| Efecto otoño del oro (Baur 2013) | C40 | Invertido tras publicarse (t −2,88) |
| E1 con órdenes limitadas | E5 | Peor (selección adversa): se queda a mercado |
| Reloj de E1 en semanas de desfase horario | E6 | Apunta a Frankfurt, sin significación: se mantiene NY |
| Hora previa al informe EIA en el crudo (comprobación del mecanismo de F1b) | C41 | Nada: el patrón es propio del gas |
| Reversión semanal en sección cruzada de divisas | C42 | Nada (t −0,19) |
| Gas tras el informe EIA: deriva o reversión | C43 | El signo cambia entre periodos |
| Estacionalidad del mismo mes en materias primas (KLN 2016) | C44 | Invertida (t −3,43); no se invierte la regla |
| **Oro largo viernes 16:00-16:55 NY** | B4 + C45 + E8 | **CERTIFICADA (2.ª ventaja)**: futuro t 4,38 en 2018-26, 9/9 años; contado independiente t 3,78; Sharpe 1,0-1,5 según coste |
| Oro viernes con salida 16:45 NY (horario de FTMO) | E8b | **Pasa**: futuro +2,26 pb en 2018-26 (t 3,68), contado t 3,76; neto ≈ +0,8 pb; EA `InpE8_Salida = 1645` |
| Continuación 5 min tras noticias (FOMC, rueda de prensa, NFP) en oro y EURUSD | C76 | Nada; informativo: reversión tras la rueda de prensa del FOMC (|t| ≈ 2, n ≈ 60) |
| Momentum de horas tras EIA (WTI) y tras NFP/FOMC (EURUSD) | C77 | Nada (con la hora de HistData corregida; FXCM tampoco) |
| Candidatas de la auditoría: EURUSD Q+1 15-16 NY; Nikkei Q+2 15-16 NY | C78 | EURUSD: FXCM confirma 2012-26 (t 4,15) pero no existía en 2003-11 → no certificada. **Nikkei: pasa C60 con la hora corregida (t 4,12, 15/16 años)**: falta medir coste en FTMO |
| El dólar tras las subastas del Tesoro (FX) | C79 | Nada (t ≈ 0 en 800 subastas) |
| Bolsa local antes de BoJ, BoE y RBA (Quantpedia 2025) | C80 | **BoE → FTSE pasa** (+31,5 pb D−2..D−1, t 2,31; ICE y Yahoo coinciden): candidata, sin validación posterior a la publicación. BoJ (t 2,07, débil desde 2018) y RBA no |
| Deriva previa al FOMC en FTSE, DAX, Nikkei y ASX | C81 | FTSE pasa en HistData (t 2,57) pero Yahoo (t 1,86) e ICE (t 0,86) no confirman; resto no pasa. Patrón débil |
| Nasdaq 01:00-03:00 NY diario (overnight drift, candidata de B2) | C82 | Fuerte 2010-2021 (t 4,17); tras publicarse +0,58 pb (t 1,02) < coste: no |
| **Oro corto D−2 09:30-10:00 NY** y **Nikkei corto Q−2 20:00-21:00 NY** (candidatas de futuros B18/B14) | C83 | **Pasan con HistData** (oro +6,3 pb t 3,08; Nikkei +13,6 pb t 4,08): E15/E16 en el EA, desactivadas hasta medir coste |
| Minutos previos a la liquidación diaria (GC, SI, ES; todos los días y fin de mes) | C84 | Nada; S&P fin de mes −6 pb hasta 2017, casi desaparecido |
| Noche frente a día en 13 futuros de metales, energía y cereales | C85 | Nada (solo ZM noche en descubrimiento; no confirma) |
| Momentum de la última media hora (Baltussen 2021) en oro y plata | C86 | Existía (plata t 3,83 total) pero nulo/negativo desde 2021 |
| Calendario × 30 min en 22 futuros del CME, solo ventanas de fondeo de futuros (QuantConnect, 11.220 reglas) | B22 | Nada: 6 seleccionadas en 2012-17, ninguna confirma |
| Pinning al strike de mayor interés abierto el día de vencimiento de opciones (oro, crudo; QuantConnect) | C87 | Oro +11 pb hasta 2018 y −11 pb desde 2019; crudo negativo: no |
| **Plata en víspera de festivo con salida 16:45 (para fondeo de futuros)** | E10b | **Pasa** con HistData (+3,4 pb, t 2,42; 2018-26 +4,5); solo en futuros (en CFD el spread la mata) |
| Bitcoin 21-23 UTC recortado a la ventana del CME (fondeo de futuros) | C90 | +1,5 pb (t 0,91) < coste del MBT: no |
| Régimen de gamma de opciones del oro (GEX) y dirección intradía | C88 | No (−1,25 pb; al revés de la teoría) |
| Cripto 21-23 UTC en SOL, XRP (y LTC, ADA, BNB informativos) | C91 | No: el efecto es general pero tras publicarse solo es significativo en BTC, ETH y BNB |
| Presión antes del pago de funding de perpetuos (BTC, ETH) | C92 | No pasa; BTC 16:00 UTC (+8,9 pb, t 2,18) y ETH 08:00 (+7,6, t 1,96) desde 2023, a vigilar |
| Oro: ruptura del máximo/mínimo de la sesión anterior (vídeo TikTok mgp.quant), ventana 08-15 NY, cierre 17:00 (o 16:45) | C93 | Pasa al límite: HistData +3,5 pb (t 2,80), GC +2,95 (t 2,24); válida también 2010-19 (fuera de la muestra del vídeo). Variante 07-14 NY no confirmada en GC (t 1,96). Sharpe neto ~0,4; 2026 negativo en GC |
| Gamma de las 0DTE del S&P (SPXW) y el ES 15-16 NY | C89 | +0,36 pb (t 0,40): no |
| Ruptura del día anterior (regla C93-B) en SI, CL, 6E, 6B, 6J, 6A, 6C, 6S, NKD | C94 | Ninguno pasa; SI y NKD positivos sin significación en la fuente principal |
| ETF apalancados de energía: continuación 14:00-14:30 NY antes de la liquidación (NG, CL; controles HO, RB) | C95 | NG pasa justo (+4,79 pb, t 2,75; coste 4 pb), candidata sin 2.ª fuente; 2026 negativo. CL no |
| Continuación antes de la liquidación en ZB, ZN, ZC, ZS, ZW, HG | C96 | Ninguno; ZN real (+0,58 pb, t 4,29) pero < coste 1,8 pb |
| Nikkei última media hora de Tokio (ETF apalancados japoneses) | C97 | −0,29 pb desde 2018: no |
| «El hueco del CME de bitcoin se cierra» (BTC, ETH) | C98 | Pierde: −32 pb (BTC); 55 % se cierran el lunes pero los no cerrados pierden más |
| **Ruptura del rango asiático (London breakout)** en oro, EURUSD, GBPUSD, USDJPY | C99 | **Oro pasa** (+3,58 pb t 3,98; GC 1 h +2,80 t 3,11); divisas no confirman |
| Bitcoin: seguir el movimiento del fin de semana (espejo de C98), con Bitstamp 2012-17 no visto | C100 | −16,5 pb fuera de muestra: no |
| Día × hora en 15 futuros | B4 | Solo pasa el oro del viernes |
| **USDJPY largo el antepenúltimo día hábil del mes, 07:00-08:00 NY** | B7 + C48 + E9 | **CERTIFICADA (3.ª ventaja)**: futuro t −4,82 en 2018-26; contado FXCM neto +2,76 pb (t 4,55), 13/15 años; Sharpe 1,1 |
| **Plata larga la última hora antes de un festivo de la NYSE** | B8 + C49 + E10 | **CERTIFICADA (4.ª ventaja)**: futuro t 3,84 en 2018-26, 100 % de años; contado t 2,35; Sharpe ~1,0 |
| **EURJPY corto el último día hábil del trimestre, 01:00-02:00 NY** | B13 + C54 + E11 | **CERTIFICADA (5.ª ventaja)**: FXCM t −3,37 en 2019-26; HistData +2,46 pb (t 2,86); 14/15 años; solo 4 operaciones/año |
| Día × hora en 15 futuros nuevos / 13 divisas | B5, B6 | Nada nuevo |
| Bancos centrales, festivos extranjeros, hora condicionada, calendario en divisas | B9-B12 | Nada nuevo |
| Dosis-respuesta de los metales con la duración del cierre | C50 | **Pasa (t 7,71)**: refuerza el mecanismo de E8/E10 |
| Metales al reabrir y durante el fin de semana; yen a fin de trimestre | C51-C53 | No |
| EURUSD primer día del trimestre; gasóleo penúltimo día del trimestre | B13/C54 | Falso positivo / sin confirmar |
| Yen de fin de trimestre frente a todos; en 2003-2011; yen de fin de mes en 2003-2011 | C55, C57, C58 | **Pasan**: refuerzan E9 y E11 |
| Yen en fin de mes normal; metales antes de cierres anticipados | C59, C56 | No (C56b informativo apoya el oro) |
| Nikkei 2.º día del trimestre (NKD) | B14/C60 | Falso positivo (precio rancio del NKD) |
| CFD de índices × calendario; cripto × calendario (incluye fin de semana) | B15, B16 | Nada |
| Niveles redondos (Osler) | C61 | Nada (bruto 0) |
| Valor relativo oro/plata y Brent/WTI | C62, C63 | Brent/WTI era artefacto de los CFD; oro/plata no |
| Adelanto entre mercados (1 h) y días extremos | B17 | Nada |
| **Materias primas no metálicas en víspera de festivo (Fabozzi-Ma-Briley 1994)** | C69 + C70 + E12 | **6.ª ventaja (prudente)**: 2000-09 +28 pb (t 2,89, 9/10 años); 2010-26 +12 pb (t 1,85, 13/17); aporta +0,04 a la cartera |
| Flujos programados (MSCI, Russell, triple hechicería, VIX, dividendos JP) | C64 | Nada (triple hechicería cerca: t −2,54) |
| Ventanas a 30 min de las ventajas certificadas | E13 | Ya eran casi óptimas; solo E11 pasa a 00:30-02:00 |
| Calendario × 30 min en 13 divisas, oro, plata y S&P | B18, B19 | Nada nuevo; plata viernes 16:30-17:00 (t 4,31) falla solo por coste |
| Materias primas el día después del festivo | C71 | Signo inestable |
| Mercados de ICE (cacao, café, azúcar, algodón, Brent, gasóleo, FTSE, gilt) | B21, C72, C73 | Nada certificado; FTSE Q−2 01-02 NY candidato débil |
| Última media hora antes del cierre en 16 futuros | B20 | Platino +2,1 pb (t 3,38, 14/17): confirma el mecanismo, pero < coste; resto nada |
| Metales y VIX; franco fin de mes; divisas refugio antes del cierre; cereales viernes verano | C65-C68 | C65 apoya el mecanismo pero no mejora el tamaño; el resto no |
| Refugios no metálicos y paladio el viernes | C46, C47 | No: el efecto del viernes es del oro (y algo plata/platino) |
| **Gas natural jueves 09:00-10:00 NY (F1b)** | descomposición de F1 | **En forward (a posteriori, sin certificar): −12 pb, 17/17 años** |
| Reversión de fin de día (Baltussen-Da-Soebhag 2025) | — | Solo acciones individuales en sección cruzada: no operable en CFD/futuros |
| Presión por pago de dividendos (Hartzmark-Solomon 2025) | — | Sin fechas de pago gratuitas del NYSE: no probable |
| Acciones de FTMO alrededor de resultados: subida previa, prima del anuncio, deriva posterior (Frazzini-Lamont; Barber et al.; PEAD) | C75 | Nada: prima solo hasta 2018; subida previa < coste; deriva no significativa |

## B. Pendientes (se completa con la búsqueda bibliográfica)
Búsqueda bibliográfica (agente, 21-oct-2026; casi todo a partir de resúmenes, no de textos completos: cada prueba se
contrasta con la fuente antes de pre-registrarla). Prioridad: mecanismo claro + datos gratuitos + años después de publicarse.

| Prior. | Candidata | Fuente | Mercado | Datos | Aviso |
|---|---|---|---|---|---|
| 1 | Día del informe de gas natural (jueves EIA): más del 50% de la rentabilidad anual | Prokopczuk, Wese Simen y Wichmann, Energy Journal 2021 | Gas natural | Diarios | — |
| 2 | Ciclo del FOMC: la prima de la bolsa se gana en las semanas pares | Cieslak, Morse y Vissing-Jorgensen, JF 2019 | S&P 500 | Diarios + fechas FOMC | — |
| 3 | Ventana de 3 días del FOMC en bonos largos | Hillenbrand, RFS 2025 | ZN/ZB | Diarios | Régimen de tipos bajando |
| 4 | Deriva previa a datos macro (no NFP/IPC) | Kurov et al., JFQA 2019 | ES, bonos | M1 + calendario | Posibles cambios de embargo |
| 5 | ~~Deriva previa al BCE, BoE, BoJ y SNB~~ → probada en C18 y C80 | Quantpedia 2025 | DAX, FTSE, Nikkei | Diarios | BoE candidata |
| 6 | Presión del pago de dividendos | Hartzmark y Solomon, AER 2025 | Índices | Calendario de pagos (no gratuito completo) | — |
| 7 | Vencimiento de futuros de BTC en el CME | Blasco et al. 2023 | BTC | Diarios | El signo cambió en 2021 |
| 8 | Rebalanceo anual de índices de materias primas (enero) | JPMorgan/Saxo (práctica) | Oro, plata | Diarios | Sin estudio académico |
| — | Con datos de pago o ya muertas: pinning de opciones, gamma de 0DTE, ETF del BoJ, Goldman roll, fixing del oro, Tether, fin de año fiscal japonés | varias | — | — | Ver informe del agente |
