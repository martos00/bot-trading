"""C94 — regla C93-B (cierre 16:45) en 9 futuros (ver PREREGISTRO_C94). Uso: python3 c94_ruptura_otros_futuros.py DIR_SCRATCH"""
import sys, glob, os
import numpy as np, pandas as pd
from multiprocessing import Pool
from c1_certificacion import t_nw
from c93_oro_ruptura_dia_anterior import carga, simula

SP = sys.argv[1] if len(sys.argv) > 1 else '.'
M = [('SI', 'hd_new/XAGUSD', 2.3), ('CL', 'hd_new/WTIUSD', 1.6), ('6E', 'hd_all/EURUSD', 0.6), ('6B', 'hd_all/GBPUSD', 0.8), ('6J', 'hd_all/USDJPY', 0.8),
     ('6A', 'hd_all/AUDUSD', 1.0), ('6C', 'hd_new/USDCAD', 1.0), ('6S', 'hd_all/USDCHF', 1.0), ('NKD', 'hd_new/JPXJPY', 1.5)]

def carga_h1(fut):
    x = pd.concat([pd.read_csv(f) for f in sorted(glob.glob(f'{SP}/databento/h1/{fut}_[0-9]*.csv'))])
    x.index = pd.to_datetime(x.ts_event).dt.tz_convert('America/New_York'); x = x.sort_index(); x = x[~x.index.duplicated()]
    ses = (x.index.tz_localize(None) + pd.Timedelta(hours=7)).normalize()
    g = pd.Series(x.instrument_id.values, index=ses).groupby(level=0)
    moda = g.agg(lambda v: v.mode().iloc[0]); mezcla = g.nunique() > 1
    excl = set(moda.index[(moda != moda.shift()) | mezcla | mezcla.shift(fill_value=False)])
    return x[['open', 'high', 'low', 'close']].set_axis(['o', 'h', 'l', 'c'], axis=1).loc['2010-06-01':'2026-09-30'], excl

def uno(m):
    fut, d, coste = m
    z = simula(carga(f'{SP}/{d}').loc['2010-06-01':'2026-09-30'], 480, 900, 1005, 1.0)
    h, ex = carga_h1(fut); w = simula(h, 480, 900, 960, 1.0, excluir=ex)
    return fut, coste, z, w

if __name__ == '__main__':
    with Pool(5) as p: res = p.map(uno, M)
    cesta = []
    for fut, coste, z, w in res:
        r = z.r * 1e4; an = r.groupby(r.index.year).sum(); t = t_nw(r.values); a, b = r.loc[:'2019'], r.loc['2020':]
        q = w.r * 1e4; tq = t_nw(q.values)
        c = {'t>=2.54': r.mean() > 0 and t >= 2.54, 'años>=60%': (an > 0).mean() >= 0.6, '2010-19>0': a.mean() > 0, '2020-26>0': b.mean() > 0,
             '>coste': r.mean() > coste, 'Databento t>=2 y >coste': q.mean() > coste and tq >= 2.0}
        lc = [(z.r[z.sg == s] * 1e4).mean() for s in (1, -1)]
        print(f'{fut}: HistData n {len(r)} {r.mean():+.2f} pb (t {t:.2f}) años+ {(an>0).sum()}/{len(an)} | 2010-19 {a.mean():+.2f} | 2020-26 {b.mean():+.2f} '
              f'| largos {lc[0]:+.2f} cortos {lc[1]:+.2f} || Databento 1h n {len(q)} {q.mean():+.2f} pb (t {tq:.2f}) | coste {coste} → '
              + ('PASA' if all(c.values()) else 'no pasa: ' + ','.join(k for k, v in c.items() if not v)))
        cesta.append((z.r / z.r.std()).rename(fut))
    k = pd.concat(cesta, axis=1).fillna(0); s = k.sum(axis=1); s = s[s != 0]
    print(f'informativo cesta igual riesgo (bruta): media por día {s.mean():.3f} (t {t_nw(s.values):.2f}); Sharpe bruto anual {s.mean()/s.std()*np.sqrt(252):.2f}')
