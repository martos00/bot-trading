# C93 — Resultados: oro, ruptura del día anterior (vídeo TikTok «mgp.quant») — 28-oct-2026

Preregistro: `PREREGISTRO_C93_oro_ruptura_dia_anterior.md` (commit 2a2b8f5, antes de calcular). Scripts: `c93_oro_ruptura_dia_anterior.py`,
`c93b_controles_y_gc.py`. Salidas: `c93_resultados.txt`, `c93b_resultados.txt`.

| Variante | Fuente | n | Media/operación | t NW | Años + | 2010-19 | 2020-26 | Veredicto |
|---|---|---|---|---|---|---|---|---|
| A (07-14 NY, cierre 16:00) | HistData | 3114 | +3,62 pb | 2,85 | 13/17 | +2,28 | +5,45 | pasa |
| A | Futuro GC | 3100 | +2,54 pb | 1,96 | 12/17 | +1,90 | +3,45 | **no confirma** |
| B (08-15 NY, cierre 17:00) | HistData | 3147 | +3,50 pb | 2,80 | 11/17 | +3,04 | +4,14 | pasa |
| B | Futuro GC | 3122 | +2,95 pb | 2,24 | 12/17 | +2,83 | +3,13 | **pasa (justo en el umbral)** |

Controles:
- No es la subida del oro: largo siempre en la misma franja ≈ −0,5 a −0,9 pb. Los cortos ganan más que los largos (+4,2 a +5,1 pb).
- El stop y el objetivo casi no influyen (94 % cierra por tiempo; sin stop ni objetivo: +3,1 a +3,3 pb). La ventaja es la continuación tras la ruptura.
- Salida a las 16:45 (firmas de futuros), variante B: +3,72 pb (t 2,99).
- Coincide con lo que dice el vídeo: ~0,03 R por operación frente a ~0,046 R del vídeo; reparto de cierres parecido (94 % frente a 89 %).

Lectura honesta:
- Es una ventaja pequeña (~3 pb brutos por operación, ~190 operaciones al año).
- Netos: ~2,2 pb en futuros (0,74 pb de coste) y ~1,5-2 pb en el CFD de FTMO (1,5 pb).
- Sharpe anual neto aproximado: 0,4 en futuros y 0,3-0,4 en FTMO.
- 2026 es negativo en GC (−883 pb acumulados) y ~0 en HistData.
- Solo la variante B queda confirmada, y en el límite. Siguiente paso: forward test en demo, sin tocar parámetros.

Contador de pruebas +2.
