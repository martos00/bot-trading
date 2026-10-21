"""Evaluación de G1 y G2 según PREREGISTRO_G1_G2.md. Uso: python3 g_evaluacion.py DIR"""
import os, sys
import numpy as np
import pandas as pd

d = sys.argv[1]


def t(x):
    x = np.asarray(x); return x.mean() / x.std(ddof=1) * np.sqrt(len(x))


def informe(nombre, r, coste, t_req):
    print(f'\n=== {nombre} ===')
    filas = {}
    for tramo, sl in (('descubrimiento 2010-2017', slice('2010', '2017')), ('confirmación 2018-2026', slice('2018', '2026'))):
        x = r.loc[sl]
        if len(x) < 10:
            print(f'  {tramo}: muy pocas operaciones ({len(x)})'); continue
        neto = x.r - x.coste
        an = neto.groupby(neto.index.year).mean()
        filas[tramo] = (x.r.mean(), neto.mean(), t(neto), (an > 0).sum(), len(an))
        print(f'  {tramo}: {len(x)} ops | bruto {x.r.mean() * 1e4:+.2f} pb | neto {neto.mean() * 1e4:+.2f} pb (t {t(neto):+.2f}) | '
              f'neto estrés {(x.r - 2 * x.coste).mean() * 1e4:+.2f} pb | años netos + {(an > 0).sum()}/{len(an)} | '
              f'aciertos {(neto > 0).mean() * 100:.0f}%')
    if 'confirmación 2018-2026' in filas and 'descubrimiento 2010-2017' in filas:
        b, n, tt, ya, yn = filas['confirmación 2018-2026']
        ok = n > 0 and tt >= t_req and (coste is None or b >= 2 * coste) and ya >= 6 and filas['descubrimiento 2010-2017'][1] > 0
        print('  VEREDICTO:', 'CONFIRMADA' if ok else 'NO CONFIRMADA')


for sim, c in (('EURUSD', 0.8e-4), ('GBPUSD', 1.2e-4)):
    r = pd.read_csv(os.path.join(d, f'g1_{sim}.csv'), parse_dates=['entrada', 'salida']).set_index('entrada')
    r['coste'] = c
    informe(f'G1 {sim} reversión asiática (coste {c * 1e4:.1f} pb)', r, c, 2.24)
g = pd.read_csv(os.path.join(d, 'g2_oro_plata.csv'), parse_dates=['entrada', 'salida']).set_index('entrada')
g['coste'] = 3e-4 / 2 + g.dias * 1.4e-4 / 2          # costes sobre el nominal total (2 patas)
informe('G2 pares oro/plata (3 pb de spreads + 1,4 pb/día de financiación, por pata)', g, None, 2.0)
