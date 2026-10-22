"""C59: cesta yen fuerte el último día hábil de meses normales, 01-02 NY. Ver PREREGISTRO_C59."""
import glob
from datetime import datetime
from zoneinfo import ZoneInfo
import numpy as np, pandas as pd
from c1_certificacion import fxcm, en, t_nw
from c45_oro_viernes import carga
from c54_fin_trimestre import tramo
NY = ZoneInfo('America/New_York'); S = '/tmp/claude-0/-home-user-bot-trading/682335b1-28ae-5d18-9355-ce7f0f968722/scratchpad/'
NORMAL = [1, 2, 4, 5, 7, 8, 10, 11]
def ultimos(idx, meses):
    dias = pd.DatetimeIndex(sorted(set(idx))); dias = dias[dias.weekday < 5]
    s = pd.Series(range(len(dias)), index=dias); fin = s.groupby(s.index.to_period('M')).cumcount(ascending=False) + 1
    return dias[(fin.values == 1) & np.isin(dias.month, meses)]
def fx(p):
    b, a = {}, {}
    for f in sorted(glob.glob(S + f'fxcm/{p}/{p}_*.csv.gz')):
        bb, aa = fxcm(f); b.update(bb); a.update(aa)
    br, ne = {}, {}
    for d in pd.bdate_range('2012-01-02', '2026-09-30'):
        t0 = datetime(d.year, d.month, d.day, 1, tzinfo=NY); t1 = datetime(d.year, d.month, d.day, 2, tzinfo=NY)
        v = [en(b, t0), en(a, t0), en(b, t1), en(a, t1)]
        if not np.isnan(v).any(): br[d] = -np.log((v[2] + v[3]) / (v[0] + v[1])); ne[d] = np.log(v[0] / v[3]) - 0.45e-4
    br, ne = pd.Series(br), pd.Series(ne); D = ultimos(br.index, NORMAL)
    return br.reindex(D).dropna(), ne.reindex(D).dropna()
B, N = {}, {}
for p in ('EURJPY', 'USDJPY', 'GBPJPY'):
    B[p], N[p] = fx(p); print(f'{p}: n {len(B[p])} bruto {B[p].mean()*1e4:.2f} pb (t {t_nw(B[p].values):.2f}) neto {N[p].mean()*1e4:.2f} pb')
m = pd.DataFrame(B).mean(axis=1).dropna(); mn = pd.DataFrame(N).mean(axis=1).dropna(); an = m.groupby(m.index.year).sum(); t = t_nw(m.values)
ok = m.mean() > 0 and t >= 2 and (an > 0).mean() >= 0.6 and mn.mean() > 0
print(f'PRINCIPAL cesta 2012-26: n {len(m)} bruto {m.mean()*1e4:.2f} pb (t {t:.2f}) neto {mn.mean()*1e4:.2f} pb años+ {(an>0).sum()}/{len(an)} → {"PASA" if ok else "NO PASA"}')
s = carga(S + 'hd_all/USDJPY').loc['2003-01-01':'2011-12-31']; r = -tramo(s, 1, 0, 1, 59); v = r.reindex(ultimos(r.index, NORMAL)).dropna()
print(f'informativo USDJPY HistData 2003-11 meses normales: n {len(v)} {v.mean()*1e4:.2f} pb (t {t_nw(v.values):.2f})')
