# C94 — Resultados: ruptura del día anterior (regla C93-B, cierre 16:45) en 9 futuros — 28-oct-2026
Preregistro `PREREGISTRO_C94_...` (commit 4e76600). Script `c94_ruptura_otros_futuros.py`, salida `c94_resultados.txt`.

| Futuro | HistData M1 (pb, t) | Databento 1 h (pb, t) | Coste | Veredicto |
|---|---|---|---|---|
| SI plata | +3,89 (1,56), 10/17 años | +5,59 (2,27) | 2,3 | no (t principal) |
| CL crudo | +6,10 (1,98); 2020-26 +1,48 | +3,12 (1,10) | 1,6 | no |
| 6E euro | +0,49 (0,82) | −0,75 | 0,6 | no |
| 6B libra | +0,92 (1,58) | +0,10 | 0,8 | no |
| 6J yen | +1,62 (2,53) | +0,50 (0,74) | 0,8 | no |
| 6A australiano | (HistData cargó solo 2010-11*) | −3,12 (−3,86) | 1,0 | no |
| 6C canadiense | −0,88 | −1,76 (−3,01) | 1,0 | no |
| 6S franco | (HistData cargó solo 2010-11*) | +0,37 (0,53) | 1,0 | no |
| NKD Nikkei | +2,23 (1,70); 2020-26 −1,23 | +3,13 (2,54) | 1,5 | no |

\* Error de ruta: el script leyó la carpeta `hd_all` de AUDUSD/USDCHF, que solo llega a 2011 (AUDUSD completo está en `hd_new`; USDCHF
completo no está en HistData local). No cambia el veredicto: ambos fallan en la confirmación de Databento, que es obligatoria.

**Ninguno pasa.** La continuación tras romper el rango de ayer es propia del oro (y quizá la plata/Nikkei, sin significación); en divisas
no existe o se invierte. Cesta de igual riesgo (informativa, bruta): Sharpe 0,62, no utilizable (incluye mercados negativos). Contador +9.
