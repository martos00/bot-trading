"""C60: Nikkei (JPXJPY HistData) largo el 2.º día hábil del trimestre 15-16 NY. Ver PREREGISTRO_C60."""
import numpy as np, pandas as pd
from c1_certificacion import t_nw
from c45_oro_viernes import carga
from c54_fin_trimestre import tramo
s = carga('/tmp/claude-0/-home-user-bot-trading/682335b1-28ae-5d18-9355-ce7f0f968722/scratchpad/hd_new/JPXJPY').loc['2010-11-01':'2026-09-30']
r = tramo(s, 15, 0, 15, 59)
dias = pd.DatetimeIndex(sorted(set(r.index))); dias = dias[dias.weekday < 5]
k = pd.Series(range(len(dias)), index=dias); pos = k.groupby(k.index.to_period('M')).cumcount().values + 1
qn = np.isin(dias.month, [1, 4, 7, 10])
def inf(nom, D, principal=False):
    v = r.reindex(D).dropna(); an = v.groupby(v.index.year).sum(); t = t_nw(v.values, 2)
    print(f'{nom}: n {len(v)} {v.mean()*1e4:.2f} pb (t {t:.2f}) años+ {(an>0).sum()}/{len(an)} | 2018-26 {v.loc["2018":].mean()*1e4:.2f} pb (t {t_nw(v.loc["2018":].values, 2):.2f})')
    if principal: print('   →', 'PASA' if v.mean() > 0 and t >= 2 and (an > 0).mean() >= 0.6 else 'NO PASA')
inf('JPXJPY Q+2 15-16 largo (principal)', dias[(pos == 2) & qn], True)
inf('   inf. Q+1', dias[(pos == 1) & qn]); inf('   inf. Q+3', dias[(pos == 3) & qn]); inf('   inf. D+2 meses normales', dias[(pos == 2) & ~qn])
print(f'   inf. resto de días {r.mean()*1e4:.2f} pb')
