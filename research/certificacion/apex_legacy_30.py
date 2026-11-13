"""Apex 300K legacy con regla de consistencia del 30 % (el mejor día < 30 % del beneficio desde el último cobro) frente al 50 %;
y variante con el 30 % también en el examen (el mejor día < 30 % del beneficio al llegar al objetivo; si no, se sigue operando).
Resto de reglas SUPUESTAS (apex_300k_manual.py). Sin rupturas (M2 con C113, M1 sin). Riesgo 0,5. Uso: python3 apex_legacy_30.py DIR_SCRATCH"""
import sys, numpy as np, pandas as pd
exec(open('plan_reinversion_etf.py').read().split('CAP, OBJ')[0])
ap = open('apex_rotacion.py').read(); motor0 = ap[ap.index('def camino'):ap.index('for hair, et in')]
base = ['yen', 'cesta_yen', 'oro_vie_1655', 'oro_D-2', 'plata_visp_1655', 'plata_viernes', 'nikkei_Q+2', 'nikkei_Q-2']
CAP, OBJ, DD, ESC = 300000, 20000, 7500, [5000, 6000, 6000, 6000, 8000, 10000]; RED = CAP + 8200; MINC = CAP + 9200; B = 20; rng = np.random.default_rng(13)
def eval_cons(R, t, regla):
    eq = hwm = mx = 0.0
    while t < len(R):
        r = R[t]; eq += r; t += 1; hwm = min(max(hwm, eq), DD); mx = max(mx, r)
        if eq <= hwm - DD: return False, t
        if eq >= OBJ and mx < regla * eq: return True, t
    return None, t
for nom, cols in (('M2 (con oro de madrugada)', base + ['c113']), ('M1 (sin oro de madrugada)', base)):
    P = C[cols].sum(axis=1); pv = P.rolling(60, min_periods=40).std().shift(1); S0 = (P * (P.std() / pv).clip(0.5, 2)).dropna().loc['2018-11-05':].values
    for hair, et in ((0.6, 'PRUDENTE'), (1.0, 'BACKTEST')):
        x = (S0 - S0.mean() * (1 - hair))
        for cf, ce in ((0.5, None), (0.3, None), (0.3, 0.3)):
            exec(motor0.replace('if r >= 350', 'if r >= 700').replace('mx < 0.5 * ben', f'mx < {cf} * ben'))
            ok = 0; n = 0; tex = []; F = []
            for _ in range(3000):
                R = camino(x, 1500); a, t = (evaluacion(R, 0) if ce is None else eval_cons(R, 0, ce)); n += 1; tex.append(t)
                if a: ok += 1; F.append(fondeada(camino(x, 1500), 0))
            pa = ok / n; tot = np.array([sum(f[0]) for f in F]); vida = np.array([f[1] for f in F]) / 21; nc = np.array([len(f[0]) for f in F])
            print(f'{nom:27s} {et:8s} consistencia fondeada {int(cf*100)} %{" + examen 30 %" if ce else "              "} | aprueba {pa*100:3.0f} % (examen medio {np.mean(tex)/21:.1f} m) | '
                  f'cobros por cuenta {nc.mean():.1f} | meses entre cobros {vida.sum()/max(nc.sum(),1):.1f} | cobrado por cuenta {tot.mean():7,.0f} $ | 20 plazas ~{20*tot.mean()/vida.mean():7,.0f} $/mes', flush=True)
