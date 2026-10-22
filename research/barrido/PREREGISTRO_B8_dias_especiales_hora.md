# Pre-registro B8 — Barrido "día especial × hora" en 30 futuros del CME — 22-oct-2026
Redactado y enviado a git ANTES de calcular.
## Tipos de día (calendario fijado ahora)
- PRE: último día hábil antes de un festivo de la NYSE (holidays.financial_holidays('NYSE')).
- POST: primer día hábil después de un festivo de la NYSE.
- OPEX: tercer viernes del mes (vencimiento mensual de opciones); si es festivo, el día hábil anterior.
- POSTOPEX: lunes siguiente a OPEX.
- D15: día 15 del mes (o el siguiente día hábil): cupones del Tesoro, impuestos trimestrales de empresas, pagos a mitad de mes.
## Regla y criterios (como B7)
Mismos 30 futuros, datos y costes que B7 (b7_cambio_mes_hora.py). Franjas de 1 h (NY, sin 17-18), signo del descubrimiento, sin cambio de
contrato en la franja. Descubrimiento 2010-06 – 2017: |t (NW)| ≥ 3,5 y n ≥ 60. Confirmación 2018 – 2026-09: (1) t ≥ Bonferroni unilateral
0,05/k_sel; (2) ≥ 60 % de años con el signo; (3) bruto ≥ 3 × coste. Lo que pase necesita otra fuente. Contador + nº de reglas.
