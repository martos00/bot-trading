"""Upcomers SIN regla de consistencia (centro de ayuda, 10-nov-2026), cuenta de 100K (precio 200 € ≈ 215 $; Horizon supuesto igual):
- Horizon (1 fase): objetivo 9 %, diaria 3 %, máx. 6 % arrastrada que se fija en el saldo inicial; fondeada 80 %, cobro cada 14 días
  con ≥ 3 % de beneficio en el ciclo.
- Odyssey (2 fases): 6 % + 6 %, diaria 4 %, máx. 6 % arrastrada (igual); fondeada igual.
Topes por cobro: se prueba con el cuadro general (800K+: 5k/7,5k/10k/15k/20k/25k/30k, luego sin tope) y sin topes. Precio del examen
supuesto 800 $ (no publicado). Comisión de cobro 19,9 $ + 2,49 %. Se deja un colchón del 3 % al cobrar. Cartera actual. 24 meses.
Uso: python3 upcomers_horizon_odyssey.py DIR_SCRATCH"""
import sys, numpy as np, pandas as pd
exec(open('plan_reinversion_etf.py').read().split('CAP, OBJ')[0])
BASE = SER / 1.3; rng = np.random.default_rng(59); B = 20; T = 504; CAP = 100_000; PRECIO = 215; COL = 0.03
TOPES = [1000, 2000, 3000, 4000, 5000, 6250, 7500]
def sim(x, fases, diaria, topes):
    st = rng.integers(0, len(x) - B, T // B + 1); R = x[(st[:, None] + np.arange(B)).ravel()[:T]]
    t = 0; pag = 0.0; cob = 0.0; perd = 0; n = 0
    while t < T:
        pag += PRECIO; ok = True
        for obj in fases:
            eq = 0.0; hwm = 0.0; ok = False
            while t < T:
                r = R[t]; t += 1; eq += r; hwm = max(hwm, eq)
                if r <= -diaria or eq <= min(hwm, 0.06) - 0.06: break
                if eq >= obj: ok = True; break
            if not ok: break
        if not ok: continue
        bal = 0.0; hwm = 0.0; k = 0; ben0 = 0.0; ini = t
        while t < T:
            r = R[t]; t += 1; bal += r; hwm = max(hwm, bal)
            if r <= -diaria or bal <= min(hwm - 0.06, 0.0): perd += 1; break
            if (t - ini) % 10 == 0 and bal - ben0 >= 0.03 and bal > COL:
                q = (bal - COL) * CAP
                if topes and k < len(TOPES): q = min(q, TOPES[k])
                bal -= q / CAP; ben0 = bal; k += 1; n += 1; cob += 0.8 * q - 19.9 - 0.0249 * 0.8 * q
    return cob - pag, perd, n
for nom, fases, diaria in (('Horizon 1 fase (9 %)', (0.09,), 0.03), ('Odyssey 2 fases (6 % + 6 %)', (0.06, 0.06), 0.04)):
    for hair, et in ((0.6, 'REAL AL 60 %'), (1.0, 'BACKTEST')):
        for r in (0.40, 0.50, 0.65):
            for topes in (True,):
                x = (BASE - BASE.mean() * (1 - hair)) * r / 0.5; res = [sim(x, fases, diaria, topes) for _ in range(1500)]
                v = np.array([q[0] for q in res])
                print(f'{nom:28s} {et:12s} riesgo {r:.2f} % {"con topes" if topes else "sin topes"} | neto 24 m {v.mean():9,.0f} $ (~{v.mean()/24:6,.0f} $/mes; mediana {np.median(v):9,.0f}; 10 % peor {np.percentile(v,10):8,.0f}) | pierde {np.mean([q[1]>0 for q in res])*100:3.0f} % | cobros {np.mean([q[2] for q in res]):.1f}')
