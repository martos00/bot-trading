"""C55: yen a fin de trimestre 01-02 NY en USDJPY, GBPJPY (FXCM) y AUDJPY (HistData). Ver PREREGISTRO_C55."""
import glob
from datetime import datetime
from zoneinfo import ZoneInfo
import numpy as np, pandas as pd
from c1_certificacion import fxcm, en, t_nw
from c45_oro_viernes import carga
from c54_fin_trimestre import tramo
NY = ZoneInfo('America/New_York'); S = '/tmp/claude-0/-home-user-bot-trading/682335b1-28ae-5d18-9355-ce7f0f968722/scratchpad/'
def q0_dias(idx):
    dias = pd.DatetimeIndex(sorted(set(idx))); dias = dias[dias.weekday < 5]
    s = pd.Series(range(len(dias)), index=dias); fin = s.groupby(s.index.to_period('M')).cumcount(ascending=False) + 1
    return dias[(fin.values == 1) & np.isin(dias.month, [3, 6, 9, 12])]
def fx(p):
    b, a = {}, {}
    for f in sorted(glob.glob(S + f'fxcm/{p}/{p}_*.csv.gz')):
        bb, aa = fxcm(f); b.update(bb); a.update(aa)
    r = {}
    for d in pd.bdate_range('2012-01-02', '2026-09-30'):
        t0 = datetime(d.year, d.month, d.day, 1, tzinfo=NY); t1 = datetime(d.year, d.month, d.day, 2, tzinfo=NY)
        v = [en(b, t0), en(a, t0), en(b, t1), en(a, t1)]
        if not np.isnan(v).any(): r[d] = -np.log((v[2] + v[3]) / (v[0] + v[1]))
    r = pd.Series(r); return r.reindex(q0_dias(r.index)).dropna()
R = {p: fx(p) for p in ('USDJPY', 'GBPJPY', 'EURJPY')}
aj = -tramo(carga(S + 'hd_new/AUDJPY').loc['2012':'2026-09-30'], 1, 0, 1, 59); R['AUDJPY'] = aj.reindex(q0_dias(aj.index)).dropna()
X = pd.DataFrame(R)
for p in X: y = X[p].dropna(); print(f'{p} corto Q0 01-02: n {len(y)} {y.mean()*1e4:.2f} pb (t {t_nw(y.values):.2f}) años+ {(y.groupby(y.index.year).sum()>0).sum()}/{y.index.year.nunique()}')
m = X[['USDJPY', 'GBPJPY', 'AUDJPY']].mean(axis=1).dropna(); t = t_nw(m.values)
print(f'PRINCIPAL media USDJPY+GBPJPY+AUDJPY: n {len(m)} {m.mean()*1e4:.2f} pb (t {t:.2f}) → {"PASA" if m.mean() > 0 and t >= 2 else "NO PASA"}')
m4 = X.mean(axis=1).dropna()
print(f'dosis-respuesta (4 pares): marzo {m4[m4.index.month == 3].mean()*1e4:.2f} pb (n {(m4.index.month == 3).sum()}) | jun/sep/dic {m4[m4.index.month != 3].mean()*1e4:.2f} pb')
