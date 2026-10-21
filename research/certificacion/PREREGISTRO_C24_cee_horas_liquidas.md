# Pre-registro C24 — Divisas de Europa central en horas con spread estrecho (21-oct-2026)

Redactado y enviado a git ANTES de calcular. Motivo (de costes, no de resultados): la muestra de Dukascopy (c23) indica que a
las 07:00 de Londres el spread de USDPLN/USDHUF es ≈ 4,8 pb frente a ≈ 2,5-3 pb a las 08:00 NY, y a las 16:00 NY vuelve a
abrirse (≈ 4 pb). Se mueven las horas a cuando los mercados de Varsovia, Budapest y Praga (09:00-17:00 CET) están abiertos.
No se ha mirado la rentabilidad de estas ventanas.

## Pruebas (pares USDPLN, USDHUF, USDCZK; factor = media de los tres)
- **M (mañana líquida):** 08:00 Londres → 08:00 NY. Signo previsto +.
- **T (tarde líquida):** 08:00 NY → 11:00 NY (≈ 17:00 CET, cierre de esos mercados). Signo previsto −.
Datos HistData M1 BID 2010-2026, como C20. El artefacto del BID se acota con la muestra de Dukascopy (spread a 08:00 Londres,
08:00 NY y 11:00 NY): se descuenta (spread_inicio − spread_fin)/2 medio antes de juzgar.

## Criterios (2 factores; Holm)
Descubrimiento 2010-2017: signo previsto. Confirmación 2018 → 2026-09: signo previsto con t de Newey-West ≥ 2,24 y ≥ 60% de
años, y además media corregida por el artefacto ≥ 3 × coste medido (spread medio a la entrada y a la salida / 2 + 0,45 pb de
comisión + 0,2 pb de deslizamiento). Contador +2 (N ≈ 1.189).
