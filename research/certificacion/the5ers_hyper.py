"""The5ers Hyper Growth (reglas de terceros, sin verificar): examen de 1 fase +10 %, pérdida máx. fija 6 % (y pausa diaria 3 %);
fondeada: cada +10 % cobras ese beneficio (supuesto 80 %) y la cuenta se DOBLA; tope 4 M$. Empieza en 20.000 $; si pierdes, examen nuevo
(~260 $). Cartera actual (Sharpe ~2,4). 10 años máx. Uso: python3 the5ers_hyper.py DIR_SCRATCH"""
import sys, numpy as np, pandas as pd
exec(open('plan_reinversion_etf.py').read().split('CAP, OBJ')[0])
BASE = SER / 1.3; rng = np.random.default_rng(31); B = 20; T = 2520
def sim(x):
    st = rng.integers(0, len(x) - B, T // B + 1); R = x[(st[:, None] + np.arange(B)).ravel()[:T]]
    t = 0; cob = 0.0; pag = 0.0; maxcap = 0; t2m = None; cap = 20000; examen = True
    while t < T:
        if examen: pag += 260; cap = 20000
        eq = 0.0
        while t < T:
            r = R[t]; t += 1
            if r <= -0.03: continue                      # pausa del día (no se opera más ese día; aproximado)
            eq += r
            if eq <= -0.06: break
            if eq >= 0.10:
                if not examen: cob += 0.8 * 0.10 * cap; cap = min(cap * 2, 4_000_000)
                examen = False; maxcap = max(maxcap, cap); eq = 0.0
                if cap >= 2_000_000 and t2m is None: t2m = t
        else: break
        examen = True
    return cob - pag, maxcap, t2m
for hair, et in ((1.0, 'BACKTEST'), (0.6, 'REAL AL 60 %')):
    print(f'\n### {et}')
    for r in (0.25, 0.35, 0.50, 0.65):
        x = (BASE - BASE.mean() * (1 - hair)) * r / 0.5; res = [sim(x) for _ in range(2000)]
        n = np.array([q[0] for q in res]); mc = np.array([q[1] for q in res]); t2 = np.array([q[2] if q[2] else np.nan for q in res])
        print(f'  riesgo {r:.2f} %: llega a 2 M$ en 10 años {np.mean(~np.isnan(t2))*100:3.0f} % (mediana {np.nanmedian(t2)/252 if np.any(~np.isnan(t2)) else float("nan"):.1f} años) | '
              f'capital máx. mediano {np.median(mc):,.0f} $ | cobrado neto 10 años: media {n.mean():,.0f} $ / mediana {np.median(n):,.0f} $')
