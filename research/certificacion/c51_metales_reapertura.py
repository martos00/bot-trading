"""C51: corto oro/plata tras la reapertura del domingo. Ver PREREGISTRO_C51. Uso: python3 c51... DIR_H1"""
import glob, os, sys
import numpy as np, pandas as pd
from scipy import stats
from c1_certificacion import t_nw
def barras(s):
    x = pd.concat([pd.read_csv(f) for f in sorted(glob.glob(os.path.join(sys.argv[1], f'{s}_*.csv')))])
    x['close'] = pd.to_numeric(x.close, errors='coerce'); x = x[x.close > 0]
    x.index = pd.to_datetime(x.ts_event, utc=True).dt.tz_convert('America/New_York'); x = x[~x.index.duplicated()].sort_index()
    return x
W = {}
for s in ('GC', 'SI'):
    x = barras(s); dom = x[(x.index.weekday == 6) & (x.index.hour == 18)]
    w1, w2 = {}, {}
    for t, fila in dom.iterrows():
        d = t.normalize()
        def p(dt, h):
            k = d + pd.Timedelta(days=dt, hours=h)
            if k in x.index and x.instrument_id[k] == fila.instrument_id: return x.close[k]
            return np.nan
        w1[d] = -np.log(p(0, 20) / fila.close); w2[d] = -np.log(p(1, 7) / fila.close)
    W[(s, 'W1')] = pd.Series(w1); W[(s, 'W2')] = pd.Series(w2)
res, ps = {}, {}
for w in ('W1', 'W2'):
    y = pd.concat([W[('GC', w)], W[('SI', w)]], axis=1).dropna(); y.index = y.index.tz_localize(None)
    m = y.mean(axis=1); an = m.groupby(m.index.year).sum(); t = t_nw(m.values)
    res[w] = (m, an, t); ps[w] = 1 - stats.norm.cdf(t)
    print(f'{w}: n {len(m)} corto {m.mean()*1e4:.2f} pb (t {t:.2f}) | GC {y.iloc[:,0].mean()*1e4:.2f} | SI {y.iloc[:,1].mean()*1e4:.2f} | 2010-17 {m.loc[:"2017"].mean()*1e4:.2f} | 2018-26 {m.loc["2018":].mean()*1e4:.2f} | años+ {(an>0).sum()}/{len(an)}')
orden = sorted(ps, key=ps.get); seguir = True
for k, w in enumerate(orden):
    seguir = seguir and ps[w] <= 0.05 / (2 - k); m, an, t = res[w]
    ok = seguir and (an > 0).mean() >= 0.6 and m.loc['2018':].mean() > 0 and m.mean() >= 3 * 1.5e-4
    print(f'  {w}: Holm {seguir} → {"PASA" if ok else "no"}')
