"""C83: segunda fuente (HistData) de oro D-2 09:30-10:00 corto y Nikkei Q-2 20:00-21:00 corto (PREREGISTRO_C83).
Uso: python3 c83_oro_d2_nikkei_q2.py DIR_XAU DIR_JPX"""
import sys
import numpy as np, pandas as pd
from c1_certificacion import t_nw
from c45_oro_viernes import carga, tramo
def ultimos(idx, k, meses=None):
    d = pd.Series(idx, index=idx); out = []
    for (y, m), g in d.groupby([idx.year, idx.month]):
        if meses and m not in meses: continue
        if len(g) > k: out.append(g.sort_values().iloc[-1 - k])
    return pd.DatetimeIndex(out)
if __name__ == "__main__":
 for nom, d, h0, m0, h1, m1, k, meses, coste in (('Oro D-2 09:30->10:00 corto', sys.argv[1], 9, 30, 9, 59, 2, None, 1.45),
                                                    ('Nikkei Q-2 20:00->21:00 corto', sys.argv[2], 20, 0, 20, 59, 1, (3, 6, 9, 12), 2.5)):
        s = carga(d).loc['2010-01-01':'2026-09-30']; r = -tramo(s, h0, m0, h1, m1) * 1e4; r = r[r.index.weekday < 5]
        dias = pd.DatetimeIndex(sorted(set(s.index.tz_localize(None).normalize()))); dias = dias[dias.weekday < 5]
        v = r.reindex(ultimos(dias, k, meses)).dropna(); otros = r.drop(v.index, errors='ignore')
        an = v.groupby(v.index.year).mean(); t = t_nw(v.values); b = v.loc['2018':]
        pasa = t >= 1.96 and (an > 0).mean() >= 0.6 and b.mean() > coste
        print(f'{nom}: n {len(v)} {v.mean():+.2f} pb (t {t:+.2f}) años+ {(an>0).sum()}/{len(an)} | 2010-17 {v.loc[:"2017"].mean():+.2f} | 2018-26 {b.mean():+.2f} (t {t_nw(b.values):+.2f}) '
              f'| resto de días {otros.mean():+.2f} | coste {coste} -> {"PASA" if pasa else "NO PASA"}')
