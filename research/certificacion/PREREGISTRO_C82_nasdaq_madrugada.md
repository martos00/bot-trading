# PREREGISTRO C82 — Nasdaq largo de 01:00 a 03:00 NY (apertura europea), cada día: segunda fuente — 28-oct-2026

Redactado y subido a git ANTES de calcular con esta fuente. Origen: B2 (futuro NQ de Databento): 2018-2026 +1,34 pb (t 2,55),
89 % de años; no pasó el umbral de Bonferroni del barrido (3,07). Es una versión del "overnight drift" (Boyarchenko, Larsen y Whelan;
blog de la Fed de NY 2021, artículo 2023), que según sus autores se ha debilitado desde 2021.

## Regla
HistData NSXUSD M1 (CFD del Nasdaq 100; hora de NY con cambio de hora). Cada día laborable (lun-vie): largo del cierre del último
minuto anterior a las 01:00 NY al cierre del último minuto anterior a las 03:00 NY (hasta 10 min atrás). Informativo: SPXUSD igual.

## Criterio
1. 2010-2026: media > 0 con t (Newey-West) ≥ 2,0 y ≥ 60 % de años positivos.
2. **Tras la publicación (2021-07 → 2026-09)**: media > 1,0 pb (coste supuesto del US100 de FTMO: spread de madrugada, a medir) y t ≥ 1,65.
Pasan los dos → candidata para medir el coste real del US100.cash a esa hora y preregistrar la estrategia. Si no → cerrado. Contador +1.
