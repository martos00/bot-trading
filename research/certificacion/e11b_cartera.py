"""E11: EURJPY fin de trimestre (PREREGISTRO_E11) y cartera de 5 ventajas. Uso: python3 e11_cartera.py DIR_GC_VIE e1_franjas.csv NG_1h.csv DIR_H1"""
import sys, io, contextlib, glob
from datetime import datetime
import numpy as np, pandas as pd
argv0 = list(sys.argv)
with contextlib.redirect_stdout(io.StringIO()):
    exec(open("e10_cartera.py").read().rsplit("def sh(p): return", 1)[0])     # oro(), yen, plata(), construir, FXCM D (USDJPY...)
sys.argv = argv0
def pata(par):
    bj, aj = {}, {}
    for f in sorted(glob.glob(S + par + '/' + par + '_*.csv.gz')):
        bb, aa = fxcm(f); bj.update(bb); aj.update(aa)
    v = {}
    for d in pd.bdate_range('2012-01-02', '2026-09-30'):
        t0 = datetime(d.year, d.month, d.day, 1, tzinfo=NY); t1 = datetime(d.year, d.month, d.day, 2, tzinfo=NY)
        w = [en(bj, t0), en(aj, t0), en(bj, t1), en(aj, t1)]
        if not np.isnan(w).any(): v[d] = w
    XJ = pd.DataFrame(v, index=['b0', 'a0', 'b1', 'a1']).T
    r_mid = -np.log((XJ.b1 + XJ.a1) / (XJ.b0 + XJ.a0)); neto = np.log(XJ.b0 / XJ.a1) - COM
    sdj = r_mid.rolling(60).std().shift(1)
    s_ = pd.Series(range(len(XJ)), index=XJ.index); finj = s_.groupby(s_.index.to_period('M')).cumcount(ascending=False) + 1
    q0 = XJ.index[(finj.values == 1) & np.isin(XJ.index.month, [3, 6, 9, 12])]
    return ((0.005 / 3 / sdj) * neto).reindex(q0)
ej = pd.concat([pata(p) for p in ('EURJPY', 'USDJPY', 'GBPJPY')], axis=1).sum(axis=1, min_count=1).dropna()
an = ej.groupby(ej.index.year).sum()
print(f'CESTA yen fin de trimestre: n {len(ej)}, {ej.mean()*4*100:.2f} %/año, Sharpe anual {ej.mean()/ej.std()*2:.2f}, años+ {(an>0).sum()}/{len(an)}')
def sh(p): return p.mean() / p.std() * np.sqrt(252)
e1x = pd.read_csv(sys.argv[2], index_col=0, parse_dates=True)
for ne, ce in (('E1 FTMO 0,79', 0.79), ('E1 bajo 0,44', 0.44)):
    e = construir(e1x, 0.005, ce).ret.loc['2018':]
    for co, cp in ((0.74, 2.3), (1.5, 4.0)):
        J = pd.concat([e.rename('e1'), oro(0.005, co).ret.loc['2018':].rename('oro'), yen.loc['2018':].rename('yen'), plata(cp).loc['2018':].rename('plata'), ej.loc['2018':].rename('ej')], axis=1).fillna(0)
        def cart(cols):
            q = J[cols].sum(axis=1); q = q * J.e1.std() / q.std(); eq = q.cumsum(); return sh(q), q.mean() * 252 * 100, (eq - eq.cummax()).min() * 100
        s4 = cart(['e1', 'oro', 'yen', 'plata']); s5 = cart(['e1', 'oro', 'yen', 'plata', 'ej'])
        print(f'  {ne} | oro {co}, plata {cp} → 4 ventajas {s4[0]:.2f} | 5 ventajas (cesta yen) {s5[0]:.2f} ({s5[1]:.1f} %/año, DD {s5[2]:.1f} %)')
