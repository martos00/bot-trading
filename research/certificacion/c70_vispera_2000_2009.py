"""C70: víspera de festivo, cesta no metálica, 2000-2009 con Yahoo. Ver PREREGISTRO_C70."""
import json
import numpy as np, pandas as pd
import holidays
from c1_certificacion import t_nw
D = '/tmp/claude-0/-home-user-bot-trading/682335b1-28ae-5d18-9355-ce7f0f968722/scratchpad/yahoo_c70/'
FEST = {pd.Timestamp(d) for d in holidays.financial_holidays('NYSE', years=range(1999, 2012))}
HAB = pd.bdate_range('1999-01-01', '2011-12-31'); HAB = HAB[~HAB.isin(list(FEST))]
PRE = pd.DatetimeIndex(sorted({HAB[HAB.searchsorted(f) - 1] for f in FEST if 0 < HAB.searchsorted(f) < len(HAB)}))
r = {}
for s in ['CL', 'HO', 'RB', 'NG', 'ZC', 'ZS', 'ZW', 'ZL', 'ZM', 'KE', 'LE', 'HE']:
    j = json.load(open(D + f'{s}.json'))['chart']['result'][0]
    c = pd.Series(j['indicators']['quote'][0]['close'], index=pd.to_datetime(j['timestamp'], unit='s').normalize()).dropna()
    c = c[~c.index.duplicated()].sort_index(); q = np.log(c).diff(); q[q.abs() > 0.08] = np.nan; r[s] = q
R = pd.DataFrame(r).loc['2000-01-01':'2009-12-31']; m = R.mean(axis=1)
v = m.reindex(PRE).dropna(); an = v.groupby(v.index.year).sum(); t = t_nw(v.values, 2)
print('mercados con datos:', {s: f'{R[s].first_valid_index().date()}' for s in R if R[s].notna().any()})
print(f'C70 cesta no metálica PRE 2000-09: n {len(v)} {v.mean()*1e4:.2f} pb (t {t:.2f}) años+ {(an>0).sum()}/{len(an)} | resto {m.drop(v.index, errors="ignore").mean()*1e4:.2f} pb → {"PASA" if v.mean() > 0 and t >= 2 and (an > 0).mean() >= 0.6 else "NO PASA"}')
