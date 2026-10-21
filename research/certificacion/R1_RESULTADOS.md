# R1 — ¿Depende la ventaja C1 del régimen? RESULTADOS (21-oct-2026)

Pre-registro: `PREREGISTRO_R1_regimenes_eurusd.md` (commit 51840ed). Código `r1_regimenes_eurusd.py`; salida `r1_resultados.txt`.

| Variable | Descubrimiento 2010-2017 | Confirmación 2018-2026 | Criterios | Decisión |
|---|---|---|---|---|
| Volatilidad (alta / baja) | +1,86 / +1,84 pb, diferencia t = +0,02 | +1,88 / +1,18 pb, t = +0,96 | 1 no, 2 no, 3 no (Sharpe filtrado 0,69 < 0,99) | **Sin filtro** |
| Tendencia (alcista / bajista) | +1,57 / +2,13 pb, t = −0,73 | +0,96 / +1,73 pb, t = −1,35 | 1 no, 2 no, 3 sí (1,01 > 0,99) | **Sin filtro** |

Informativo (regímenes combinados): la ventaja es positiva en los cuatro regímenes de volatilidad × tendencia en los dos
tramos (de +0,84 a +2,45 pb). **La ventaja no depende del régimen**: funciona igual con volatilidad alta o baja y con el euro
en tendencia alcista o bajista. No se añade ningún filtro; la estrategia E1 queda como estaba. N acumulado: +2.
