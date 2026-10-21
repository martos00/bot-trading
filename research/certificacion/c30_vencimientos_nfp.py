"""C30: semana de vencimiento mensual (ES) y ventana previa al NFP (GC, ZN). Ver PREREGISTRO_C30.
Uso: python3 c30_vencimientos_nfp.py ES_1m.pkl DIR_H1"""
import glob, os, sys
import numpy as np, pandas as pd
from scipy import stats
from c1_certificacion import t_nw
es_pkl, H = sys.argv[1:3]
res = {}
# X: cierres de las 16:00 NY del ES (última barra M1 que termina ≤ 16:00) con su contrato
x = pd.read_pickle(es_pkl); t = pd.to_datetime(x.ts_event).dt.tz_convert('America/New_York').dt.tz_localize(None) + pd.Timedelta(minutes=1)
x = x.assign(t=t)[(t.dt.hour * 60 + t.dt.minute <= 960) & (t.dt.hour * 60 + t.dt.minute > 900) & (t.dt.weekday < 5)]
c = x.groupby(x.t.dt.normalize()).agg(c=('close', 'last'), id=('instrument_id', 'last'))
c = c.loc[:'2026-09-30']
def tercer_viernes(y, m):
    d = pd.Timestamp(y, m, 1); return d + pd.Timedelta(days=(4 - d.weekday()) % 7 + 14)
ev, otras = [], []
viernes = [d for d in c.index if d.weekday() == 4]
for i in range(1, len(viernes)):
    v0, v1 = viernes[i - 1], viernes[i]
    if (v1 - v0).days != 7 or c.id[v0] != c.id[v1]: continue
    r = np.log(c.c[v1] / c.c[v0])
    (ev if v1 == tercer_viernes(v1.year, v1.month) else otras).append((v1, r))
X = pd.Series(dict(ev)); O = pd.Series(dict(otras))
res['X ES semana de vencimiento (+)'] = (X, O, 0.6e-4, +1)
# N: GC y ZN de 17:00 NY del jueves a 08:00 NY del viernes del NFP (primer viernes)
for s, co in (('GC', 0.5e-4), ('ZN', 1.8e-4)):
    h = pd.concat([pd.read_csv(f, parse_dates=['ts_event']) for f in sorted(glob.glob(os.path.join(H, f'{s}_*.csv')))]).drop_duplicates('ts_event')
    fin = h.ts_event.dt.tz_convert('America/New_York').dt.tz_localize(None) + pd.Timedelta(hours=1)
    h = pd.DataFrame({'c': h.close.values, 'id': h.instrument_id.values}, index=fin).sort_index()
    def pre(f):
        a = h.loc[f - pd.Timedelta(days=1) + pd.Timedelta(hours=17)] if (f - pd.Timedelta(days=1) + pd.Timedelta(hours=17)) in h.index else None
        b = h.loc[f + pd.Timedelta(hours=8)] if (f + pd.Timedelta(hours=8)) in h.index else None
        if a is None or b is None or a.id != b.id: return np.nan
        return np.log(b.c / a.c)
    nfp = [tercer_viernes(y, m) - pd.Timedelta(days=14) for y in range(2010, 2027) for m in range(1, 13)]
    nfp = [f for f in nfp if pd.Timestamp('2010-07-01') <= f <= pd.Timestamp('2026-09-30')]
    N = pd.Series({f: pre(f) for f in nfp}).dropna()
    otros = [f for f in pd.date_range('2010-07-01', '2026-09-30', freq='W-FRI') if f not in set(nfp)]
    NO = pd.Series({f: pre(f) for f in otros}).dropna()
    sg = np.sign(N.loc[:'2017'].mean())
    res[f'N {s} pre-NFP (sentido {"+" if sg > 0 else "-"})'] = (N * sg, NO * sg, co, 0)
ps, filas = [], []
for nom, (x, o, co, prev) in res.items():
    d, cf = x.loc[:'2017'], x.loc['2018':]; an = (cf - co).groupby(cf.index.year).sum(); t = t_nw(cf.values)
    ps.append(1 - stats.norm.cdf(t)); filas.append((nom, d, cf, an, co, o.loc['2018':]))
orden = np.argsort(ps); ok = [False] * len(filas); seguir = True
for k, i in enumerate(orden):
    seguir = seguir and ps[i] <= 0.05 / (len(filas) - k); ok[i] = seguir
for (nom, d, cf, an, co, oc), okh in zip(filas, ok):
    dif = (cf.mean() - oc.mean()) / np.sqrt(cf.var() / len(cf) + oc.var() / len(oc))
    cert = d.mean() > 0 and okh and (an > 0).mean() >= 0.6 and cf.mean() >= 3 * co
    print(f'{nom}: 2010-17 n {len(d)} {d.mean()*1e4:6.1f} pb (t {t_nw(d.values):.2f}) | 2018-26 n {len(cf)} {cf.mean()*1e4:6.1f} pb (t {t_nw(cf.values):.2f}) '
          f'años+ {(an>0).sum()}/{len(an)} | resto {oc.mean()*1e4:.1f} pb dif t {dif:.2f} | Holm {okh} → {"CERTIFICADA" if cert else "no"}')
