"""C82: Nasdaq largo 01:00 -> 03:00 NY cada laborable (PREREGISTRO_C82). Uso: python3 c82_nasdaq_madrugada.py DIR_NSXUSD DIR_SPXUSD"""
import sys
import numpy as np, pandas as pd
from c1_certificacion import t_nw
from c45_oro_viernes import carga, tramo
for nom, d in (('Nasdaq NSXUSD', sys.argv[1]), ('S&P SPXUSD (inf.)', sys.argv[2])):
    s = carga(d).loc['2010-01-01':'2026-09-30']; r = tramo(s, 1, 0, 2, 59) * 1e4; r = r[r.index.weekday < 5]
    an = r.groupby(r.index.year).mean(); p = r.loc['2021-07-01':]; t = t_nw(r.values); tp = t_nw(p.values)
    pasa = r.mean() > 0 and t >= 2 and (an > 0).mean() >= 0.6 and p.mean() > 1.0 and tp >= 1.65
    print(f'{nom}: n {len(r)} {r.mean():+.2f} pb (t {t:+.2f}) años+ {(an>0).sum()}/{len(an)} | 2010-17 {r.loc[:"2017"].mean():+.2f} | 2018-jun21 {r.loc["2018":"2021-06"].mean():+.2f} '
          f'| tras publicarse (2021-07 -> 2026-09) n {len(p)} {p.mean():+.2f} pb (t {tp:+.2f})' + (f' -> {"PASA" if pasa else "NO PASA"}' if 'NSX' in nom else ''))
    print('   por año:', (an.round(2)).to_dict())
