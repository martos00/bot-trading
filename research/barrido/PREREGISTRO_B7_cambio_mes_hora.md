# Pre-registro B7 — Barrido "día del cambio de mes × hora" en 30 futuros del CME — 22-oct-2026
Redactado y enviado a git ANTES de calcular.
## Motivo
Hay flujos programados en torno al cambio de mes (rebalanceos de fondos y pensiones, fixings de fin de mes, entradas por nóminas) que
pueden concentrarse en horas concretas. B4/B5 cruzaron la hora con el día de la semana; aquí se cruza con la posición en el mes.
## Regla
Mercados y costes: los 15 de B4 (b4_dia_hora_futuros.py) + los 15 de B5 (b5_dia_hora_futuros_nuevos.py), mismos datos h1/ES 1 min.
Tipos de día (días hábiles con datos del propio mercado): D−2 (antepenúltimo), D−1 (penúltimo), D0 (último del mes), D+1 (primero del
mes siguiente), D+2 (segundo). Franjas de 1 h (hora NY, sin 17-18), con el signo del descubrimiento; sin cambios de contrato en la franja.
## Criterios (como B4, ajustados a menos observaciones)
Descubrimiento 2010-06 – 2017: |t (NW)| ≥ 3,5 y n ≥ 80. Confirmación 2018 – 2026-09: (1) t ≥ Bonferroni unilateral 0,05/k_sel;
(2) ≥ 60 % de años con el signo; (3) bruto ≥ 3 × coste. Lo que pase necesita otra fuente antes de operar. Contador + nº de reglas.
