# Pre-registro C10 — Dos flujos con causa conocida en divisas: "gotobi" del yen y prima del dólar en días de la Fed (21-oct-2026)

Redactado y enviado a git ANTES de calcular ningún resultado. Ninguna de las dos se ha probado en el proyecto (H71 probó
el fixing de Tokio todos los días, sin condicionar a los días gotobi; N2 probó los días de la Fed en el S&P 500, no en
divisas). Ambas deberían ser independientes de E1 (otro par u otra hora, pocos días al año).

## G — Anomalía gotobi (Bessho, Sugimoto y Suzuki, arXiv 2301.13204, leída)
Mecanismo: las importadoras japonesas pagan en dólares los días gotobi (5, 10, 15, 20, 25 y último día del mes) al tipo
TTM que se fija a las 09:55 de Tokio; los bancos compran dólares antes y el USD/JPY sube hasta las 09:55. Su estrategia
(EBS 2018-2020): comprar USD/JPY a las 03:00 de Tokio y vender a las 09:55 los días gotobi.
- **Regla:** compra de USD/JPY a las 03:00 Tokio y venta a las 09:55 Tokio del día gotobi. Día gotobi: 5, 10, 15, 20, 25 y
  último día del mes; si cae en sábado, domingo o festivo de Japón (paquete `holidays`), se adelanta al día laborable
  anterior. La posición cruza el rollover de las 17:00 NY (swap).

## F — Prima de los días de la Fed en divisas (Mueller, Tahbaz-Salehi y Vedolin, JF 2017; leído el resumen)
Una cartera corta en dólares y larga en las demás divisas gana bastante más los días de anuncio programado del FOMC.
Mecanismo propuesto: compensación por soportar la incertidumbre de política monetaria.
- **Regla:** corto en USD contra una cesta igual de EUR, GBP, JPY, CHF y AUD desde las 16:00 NY del día anterior al anuncio
  hasta las 16:00 NY del día del anuncio. Fechas programadas del FOMC de `research/nuevas/fechas_fomc.py`. Cruza el rollover.

## Datos, tramos y costes
- **Descubrimiento: HistData M1 BID 2003-2011** (precio = cierre del último minuto ≤ hora, tolerancia 5 min). Ningún extremo
  de las ventanas cae en el rollover, así que el artefacto del BID no aplica.
- **Confirmación: FXCM M1 BID/ASK 2012-01 → 2026-09**, ejecutable: se compra al ASK y se vende al BID reales.
- Además, en confirmación: comisión 0,45 pb + 0,1 pb de deslizamiento por lado + financiación 0,5 pb por noche (como en N3).

## Criterios (cada regla; 2 pruebas → t ≥ 2,24 en confirmación)
- Descubrimiento: media bruta > 0.
- Confirmación (todos): (1) media neta ejecutable > 0 con t ≥ 2,24; (2) media en precio medio ≥ 3 × coste medio;
  (3) neto positivo en ≥ 60% de los años.
- Informativo: correlación con E1, cada par de F por separado, G sin cruzar el rollover (05:00 → 09:55 Tokio).
Contador: +2 (N acumulado ≈ 1.162). Si una regla falla, se descarta sin cambiar horas ni días.
