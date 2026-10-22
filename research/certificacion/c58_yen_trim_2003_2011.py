"""C58: USDJPY corto el último día hábil del trimestre 01-02 NY, 2003-2011 (HistData). Ver PREREGISTRO_C58."""
import numpy as np, pandas as pd
from c1_certificacion import t_nw
from c45_oro_viernes import carga
from c54_fin_trimestre import tramo
s = carga('/tmp/claude-0/-home-user-bot-trading/682335b1-28ae-5d18-9355-ce7f0f968722/scratchpad/hd_all/USDJPY').loc['2003-01-01':'2011-12-31']
r = -tramo(s, 1, 0, 1, 59)
dias = pd.DatetimeIndex(sorted(set(r.index))); dias = dias[dias.weekday < 5]
k = pd.Series(range(len(dias)), index=dias); fin = k.groupby(k.index.to_period('M')).cumcount(ascending=False) + 1
q0 = dias[(fin.values == 1) & np.isin(dias.month, [3, 6, 9, 12])]; m0 = dias[(fin.values == 1) & ~np.isin(dias.month, [3, 6, 9, 12])]
v = r.reindex(q0).dropna(); an = v.groupby(v.index.year).sum(); t = t_nw(v.values, 2)
print(f'USDJPY corto Q0 01-02, 2003-11: n {len(v)} {v.mean()*1e4:.2f} pb (t {t:.2f}) años+ {(an>0).sum()}/{len(an)} → {"PASA" if v.mean() > 0 and t >= 1.65 and (an > 0).mean() >= 0.6 else "NO PASA"}')
w = r.reindex(m0).dropna(); print(f'   informativo: último día de los demás meses {w.mean()*1e4:.2f} pb (t {t_nw(w.values, 2):.2f}, n {len(w)}) | resto de días {r.drop(list(q0) + list(m0), errors="ignore").mean()*1e4:.2f} pb')
