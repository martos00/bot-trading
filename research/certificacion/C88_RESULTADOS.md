# C88 — Resultados: régimen de gamma de las opciones del oro y dirección intradía (10:00 → 13:30) — 28-oct-2026
Reglas en PREREGISTRO_C88_C89 (+ anexo: opciones horarias, entrada 10:00). Código `c88_quantconnect_plantilla.py`; eventos
`c88_eventos_quantconnect.txt`. 2.704 días (2012-11 → 2026-07); GEX < 0 en 979.

| | n | Media | t | ≤ 2018 | ≥ 2019 |
|---|---|---|---|---|---|
| **Regla** (GEX<0 → seguir el movimiento nocturno; GEX>0 → contrario) | 2.704 | −1,25 pb | −1,12 | +0,79 | −2,78 (t −2,04) |
| Control: seguir siempre el movimiento nocturno | 2.704 | +1,00 | 0,88 | −2,27 | +3,45 (t 2,48) |
| Seguir el movimiento con GEX<0 / con GEX>0 | 979 / 1.725 | −0,35 / +1,77 | | | |

**NO PASA.** La gamma no ordena la dirección como predice la teoría (incluso al revés). Informativo, no preregistrado como prueba: desde
2019 el oro tiende a continuar de 10:00 a 13:30 el movimiento desde el cierre anterior (+3,45 pb, t 2,48); no se usa (sería selección a
posteriori). Contador +1.
