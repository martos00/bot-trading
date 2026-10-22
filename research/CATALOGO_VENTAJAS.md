# Catálogo de ventajas: probadas y pendientes (21-oct-2026)

Objetivo: no repetir pruebas y ordenar las que quedan por mecanismo y fecha de publicación (las recientes han tenido menos
tiempo de desaparecer). Cada prueba nueva se pre-registra antes de calcular. Contador acumulado de pruebas ≈ 1.168.

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
| SMC / ICT (barrido, MSS, FVG, oferta-demanda) | H2, Sweep-MSS-FVG MT5 | Sobreajuste; negativas |
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
| Día × hora en 15 futuros | B4 | Solo pasa el oro del viernes |
| **Gas natural jueves 09:00-10:00 NY (F1b)** | descomposición de F1 | **En forward (a posteriori, sin certificar): −12 pb, 17/17 años** |
| Reversión de fin de día (Baltussen-Da-Soebhag 2025) | — | Solo acciones individuales en sección cruzada: no operable en CFD/futuros |
| Presión por pago de dividendos (Hartzmark-Solomon 2025) | — | Sin fechas de pago gratuitas del NYSE: no probable |

## B. Pendientes (se completa con la búsqueda bibliográfica)
Búsqueda bibliográfica (agente, 21-oct-2026; casi todo a partir de resúmenes, no de textos completos: cada prueba se
contrasta con la fuente antes de pre-registrarla). Prioridad: mecanismo claro + datos gratuitos + años después de publicarse.

| Prior. | Candidata | Fuente | Mercado | Datos | Aviso |
|---|---|---|---|---|---|
| 1 | Día del informe de gas natural (jueves EIA): más del 50% de la rentabilidad anual | Prokopczuk, Wese Simen y Wichmann, Energy Journal 2021 | Gas natural | Diarios | — |
| 2 | Ciclo del FOMC: la prima de la bolsa se gana en las semanas pares | Cieslak, Morse y Vissing-Jorgensen, JF 2019 | S&P 500 | Diarios + fechas FOMC | — |
| 3 | Ventana de 3 días del FOMC en bonos largos | Hillenbrand, RFS 2025 | ZN/ZB | Diarios | Régimen de tipos bajando |
| 4 | Deriva previa a datos macro (no NFP/IPC) | Kurov et al., JFQA 2019 | ES, bonos | M1 + calendario | Posibles cambios de embargo |
| 5 | Deriva previa al BCE, BoE, BoJ y SNB | Quantpedia 2025 | DAX, FTSE, Nikkei | Diarios | Contradicha por Brusa et al. 2020 |
| 6 | Presión del pago de dividendos | Hartzmark y Solomon, AER 2025 | Índices | Calendario de pagos (no gratuito completo) | — |
| 7 | Vencimiento de futuros de BTC en el CME | Blasco et al. 2023 | BTC | Diarios | El signo cambió en 2021 |
| 8 | Rebalanceo anual de índices de materias primas (enero) | JPMorgan/Saxo (práctica) | Oro, plata | Diarios | Sin estudio académico |
| — | Con datos de pago o ya muertas: pinning de opciones, gamma de 0DTE, ETF del BoJ, Goldman roll, fixing del oro, Tether, fin de año fiscal japonés | varias | — | — | Ver informe del agente |
