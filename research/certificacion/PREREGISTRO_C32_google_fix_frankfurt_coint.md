# Pre-registro C32 — Tres ideas de Google: London Fix, Frankfurt breakout, cointegración EUR/SEK-EUR/NOK (21-oct-2026)

Redactado y enviado a git ANTES de calcular. Antecedentes: H71 (fixings, horas completas) y B2 (franjas de 1-2 h) no miraron
ventanas de 15 minutos alrededor del fix ni rupturas; la cointegración solo se probó en índices.

- **L London Fix (EUR/USD y GBP/USD):** Krohn-Mueller-Whelan: el USD se aprecia antes del fix de las 16:00 de Londres y se
  deprecia después. Regla diaria: corto del par (largo USD) 15:45 → 16:00 Londres y largo 16:00 → 16:15 Londres. Media de los
  dos pares. FXCM M1 BID/ASK, ejecución al ASK/BID reales + 0,45 pb de comisión + 0,1 pb de deslizamiento por lado y operación.
- **F Frankfurt breakout (EUR/USD y EUR/JPY):** rango = máximo y mínimo de 06:00-07:00 UTC. De 07:00 a 09:00 UTC, entrada en
  la primera ruptura (orden stop en el máximo o el mínimo), stop en el otro extremo del rango, salida a las 09:00 UTC o en el
  stop. FXCM, mismos costes.
- **P Cointegración EUR/SEK–EUR/NOK:** diferencial s = ln(EURSEK) − β·ln(EURNOK), β por MCO en 250 días anteriores; z con
  media y desviación de 60 días; entrada si |z| > 2 en contra, salida en z = 0 o a los 20 días. Cierres de las 16:00 NY de
  HistData (BID). Coste 10 pb por ida y vuelta del par de patas + financiación ignorada (declarada).
## Tramos y criterios (3 pruebas, Holm)
L y F: descubrimiento 2012-2018, confirmación 2019-2026-09 (FXCM). P: 2010-2017 y 2018-2026.
Confirmación: media neta > 0 con t que supere Holm, ≥ 60% de años, bruto ≥ 3 × coste. Contador +3 (N ≈ 1.800).
