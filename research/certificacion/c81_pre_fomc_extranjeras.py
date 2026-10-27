"""C81: deriva previa al FOMC en FTSE, DAX, Nikkei y ASX (PREREGISTRO_C81). Uso: python3 c81_pre_fomc_extranjeras.py DIR_HD_NEW FOMC_CSV"""
import os, sys
import numpy as np, pandas as pd
from c1_certificacion import t_nw
from c80_deriva_previa_bc import cierres
hd, fc = sys.argv[1:3]
fomc = pd.DatetimeIndex(pd.read_csv(fc).iloc[:, 0]); fomc = fomc[(fomc >= '2010-06-01') & (fomc <= '2026-09-30')]
for nom, d, tz, hh, mm in (('FTSE', 'UKXGBP', 'Europe/London', 16, 30), ('DAX', 'GRXEUR', 'Europe/Berlin', 17, 30),
                           ('Nikkei', 'JPXJPY', 'Asia/Tokyo', 15, 0), ('ASX', 'AUXAUD', 'Australia/Sydney', 16, 0)):
    c = cierres(os.path.join(hd, d), tz, hh, mm); ret = np.log(c / c.shift(1)).dropna() * 1e4
    r = ret.reindex(fomc).dropna(); otros = ret.drop(r.index, errors='ignore')
    a, b = r.loc[:'2017'], r.loc['2018':]; an = r.groupby(r.index.year).mean(); t = t_nw(r.values)
    pasa = t >= 2.24 and a.mean() > 0 and b.mean() > 3.5 and (an > 0).mean() >= 0.6
    print(f'{nom}: n {len(r)} {r.mean():+.1f} pb (t {t:+.2f}) | 2010-17 {a.mean():+.1f} | 2018-26 {b.mean():+.1f} (t {t_nw(b.values):+.2f}) | años+ {(an>0).sum()}/{len(an)} '
          f'| inf. resto de días {otros.mean():+.1f} pb -> {"PASA" if pasa else "NO PASA"}')
