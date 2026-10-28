"""C86: momentum de la ultima media hora antes de la liquidacion en GC y SI (PREREGISTRO_C86). Uso: python3 c86_momentum_cierre_metales.py DIR_M1"""
import glob, os, sys
import numpy as np, pandas as pd
from c1_certificacion import t_nw
from c84_ventana_liquidacion import cargar
M = sys.argv[1]
for nom, s, (hs, ms), coste in (('Oro GC', 'GC', (13, 30), 0.74), ('Plata SI', 'SI', (13, 25), 2.3)):
    x = cargar(sorted(glob.glob(os.path.join(M, f'{s}_*.csv'))))
    df = pd.DataFrame({'c': x.close.values, 'i': x.instrument_id.values, 'dia': x.index.normalize(), 'm': x.index.hour * 60 + x.index.minute})
    liq, ent = hs * 60 + ms, hs * 60 + ms - 30
    L = df[(df.m < liq) & (df.m >= liq - 10)].groupby('dia').last(); E = df[(df.m < ent) & (df.m >= ent - 10)].groupby('dia').last()
    j = E.join(L, lsuffix='e', rsuffix='l', how='inner'); j = j[j.index.dayofweek < 5]
    prev_c, prev_i = j.cl.shift(1), j.il.shift(1)
    ok = (j.ie == j.il) & (prev_i == j.ie)
    sig = np.sign(np.log(j.ce / prev_c)); r = (sig * np.log(j.cl / j.ce) * 1e4)[ok & (sig != 0)].dropna().loc['2010-06-01':'2026-09-30']
    an = r.groupby(r.index.year).mean(); t = t_nw(r.values); a, b, p = r.loc[:'2017'], r.loc['2018':], r.loc['2021':]
    pasa = r.mean() > 0 and t >= 1.96 and a.mean() > 0 and b.mean() > 0 and p.mean() > coste and (an > 0).mean() >= 0.6
    print(f'{nom}: n {len(r)} {r.mean():+.2f} pb (t {t:+.2f}) años+ {(an>0).sum()}/{len(an)} | 2010-17 {a.mean():+.2f} | 2018-26 {b.mean():+.2f} | 2021-26 {p.mean():+.2f} (t {t_nw(p.values):+.2f}) | coste {coste} -> {"PASA" if pasa else "NO PASA"}')
