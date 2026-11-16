import sys, numpy as np, pandas as pd
src = open('apex_examen_minuto.py').read(); exec(src[:src.index("otros =")])
r = {}
for fin in (1012, 1013, 1014, 1015, 1016, 1017):
    v = {}
    for d, s in smin.items():
        if isinstance(s, pd.DataFrame):
            if s.i.nunique() > 1: continue
            s = pd.Series(s.c.values, index=s.m.values).groupby(level=0).last()
        a = ultimo(s, 990); e = ultimo(s, fin); sg = SSd.get(d, np.nan)
        if a == a and e == e and sg == sg: v[d] = (e / a - 1) / sg - 2.3e-4 / sg
    r[fin] = pd.Series(v).sort_index().loc['2018':]
for f in r: print(f, f'{r[f].mean():+.3f} σ  t {r[f].mean()/r[f].std()*np.sqrt(len(r[f])):.2f}  n {len(r[f])}')
