# Pre-registro B12 — Barrido "hora × signo de las 24 h previas" (momentum/reversión intradía) en 30 futuros y 13 divisas — 22-oct-2026
Redactado y enviado a git ANTES de calcular.
## Regla (una por mercado y hora)
Para la franja de 1 h que empieza a la hora h (NY): señal = signo de la rentabilidad de las 24 h previas (de h−24 a h; si falta, sin señal).
Rentabilidad de la regla = señal × rentabilidad de la franja (momentum si sale positiva; reversión si negativa: el signo lo fija el descubrimiento).
Sin cambios de contrato en las 24 h ni en la franja. Mismos datos y costes que B10 (futuros) y B9 (divisas, costes reales), mismos tramos.
## Criterios
Selección |t (NW)| ≥ 3,5 y n ≥ 500 en el descubrimiento. Confirmación con su signo: (1) t ≥ Bonferroni unilateral 0,05/k_sel (futuros y divisas
por separado); (2) ≥ 60 % de años con el signo; (3) bruto ≥ 3 × coste. Lo que pase necesita otra fuente. Contador + nº de reglas.
