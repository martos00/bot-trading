# Pre-registro E9 — Estrategia "yen de fin de mes" (B7 + C48) — 22-oct-2026
Congelada ANTES del backtest con tamaño y la cartera.
- Antepenúltimo día hábil (lun-vie, calendario de días con mercado) de cada mes: compra USDJPY a las 07:00:00 NY, cierre a las 08:00:00 NY.
- Tamaño: riesgo 0,5 % / (desviación de las últimas 24 operaciones D−2 de 07-08); stop de catástrofe a 4 desviaciones.
- Noticias FTMO: si hay noticia de alto impacto de USD o JPY a ±2 min de 07:00 u 08:00 NY, no se opera ese mes (se pierde 1 de 12).
- Coste: el real de FXCM (≈ 0,68 pb + comisión ya incluida); en FTMO se medirá con el script de costes.
Backtest informativo 2012-2026 y cartera con E1 + E8 (+ gas como informativo). Luego demo/forward.
