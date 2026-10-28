"""E10b: plata larga en vispera de festivo NYSE 16:00 -> 16:45 NY, segunda fuente HistData (PREREGISTRO_E10b). Uso: python3 e10b_plata_vispera_1645.py DIR_XAG"""
import sys
import holidays, numpy as np, pandas as pd
from c1_certificacion import t_nw
from c45_oro_viernes import carga, tramo
fest = holidays.financial_holidays('NYSE', years=range(2010, 2027))
s = carga(sys.argv[1]).loc['2010-06-01':'2026-09-30']
r = tramo(s, 16, 0, 16, 44) * 1e4
def vispera(d):
    if d.weekday() >= 5 or d.date() in fest: return False
    n = d + pd.Timedelta(days=1)
    while n.weekday() >= 5: n += pd.Timedelta(days=1)
    return n.date() in fest
v = r[[vispera(d) for d in r.index]]
an = v.groupby(v.index.year).mean(); t = t_nw(v.values); b = v.loc['2018':]
pasa = v.mean() > 0 and t >= 2 and (an > 0).mean() >= 0.6 and b.mean() > 2.3
print(f'XAGUSD vispera 16:00->16:45: n {len(v)} {v.mean():+.2f} pb (t {t:+.2f}) años+ {(an>0).sum()}/{len(an)} | 2010-17 {v.loc[:"2017"].mean():+.2f} | 2018-26 {b.mean():+.2f} (t {t_nw(b.values):+.2f}) | resto de dias {r.drop(v.index).mean():+.2f} -> {"PASA" if pasa else "NO PASA"}')
