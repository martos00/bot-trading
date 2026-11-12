"""Upcomers Horizon: examen con riesgo alto y fondeada a 0,8. Tiempo hasta el 1.er cobro e ingresos en 24 meses (reglas de upcomers_cfd_c116.py).
Uso: python3 upcomers_examen_alto_cobro.py SERIE_CSV"""
import sys, numpy as np, pandas as pd
V = pd.read_csv(sys.argv[1], index_col=0, parse_dates=True)['nueva'].dropna().values
rng = np.random.default_rng(11); B = 20; T = 504; COL = 0.03; TOPES = [5000, 7500, 10000, 15000, 20000, 25000, 30000]
def sim(xe, xf, cap, precio):
    st = rng.integers(0, len(xe) - B, T // B + 1); idx = (st[:, None] + np.arange(B)).ravel()[:T]; Re, Rf = xe[idx], xf[idx]
    t = 0; pag = cob = 0.0; m1 = None
    while t < T:
        pag += precio; eq = h = 0.0; ok = False
        while t < T:
            r = Re[t]; t += 1; eq += r; h = max(h, eq)
            if r <= -0.03 or eq <= min(h, 0.06) - 0.06: break
            if eq >= 0.09: ok = True; break
        if not ok: continue
        bal = h = 0.0; k = 0; ben0 = 0.0; ini = t
        while t < T:
            r = Rf[t]; t += 1; bal += r; h = max(h, bal)
            if r <= -0.03 or bal <= min(h - 0.06, 0.0): break
            if (t - ini) % 10 == 0 and bal - ben0 >= 0.03 and bal > COL:
                q = (bal - COL) * cap
                if cap >= 800_000 and k < len(TOPES): q = min(q, TOPES[k])
                bal -= q / cap; ben0 = bal; k += 1; cob += 0.8 * q * (1 - 0.0249) - 19.9
                if m1 is None: m1 = t / 21
    return cob - pag, m1, pag
for hair, et in ((0.6, 'PRUDENTE'), (1.0, 'BACKTEST')):
    xf = (V - V.mean() * (1 - hair)) * 0.8 / 0.5
    for cn, cap, pr, rex in (('50K', 50_000, 103, (0.8, 1.25, 1.5)), ('1,5M', 1_500_000, 2300, (0.8, 1.0))):
        for re in rex:
            xe = (V - V.mean() * (1 - hair)) * re / 0.5; res = [sim(xe, xf, cap, pr) for _ in range(3000)]
            v = np.array([q[0] for q in res]); m1 = np.array([q[1] if q[1] is not None else np.nan for q in res]); pg = np.array([q[2] for q in res])
            print(f'{et:8s} {cn:4s} examen {re:.2f} / fondeada 0,80 | 1.er cobro: mediana {np.nanmedian(m1):.1f} m; en <4 m {np.mean(m1<4)*100:3.0f} %, <6 m {np.mean(m1<6)*100:3.0f} %, <9 m {np.mean(m1<9)*100:3.0f} %, nunca en 2 años {np.mean(np.isnan(m1))*100:3.0f} % '
                  f'| neto 24 m: media {v.mean()/24:7,.0f} $/mes, mediana {np.median(v)/24:7,.0f} $/mes | gastado en exámenes {pg.mean():,.0f} $')
