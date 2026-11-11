"""The5ers Hyper Growth: probabilidad de subir un escalón (+10 % antes de −6 %) y tiempo, según el riesgo. Cartera actual (con C113).
Uso: python3 the5ers_escalon.py DIR_SCRATCH"""
import sys, numpy as np
exec(open('plan_reinversion_etf.py').read().split('CAP, OBJ')[0])
rng = np.random.default_rng(89); B = 20; T = 2520
def escalon(x):
    st = rng.integers(0, len(x) - B, T // B + 1); R = x[(st[:, None] + np.arange(B)).ravel()[:T]]; eq = 0.0
    for t, r in enumerate(R):
        if r <= -0.03: continue
        eq += r
        if eq <= -0.06: return False, t
        if eq >= 0.10: return True, t
    return None, T
for hair, et in ((0.6, 'REAL AL 60 %'), (1.0, 'BACKTEST')):
    for r in (0.25, 0.35, 0.45, 0.55, 0.65):
        x = (SER - SER.mean() * (1 - hair)) * r / 0.65; res = [escalon(x) for _ in range(4000)]
        ok = [t for e, t in res if e]; p = len(ok) / len(res)
        print(f'{et:12s} riesgo {r:.2f} %: sube el escalón {p*100:3.0f} % | tarda (mediana) {np.median(ok)/21:4.1f} meses | prob. de subir 3 escalones seguidos {p**3*100:3.0f} % | 5 seguidos {p**5*100:3.0f} %')
