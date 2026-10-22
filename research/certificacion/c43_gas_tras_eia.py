"""C43: gas natural tras el informe EIA del jueves: deriva (D) o reversión (R). Ver PREREGISTRO_C43. Uso: python3 c43_gas_tras_eia.py DIR"""
import glob, os, sys
import numpy as np, pandas as pd
from scipy import stats
from c1_certificacion import t_nw
COSTE = 4.7e-4
filas = {}
for f in sorted(glob.glob(os.path.join(sys.argv[1], '*.csv'))):
    x = pd.read_csv(f)
    if len(x) < 50: continue
    x.index = pd.to_datetime(x.ts_event, utc=True).dt.tz_convert('America/New_York'); x = x.sort_index()
    if x.instrument_id.nunique() > 1: continue
    hm = x.index.hour * 60 + x.index.minute
    def px(m):                                     # precio en el minuto m = cierre de la última vela que empieza antes de m
        y = x.close[(hm < m) & (hm >= m - 10)]
        return y.iloc[-1] if len(y) else np.nan
    p0, p1, p2 = px(10 * 60 + 30), px(10 * 60 + 41), px(14 * 60 + 31)   # 10:29 cierre, 10:40 cierre, 14:30 cierre
    if np.isnan([p0, p1, p2]).any(): continue
    m = np.log(p1 / p0); r = np.log(p2 / p1)
    filas[pd.Timestamp(os.path.basename(f)[:10])] = (m, r)
X = pd.DataFrame(filas, index=['m', 'r']).T
X = X[X.m.abs() >= 0.005]
X['D'] = np.sign(X.m) * X.r; X['R'] = -X['D']
print(f'jueves con |m| >= 0,5%: {len(X)}; correlación m–resto {X.m.corr(X.r):.3f}')
ps, filas2 = [], []
for k in ('D', 'R'):
    d, c = X[k].loc[:'2017'], X[k].loc['2018':]
    t = t_nw((c - COSTE).values); ps.append(1 - stats.norm.cdf(t)); filas2.append((k, d, c, t))
orden = np.argsort(ps); ok = [False] * 2; seguir = True
for j, i in enumerate(orden):
    seguir = seguir and ps[i] <= 0.05 / (2 - j); ok[i] = seguir
for (k, d, c, t), o in zip(filas2, ok):
    an = (c - COSTE).groupby(c.index.year).sum()
    cert = o and (an > 0).mean() >= 0.6 and c.mean() >= 3 * COSTE
    print(f'{k}: 2010-17 n {len(d)} bruto {d.mean()*1e4:.1f} pb (t {t_nw(d.values):.2f}) | 2018-26 n {len(c)} bruto {c.mean()*1e4:.1f} pb neto {(c.mean()-COSTE)*1e4:.1f} pb '
          f'(t {t:.2f}) años+ {(an>0).sum()}/{len(an)} | Holm {o} → {"CERTIFICADA" if cert else "no"}')
