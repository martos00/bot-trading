"""Tradeify 150K (usuario 11-nov-2026: 230 €, consistencia 40 % solo en la evaluación; notas previas: Flex 150K pérdida 4.500 $ al
cierre del día, sin límite diario, cobro tras 5 días ganadores ≥ 250 $, máx. 50 % del beneficio y 4.500 $ por cobro; posible paso a
cuenta real tras ~10 cobros). Objetivo de la evaluación supuesto 9.000 $. Cartera actual con C113, riesgo 0,65 % y 0,5 %.
Uso: python3 tradeify_150k.py DIR_SCRATCH"""
import sys, numpy as np, pandas as pd
exec(open('plan_reinversion_etf.py').read().split('CAP, OBJ')[0])
CAP = 150000; OBJ = 9000; DD = 4500; PRECIO = 250; B = 20; T = 504; rng = np.random.default_rng(71)
def sim(x):
    st = rng.integers(0, len(x) - B, T // B + 1); R = x[(st[:, None] + np.arange(B)).ravel()[:T]] * CAP
    t = 0; pag = 0.0; cob = 0.0; perd = 0; ncob = 0; t_ap = None; ex = 0
    while t < T:
        pag += PRECIO; ex += 1; eq = hwm = 0.0; mx = 0.0; ok = False
        while t < T:
            r = R[t]; t += 1; eq += r; hwm = min(max(hwm, eq), DD); mx = max(mx, r)
            if eq <= hwm - DD: break
            if eq >= OBJ and mx <= 0.40 * eq: ok = True; break
        if not ok: continue
        if t_ap is None: t_ap = t
        bal = hwm = 0.0; dias = 0; k = 0
        while t < T and k < 10:
            r = R[t]; t += 1; bal += r; hwm = min(max(hwm, bal), DD + 100)
            if bal <= hwm - DD: perd += 1; break
            if r >= 250: dias += 1
            if dias >= 5 and bal > 0:
                q = min(0.5 * bal, 4500); bal -= q; cob += 0.9 * q; dias = 0; k += 1; ncob += 1
        if k >= 10: break      # pasa a cuenta real (no se cuenta)
    return cob - pag, perd, ncob, t_ap, ex
for hair, et in ((0.6, 'REAL AL 60 %'), (1.0, 'BACKTEST')):
    for r in (0.50, 0.65):
        x = (SER - SER.mean() * (1 - hair)) * r / 0.65; res = [sim(x) for _ in range(3000)]
        n = np.array([q[0] for q in res]); ta = np.array([q[3] if q[3] else np.nan for q in res])
        print(f'{et:12s} riesgo {r:.2f} %: aprueba en 2 años {np.mean(~np.isnan(ta))*100:3.0f} % (mediana {np.nanmedian(ta)/21:.1f} meses) | exámenes {np.mean([q[4] for q in res]):.1f} | '
              f'pierde la fondeada {np.mean([q[1]>0 for q in res])*100:3.0f} % | cobros {np.mean([q[2] for q in res]):.1f} | neto 2 años {n.mean():7,.0f} $ (mediana {np.median(n):7,.0f}) = ~{n.mean()/24:5,.0f} $/mes | P(perder) {(n<0).mean()*100:3.0f} %')
