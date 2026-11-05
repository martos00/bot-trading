# C109 — Resultados: tono de los comunicados de la Fed y bono, dólar y oro al día siguiente — 05-nov-2026
Preregistro commit 57f74fe. 134 comunicados (federalreserve.gov, 2010-2026), tono por diccionario fijo (sin puntuación manual).
Script `c109_tono_fed.py`, salida `c109_resultados.txt`, tono por comunicado `c109_tono_por_comunicado.csv`.

| | n | 2010-17 | 2018-26 | Veredicto |
|---|---|---|---|---|
| **Principal h1** (ZN + 6E + GC, Databento) | 85 | +0,006 (t 0,07) | **+0,196 (t 2,67)** | **PASA el criterio fijado** |
| Principal h5 | 85 | +0,032 | +0,182 (t 1,92) | no pasa |
| h1 por activo: ZN / 6E / GC | | +1,9 / −4,0 / +5,1 pb | +13,0 / +11,5 / +8,6 pb | |

Comprobaciones posteriores (informativas):
- Segunda fuente (EURUSD y oro de HistData + ZN): 2018-26 +0,185 (t 2,38, n 36); sin 2022: +0,138 (t 2,08).
- Por año (conjunto): 2018 +0,11 · 2019 +0,15 · 2020 +0,02 · 2021 +0,13 · 2022 +0,56 · 2023 +0,28 · 2024 +0,51 · **2025 −0,09 · 2026 −0,25**.
- Sharpe anual aproximado 2018-26: ~0,6 (pocas operaciones: ~4-8 comunicados al año con señal).

Lectura honesta: pasa formalmente, pero es **débil**: no existía en 2010-2017, la muestra de confirmación es pequeña (36-45
comunicados), pesa mucho 2022-2024 (ciclo de subidas de tipos) y 2025-2026 son negativos. Además exige mantener la posición de un
día para otro (solo cuentas que lo permitan, p. ej. DTF). Estado: **candidata**, no se añade al bot; seguimiento en real comunicado a
comunicado (forward) y revisión cuando haya ≥ 20 comunicados nuevos. Contador +2.
