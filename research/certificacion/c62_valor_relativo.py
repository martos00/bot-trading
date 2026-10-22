"""C62: reversión del diferencial oro/plata y Brent/WTI. Ver PREREGISTRO_C62."""
import glob, os
import numpy as np, pandas as pd
from scipy import stats
from c1_certificacion import t_nw
from c45_oro_viernes import carga
S = '/tmp/claude-0/-home-user-bot-trading/682335b1-28ae-5d18-9355-ce7f0f968722/scratchpad/'
def futuro(s):
    x = pd.concat([pd.read_csv(f) for f in glob.glob(S + f'databento/curva/{s}_*.csv') if os.path.getsize(f) > 100])
    x = x[x.symbol == f'{s}.c.0']; x['dia'] = pd.to_datetime(x.ts_event).dt.tz_localize(None).dt.normalize()
    y = x.drop_duplicates('dia').set_index('dia').sort_index(); y = y[y.index.weekday < 5]
    return y.close, y.instrument_id
def cfd16(s):
    c = carga(S + 'hd_new/' + s); t = c.index.tz_localize(None)
    m = (t.hour == 15) & (t.minute == 59); return pd.Series(c.values[m], index=t[m].normalize())
def backtest(A, B, coste, cambioA=None, cambioB=None):
    df = pd.concat([np.log(A).rename('a'), np.log(B).rename('b')], axis=1).dropna()
    s = df.a - df.b; z = (s - s.rolling(60).mean().shift(1)) / s.rolling(60).std().shift(1)
    ra, rb = df.a.diff(), df.b.diff()
    if cambioA is not None: ra[cambioA.reindex(df.index) != cambioA.reindex(df.index).shift()] = np.nan
    if cambioB is not None: rb[cambioB.reindex(df.index) != cambioB.reindex(df.index).shift()] = np.nan
    ops, pos, ini, acum, dias = [], 0, None, 0.0, 0
    for i in range(61, len(df)):
        if pos != 0:
            acum += pos * ((ra.iloc[i] if not np.isnan(ra.iloc[i]) else 0) - (rb.iloc[i] if not np.isnan(rb.iloc[i]) else 0)) / 2; dias += 1
            if np.sign(z.iloc[i]) == pos or dias >= 20:
                ops.append((df.index[i], acum - coste - 0.5e-4 * dias, dias)); pos = 0
        elif abs(z.iloc[i]) > 2:
            pos, acum, dias = -np.sign(z.iloc[i]), 0.0, 0                 # z>2: A cara → corto A, largo B (pos=-1 sobre a−b)
    return pd.DataFrame(ops, columns=['dia', 'neto', 'dias']).set_index('dia')
gc, gci = futuro('GC'); si, sii = futuro('SI')
res = {'oro/plata': backtest(gc, si, 6e-4, gci, sii), 'Brent/WTI': backtest(cfd16('BCOUSD'), cfd16('WTIUSD'), 8e-4)}
ps = {}
for k, X in res.items():
    c = X.loc['2018':]; ps[k] = 1 - stats.norm.cdf(t_nw(c.neto.values, 2))
seguir = True
for j, k in enumerate(sorted(ps, key=ps.get)):
    X = res[k]; d, c = X.loc[:'2017'], X.loc['2018':]; an = c.neto.groupby(c.index.year).sum(); t = t_nw(c.neto.values, 2)
    seguir = seguir and ps[k] <= 0.05 / (2 - j); ok = seguir and (an > 0).mean() >= 0.6 and c.neto.mean() > 0
    print(f'{k}: 2010-17 n {len(d)} neto {d.neto.mean()*1e4:.1f} pb/op | 2018-26 n {len(c)} neto {c.neto.mean()*1e4:.1f} pb/op (t {t:.2f}) años+ {(an>0).sum()}/{len(an)} '
          f'días medios {c.dias.mean():.1f} peor {c.neto.min()*1e4:.0f} pb | Holm {seguir} → {"CERTIFICADA" if ok else "no"}')
