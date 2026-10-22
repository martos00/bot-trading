"""C44: estacionalidad del mismo mes (KLN 2016) en 16 materias primas. Ver PREREGISTRO_C44. Uso: python3 c44... DIR_CURVA"""
import glob, os, sys
import numpy as np, pandas as pd
from c1_certificacion import t_nw
D = sys.argv[1]
SIMS = ['CL', 'HO', 'RB', 'NG', 'GC', 'SI', 'HG', 'PL', 'ZC', 'ZS', 'ZW', 'ZL', 'ZM', 'KE', 'LE', 'HE']
r = {}
for s in SIMS:
    x = pd.concat([pd.read_csv(f) for f in glob.glob(os.path.join(D, f'{s}_*.csv')) if os.path.getsize(f) > 100])
    x = x[x.symbol == f'{s}.c.0']; x['dia'] = pd.to_datetime(x.ts_event).dt.tz_localize(None).dt.normalize()
    y = x.drop_duplicates('dia').set_index('dia').sort_index(); y = y[y.index.weekday < 5]
    with np.errstate(invalid='ignore', divide='ignore'):
        q = np.log(y.close.where(y.close > 0)).diff()
    q[y.instrument_id != y.instrument_id.shift()] = np.nan; r[s] = q
R = pd.DataFrame(r).loc[:'2026-09-30']
n = R.notna().groupby(R.index.to_period('M')).sum(); M = R.groupby(R.index.to_period('M')).sum(min_count=1); M[n < 10] = np.nan
out, ant = {}, pd.Series(0.0, index=SIMS)
for i in range(1, len(M)):
    per = M.index[i]; hist = M.iloc[:i]; hist = hist[hist.index.month == per.month]
    sg = hist.mean().where(hist.notna().sum() >= 5).dropna(); nxt = M.iloc[i]
    sg = sg[nxt.reindex(sg.index).notna()]
    if len(sg) < 9: continue
    k = len(sg) // 3; o = sg.sort_values(); w = pd.Series(0.0, index=SIMS); w[o.index[-k:]] = 1 / k; w[o.index[:k]] = -1 / k
    out[per.to_timestamp()] = (w * nxt.reindex(SIMS).fillna(0)).sum() - (w - ant).abs().sum() * 3e-4; ant = w
x = pd.Series(out); c = x.loc['2016':]; an = c.groupby(c.index.year).sum()
print(f'meses evaluados: {len(x)} (desde {x.index.min().date()}); 2016-2026: n {len(c)} media {c.mean()*100:.2f} %/mes (t {t_nw(c.values, 3):.2f}) '
      f'Sharpe {c.mean()/c.std()*np.sqrt(12):.2f} años+ {(an>0).sum()}/{len(an)}')
print('por año (%):', (an * 100).round(1).to_dict())
crit = {'1 t>=2': c.mean() > 0 and t_nw(c.values, 3) >= 2, '2 años>=60%': (an > 0).mean() >= 0.6}
print('CRITERIOS:', crit, '→ CERTIFICADA' if all(crit.values()) else '→ NO CERTIFICADA')
