# Pre-registro B4 — Barrido día de la semana × hora en 16 futuros del CME — 22-oct-2026
Redactado y enviado a git ANTES de calcular el barrido. Ya se conoce una celda (gas natural jueves 09:00-10:00, F1b, hallada a
posteriori): se informa como control y NO cuenta como hallazgo aunque pase.
## Regla
Mismos datos, hora de NY, costes y exclusiones que B2 (b2_barrido_futuros.py): ES (1 min → hora), NQ, ZN, ZB, CL, NG, GC, SI, HG, ZS,
ZC, 6E, 6J, 6B, 6A (h1 de Databento). Franjas de 1 hora (inicio 0-22, sin la pausa de 17-18), separadas por día de la semana (lun-vie).
Rentabilidad de la franja con el signo del descubrimiento; sin cambios de contrato dentro de la franja.
## Tramos y criterios (más estrictos que B2 porque hay ≈ 5 veces más reglas)
Descubrimiento 2010-06 – 2017: selección si |t (NW)| ≥ 3,5 y n ≥ 200. Confirmación 2018 – 2026-09, para cada seleccionada con su signo:
(1) t ≥ umbral de Bonferroni unilateral 0,05 / k_sel; (2) ≥ 60 % de años con el signo; (3) bruto ≥ 3 × coste del futuro.
Contador + nº de reglas evaluadas.
