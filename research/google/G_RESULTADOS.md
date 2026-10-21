# G1 y G2 — Ideas de Google: RESULTADOS (21-oct-2026)

Pre-registro: `PREREGISTRO_G1_G2.md` (commit e460e15, antes de calcular). Código: `g1_asia_reversion.py`, `g2_oro_plata.py`,
`g_evaluacion.py`; salida: `g_resultados.txt`. HistData M1 2010-2026.

## G1 — Reversión a la media en la sesión asiática (Bollinger 20,2 en 15 min, 19:00-01:00 NY, cierre a las 02:00)
| Par | Tramo | Ops | Bruto/op | Neto/op | t neto | Años netos + | Aciertos |
|---|---|---|---|---|---|---|---|
| EURUSD | 2010-2017 | 2.427 | +0,89 pb | +0,09 pb | +0,33 | 4/8 | 62% |
| EURUSD | 2018-2026 | 2.707 | +0,55 pb | −0,25 pb | −1,33 | 2/9 | 60% |
| GBPUSD | 2010-2017 | 2.361 | +0,75 pb | −0,45 pb | −1,24 | 3/8 | 62% |
| GBPUSD | 2018-2026 | 2.602 | +0,67 pb | −0,53 pb | −2,41 | 2/9 | 59% |
**No confirmada.** Acierta el 60% de las veces (la "alta probabilidad" que se le atribuye), pero gana menos de 1 pb bruto
por operación, menos que el coste del spread asiático más la comisión. Neta, pierde.

## G2 — Pares oro/plata (z de 60 días de ln(oro/plata), |z| > 2, salida en z = 0 o a los 20 días)
| Tramo | Ops | Bruto/op | Neto/op | t neto | Años netos + |
|---|---|---|---|---|---|
| 2010-2017 | 41 | −34,2 pb | −48,3 pb | −1,19 | 1/8 |
| 2018-2026 | 47 | −16,9 pb | −31,2 pb | −0,58 | 4/9 |
**No confirmada**, y negativa incluso antes de costes: la relación oro/plata no vuelve a su media en 60 días; cuando se
separa suele seguir separándose (duración media 18 días, casi siempre se sale por el límite de 20).

## Veredicto
Ninguna de las dos ideas tiene ventaja. N acumulado del proyecto: +3.
