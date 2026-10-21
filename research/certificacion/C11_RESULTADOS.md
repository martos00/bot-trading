# Resultados C11 — Impulso de la última media hora del S&P 500 con gamma negativa: NO CERTIFICADA

Pre-registro: `PREREGISTRO_C11_gamma_momentum.md` (commit da7e5e2). Script `c11_gamma_momentum.py`, salida `c11_resultados.txt`.
GEX de SqueezeMetrics (gratuito); 297 de 3.597 días (8,3%) con GEX del día anterior < 0.

| | 2011-2018 | 2019-2026 (confirmación) |
|---|---|---|
| GEX < 0 (la regla) | bruto 3,2 pb, neto 2,2 pb (t 0,41) | bruto 2,9 pb, **neto 1,9 pb (t 0,60)**, bruto/coste 2,9 |
| GEX ≥ 0 | neto 0,1 pb | neto −1,5 pb (t −2,58) |
| Sin condición | neto 0,2 pb | neto −1,2 pb |

El signo es el que predice la teoría (más impulso con gamma negativa), pero el efecto es de unos 3 pb frente a 1 pb de coste
y no es significativo (pocos días). Falla los criterios 1 y 2. **Descartada.**

Informativo, a posteriori: la regla del 80% (C9) gana más con GEX < 0 (65 operaciones, +16 pb, t 2,72) que con GEX ≥ 0
(+2,1 pb), lo contrario de lo que predice la teoría para una estrategia de reversión. Con 65 operaciones y mirado después,
no se usa para nada.
