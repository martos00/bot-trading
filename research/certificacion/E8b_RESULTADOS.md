# E8b — Resultados: oro largo el viernes 16:00 → 16:45 NY — 27-oct-2026
Reglas congeladas en PREREGISTRO_E8b (commit b7a99fc). Script `e8b_oro_viernes_1645.py`, salida `e8b_resultados.txt`.

| Fuente | n | Media | t | Años + | 2010-17 | 2018-26 |
|---|---|---|---|---|---|---|
| Futuro GC (Databento) | 782 | +2,48 pb | 5,51 | 14/17 | +2,75 (t 4,15) | +2,26 (t 3,68) |
| Contado XAUUSD (HistData, BID) | 783 | +1,84 pb | 3,76 | 15/17 | +2,48 (t 3,48) | +1,25 (t 1,88) |
| Informativo: futuro 16:45 → 16:55 (lo que se pierde) | 782 | +0,76 pb | 3,88 | 14/17 | | |

**PASA todos los criterios** (futuro 2018-26 +2,26 pb > coste FTMO 1,45 pb). E8 se reactiva en FTMO con salida 16:45 NY
(`InpE8_Salida = 1645`). Margen neto estrecho (+0,8 pb por viernes en 2018-26). Sharpe de la cartera con costes FTMO,
2018-26: sin oro 1,16; con E8b 1,28 (con la regla original 16:55 sería 1,46). Pendiente: el coste del oro en FTMO solo se midió en
4 viernes de desfase horario; hay que medirlo en viernes normales a las 16:00-16:45 NY (el registro del EA lo anota).
