# PREREGISTRO C101 — Ruptura del rango asiático (regla C99) en plata, crudo, Nikkei y S&P 500 — 28-oct-2026

Redactado y subido a git ANTES de calcular. C99 pasó en el oro (dos fuentes) y falló en divisas. ¿Es propia del oro o de las materias
primas e índices? Regla idéntica a C99 (rango 19:00-03:00 NY, ruptura 03:00-11:00, stop en el otro extremo, objetivo 1× rango, cierre 16:45).

| Futuro | Principal (1 min) | Confirmación | Coste (pb) |
|---|---|---|---|
| SI plata | Databento SI 1 min (contrato frontal; cambios excluidos) | HistData XAGUSD 1 min | 2,3 |
| CL crudo | HistData WTIUSD 1 min | Databento CL 1 h | 1,6 |
| NKD Nikkei | HistData JPXJPY 1 min | Databento NKD 1 h | 1,5 |
| ES S&P 500 | Databento ES 1 min | (sin segunda fuente: solo candidata) | 0,73 |

## Criterio (Bonferroni unilateral 0,05/4 → t ≥ 2,50)
Principal: media > 0 con t (Newey-West) ≥ 2,50; ≥ 60 % de años positivos; > 0 en 2010-19 y 2020-26; media > coste. Confirmación:
media > coste con t ≥ 2,0. Contador +4.
