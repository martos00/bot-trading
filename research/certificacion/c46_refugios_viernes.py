"""C46: refugios en la última hora del viernes (16:00-17:00 NY). Ver PREREGISTRO_C46. Uso: python3 c46... DIR_H1 ES_1m.pkl"""
import glob, os, sys
import numpy as np, pandas as pd
from scipy import stats
from c1_certificacion import t_nw
H, ES = sys.argv[1:3]
COSTE = {'ES': 0.73, 'ZN': 1.8, 'ZB': 2.7, '6J': 1.2}
SIGNO = {'6J': 1, 'ZN': 1, 'ZB': 1, 'ES': -1}
def horario(s):                                     # copia de b2_barrido_futuros.horario
    if s == 'ES':
        x = pd.read_pickle(ES); t = pd.to_datetime(x.ts_event).dt.tz_convert('America/New_York').dt.tz_localize(None) + pd.Timedelta(minutes=1)
        return x.assign(t=t.dt.ceil('h')).groupby('t').agg(c=('close', 'last'), id=('instrument_id', 'last'))
    x = pd.concat([pd.read_csv(f, parse_dates=['ts_event']) for f in sorted(glob.glob(os.path.join(H, f'{s}_*.csv')))]).drop_duplicates('ts_event')
    fin = x.ts_event.dt.tz_convert('America/New_York').dt.tz_localize(None) + pd.Timedelta(hours=1)
    return pd.DataFrame({'c': x.close.values, 'id': x.instrument_id.values}, index=fin).sort_index()
R = {}
for s in SIGNO:
    h = horario(s).loc[:'2026-09-30']; h = h[h.index.weekday == 4]
    a = h[h.index.hour == 16]; b = h[h.index.hour == 17]
    a.index = a.index.normalize(); b.index = b.index.normalize()
    j = a.join(b, lsuffix='0', rsuffix='1', how='inner'); j = j[j.id0 == j.id1]
    R[s] = SIGNO[s] * np.log(j.c1 / j.c0)
X = pd.DataFrame(R)
ps = {}
for s in X:
    y = X[s].dropna(); t = t_nw(y.values); ps[s] = 1 - stats.norm.cdf(t)
    an = y.groupby(y.index.year).sum()
    print(f'{s} ({"largo" if SIGNO[s] > 0 else "corto"}): n {len(y)} {y.mean()*1e4:.2f} pb (t {t:.2f}) | 2010-17 {y.loc[:"2017"].mean()*1e4:.2f} | 2018-26 {y.loc["2018":].mean()*1e4:.2f} (t {t_nw(y.loc["2018":].values):.2f}) | años+ {(an>0).sum()}/{len(an)} | coste {COSTE[s]}')
m = X.mean(axis=1).dropna(); print(f'CONJUNTA (media de las 4 con su signo): {m.mean()*1e4:.2f} pb (t {t_nw(m.values):.2f}) → {"PASA" if t_nw(m.values) >= 2 else "NO PASA"}')
orden = sorted(ps, key=ps.get); seguir = True
for k, s in enumerate(orden):
    seguir = seguir and ps[s] <= 0.05 / (4 - k)
    print(f'  Holm {s}: {"significativa" if seguir else "no"}')
