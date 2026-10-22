"""C67: cesta corto USDJPY + corto USDCHF + corto AUDUSD el viernes 16:00-16:55 NY (FXCM). Ver PREREGISTRO_C67."""
import glob
from datetime import datetime
from zoneinfo import ZoneInfo
import numpy as np, pandas as pd
import holidays
from c1_certificacion import fxcm, en, t_nw
NY = ZoneInfo('America/New_York'); S = '/tmp/claude-0/-home-user-bot-trading/682335b1-28ae-5d18-9355-ce7f0f968722/scratchpad/fxcm/'
FEST = {pd.Timestamp(d) for d in holidays.financial_holidays('NYSE', years=range(2011, 2028))}
HAB = pd.bdate_range('2011-01-01', '2027-12-31'); HAB = HAB[~HAB.isin(list(FEST))]
PRE = {HAB[HAB.searchsorted(f) - 1] for f in FEST if 0 < HAB.searchsorted(f) < len(HAB)}
B, N = {}, {}
for p in ('USDJPY', 'USDCHF', 'AUDUSD'):
    b, a = {}, {}
    for f in sorted(glob.glob(S + f'{p}/{p}_*.csv.gz')):
        bb, aa = fxcm(f); b.update(bb); a.update(aa)
    br, ne = {}, {}
    for d in pd.bdate_range('2012-01-02', '2026-09-30'):
        if d.weekday() != 4 and d not in PRE: continue
        t0 = datetime(d.year, d.month, d.day, 16, tzinfo=NY); t1 = t0.replace(minute=55)
        v = [en(b, t0), en(a, t0), en(b, t1), en(a, t1)]
        if np.isnan(v).any(): continue
        br[d] = -np.log((v[2] + v[3]) / (v[0] + v[1])); ne[d] = np.log(v[0] / v[3]) - 0.45e-4        # corto: vende al BID, recompra al ASK
    B[p], N[p] = pd.Series(br), pd.Series(ne)
Bm = pd.DataFrame(B).mean(axis=1).dropna(); Nm = pd.DataFrame(N).mean(axis=1).dropna()
for p in B: v = B[p][B[p].index.weekday == 4]; print(f'{p} corto viernes: {v.mean()*1e4:.2f} pb (t {t_nw(v.values):.2f}) neto {N[p][N[p].index.weekday == 4].mean()*1e4:.2f} pb')
v = Bm[Bm.index.weekday == 4]; vn = Nm[Nm.index.weekday == 4]; an = v.groupby(v.index.year).sum(); t = t_nw(v.values)
print(f'CESTA viernes: n {len(v)} bruto {v.mean()*1e4:.2f} pb (t {t:.2f}) años+ {(an>0).sum()}/{len(an)} | neto {vn.mean()*1e4:.2f} pb → {"PASA (existe)" if v.mean() > 0 and t >= 2 and (an > 0).mean() >= 0.6 else "NO PASA"}{"; neto ≤ 0: NO OPERABLE" if vn.mean() <= 0 else ""}')
w = Bm[Bm.index.isin(list(PRE)) & (Bm.index.weekday != 4)]; print(f'informativo vísperas no viernes: n {len(w)} {w.mean()*1e4:.2f} pb (t {t_nw(w.values):.2f})')
