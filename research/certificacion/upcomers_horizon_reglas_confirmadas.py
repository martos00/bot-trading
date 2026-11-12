"""Upcomers Horizon 50K CFD con las reglas de cobro confirmadas por soporte (12-nov-2026): 3 % del saldo inicial de beneficio entre
cobros, 3 días con ≥ 0,5 % de ganancia (desde el último cobro), cada 14 días (10 hábiles), mínimo 50 $, sin consistencia.
Examen 1,5 / fondeada 0,8 (y 1,0 / 0,8 y 1,5 / 0,65); colchón 1 % o 3 %. Uso: python3 upcomers_horizon_reglas_confirmadas.py SERIE_CSV"""
import sys, numpy as np, pandas as pd
V = pd.read_csv(sys.argv[1], index_col=0, parse_dates=True)['nueva'].dropna().values
B = 20; T = 504; CAP = 50_000; PRECIO = 103
def sim(rng, xe, xf, col):
    st = rng.integers(0, len(xe) - B, T // B + 1); idx = (st[:, None] + np.arange(B)).ravel()[:T]; Re, Rf = xe[idx], xf[idx]
    t = 0; pag = cob = 0.0; m1 = None; n = 0
    while t < T:
        pag += PRECIO; eq = h = 0.0; ok = False
        while t < T:
            r = Re[t]; t += 1; eq += r; h = max(h, eq)
            if r <= -0.03 or eq <= min(h, 0.06) - 0.06: break
            if eq >= 0.09: ok = True; break
        if not ok: continue
        bal = h = 0.0; ben0 = 0.0; ini = t; dias = 0
        while t < T:
            r = Rf[t]; t += 1; bal += r; h = max(h, bal)
            if r <= -0.03 or bal <= min(h - 0.06, 0.0): break
            if r >= 0.005: dias += 1
            if (t - ini) % 10 == 0 and bal - ben0 >= 0.03 and dias >= 3 and bal - col > 50 / CAP:
                q = (bal - col) * CAP; bal = col; ben0 = col; dias = 0; n += 1; cob += 0.8 * q * (1 - 0.0249) - 19.9
                if m1 is None: m1 = t / 21
    return cob - pag, m1, n, pag
for hair, et in ((0.6, 'PRUDENTE'), (1.0, 'BACKTEST')):
    for re, rf in ((1.5, 0.8), (1.0, 0.8), (1.5, 0.65)):
        xe = (V - V.mean() * (1 - hair)) * re / 0.5; xf = (V - V.mean() * (1 - hair)) * rf / 0.5
        for col in (0.01, 0.03):
            rng = np.random.default_rng(9); res = [sim(rng, xe, xf, col) for _ in range(3000)]
            v = np.array([q[0] for q in res]); m1 = np.array([q[1] if q[1] is not None else np.nan for q in res])
            print(f'{et:8s} examen {re} / fondeada {rf} | colchón {col*100:.0f} % | 1.er cobro mediana {np.nanmedian(m1):.1f} m (<4 m {np.mean(m1<4)*100:3.0f} %, <6 m {np.mean(m1<6)*100:3.0f} %) '
                  f'| cobros en 2 años {np.mean([q[2] for q in res]):.1f} | neto media {v.mean()/24:4.0f} $/mes, mediana {np.median(v)/24:4.0f} $/mes | exámenes {np.mean([q[3] for q in res]):.0f} $')
