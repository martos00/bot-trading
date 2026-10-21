# Resultados C24 — PLN/HUF/CZK en horas con spread estrecho: efecto real pero NO OPERABLE

Pre-registro `PREREGISTRO_C24_cee_horas_liquidas.md`; salida `c24_resultados.txt` (código en línea en el commit).

| Factor (USDPLN, USDHUF, USDCZK) | 2010-2017 | 2018-2026 |
|---|---|---|
| M: 08:00 Londres → 08:00 NY (+) | +3,7 pb (t 4,11), 8/8 años | **+1,8 pb (t 2,37), 9/9 años** |
| T: 08:00 → 11:00 NY (−) | +0,1 pb (t 0,13) | +1,1 pb (t 1,45) |

- **Mañana:** al empezar una hora más tarde (spread más estrecho, artefacto del BID pequeño) el efecto sigue ahí (9/9 años),
  pero es de ≈ 1,8 pb. El coste de operarlo (medio spread a la entrada y a la salida, ≈ 2,5-3 pb en Dukascopy, más 0,65 pb de
  comisión y deslizamiento) es mayor. **No operable.** Correlación con E1 0,45.
- **Tarde:** terminando a las 11:00 NY (mercados locales aún abiertos) el efecto desaparece: el "retorno del dólar" de C23
  (08:00 → 16:00 NY) se debía sobre todo al spread ancho de las 16:00 NY (artefacto) y a horas ilíquidas. **Descartada.**

## Revisión de C20, C22 y C23
El mecanismo de sesión europea existe en las divisas de Europa central (sigue presente con horas líquidas), pero las cifras
de C20/C22/C23 (3-5 pb) estaban infladas por el spread ancho de las 07:00 Londres y las 16:00 NY en datos solo BID. Con
horas líquidas queda ≈ 1,8 pb, por debajo del coste minorista. La cartera "25%" de c23_cartera.txt queda **anulada**.
