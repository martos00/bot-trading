"""Upcomers Horizon (9 %, diaria 3 %, máx. 6 % arrastrada que se fija en el saldo inicial; fondeada 80 %, cobro cada 14 días con ≥ 3 %;
topes 800K+: 5k/7,5k/10k/15k/20k/25k/30k y luego sin tope; colchón 3 %) con la cartera de CFD con costes reales de FTMO
(cartera_cfd_ftmo.py, con diarias). Riesgos que dan ~20 %/año en el backtest y ~20 %/año al 60 %. Cuenta de 2 M$ (precio supuesto
2.500 $; reset gratis 1 vez). 24 meses. Uso: python3 upcomers_cfd_20pc.py DIR_SCRATCH"""
import sys, numpy as np, pandas as pd
src = open('cartera_cfd_ftmo.py').read().split('for nom, cols in')[0]; exec(src)
SCFD = volctl(X[list(AJ)].sum(axis=1)).values          # serie a riesgo 0,5 %
CAP = 2_000_000; PRECIO = 2500; TOP = [5000, 7500, 10000, 15000, 20000, 25000, 30000]; B = 20; T = 504; rng = np.random.default_rng(101)
def examen(R, t):
    eq = hwm = 0.0
    while t < len(R):
        r = R[t]; t += 1; eq += r; hwm = max(hwm, eq)
        if r <= -0.03 or eq <= min(hwm, 0.06) - 0.06: return False, t
        if eq >= 0.09: return True, t
    return None, t
def sim(x):
    st = rng.integers(0, len(x) - B, T // B + 1); R = x[(st[:, None] + np.arange(B)).ravel()[:T]]
    t = 0; pag = 0.0; cob = 0.0; perd = 0; susp = 0; ex = 0; reset = True
    while t < T:
        if not reset: pag += PRECIO
        ok, t = examen(R, t); ex += 1
        if ok is False:
            susp += 1
            if reset: reset = False; ok, t = examen(R, t); ex += 1
            if not ok: reset = False; continue
        if not ok: break
        reset = False; bal = hwm = 0.0; k = 0; ben0 = 0.0; ini = t
        while t < T:
            r = R[t]; t += 1; bal += r; hwm = max(hwm, bal)
            if r <= -0.03 or bal <= min(hwm - 0.06, 0.0): perd += 1; break
            if (t - ini) % 10 == 0 and bal - ben0 >= 0.03 and bal > 0.03:
                q = (bal - 0.03) * CAP
                if k < len(TOP): q = min(q, TOP[k])
                bal -= q / CAP; ben0 = bal; k += 1; cob += 0.8 * q * (1 - 0.0249) - 19.9
    return cob - PRECIO - pag, perd, susp, ex
for hair, et in ((1.0, 'BACKTEST'), (0.6, 'REAL AL 60 %')):
    for r in (0.5, 0.95, 1.6):
        x = (SCFD - SCFD.mean() * (1 - hair)) * r / 0.5; e = np.cumsum(x)
        res = [sim(x) for _ in range(2000)]; v = np.array([q[0] for q in res])
        print(f'{et:12s} riesgo {r:.2f} %: rent. {x.mean()*252*100:5.1f} %/año | caída máx. histórica {(e-np.maximum.accumulate(e)).min()*100:5.1f} % | peor día {x.min()*100:5.2f} % | '
              f'suspende algún examen {np.mean([q[2]>0 for q in res])*100:3.0f} % | pierde la fondeada {np.mean([q[1]>0 for q in res])*100:3.0f} % | neto 24 m {v.mean():9,.0f} $ (~{v.mean()/24:6,.0f} $/mes; mediana {np.median(v):9,.0f})')
