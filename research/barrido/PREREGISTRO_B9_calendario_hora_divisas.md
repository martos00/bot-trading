# Pre-registro B9 — Barrido "día de calendario × hora" en 13 pares de divisas (FXCM, BID/ASK reales) — 22-oct-2026
Redactado y enviado a git ANTES de calcular. Ya conocido (control, no cuenta): USDJPY D−2 07-08 NY (B7/C48) y EURUSD 06-08 NY (E1).
## Tipos de día
D−2, D−1, D0, D+1, D+2 (como B7, días hábiles con datos del propio par) y PRE, POST, OPEX, POSTOPEX, D15 (como B8). 10 tipos.
## Regla y criterios
Mismos pares, precios (mid al minuto hh:59), costes reales (medio spread entrada + salida + 0,45 pb) y franjas que B6 (sin 16-18 NY).
Descubrimiento 2012-2018: |t (NW)| ≥ 3,5 y n ≥ 60. Confirmación 2019 – 2026-09: (1) t ≥ Bonferroni unilateral 0,05/k_sel; (2) ≥ 60 % de años
con el signo; (3) bruto ≥ 3 × coste. Lo que pase necesita otra fuente (HistData) antes de operar. Contador + nº de reglas.
