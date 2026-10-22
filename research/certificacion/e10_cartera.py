"""E10: plata víspera de festivo (PREREGISTRO_E10) y cartera E1 + oro + yen + plata. Uso: python3 e10_cartera.py DIR_GC_VIE e1_franjas.csv NG_1h.csv DIR_H1"""
import glob, os, sys, io, contextlib
import numpy as np, pandas as pd
import holidays
H1 = sys.argv[4]; sys.argv = sys.argv[:4]
with contextlib.redirect_stdout(io.StringIO()):
    exec(open("e9_cartera.py").read().split("def sh(p): return")[0])        # oro(), gas(), yen
from e1_estrategia import construir
FEST = {pd.Timestamp(d) for d in holidays.financial_holidays('NYSE', years=range(2009, 2028))}
HAB = pd.bdate_range('2009-01-01', '2027-12-31'); HAB = HAB[~HAB.isin(list(FEST))]
PRE = pd.DatetimeIndex(sorted({HAB[HAB.searchsorted(f) - 1] for f in FEST if 0 < HAB.searchsorted(f) < len(HAB)}))
x = pd.concat([pd.read_csv(f) for f in sorted(glob.glob(os.path.join(H1, 'SI_*.csv')))])
for c in ('close', 'low'): x[c] = pd.to_numeric(x[c], errors='coerce')
x = x[x.close > 0]; x.index = pd.to_datetime(x.ts_event, utc=True).dt.tz_convert('America/New_York') + pd.Timedelta(hours=1)
x = x[~x.index.duplicated()].sort_index()
a = x[x.index.hour == 16]; b = x[x.index.hour == 17]; a.index = a.index.tz_localize(None).normalize(); b.index = b.index.tz_localize(None).normalize()
j = a[['close', 'instrument_id']].join(b[['close', 'instrument_id', 'low']], lsuffix='0', rsuffix='1', how='inner')
j = j[(j.instrument_id0 == j.instrument_id1) & j.index.isin(PRE)]
rs = np.log(j.close1 / j.close0); sds = rs.rolling(24).std().shift(1); advs = 1 - j.low / j.close0
def plata(c):
    w = (0.005 / sds).clip(upper=20); st = advs >= 4 * sds
    return (w * (np.where(st, -(4 * sds + 1e-4), rs) - c / 1e4)).dropna()
def sh(p): return p.mean() / p.std() * np.sqrt(252)
for c in (2.3, 4.0):
    p = plata(c); an = p.groupby(p.index.year).sum()
    print(f'PLATA víspera festivo (coste {c} pb): {p.mean()*len(p)/len(an)*100:.2f} %/año, Sharpe anual {p.mean()/p.std()*np.sqrt(len(p)/len(an)):.2f}, años+ {(an>0).sum()}/{len(an)}, n {len(p)}')
e1x = pd.read_csv(sys.argv[2], index_col=0, parse_dates=True)
print('Sharpe 2018-2026 (cada pata al 0,5 %; cartera reescalada a la volatilidad de E1 solo):')
for ne, ce in (('E1 FTMO 0,79', 0.79), ('E1 bajo 0,44', 0.44)):
    e = construir(e1x, 0.005, ce).ret.loc['2018':]
    for co, cp in ((0.74, 2.3), (1.5, 4.0)):
        J = pd.concat([e.rename('e1'), oro(0.005, co).ret.loc['2018':].rename('oro'), yen.loc['2018':].rename('yen'), plata(cp).loc['2018':].rename('plata')], axis=1).fillna(0)
        def cart(cols):
            q = J[cols].sum(axis=1); q = q * J.e1.std() / q.std(); eq = q.cumsum(); return sh(q), q.mean() * 252 * 100, (eq - eq.cummax()).min() * 100
        s3 = cart(['e1', 'oro', 'yen']); s4 = cart(['e1', 'oro', 'yen', 'plata'])
        print(f'  {ne} | oro {co} pb, plata {cp} pb → E1+oro+yen {s3[0]:.2f} | E1+oro+yen+plata {s4[0]:.2f} ({s4[1]:.1f} %/año, DD {s4[2]:.1f} %) | corr plata-oro {J.plata.corr(J.oro):.2f}')
