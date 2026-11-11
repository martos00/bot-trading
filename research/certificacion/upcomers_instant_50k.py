"""Upcomers CFD «Apex» de financiación inmediata, 50K (centro de ayuda, 10-nov-2026): sin examen ni consistencia; pérdida máx. 3 %
arrastrada que NUNCA se fija; diaria 2 %; cobro cada 14 días si hay ≥ 3 % de beneficio en el ciclo; 80 %; primer cobro máx. 500 $
(los siguientes, supuestos: 1.000/1.000/1.500/1.500 $ y luego 1.500 $). Precio supuesto 200 $ (no publicado). Cartera actual. 24 meses.
Uso: python3 upcomers_instant_50k.py DIR_SCRATCH"""
import sys, numpy as np, pandas as pd
exec(open('plan_reinversion_etf.py').read().split('CAP, OBJ')[0])
BASE = SER / 1.3; rng = np.random.default_rng(73); B = 20; T = 504; CAP = 50000; PRECIO = 200; TOP = [500, 1000, 1000, 1500, 1500]
def sim(x):
    st = rng.integers(0, len(x) - B, T // B + 1); R = x[(st[:, None] + np.arange(B)).ravel()[:T]]
    t = 0; pag = 0.0; cob = 0.0; n = 0; compras = 0
    while t < T:
        pag += PRECIO; compras += 1; bal = hwm = 0.0; ben0 = 0.0; ini = t; k = 0
        while t < T:
            r = R[t]; t += 1; bal += r; hwm = max(hwm, bal)
            if r <= -0.02 or bal <= hwm - 0.03: break
            if (t - ini) % 10 == 0 and bal - ben0 >= 0.03:
                q = min((bal - ben0) * CAP, TOP[min(k, 4)]); bal -= q / CAP; hwm = max(bal, hwm - q / CAP); ben0 = bal; k += 1; n += 1; cob += 0.8 * q
    return cob - pag, n, compras
for hair, et in ((0.6, 'REAL AL 60 %'), (1.0, 'BACKTEST')):
    for r in (0.20, 0.30, 0.40, 0.65):
        x = (BASE - BASE.mean() * (1 - hair)) * r / 0.5; res = [sim(x) for _ in range(3000)]
        v = np.array([q[0] for q in res])
        print(f'{et:12s} riesgo {r:.2f} %: neto 2 años {v.mean():7,.0f} $ (~{v.mean()/24:5,.0f} $/mes; mediana {np.median(v):7,.0f}) | cobros {np.mean([q[1] for q in res]):.1f} | cuentas compradas {np.mean([q[2] for q in res]):.1f} | P(perder) {(v<0).mean()*100:3.0f} %')
