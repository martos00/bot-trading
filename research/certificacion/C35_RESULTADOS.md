# C35 — Resultados: base de los futuros del VIX (Simon-Campasano) — 21-oct-2026

Reglas congeladas en PREREGISTRO_C35 (enviado a git antes de descargar). Datos: liquidaciones oficiales CBOE de cada contrato VX + VIX de contado CBOE.

Regla: roll diario = (futuro − VIX) / días hábiles al vencimiento; corto si > 0,10, largo si < −0,10; coste 0,05 pt por entrada.

| Periodo | Media neta | t (NW) | Sharpe | Años + | Peor día | Caída máx |
|---|---|---|---|---|---|---|
| 2013-14 (réplica) | −0,0032 pt/día | −0,31 | −0,20 | 1/2 | −2,5 pt | −4,0 pt |
| 2015-26 (confirmación) | +0,0030 pt/día | 0,19 | 0,06 | 6/12 | −12,1 pt | −54,5 pt |

Por año (pt): 2015 +2,2 · 2016 +11,8 · 2017 +4,3 · 2018 −13,3 · 2019 −1,3 · 2020 +33,4 · 2021 −9,9 · 2022 −13,8 · 2023 +2,7 · 2024 −5,4 · 2025 +4,0 · 2026 −5,8

**NO CERTIFICADA** (t 0,19 < 2; 50 % de años positivos < 60 %). La prima publicada de la base del VIX no sobrevive a costes en el periodo reciente y tiene colas extremas (feb-2018, mar-2020). Descartada; no se reajusta.
