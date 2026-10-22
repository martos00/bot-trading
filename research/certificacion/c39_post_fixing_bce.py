"""C39: rebote del EURUSD tras el fixing del BCE (14:15 Frankfurt). Ver PREREGISTRO_C39."""
from datetime import datetime
from zoneinfo import ZoneInfo
import numpy as np, pandas as pd
from c1_certificacion import t_nw
import glob
from c1_certificacion import fxcm, en
S = '/tmp/claude-0/-home-user-bot-trading/682335b1-28ae-5d18-9355-ce7f0f968722/scratchpad/'
COM, DESL = 0.45e-4, 0.1e-4
def carga(par):                              # copia de c32_google (mismos datos FXCM)
    b, a = {}, {}
    for f in sorted(glob.glob(S + f'fxcm/{par}/{par}_*.csv.gz')):
        bb, aa = fxcm(f); b.update(bb); a.update(aa)
    return b, a
def ejec(b, a, t0, t1, lado):                # copia de c32_google: ASK/BID reales, comisión y deslizamiento
    b0, a0, b1, a1 = en(b, t0), en(a, t0), en(b, t1), en(a, t1)
    if np.isnan([b0, a0, b1, a1]).any(): return np.nan, np.nan
    bruto = lado * np.log(((b1 + a1) / 2) / ((b0 + a0) / 2))
    neto = (np.log(b1 / a0) if lado > 0 else np.log(b0 / a1)) - COM - 2 * DESL
    return bruto, neto
FRA = ZoneInfo('Europe/Berlin')
def festivo(d):
    from dateutil.easter import easter
    e = pd.Timestamp(easter(d.year))
    return (d.month, d.day) in ((1, 1), (5, 1), (12, 25), (12, 26)) or d in (e - pd.Timedelta(days=2), e + pd.Timedelta(days=1))
b, a = carga('EURUSD')
filas = {}
for d in pd.bdate_range('2012-01-03', '2026-09-30'):
    if festivo(d): continue
    t = lambda h, m: datetime(d.year, d.month, d.day, h, m, tzinfo=FRA)
    p = ejec(b, a, t(14, 15), t(15, 15), +1); q = ejec(b, a, t(14, 15), t(14, 45), +1); r = ejec(b, a, t(14, 0), t(14, 15), -1)
    if not np.isnan(p[0]): filas[d] = (*p, *q, *r)
X = pd.DataFrame(filas, index=['bruto', 'neto', 'b30', 'n30', 'bpre', 'npre']).T
for a0, a1 in (('2012', '2018'), ('2019', '2026')):
    y = X.loc[a0:a1]; an = y.neto.groupby(y.index.year).sum()
    print(f'{a0}-{a1}: n {len(y)} bruto {y.bruto.mean()*1e4:.2f} pb neto {y.neto.mean()*1e4:.2f} pb (t {t_nw(y.neto.values):.2f}) años+ {(an>0).sum()}/{len(an)} '
          f'| inf. 14:15-14:45 bruto {y.b30.mean()*1e4:.2f} pb (t {t_nw(y.b30.dropna().values):.2f}) | inf. 14:00-14:15 corto bruto {y.bpre.mean()*1e4:.2f} pb (t {t_nw(y.bpre.dropna().values):.2f})')
c = X.loc['2019':]; an = c.neto.groupby(c.index.year).sum(); coste = (c.bruto - c.neto).mean()
crit = {'1 t>=2': c.neto.mean() > 0 and t_nw(c.neto.values) >= 2, '2 años>=60%': (an > 0).mean() >= 0.6, '3 bruto>=3·coste': c.bruto.mean() >= 3 * coste}
print(f'coste medio {coste*1e4:.2f} pb; CRITERIOS:', crit, '→ CERTIFICADA' if all(crit.values()) else '→ NO CERTIFICADA')
