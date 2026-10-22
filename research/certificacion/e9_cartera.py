"""E9: yen de fin de mes (PREREGISTRO_E9) y cartera E1 + oro (E8) + yen (+ gas informativo).
Uso: python3 e9_cartera.py DIR_GC_VIE e1_franjas.csv NG_1h.csv"""
import sys, io, contextlib
from datetime import datetime
import numpy as np, pandas as pd
from e1_estrategia import construir
with contextlib.redirect_stdout(io.StringIO()):
    exec(open('cartera_e1_oro_gas.py').read().split("def sh(p)")[0])          # define oro() y gas()
    src = open('c48_yen_d2.py').read().split("x = serie(")[0]; exec(src)       # carga FXCM y calendario D−2
b, a = D['USDJPY']; filas = {}
for d in fin.index[fin.values == 3]:
    t0 = datetime(d.year, d.month, d.day, 7, tzinfo=NY); t1 = datetime(d.year, d.month, d.day, 8, tzinfo=NY)
    a0, b1 = en(a, t0), en(b, t1)
    m0 = int(t0.timestamp()) // 60; bajos = [b[m] for m in range(m0, m0 + 60) if m in b]
    if np.isnan([a0, b1]).any() or not bajos: continue
    filas[d] = (np.log(b1 / a0) - COM, min(bajos) / a0 - 1)
Y = pd.DataFrame(filas, index=['neto', 'adv']).T
sdy = Y.neto.rolling(24).std().shift(1); w = (0.005 / sdy).clip(upper=20); stop = Y.adv <= -4 * sdy
yen = (w * np.where(stop, -(4 * sdy + 0.5e-4), Y.neto)).dropna()
def sh(p): return p.mean() / p.std() * np.sqrt(252)
an = yen.groupby(yen.index.year).sum()
print(f'YEN solo (riesgo 0,5 %): {yen.mean()*12*100:.1f} %/año, Sharpe anual {yen.mean()/yen.std()*np.sqrt(12):.2f}, años+ {(an>0).sum()}/{len(an)}, stops {int(stop.sum())}')
e1x = pd.read_csv(sys.argv[2], index_col=0, parse_dates=True)
print('Sharpe 2018-2026 (cada pata al 0,5 %; cartera reescalada a la volatilidad de E1 solo):')
for ne, ce in (('E1 FTMO 0,79', 0.79), ('E1 bajo 0,44', 0.44)):
    e = construir(e1x, 0.005, ce).ret.loc['2018':]
    for co in (0.74, 1.5):
        g = oro(0.005, co).ret.loc['2018':]; n = gas(0.005, 4.7).loc['2018':]; y = yen.loc['2018':]
        J = pd.concat([e.rename('e1'), g.rename('oro'), y.rename('yen'), n.rename('gas')], axis=1).fillna(0)
        def cart(cols):
            p = J[cols].sum(axis=1); p = p * J.e1.std() / p.std(); eq = p.cumsum(); return sh(p), p.mean() * 252 * 100, (eq - eq.cummax()).min() * 100
        s3, r3, d3 = cart(['e1', 'oro', 'yen']); s4, r4, d4 = cart(['e1', 'oro', 'yen', 'gas'])
        print(f'  {ne} | oro {co} pb → E1+oro {cart(["e1","oro"])[0]:.2f} | E1+oro+yen {s3:.2f} ({r3:.1f} %/año, DD {d3:.1f} %) | +gas {s4:.2f} ({r4:.1f} %/año, DD {d4:.1f} %) '
              f'| corr yen-E1 {J.yen.corr(J.e1):.3f}')
