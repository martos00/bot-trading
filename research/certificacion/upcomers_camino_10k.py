"""¿Cuándo se llega a 10.000 $/mes (cobrado neto en los últimos 12 meses ≥ 120.000 $) con Upcomers Horizon y la cartera CFD C116?
Reglas confirmadas (12-nov-2026): 3 % de beneficio entre cobros, 3 días con ≥ 0,5 %, cada 14 días, 80 %, comisión 19,9 $ + 2,49 %,
topes 800K+: 5k/7,5k/10k/15k/20k/25k/30k y luego sin tope; colchón 3 %. Si se suspende o se pierde, se compra otra igual.
A: 2M desde el mes 0 (precio supuesto 2.900 $). B: 50K (103 $) y, en cuanto lo cobrado alcanza 2.900 $, se compra la 2M (la 50K sigue).
Examen 1,0 en la 2M, 1,5 en la 50K; fondeada 0,8. 36 meses. Uso: python3 upcomers_camino_10k.py SERIE_CSV"""
import sys, numpy as np, pandas as pd
V = pd.read_csv(sys.argv[1], index_col=0, parse_dates=True)['nueva'].dropna().values
TOP = [5000, 7500, 10000, 15000, 20000, 25000, 30000]; T = 756; B = 20
class Cuenta:
    def __init__(s, cap, precio, re, rf, t0): s.cap, s.precio, s.re, s.rf = cap, precio, re, rf; s.nueva(t0)
    def nueva(s, t): s.fase = 'ex'; s.eq = s.h = 0.0; s.k = 0; s.gasto = s.precio; s.t0 = t
    def dia(s, r05, t):          # r05: rentabilidad del día a riesgo 0,5; devuelve (cobro neto, gasto)
        g = 0.0; c = 0.0
        if s.fase == 'ex':
            r = r05 * s.re / 0.5; s.eq += r; s.h = max(s.h, s.eq)
            if r <= -0.03 or s.eq <= min(s.h, 0.06) - 0.06: s.nueva(t); g = s.precio
            elif s.eq >= 0.09: s.fase = 'fo'; s.bal = s.h = 0.0; s.ben0 = 0.0; s.dias = 0; s.ini = t
        else:
            r = r05 * s.rf / 0.5; s.bal += r; s.h = max(s.h, s.bal)
            if r >= 0.005: s.dias += 1
            if r <= -0.03 or s.bal <= min(s.h - 0.06, 0.0): s.nueva(t); g = s.precio
            elif (t - s.ini) % 10 == 0 and s.bal - s.ben0 >= 0.03 and s.dias >= 3 and s.bal > 0.03:
                q = (s.bal - 0.03) * s.cap
                if s.cap >= 800_000 and s.k < len(TOP): q = min(q, TOP[s.k])
                s.bal -= q / s.cap; s.ben0 = s.bal; s.k += 1; s.dias = 0; c = 0.8 * q * (1 - 0.0249) - 19.9
        return c, g
def camino(rng, x, plan):
    st = rng.integers(0, len(x) - B, T // B + 1); R = x[(st[:, None] + np.arange(B)).ravel()[:T]]
    cob = np.zeros(T); caja = 0.0; cs = []
    if plan == 'A': cs.append(Cuenta(2_000_000, 2900, 1.0, 0.8, 0)); caja -= 2900
    else: cs.append(Cuenta(50_000, 103, 1.5, 0.8, 0)); caja -= 103
    grande = plan == 'A'
    for t in range(T):
        for c in cs:
            q, g = c.dia(R[t], t); cob[t] += q; caja += q - g
        if not grande and caja >= 2900:
            cs.append(Cuenta(2_000_000, 2900, 1.0, 0.8, t)); caja -= 2900; grande = True
    m = np.add.reduceat(cob, np.arange(0, T, 21)); doce = np.convolve(m, np.ones(12), 'full')[:len(m)]
    llega = np.argmax(doce >= 120_000) + 1 if (doce >= 120_000).any() else np.nan
    return llega, m[:12].sum(), m[12:24].sum(), m[24:36].sum()
for hair, et in ((0.6, 'PRUDENTE'), (1.0, 'BACKTEST')):
    x = V - V.mean() * (1 - hair)
    for plan in ('A', 'B'):
        rng = np.random.default_rng(10); res = np.array([camino(rng, x, plan) for _ in range(2000)])
        ll = res[:, 0]
        print(f'{et:8s} plan {plan} ({"2M desde el inicio" if plan == "A" else "50K y luego 2M con lo cobrado"}) | llega a 10k/mes (12 meses seguidos): '
              f'en 2 años {np.mean(ll <= 24)*100:3.0f} %, en 3 años {np.mean(ll <= 36)*100:3.0f} %, mes mediano {np.nanmedian(ll):.0f} | cobrado año 1 {np.median(res[:,1]):8,.0f} $ (media {res[:,1].mean():8,.0f}), '
              f'año 2 {np.median(res[:,2]):8,.0f} $ (media {res[:,2].mean():8,.0f}), año 3 {np.median(res[:,3]):8,.0f} $ (media {res[:,3].mean():8,.0f})')
