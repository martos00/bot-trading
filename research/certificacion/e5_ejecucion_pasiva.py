"""E5: E1 (EURUSD corto 06:00→08:00 NY) con órdenes limitadas. Ver PREREGISTRO_E5."""
import glob
from datetime import datetime
from zoneinfo import ZoneInfo
import numpy as np, pandas as pd
from dateutil.easter import easter
from c1_certificacion import t_nw
NY = ZoneInfo('America/New_York')
S = '/tmp/claude-0/-home-user-bot-trading/682335b1-28ae-5d18-9355-ce7f0f968722/scratchpad/fxcm/EURUSD/'
COM, DESL = 0.45e-4, 0.1e-4
x = pd.concat([pd.read_csv(f, compression='gzip') for f in sorted(glob.glob(S + 'EURUSD_*.csv.gz'))])
x.index = ((pd.to_datetime(x.DateTime, format='%m/%d/%Y %H:%M:%S.%f') - pd.Timestamp('1970-01-01')) // pd.Timedelta(minutes=1)).to_numpy()
x = x[~x.index.duplicated()].sort_index()
def festivo(d):
    e = pd.Timestamp(easter(d.year))
    return (d.month, d.day) in ((1, 1), (5, 1), (12, 25), (12, 26)) or d in (e - pd.Timedelta(days=2), e + pd.Timedelta(days=1))
def m(d, h, mi): return int(datetime(d.year, d.month, d.day, h, mi, tzinfo=NY).timestamp()) // 60
filas = {}
for d in pd.bdate_range('2012-01-03', '2026-09-30'):
    if festivo(d): continue
    k = [m(d, 5, 59), m(d, 6, 9), m(d, 7, 49), m(d, 7, 59)]
    if not all(i in x.index for i in k): continue
    v_e = x.loc[m(d, 6, 0):m(d, 6, 9)]; v_x = x.loc[m(d, 7, 50):m(d, 7, 59)]
    if len(v_e) < 5 or len(v_x) < 5: continue
    b0, a0 = x.BidClose[k[0]], x.AskClose[k[0]]; b8, a8 = x.BidClose[k[3]], x.AskClose[k[3]]
    ref = np.log(b0 / a8) - COM - 2 * DESL
    Le = a0; pe = (v_e.BidHigh >= Le).any()
    ent = Le if pe else x.BidClose[k[1]]
    Lx = x.BidClose[k[2]]; px = (v_x.AskLow <= Lx).any()
    sal = Lx if px else a8
    e5 = np.log(ent / sal) - COM - DESL * ((not pe) + (not px))
    filas[d] = (ref, e5, pe, px)
X = pd.DataFrame(filas, index=['e1', 'e5', 'pe', 'px']).T.astype(float); X['mej'] = X.e5 - X.e1
for a0, a1 in (('2012', '2018'), ('2019', '2026')):
    y = X.loc[a0:a1]; an = y.mej.groupby(y.index.year).sum()
    print(f'{a0}-{a1}: n {len(y)} E1 neto {y.e1.mean()*1e4:.2f} pb | E5 neto {y.e5.mean()*1e4:.2f} pb (t {t_nw(y.e5.values):.2f}) | mejora {y.mej.mean()*1e4:.2f} pb '
          f'(t {t_nw(y.mej.values):.2f}) años+ {(an>0).sum()}/{len(an)} | relleno pasivo entrada {y.pe.mean()*100:.0f}% salida {y.px.mean()*100:.0f}%')
c = X.loc['2019':]; an = c.mej.groupby(c.index.year).sum()
crit = {'1 mejora t>=2': c.mej.mean() > 0 and t_nw(c.mej.values) >= 2, '2 años>=60%': (an > 0).mean() >= 0.6, '3 E5 neto>0': c.e5.mean() > 0}
print('CRITERIOS:', crit, '→ ADOPTADA' if all(crit.values()) else '→ NO ADOPTADA')
