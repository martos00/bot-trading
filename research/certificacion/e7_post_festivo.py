"""E7: E1 el primer día hábil tras un festivo TARGET o del Reino Unido. Ver PREREGISTRO_E7. FXCM M1 mid."""
import glob
from datetime import datetime
from zoneinfo import ZoneInfo
import holidays
import numpy as np, pandas as pd
from dateutil.easter import easter
from scipy import stats
from c1_certificacion import fxcm, en, t_nw
NY = ZoneInfo('America/New_York')
S = '/tmp/claude-0/-home-user-bot-trading/682335b1-28ae-5d18-9355-ce7f0f968722/scratchpad/fxcm/EURUSD/'
b, a = {}, {}
for f in sorted(glob.glob(S + 'EURUSD_*.csv.gz')):
    bb, aa = fxcm(f); b.update(bb); a.update(aa)
uk = holidays.UK(subdiv='ENG', years=range(2011, 2027))
def target(d):
    e = pd.Timestamp(easter(d.year))
    return (d.month, d.day) in ((1, 1), (5, 1), (12, 25), (12, 26)) or d in (e - pd.Timedelta(days=2), e + pd.Timedelta(days=1))
def fest(d): return target(d) or d.date() in uk
filas = []
dias = pd.bdate_range('2012-01-03', '2026-09-30')
for d in dias:
    if fest(d): continue
    prev = d - pd.offsets.BDay(1)
    t0, t1 = datetime(d.year, d.month, d.day, 6, tzinfo=NY), datetime(d.year, d.month, d.day, 8, tzinfo=NY)
    p0, p1 = (en(b, t0) + en(a, t0)) / 2, (en(b, t1) + en(a, t1)) / 2
    if np.isnan([p0, p1]).any(): continue
    filas.append(dict(dia=d, post=fest(prev), lunes=d.weekday() == 0, r=-np.log(p1 / p0)))
X = pd.DataFrame(filas).set_index('dia')
p, q = X[X.post].r, X[~X.post].r
t = stats.ttest_ind(p, q, equal_var=False)
print(f'post-festivo: n {len(p)} media {p.mean()*1e4:.2f} pb (t {t_nw(p.values):.2f}) | resto: n {len(q)} media {q.mean()*1e4:.2f} pb | diferencia {(p.mean()-q.mean())*1e4:.2f} pb (t Welch {t.statistic:.2f})')
l = X[X.lunes & ~X.post].r
print(f'informativo: lunes normales n {len(l)} media {l.mean()*1e4:.2f} pb; resto no lunes {X[~X.lunes & ~X.post].r.mean()*1e4:.2f} pb')
print('DECISIÓN:', 'pasa → pre-registrar regla de tamaño para forward' if t.statistic >= 1.65 else 'no pasa → nada')
