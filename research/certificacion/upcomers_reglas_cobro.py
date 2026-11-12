"""Upcomers 50K Horizon (examen 1,5; fondeada 0,8): sensibilidad a las reglas de cobro. Soporte (12-nov-2026): mínimo 50 $ de beneficio,
posiciones cerradas, «muchos programas requieren 1 % del balance inicial entre cobros». Se prueba: mínimo entre cobros 1 % o 3 %;
cada cuánto se puede pedir (5 o 10 días hábiles); colchón que se deja sobre el saldo inicial (0,5 / 1 / 2 / 3 %).
Uso: python3 upcomers_reglas_cobro.py SERIE_CSV"""
import sys, numpy as np, pandas as pd
V = pd.read_csv(sys.argv[1], index_col=0, parse_dates=True)['nueva'].dropna().values
B = 20; T = 504; CAP = 50_000; PRECIO = 103
def sim(rng, xe, xf, minimo, cada, col):
    st = rng.integers(0, len(xe) - B, T // B + 1); idx = (st[:, None] + np.arange(B)).ravel()[:T]; Re, Rf = xe[idx], xf[idx]
    t = 0; pag = cob = 0.0; m1 = None; n = 0; perd = 0
    while t < T:
        pag += PRECIO; eq = h = 0.0; ok = False
        while t < T:
            r = Re[t]; t += 1; eq += r; h = max(h, eq)
            if r <= -0.03 or eq <= min(h, 0.06) - 0.06: break
            if eq >= 0.09: ok = True; break
        if not ok: continue
        bal = h = 0.0; ben0 = 0.0; ini = t
        while t < T:
            r = Rf[t]; t += 1; bal += r; h = max(h, bal)
            if r <= -0.03 or bal <= min(h - 0.06, 0.0): perd += 1; break
            if (t - ini) % cada == 0 and bal - ben0 >= minimo and bal - col > 50 / CAP:
                q = (bal - col) * CAP; bal = col; ben0 = col; n += 1; cob += 0.8 * q * (1 - 0.0249) - 19.9
                if m1 is None: m1 = t / 21
    return cob - pag, m1, n, perd
for hair, et in ((0.6, 'PRUDENTE'), (1.0, 'BACKTEST')):
    xe = (V - V.mean() * (1 - hair)) * 1.5 / 0.5; xf = (V - V.mean() * (1 - hair)) * 0.8 / 0.5
    for minimo in (0.01, 0.03):
        for cada in (5, 10):
            for col in (0.005, 0.01, 0.02, 0.03):
                rng = np.random.default_rng(5); res = [sim(rng, xe, xf, minimo, cada, col) for _ in range(2500)]
                v = np.array([q[0] for q in res]); m1 = np.array([q[1] if q[1] is not None else np.nan for q in res])
                print(f'{et:8s} mínimo {minimo*100:.0f} % | cada {cada:2d} días | colchón {col*100:3.1f} % | 1.er cobro mediana {np.nanmedian(m1):4.1f} m (<4 m {np.mean(m1<4)*100:3.0f} %) | '
                      f'cobros en 2 años {np.mean([q[2] for q in res]):4.1f} | neto media {v.mean()/24:4.0f} $/mes, mediana {np.median(v)/24:4.0f} $/mes | pierde fondeada {np.mean([q[3]>0 for q in res])*100:3.0f} %')
