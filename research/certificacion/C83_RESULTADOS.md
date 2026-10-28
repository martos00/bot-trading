# C83 — Resultados: segunda fuente (HistData) de dos candidatas de futuros — 28-oct-2026
Reglas en PREREGISTRO_C83. Script `c83_oro_d2_nikkei_q2.py`, salida `c83_resultados.txt`. Rentabilidad del corto (positivo = gana).

| Regla | n | Media | t | Años + | 2010-17 | 2018-26 | Resto de días | Veredicto |
|---|---|---|---|---|---|---|---|---|
| **Oro corto D−2 09:30-10:00 NY** | 200 | +6,29 pb | 3,08 | 15/17 | +6,71 | +5,89 (t 1,72) | +1,18 | **PASA** |
| **Nikkei corto Q−2 20:00-21:00 NY** | 52 | +13,57 pb | 4,08 | 13/16 | +14,31 | +12,98 (t 2,43) | +0,50 | **PASA** |

Dos fuentes (futuros Databento + CFD HistData) coinciden. Encajan con mecanismos ya certificados: el oro cae el mismo día de fin de mes
en que el yen se vende frente al dólar (E9, compras de dólares), y el Nikkei se vende al final del trimestre y se compra al empezar
el siguiente (E13). Aviso: el oro en 2018-26 es más débil (t 1,72) y ambas salen de barridos con muchas reglas; la confirmación es en los
mismos años con otra fuente, no fuera de muestra temporal. Añadidas al EA como E15 y E16 **desactivadas** hasta medir sus costes en
FTMO (condición: coste ≤ 1/2 de la media 2018-26: oro ≤ 2,9 pb, Nikkei ≤ 6,5 pb). Cartera 2018-26 con costes: 1,35 → 1,44. Contador +2.
