"""C102 — regla C99 en HG, 6A, 6N, PL, PA (PREREGISTRO_C102). Uso: python3 c102_ruptura_asiatica_asia.py DIR_SCRATCH"""
import sys
import numpy as np, pandas as pd
from multiprocessing import Pool
from c1_certificacion import t_nw
from c93_oro_ruptura_dia_anterior import carga
import c94_ruptura_otros_futuros as c94
from c99_ruptura_rango_asiatico import simula
SP = sys.argv[1]; c94.SP = SP
COSTE = {'HG': 2.0, '6A': 1.0, '6N': 1.2, 'PL': 3.0, 'PA': 4.0}; HD = {'6A': 'hd_new/AUDUSD', '6N': 'hd_new/NZDUSD'}
def uno(f):
    h, ex = c94.carga_h1(f); a = simula(h, ex)
    b = simula(carga(f'{SP}/{HD[f]}').loc['2010-06-01':'2026-09-30']) if f in HD else None
    return f, a, b
def inf(nom, d): return nom, simula(carga(f'{SP}/hd_new/{d}').loc['2010-06-01':'2026-09-30']), None
if __name__ == '__main__':
    with Pool(5) as pl: res = pl.map(uno, list(COSTE))
    for f, r, q in res:
        an = r.groupby(r.index.year).sum(); t = t_nw(r.values); a, b = r.loc[:'2019'], r.loc['2020':]; co = COSTE[f]
        c = {'t>=2.58': r.mean() > 0 and t >= 2.58, 'años>=60%': (an > 0).mean() >= 0.6, '2010-19>0': a.mean() > 0, '2020-26>0': b.mean() > 0, '>coste': r.mean() > co}
        if q is not None: c['confirmación'] = q.mean() > co and t_nw(q.values) >= 2
        cf = f'HistData 1 min n {len(q)} {q.mean():+.2f} (t {t_nw(q.values):.2f})' if q is not None else 'sin 2.ª fuente'
        print(f'{f}: Databento 1 h n {len(r)} {r.mean():+.2f} pb (t {t:.2f}) años+ {(an>0).sum()}/{len(an)} | 2010-19 {a.mean():+.2f} | 2020-26 {b.mean():+.2f} || {cf} → '
              + ('PASA' if all(c.values()) else 'no pasa: ' + ','.join(k for k, v in c.items() if not v)))
    for nom, d in (('informativo Hang Seng', 'HKXHKD'), ('informativo ASX 200', 'AUXAUD')):
        _, r, _ = inf(nom, d); print(f'{nom}: HistData n {len(r)} {r.mean():+.2f} pb (t {t_nw(r.values):.2f}) | 2020-26 {r.loc["2020":].mean():+.2f}')
