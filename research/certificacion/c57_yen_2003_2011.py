"""C57: USDJPY largo D−2 07-08 NY en 2003-2011 con HistData. Ver PREREGISTRO_C57."""
import numpy as np, pandas as pd
from c1_certificacion import t_nw
from c45_oro_viernes import carga
from c54_fin_trimestre import tramo
S = '/tmp/claude-0/-home-user-bot-trading/682335b1-28ae-5d18-9355-ce7f0f968722/scratchpad/hd_all/'
def d2(idx):
    dias = pd.DatetimeIndex(sorted(set(idx))); dias = dias[dias.weekday < 5]
    s = pd.Series(range(len(dias)), index=dias); fin = s.groupby(s.index.to_period('M')).cumcount(ascending=False) + 1
    return dias[fin.values == 3]
for p, sg, principal in (('USDJPY', 1, True), ('EURUSD', -1, False), ('USDCHF', 1, False)):
    s = carga(S + p).loc['2003-01-01':'2011-12-31']; r = sg * tramo(s, 7, 0, 7, 59); D = d2(r.index)
    v = r.reindex(D).dropna(); resto = r.drop(D, errors='ignore'); an = v.groupby(v.index.year).sum(); t = t_nw(v.values)
    print(f'{p} {"largo" if sg > 0 else "corto"} D−2 07-08, 2003-11: n {len(v)} {v.mean()*1e4:.2f} pb (t {t:.2f}) años+ {(an>0).sum()}/{len(an)} | resto de días {resto.mean()*1e4:.2f} pb')
    if principal: print('   →', 'PASA' if v.mean() > 0 and t >= 1.65 and (an > 0).mean() >= 0.6 else 'NO PASA', '| por año (pb):', (an * 1e4).round(0).to_dict())
