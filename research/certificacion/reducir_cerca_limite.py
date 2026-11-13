"""Regla de gestión: en la cuenta fondeada, si el margen hasta el límite de pérdida baja de M, se opera a una fracción f del riesgo hasta
recuperarlo. Apex 150K EOD (a mano, sin rupturas, riesgo 0,5; reglas confirmadas) y Upcomers Horizon 50K y 2M (EA, fondeada 0,8; reglas
confirmadas). Se informan TODAS las variantes probadas. Uso: python3 reducir_cerca_limite.py DIR_SCRATCH"""
import sys, numpy as np, pandas as pd
src = open('apex_150k_eod_real.py').read(); exec(src[:src.index('for nom, cols in')])
P = C[base + ['c113']].sum(axis=1); pv = P.rolling(60, min_periods=40).std().shift(1); SA = (P * (P.std() / pv).clip(0.5, 2)).dropna().loc['2018-11-05':].values
def apex_pa(R, M, f):
    bal = hwm = 0.0; dias = 0; mx = 0.0; b0 = 0.0; q = []
    for t, r0 in enumerate(R):
        piso = 100 if hwm >= 4100 else hwm - 4000
        r = r0 * (f if bal - piso < M else 1.0); r = max(r, -2500)
        bal += r; hwm = max(hwm, bal); piso = 100 if hwm >= 4100 else hwm - 4000
        if bal <= piso: return q, t + 1, True
        if r >= 350: dias += 1
        mx = max(mx, r); ben = bal - b0
        if bal >= 4600 and dias >= 5 and ben > 0 and mx < 0.5 * ben:
            a = min(ESC[len(q)], bal - 4100)
            if a >= 500:
                bal -= a; q.append(a); dias = 0; mx = 0.0; b0 = bal
                if len(q) == 6: return q, t + 1, False
    return q, len(R), False
V = pd.read_csv(f'{SP}/serie_cfd_c116.csv', index_col=0, parse_dates=True)['nueva'].dropna().values
def upc_pa(R, cap, M, f):     # R a riesgo 0,8 en fracción; colchón 3 %
    bal = hwm = 0.0; b0 = 0.0; ini = 0; d = 0; k = 0; cob = 0.0
    TOP = [5000, 7500, 10000, 15000, 20000, 25000, 30000]
    for t, r0 in enumerate(R):
        piso = min(hwm - 0.06, 0.0)
        r = r0 * (f if bal - piso < M else 1.0)
        bal += r; hwm = max(hwm, bal); piso = min(hwm - 0.06, 0.0)
        if r <= -0.03 or bal <= piso: return cob, t + 1, True, k
        if r >= 0.005: d += 1
        if (t - ini) % 10 == 0 and bal - b0 >= 0.03 and d >= 3 and bal > 0.03:
            q = (bal - 0.03) * cap
            if cap >= 800_000 and k < 7: q = min(q, TOP[k])
            bal -= q / cap; b0 = bal; k += 1; d = 0; cob += 0.8 * q * (1 - 0.0249) - 19.9
    return cob, len(R), False, k
rng2 = np.random.default_rng(21)
def cam(x, T): st = rng2.integers(0, len(x) - 20, T // 20 + 1); return x[(st[:, None] + np.arange(20)).ravel()[:T]]
for hair, et in ((0.6, 'PRUDENTE'), (1.0, 'BACKTEST')):
    x = (SA - SA.mean() * (1 - hair)) * CAP
    for M, f in ((0, 1.0), (1000, 0.5), (1500, 0.5), (2000, 0.5), (2500, 0.5), (1500, 0.25), (2000, 0.25)):
        rng2 = np.random.default_rng(21); F = [apex_pa(cam(x, 2000), M, f) for _ in range(3000)]
        tot = np.array([sum(q) for q, _, _ in F]); vida = np.array([v for _, v, _ in F]) / 21
        print(f'{et:8s} APEX 150K | {"sin regla" if M == 0 else f"margen < {M:,} $ → riesgo ×{f}":28s} | 6 cobros {np.mean([len(q)==6 for q,_,_ in F])*100:3.0f} % | se pierde {np.mean([p for _,_,p in F])*100:3.0f} % | '
              f'cobrado por cuenta {tot.mean():6,.0f} $ | vida {vida.mean():4.1f} m | por plaza y mes {tot.mean()/vida.mean():5,.0f} $', flush=True)
    xu = (V - V.mean() * (1 - hair)) * 0.8 / 0.5
    for cap in (50_000, 2_000_000):
        for M, f in ((0, 1.0), (0.02, 0.5), (0.03, 0.5), (0.04, 0.5), (0.03, 0.25)):
            rng2 = np.random.default_rng(22); F = [upc_pa(cam(xu, 504), cap, M, f) for _ in range(3000)]
            c = np.array([a for a, _, _, _ in F])
            print(f'{et:8s} UPCOMERS {cap//1000}K fondeada (24 m) | {"sin regla" if M == 0 else f"margen < {M*100:.0f} % → riesgo ×{f}":24s} | se pierde {np.mean([p for _,_,p,_ in F])*100:3.0f} % | '
                  f'cobros {np.mean([k for *_, k in F]):4.1f} | cobrado medio {c.mean():9,.0f} $ (mediana {np.median(c):9,.0f})', flush=True)
