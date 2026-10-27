# C80 — Resultados: bolsa local antes de BoJ, BoE y RBA (cierre D−3 → cierre D−1) — 27-oct-2026
Reglas en PREREGISTRO_C80 (commit 37dd366). Script `c80_deriva_previa_bc.py`, salida `c80_resultados.txt`. HistData con hora de NY corregida.

| Banco → bolsa | n | D−2..D−1 | t | 2010-17 | 2018-26 | Años con el signo | D0 (inf.) | Veredicto |
|---|---|---|---|---|---|---|---|---|
| BoJ → Nikkei | 158 | +38,3 pb | 2,07 | +47,4 | +26,9 (t 0,88) | 12/17 | +12,2 | NO PASA (t < 2,13; débil desde 2018) |
| **BoE → FTSE (2015-26)** | 75 | **+31,5 pb** | **2,31** | +27,1 | **+32,0 (t 2,10)** | 8/10 | −4,0 | **PASA** |
| RBA → ASX | — | 2010-17 −15,5 pb (t −1,28) | | | | | | NO PASA (sin signo) |

## Comprobaciones de la BoE (hechas después, informativas)
| Fuente | n | D−2..D−1 | t | Cualquier par de días | Tras publicarse el estudio (jun-2025 → sep-2026) |
|---|---|---|---|---|---|
| HistData UKXGBP (CFD) | 75 | +31,5 pb | 2,31 | — | — |
| Futuro FTSE de ICE (Databento, 2019-26) | 62 | +34,6 pb | 1,96 | +7,3 pb | n 11: −12,4 pb |
| Índice FTSE 100 (Yahoo, 2015-26) | 78 | +35,9 pb | 2,99 | +3,4 pb | n 11: +14,1 pb |

Tres fuentes coinciden (≈ +32-36 pb frente a +3-7 pb en un par de días cualquiera). Pero la muestra es la misma época que la del estudio
(Quantpedia, datos 2010-2025): es una **replicación, no una validación posterior a la publicación**; desde junio de 2025 solo hay 11 casos
y no dicen nada (−12 / +14 pb según la fuente). **Candidata** (8 operaciones al año, mantener 2 días). Para operarla habría que
preregistrar la estrategia con el coste real del UK100 de FTMO (spread + 2 noches de financiación; supuesto 6 pb) y vigilarla en vivo.
Contador +3.
