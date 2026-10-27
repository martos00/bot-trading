"""C78: segunda fuente de las candidatas reaparecidas en la auditoria de la hora de HistData (27-oct-2026).
EURUSD largo Q+1 (1.er dia habil del trimestre) 15:00 -> 16:00 NY con FXCM (punto medio), 2012-2026.
Criterio de C54 (fijado el 22-oct): media > 0 con t (NW) >= 2,0 y >= 60 % de años positivos.
Uso: python3 c78_candidatas_otra_fuente.py DIR_FXCM"""
import sys
import numpy as np, pandas as pd
from c1_certificacion import t_nw
from c77b_fomc_eurusd_fxcm import serie_fxcm
from c76_continuacion_noticias import precio
s = serie_fxcm(sys.argv[1], 'EURUSD')
dias = pd.DatetimeIndex(sorted(set(s.index.normalize()))); dias = dias[dias.dayofweek < 5]
q1 = [g.min() for (y, m), g in pd.Series(dias, index=dias).groupby([dias.year, dias.month]) if m in (1, 4, 7, 10)]
r = {}
for d in q1:
    a, b = precio(s, d + pd.Timedelta(hours=15)), precio(s, d + pd.Timedelta(hours=16))
    if not (np.isnan(a) or np.isnan(b)): r[d] = np.log(b / a) * 1e4
r = pd.Series(r).loc['2012':'2026-09-30']; an = r.groupby(r.index.year).sum()
print(f'EURUSD FXCM Q+1 15->16 largo: n {len(r)} {r.mean():+.2f} pb (t {t_nw(r.values):+.2f}) años+ {(an>0).sum()}/{len(an)} | '
      f'2012-18 {r.loc[:"2018"].mean():+.2f} | 2019-26 {r.loc["2019":].mean():+.2f} -> {"PASA" if r.mean()>0 and t_nw(r.values)>=2 and (an>0).mean()>=0.6 else "NO PASA"}')
