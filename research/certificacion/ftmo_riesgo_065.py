"""Firma de CFD tipo FTMO (100.000 $: fase 1 +10 %, fase 2 +5 %, pérdida máx. 10 % fija, diaria 5 %, examen 540 $ devuelto con el
primer cobro, cobros cada 14 días del 80 %). Serie: cartera actual de 150K (Sharpe ~2,4, aproxima la de CFD). 24 meses.
Uso: python3 ftmo_riesgo_065.py DIR_SCRATCH"""
import sys, numpy as np, pandas as pd
exec(open('plan_reinversion_etf.py').read().split('CAP, OBJ')[0])
BASE = SER / 1.3          # SER está a 0,65 % → pasar a 0,5 %
rng = np.random.default_rng(29); B = 20; T = 504; CUOTA = 540
def sim(x):
    st = rng.integers(0, len(x) - B, T // B + 1); R = x[(st[:, None] + np.arange(B)).ravel()[:T]]
    t = 0; pag = 0.0; cob = 0.0; perd = 0; examenes = 0
    while t < T:
        examenes += 1; pag += CUOTA; ok = True
        for obj in (0.10, 0.05):
            eq = 0.0
            while t < T:
                r = R[t]; eq += r; t += 1
                if eq <= -0.10 or r <= -0.05: ok = False; break
                if eq >= obj: break
            if not ok or t >= T: break
        if not ok or t >= T: continue
        eq = 0.0; ini = t; primero = True
        while t < T:
            r = R[t]; eq += r; t += 1
            if eq <= -0.10 or r <= -0.05: perd += 1; break
            if (t - ini) % 10 == 0 and eq > 0:
                q = eq * 100000 * 0.8; cob += q + (CUOTA if primero else 0); primero = False; eq = 0.0
    return cob - pag, perd, examenes
for hair, et in ((1.0, 'BACKTEST'), (0.6, 'REAL AL 60 %')):
    print(f'\n### {et} — cuenta de 100.000 $, 24 meses')
    for r in (0.40, 0.50, 0.65, 0.80, 1.00):
        x = (BASE - BASE.mean() * (1 - hair)) * r / 0.5; res = [sim(x) for _ in range(3000)]
        n = np.array([q[0] for q in res])
        print(f'  riesgo {r:.2f} %: neto medio {n.mean():8,.0f} $ (mediana {np.median(n):8,.0f}; 10 % peor {np.percentile(n,10):7,.0f}) | pierde la fondeada (alguna vez) {np.mean([q[1]>0 for q in res])*100:3.0f} % | exámenes {np.mean([q[2] for q in res]):.1f} | P(perder dinero) {(n<0).mean()*100:3.0f} %')
