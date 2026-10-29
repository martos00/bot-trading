"""C101 — regla C99 en SI, CL, NKD, ES (PREREGISTRO_C101). Uso: python3 c101_ruptura_asiatica_otros.py DIR_SCRATCH"""
import sys, glob, os
import numpy as np, pandas as pd
from multiprocessing import Pool
from c1_certificacion import t_nw
from c93_oro_ruptura_dia_anterior import carga
import c94_ruptura_otros_futuros as c94
from c99_ruptura_rango_asiatico import simula
SP = sys.argv[1]; c94.SP = SP

def db_1m(df):
    df.index = pd.DatetimeIndex(pd.to_datetime(df.ts_event, utc=True)).tz_convert('America/New_York'); df = df[~df.index.duplicated()].sort_index()
    ses = (df.index.tz_localize(None) + pd.Timedelta(hours=5)).normalize()
    g = pd.Series(df.instrument_id.values, index=ses).groupby(level=0); moda = g.agg(lambda v: v.mode().iloc[0]); mez = g.nunique() > 1
    excl = set(moda.index[(moda != moda.shift()) | mez])
    return df[['open', 'high', 'low', 'close']].set_axis(['o', 'h', 'l', 'c'], axis=1).loc['2010-06-01':'2026-09-30'], excl

def uno(fut):
    if fut == 'SI':
        p, ex = db_1m(pd.concat([pd.read_csv(f) for f in sorted(glob.glob(f'{SP}/m1/SI_*.csv'))])); a = simula(p, ex)
        b = simula(carga(f'{SP}/hd_new/XAGUSD').loc['2010-06-01':'2026-09-30'])
    elif fut == 'ES':
        p, ex = db_1m(pd.read_pickle(f'{SP}/databento/ES_1m.pkl')); a = simula(p, ex); b = None
    else:
        d = {'CL': 'hd_new/WTIUSD', 'NKD': 'hd_new/JPXJPY'}[fut]
        a = simula(carga(f'{SP}/{d}').loc['2010-06-01':'2026-09-30']); h, ex = c94.carga_h1(fut); b = simula(h, ex)
    return fut, a, b

COSTE = {'SI': 2.3, 'CL': 1.6, 'NKD': 1.5, 'ES': 0.73}
if __name__ == '__main__':
    with Pool(4) as pl: res = pl.map(uno, list(COSTE))
    for fut, r, q in res:
        an = r.groupby(r.index.year).sum(); t = t_nw(r.values); a, b = r.loc[:'2019'], r.loc['2020':]; co = COSTE[fut]
        c = {'t>=2.50': r.mean() > 0 and t >= 2.5, 'años>=60%': (an > 0).mean() >= 0.6, '2010-19>0': a.mean() > 0, '2020-26>0': b.mean() > 0, '>coste': r.mean() > co}
        if q is not None: c['confirmación'] = q.mean() > co and t_nw(q.values) >= 2
        conf = f'confirmación n {len(q)} {q.mean():+.2f} (t {t_nw(q.values):.2f})' if q is not None else 'sin segunda fuente'
        print(f'{fut}: principal n {len(r)} {r.mean():+.2f} pb (t {t:.2f}) años+ {(an>0).sum()}/{len(an)} | 2010-19 {a.mean():+.2f} | 2020-26 {b.mean():+.2f} || {conf} → '
              + ('PASA' if all(c.values()) else 'no pasa: ' + ','.join(k for k, v in c.items() if not v)))
