"""C79: el dolar tras las subastas del Tesoro (PREREGISTRO_C79, commit 1cc8525). Uso: python3 c79_divisas_subastas.py SUBASTAS_JSON DIR_FXCM"""
import json, sys
import numpy as np, pandas as pd
from c1_certificacion import t_nw
from c77b_fomc_eurusd_fxcm import serie_fxcm
from c76_continuacion_noticias import precio
TERM = ('2-Year', '3-Year', '5-Year', '7-Year', '10-Year', '20-Year', '30-Year')
d = json.load(open(sys.argv[1]))['data']
sub = sorted({pd.Timestamp(x['auction_date']) for x in d if x['security_type'] in ('Note', 'Bond') and x['inflation_index_security'] == 'No'
              and x['floating_rate'] == 'No' and any(x['security_term'].startswith(t) for t in TERM)})
sub = pd.DatetimeIndex(sub); sub = sub[(sub >= '2012-01-01') & (sub <= '2026-09-30')]
P = {p: serie_fxcm(sys.argv[2], p) for p in ('EURUSD', 'USDJPY', 'GBPUSD')}
SG = {'EURUSD': -1, 'USDJPY': 1, 'GBPUSD': -1}
dias = pd.DatetimeIndex(sorted(set(P['EURUSD'].index.normalize()))); dias = dias[dias.dayofweek < 5]
sig = {d0: d1 for d0, d1 in zip(dias[:-1], dias[1:])}
def dolar(d0, t0, d1, t1):
    v = [SG[p] * np.log(precio(P[p], d1 + t1) / precio(P[p], d0 + t0)) for p in P]
    return np.nanmean(v) * 1e4 if np.sum(~np.isnan(v)) == 3 else np.nan
h13, h14 = pd.Timedelta(hours=13), pd.Timedelta(hours=14)
es_sub = set(sub)
for nom, fn in (('W1 13:00->14:00', lambda x: dolar(x, h13, x, h14)), ('W2 13:00->13:00 dia siguiente', lambda x: dolar(x, h13, sig[x], h13) if x in sig else np.nan)):
    r = pd.Series({x: fn(x) for x in sub if x in set(dias)}).dropna()
    otros = pd.Series({x: fn(x) for x in dias[::3] if x not in es_sub and x >= pd.Timestamp('2012-01-01')}).dropna()
    a, b = r.loc[:'2018'], r.loc['2019':]
    ta = t_nw(a.values); s = np.sign(a.mean()) if abs(ta) >= 2 else 0
    tb = t_nw(b.values) * s if s else np.nan; anb = b.groupby(b.index.year).mean()
    pasa = bool(s) and tb >= 2.24 and (np.sign(anb) == s).mean() >= 0.6 and b.mean() * s > 0.6
    print(f'{nom}: dias de subasta n {len(r)} | 2012-18 {a.mean():+.2f} pb (t {ta:+.2f}) -> signo {int(s)} | 2019-26 {b.mean():+.2f} pb (t con signo {tb if s else float("nan"):+.2f}) '
          f'| informativo dias sin subasta {otros.mean():+.2f} pb -> {"PASA" if pasa else "NO PASA"}')
