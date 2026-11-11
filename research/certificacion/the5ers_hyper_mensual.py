"""The5ers Hyper Growth por años (mismas reglas supuestas que the5ers_hyper.py: examen +10 %, pérdida fija 6 %, pausa diaria 3 %; cada
+10 % cobras el 80 % de ese 10 % y la cuenta se dobla; tope 4 M$). Empieza con 5.000 $ (~39 $) o 20.000 $ (~165 $, supuesto).
Uso: python3 the5ers_hyper_mensual.py DIR_SCRATCH"""
import sys, numpy as np, pandas as pd
exec(open('plan_reinversion_etf.py').read().split('CAP, OBJ')[0])
BASE = SER / 1.3; rng = np.random.default_rng(67); B = 20; T = 252 * 6
def sim(x, ini, precio):
    st = rng.integers(0, len(x) - B, T // B + 1); R = x[(st[:, None] + np.arange(B)).ravel()[:T]]
    t = 0; anual = np.zeros(6); examen = True; cap = ini
    while t < T:
        if examen: anual[min(t // 252, 5)] -= precio; cap = ini
        eq = 0.0; perdida = False
        while t < T:
            r = R[t]; t += 1
            if r <= -0.03: continue
            eq += r
            if eq <= -0.06: perdida = True; break
            if eq >= 0.10:
                if not examen: anual[min(t // 252, 5)] += 0.8 * 0.10 * cap; cap = min(cap * 2, 4_000_000)
                examen = False; eq = 0.0
        if perdida: examen = True
    return anual
for ini, precio in ((5000, 39), (20000, 165)):
    for hair, et in ((0.6, 'REAL AL 60 %'), (1.0, 'BACKTEST')):
        for r in (0.50, 0.65):
            x = (BASE - BASE.mean() * (1 - hair)) * r / 0.5; A = np.array([sim(x, ini, precio) for _ in range(2000)])
            print(f'empieza {ini:6,} $ | {et:12s} | riesgo {r:.2f} % | al MES de media por año: ' + ' | '.join(f'año {i+1}: {A[:, i].mean()/12:7,.0f} $ (mediana {np.median(A[:, i])/12:6,.0f})' for i in range(6)))
