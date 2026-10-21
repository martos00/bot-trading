# Pre-registro C6 — Cobertura de renta variable en el fixing de Londres de fin de mes (Melvin y Prins 2015)

Redactado y enviado a git ANTES de descargar los índices y de calcular ningún resultado (21-oct-2026).

## Fuente y mecanismo
Melvin, M. y Prins, J. (2015), "Equity hedging and exchange rates at the London 4 p.m. fix", *Journal of Financial
Markets* 22, 50-72. **No he podido leer el texto completo** (ScienceDirect devuelve 403); lo que sigue se basa en el
resumen publicado y en citas de otros trabajos: la subida de la bolsa de un país durante el mes predice que su divisa se
deprecia antes del fixing de las 16:00 de Londres del último día del mes, con cierta reversión después. Mecanismo: los
inversores internacionales cubren el riesgo de divisa de sus carteras de acciones y ajustan la cobertura una vez al mes, en
el fixing de fin de mes. Si las acciones extranjeras de un inversor de EE. UU. han subido, tiene que vender más divisa
extranjera; si las acciones de EE. UU. de un inversor extranjero han subido, tiene que vender más dólares. El flujo neto
depende de la rentabilidad relativa de las dos bolsas.

**Distinto de lo ya probado:** H71 (fixings diarios de KMW 2024, todos los días, sin señal) y H72 (rebalanceo 60/40 de
acciones contra bonos) no usan esta señal ni este evento.

## Regla (una sola especificación, sin alternativas)
- **Día:** último día laborable (lunes-viernes) del mes con datos a las dos horas.
- **Señal para cada divisa X frente al USD:** S = R_X − R_EEUU, donde R es la rentabilidad del índice bursátil en moneda
  local desde el cierre del último día del mes anterior hasta el cierre del **día laborable anterior** al día de la
  operación (dato conocido antes de entrar; sin mirar el futuro).
  Índices (Yahoo, precio): EE. UU. ^GSPC; EUR ^STOXX50E; GBP ^FTSE; JPY ^N225; CHF ^SSMI; AUD ^AXJO.
- **Posición:** si S > 0 (la bolsa extranjera lo hizo mejor) → **comprar USD** frente a X; si S < 0 → vender USD.
- **Ventana:** entrada a las **14:00 de Londres**, salida a las **16:00 de Londres** (hora de Londres con su horario de
  verano). Precio = cierre del último minuto que termina en o antes de la hora (tolerancia 5 min), como en C1.
- **Pares:** EUR/USD, GBP/USD, USD/JPY, USD/CHF, AUD/USD.
- **Factor (prueba principal):** media simple de los 5 pares cada mes → una observación por mes.
- **Descriptivo (no es criterio):** reversión 16:00 → 17:00 Londres con el signo contrario; cada par por separado.

## Datos
- **Descubrimiento / prueba principal: FXCM M1 BID y ASK, 2012-01 → 2026-09** (≈ 177 meses). Rentabilidad sobre el precio
  medio (BID+ASK)/2; spread medido de esos mismos datos.
- **Confirmación independiente: HistData M1 (solo BID; hora de Nueva York con horario de verano), 2003-01 → 2011-12**
  (≈ 108 meses), fuente y período distintos. Con BID solo: la ventana 14-16 Londres está lejos del rollover de las 17:00 NY,
  así que el artefacto del BID no aplica.
- Si un índice no tiene dato para ese mes, ese par queda fuera ese mes (no se rellena).

## Costes (por par y mes, ida y vuelta)
Medio spread medido a la entrada + medio spread medido a la salida + comisión 0,45 pb (FTMO, 5 $ por lote ida y vuelta) +
0,1 pb de deslizamiento por lado. En HistData (sin ASK) se usa la mediana del coste FXCM de cada par.

## Criterios de certificación (todos)
1. FXCM 2012-2026: media neta del factor > 0 con t ≥ 2,0 (meses independientes: t simple).
2. FXCM: media bruta ≥ 3 × coste medio.
3. FXCM: factor neto positivo en ≥ 60% de los años.
4. HistData 2003-2011: media bruta > 0 con t unilateral ≥ 1,645.
Contador de selección múltiple: +1 prueba principal (N acumulado del proyecto ≈ 1.155). Los pares por separado y la
reversión son descriptivos y no se usan para decidir. Si falla cualquiera, se descarta y no se modifica la regla.

## Potencia (aviso)
Un evento al mes: ≈ 177 observaciones. Si el efecto fuera de 3 pb con una volatilidad del factor de 15 pb, t ≈ 2,7.
Con efectos de 1-2 pb no se distinguiría del ruido: un resultado negativo no demuestra que no exista.
