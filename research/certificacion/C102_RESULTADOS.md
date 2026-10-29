# C102 — Resultados: ruptura del rango asiático en futuros ligados a Asia — 29-oct-2026
Preregistro y anexo (confirmación QuantConnect) antes de calcular cada parte. Scripts `c102_ruptura_asiatica_asia.py`,
`c102_quantconnect_plantilla.py`; salida `c102_resultados.txt`.

| Futuro | Databento 1 h | Años + | 2010-19 / 2020-26 | Confirmación | Veredicto |
|---|---|---|---|---|---|
| **HG cobre** | **+6,49 pb (t 4,48)** | 13/17 | +6,62 / +6,30 | **QuantConnect 1 min +4,91 (t 3,44)**, 13/16 años | **PASA** |
| PA paladio | +8,18 (t 4,39) | 16/17 | +7,79 / +8,71 | QuantConnect PA inservible (precio congelado en 2022) | candidata sin confirmar; coste real dudoso (5-10 pb) |
| PL platino | +2,33 (t 1,51) | 8/17 | | — | no |
| 6A australiano | −3,67 (t −4,97) | 5/17 | | HistData +0,76 | no |
| 6N neozelandés | −0,73 | 8/17 | | HistData +0,87 | no |
Informativo: Hang Seng (HistData) +4,93 pb (t 4,29); ASX 200 +0,69.

Cobre: 2022-2025 débil (−0,3 / −0,1 / +0,9 / +1,4 en QuantConnect). Correlación con oro C99 0,07 y con NKD C101 0,11. Sharpe neto sola ~0,57.
Cartera con NKD y cobre a tamaño reducido (pesos elegidos sobre el mismo histórico, optimista): firma normal 1,77 → 1,89; permisiva 2,15 → 2,26.
Patrón: la continuación tras romper el rango asiático aparece en mercados con mucha actividad asiática (oro, Nikkei, cobre, Hang Seng,
paladio) y no en divisas. Contador +5 (+1 confirmación).
