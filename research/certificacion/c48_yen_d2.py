"""C48: USDJPY largo D−2 07:00→08:00 NY con FXCM BID/ASK. Ver PREREGISTRO_C48."""
import glob
from datetime import datetime
from zoneinfo import ZoneInfo
import numpy as np, pandas as pd
from c1_certificacion import fxcm, en, t_nw
NY = ZoneInfo('America/New_York'); S = '/tmp/claude-0/-home-user-bot-trading/682335b1-28ae-5d18-9355-ce7f0f968722/scratchpad/fxcm/'
COM = 0.45e-4
def carga(p):
    b, a = {}, {}
    for f in sorted(glob.glob(S + f'{p}/{p}_*.csv.gz')):
        bb, aa = fxcm(f); b.update(bb); a.update(aa)
    return b, a
D = {p: carga(p) for p in ('USDJPY', 'USDCHF', 'EURUSD', 'GBPUSD')}
dias = pd.bdate_range('2012-01-02', '2026-09-30')
def tiene(d):
    b, a = D['USDJPY']; t = datetime(d.year, d.month, d.day, 7, tzinfo=NY); return not np.isnan(en(b, t))
dias = [d for d in dias if tiene(d)]
s = pd.Series(range(len(dias)), index=pd.DatetimeIndex(dias)); fin = s.groupby(s.index.to_period('M')).cumcount(ascending=False) + 1
def tramo(p, d, h0, h1, lado):
    b, a = D[p]; t0 = datetime(d.year, d.month, d.day, h0, tzinfo=NY); t1 = datetime(d.year, d.month, d.day, h1, tzinfo=NY)
    b0, a0, b1, a1 = en(b, t0), en(a, t0), en(b, t1), en(a, t1)
    if np.isnan([b0, a0, b1, a1]).any(): return np.nan, np.nan
    bruto = lado * np.log((b1 + a1) / (b0 + a0)); neto = (np.log(b1 / a0) if lado > 0 else np.log(b0 / a1)) - COM
    return bruto, neto
def serie(p, k, h0, h1, lado):
    rr = {d: tramo(p, d, h0, h1, lado) for d in fin.index[fin.values == k]}
    return pd.DataFrame(rr, index=['bruto', 'neto']).T.dropna()
x = serie('USDJPY', 3, 7, 8, +1); an = x.neto.groupby(x.index.year).sum()
print(f'USDJPY largo D−2 07-08 NY: n {len(x)} bruto {x.bruto.mean()*1e4:.2f} pb neto {x.neto.mean()*1e4:.2f} pb (t {t_nw(x.neto.values):.2f}) años+ {(an>0).sum()}/{len(an)} '
      f'| 2012-18 neto {x.neto.loc[:"2018"].mean()*1e4:.2f} | 2019-26 neto {x.neto.loc["2019":].mean()*1e4:.2f} (t {t_nw(x.neto.loc["2019":].values):.2f}) | coste medio {(x.bruto-x.neto).mean()*1e4:.2f} pb')
print('   por año neto (pb):', (an * 1e4).round(1).to_dict())
crit = {'1 t>=2': x.neto.mean() > 0 and t_nw(x.neto.values) >= 2, '2 años>=60%': (an > 0).mean() >= 0.6, '3 2019-26>0': x.neto.loc['2019':].mean() > 0}
print('CRITERIOS:', crit, '→ CONFIRMADA' if all(crit.values()) else '→ NO CONFIRMADA')
print('informativo (bruto, pb, t):')
for nom, cfg in {'USDCHF largo D−2 07-08': ('USDCHF', 3, 7, 8, 1), 'EURUSD corto D−2 07-08': ('EURUSD', 3, 7, 8, -1), 'GBPUSD corto D−2 07-08': ('GBPUSD', 3, 7, 8, -1),
                                   'USDJPY largo D−3 07-08': ('USDJPY', 4, 7, 8, 1), 'USDJPY largo D−1 07-08': ('USDJPY', 2, 7, 8, 1), 'USDJPY largo D−2 06-07': ('USDJPY', 3, 6, 7, 1),
                                   'USDJPY largo D−2 08-09': ('USDJPY', 3, 8, 9, 1), 'USDJPY largo resto de días 07-08': None}.items():
    if nom.startswith('USDJPY largo resto'):
        rr = {d: tramo('USDJPY', d, 7, 8, 1) for d in fin.index[fin.values > 4][::3]}; y = pd.DataFrame(rr, index=['bruto', 'neto']).T.dropna()
    else: y = serie(*cfg)
    print(f'   {nom}: {y.bruto.mean()*1e4:.2f} pb (t {t_nw(y.bruto.values):.2f}) n {len(y)}')
