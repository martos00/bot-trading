# C75 — Resultados: acciones de FTMO alrededor de la publicación de resultados — 26-oct-2026
Reglas congeladas en PREREGISTRO_C75 (commit 4c80015). Script `c75_acciones_resultados.py`, salida `c75_resultados.txt`,
eventos `c75_eventos.csv`. 2.438 anuncios en 45 acciones (2012-01 a 2026-10). Desviación de datos antes de calcular: se excluye
RTN (Raytheon antigua), porque la historia de RTX en Yahoo es la de UTX.

Exceso sobre SPY menos la media de la propia acción en días sin resultados (media por evento; t agrupado por fecha):

| Regla | 2012-2018 | 2019-2026 | Coste | Veredicto |
|---|---|---|---|---|
| A1 subida previa (R−2 → R−1, sin aguantar el anuncio) | +5,7 pb (t 1,75) | +6,7 pb (t 0,42) | 8 pb | NO PASA: menor que el coste |
| A2 prima con el anuncio (R−1 → R) | +38,7 pb (t 2,19) | +6,4 pb (t −1,01) | 8 pb | NO PASA: desaparece en 2019-2026 |
| B deriva tras el anuncio (5 días en la dirección de la reacción) | +20,3 pb (t 1,50) | +25,9 pb (t 0,82) | 20 pb | NO PASA: no significativa, neto ≈ 0 |

- A2: la prima clásica existía en 2012-2018 y en 2019-2026 se pierde (media por fecha −26 pb). Además depende de unos pocos huecos enormes (mediana por evento ≈ 0).
- B: es la más estable (≈ +17-20 pb por fecha en las dos mitades), pero no es significativa y los costes supuestos (5 noches de financiación) se la comen.
- **Ninguna certificada. Cerrada sin variantes.** Contador +3. Con la lista actual de FTMO existe sesgo de supervivencia: se corrige con el ajuste frente a días sin resultados, pero no del todo.
