"""Examen Horizon de Upcomers (9 %, diaria 3 %, 6 % arrastrada que se fija en el inicial) según el riesgo SOLO del examen.
Si suspende, se compra otro (50K: 103 $; 1,5M: 2.300 $). Mide: probabilidad de aprobar a la 1.ª, tiempo hasta aprobar (con reintentos),
coste medio hasta aprobar. Cartera CFD C116 (serie a riesgo 0,5 con control de vol.). Uso: python3 upcomers_examen_riesgo.py SERIE_CSV"""
import sys, numpy as np, pandas as pd
V = pd.read_csv(sys.argv[1], index_col=0, parse_dates=True)['nueva'].dropna().values
rng = np.random.default_rng(7)
def intento(R, t):
    eq = h = 0.0
    while t < len(R):
        r = R[t]; t += 1; eq += r; h = max(h, eq)
        if r <= -0.03 or eq <= min(h, 0.06) - 0.06: return False, t
        if eq >= 0.09: return True, t
    return None, t
for hair, et in ((0.6, 'PRUDENTE'), (1.0, 'BACKTEST')):
    for r in (0.8, 1.0, 1.25, 1.5, 2.0):
        x = (V - V.mean() * (1 - hair)) * r / 0.5; prim = []; tiempo = []; nint = []
        for _ in range(4000):
            st = rng.integers(0, len(x) - 20, 40); R = x[(st[:, None] + np.arange(20)).ravel()]
            t = 0; k = 0; ok = None
            while t < len(R):
                ok, t = intento(R, t); k += 1
                if k == 1: prim.append(ok is True)
                if ok: break
            tiempo.append(t / 21 if ok else np.nan); nint.append(k)
        tm = np.array(tiempo); n = np.array(nint)
        print(f'{et:8s} riesgo examen {r:.2f}: aprueba a la 1.ª {np.mean(prim)*100:3.0f} % | aprobado en <2 m {np.mean(tm<2)*100:3.0f} %, <3 m {np.mean(tm<3)*100:3.0f} %, <6 m {np.mean(tm<6)*100:3.0f} % | '
              f'tiempo mediano {np.nanmedian(tm):.1f} m | exámenes medios {n.mean():.2f} (50K {n.mean()*103:.0f} $; 1,5M {n.mean()*2300:,.0f} $)')
