"""C28: grano el día del WASDE, oro antes del aviso de entrega, ganado el día de Cattle on Feed (PREREGISTRO_C28).
Uso: python3 c28_grano_oro_ganado.py DIR_AGRO DIR_FECHAS_USDA"""
import glob, os, sys
import numpy as np, pandas as pd
from scipy import stats
from c1_certificacion import t_nw
D, F = sys.argv[1:3]
def serie(s):
    x = pd.concat([pd.read_csv(f, parse_dates=['ts_event']) for f in sorted(glob.glob(os.path.join(D, f'{s}_*.csv')))])
    x['dia'] = x.ts_event.dt.tz_localize(None).dt.normalize()
    x = x[x.dia.dt.weekday < 5].drop_duplicates('dia').set_index('dia').sort_index()
    r = np.log(x.close).diff(); r[x.instrument_id != x.instrument_id.shift()] = np.nan
    return r.loc[:'2026-09-30']
def fechas(n): return pd.to_datetime(open(os.path.join(F, n + '.fechas')).read().split())
def tdif(a, b): return (a.mean() - b.mean()) / np.sqrt(a.var() / len(a) + b.var() / len(b))
res = {}
# W: corto el día del WASDE (rentabilidad del día del informe)
w = fechas('world-agricultural-supply-and-demand-estimates')
ws = []
for s in ('ZC', 'ZS', 'ZW'):
    r = serie(s); ws.append((-r.reindex(w)).dropna().rename(s))
W = pd.concat(ws, axis=1).mean(axis=1, skipna=False).dropna()
Wresto = pd.concat([-serie(s).rename(s) for s in ('ZC', 'ZS', 'ZW')], axis=1).mean(axis=1).drop(W.index, errors='ignore').dropna()
res['W grano día WASDE'] = (W, Wresto, 6e-4)
# G: corto de oro de FND−6 a FND−1
r = serie('GC'); ix = r.index; ev = []
for y in range(2010, 2027):
    for m in (1, 3, 5, 7, 9, 11):
        fnd = pd.Timestamp(y, m, 1) + pd.offsets.BMonthEnd(0)
        if fnd > pd.Timestamp('2026-09-30') or fnd < ix[10]: continue
        i = ix.searchsorted(fnd)
        if i >= len(ix): continue
        tramo = r.iloc[i - 6:i - 1]
        if len(tramo) == 5 and tramo.notna().all(): ev.append((ix[i], -tramo.sum()))
G = pd.Series(dict(ev))
Gresto = pd.Series([-r.iloc[j:j + 5].sum() for j in range(0, len(r) - 5, 5)], index=r.index[0:len(r) - 5:5]).dropna()
res['G oro antes del aviso de entrega'] = (G, Gresto, 1e-4)
# L: corto de ganado el día de Cattle on Feed
c = fechas('cattle-feed'); r = serie('LE')
L = (-r.reindex(c)).dropna(); res['L ganado día Cattle on Feed'] = (L, (-r.drop(L.index, errors='ignore')).dropna(), 2e-4)
ps, filas = [], []
for nom, (x, o, co) in res.items():
    d, cf = x.loc['2010':'2017'], x.loc['2018':'2026']; ne = cf - co; an = ne.groupby(ne.index.year).sum()
    t = t_nw(ne.values); ps.append(1 - stats.norm.cdf(t))
    filas.append((nom, d, cf, ne, an, co, o))
orden = np.argsort(ps); ok = [False] * 3; seguir = True
for k, i in enumerate(orden):
    seguir = seguir and ps[i] <= 0.05 / (3 - k); ok[i] = seguir
for (nom, d, cf, ne, an, co, o), okh in zip(filas, ok):
    oc = o.loc['2018':'2026']
    cert = d.mean() > 0 and okh and (an > 0).mean() >= 0.6 and cf.mean() >= 3 * co and tdif(cf, oc) >= 1.645
    print(f'{nom}: 2010-17 n {len(d)} {d.mean()*1e4:6.1f} pb (t {t_nw(d.values):.2f}) | 2018-26 n {len(cf)} bruto {cf.mean()*1e4:6.1f} pb '
          f'neto {ne.mean()*1e4:6.1f} pb (t {t_nw(ne.values):.2f}) años+ {(an>0).sum()}/{len(an)} | normal {oc.mean()*1e4:.1f} pb dif t {tdif(cf, oc):.2f} | Holm {okh} → {"CERTIFICADA" if cert else "no"}')
    print('   neto por año (pb):', (an * 1e4).round(0).to_dict())
