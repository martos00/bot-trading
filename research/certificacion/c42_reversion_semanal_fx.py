"""C42: reversión semanal en sección cruzada de 7 divisas frente al USD. Ver PREREGISTRO_C42."""
import glob
from datetime import datetime
from zoneinfo import ZoneInfo
import numpy as np, pandas as pd
from c1_certificacion import fxcm, en, t_nw
NY = ZoneInfo('America/New_York')
S = '/tmp/claude-0/-home-user-bot-trading/682335b1-28ae-5d18-9355-ce7f0f968722/scratchpad/fxcm/'
def carga(par):
    b, a = {}, {}
    for f in sorted(glob.glob(S + f'{par}/{par}_*.csv.gz')):
        bb, aa = fxcm(f); b.update(bb); a.update(aa)
    return b, a
pares = {p: carga(p) for p in ('EURUSD', 'GBPUSD', 'USDJPY', 'USDCHF', 'AUDUSD', 'USDCAD', 'EURNZD')}
def mid(p, t):
    b, a = pares[p]; return (en(b, t) + en(a, t)) / 2
viernes = pd.date_range('2012-01-06', '2026-09-30', freq='W-FRI')
P = {}
for d in viernes:
    for k in range(4):                                 # si el viernes no tiene datos (festivo), el día hábil anterior
        e = d - pd.Timedelta(days=k); t = datetime(e.year, e.month, e.day, 16, tzinfo=NY)
        v = {p: mid(p, t) for p in pares}
        if not np.isnan(list(v.values())).any(): break
    else: continue
    P[d] = {'EUR': v['EURUSD'], 'GBP': v['GBPUSD'], 'JPY': 1 / v['USDJPY'], 'CHF': 1 / v['USDCHF'], 'AUD': v['AUDUSD'],
            'CAD': 1 / v['USDCAD'], 'NZD': v['EURUSD'] / v['EURNZD']}
P = pd.DataFrame(P).T; R = np.log(P).diff()
coste = pd.Series(1.5e-4, index=P.columns); coste['NZD'] = 2.5e-4
def cartera(k):
    out, ant = {}, pd.Series(0.0, index=P.columns)
    for i in range(1, len(R) - 1):
        r = R.iloc[i].dropna()
        if len(r) < 7: ant = ant * 0; continue
        o = r.sort_values(); w = pd.Series(0.0, index=P.columns); w[o.index[:k]] = 1 / (2 * k); w[o.index[-k:]] = -1 / (2 * k)
        nxt = R.iloc[i + 1]
        if nxt.isna().any(): ant = w; continue
        out[R.index[i + 1]] = (w * nxt).sum() - ((w - ant).abs() * coste).sum()
        ant = w
    return pd.Series(out)
for k, nom in ((2, 'principal 2+2'), (1, 'informativo 1+1')):
    x = cartera(k)
    for a0, a1 in (('2012', '2018'), ('2019', '2026')):
        y = x.loc[a0:a1]; an = y.groupby(y.index.year).sum()
        print(f'{nom} {a0}-{a1}: n {len(y)} media {y.mean()*1e4:.2f} pb/sem (t {t_nw(y.values, 4):.2f}) Sharpe {y.mean()/y.std()*np.sqrt(52):.2f} años+ {(an>0).sum()}/{len(an)}')
    if k == 2:
        c = x.loc['2019':]; an = c.groupby(c.index.year).sum()
        crit = {'1 t>=2': c.mean() > 0 and t_nw(c.values, 4) >= 2, '2 años>=60%': (an > 0).mean() >= 0.6}
        print('   por año (%):', (an * 100).round(2).to_dict()); print('CRITERIOS:', crit, '→ CERTIFICADA' if all(crit.values()) else '→ NO CERTIFICADA')
