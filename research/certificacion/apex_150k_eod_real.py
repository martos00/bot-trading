"""Apex 150K EOD con las reglas actuales (terceros con fecha 2026: ProEA/proptradingvibes/rbtrading/tradetanto).
Examen: objetivo 9.000 $, pérdida máx. 4.000 $ EOD arrastrada (se fija en 159.000 $ al llegar a 163.000 $), límite diario 2.000 $
(se aproxima recortando la pérdida del día a −2.000 $), plazo 30 días naturales (21 hábiles) sin reset: si no llega, se suspende.
Fondeada: pérdida 4.000 $ EOD que se fija en 150.100 $; límite diario 2.500 $ (nivel 1; se aproxima igual); cobro con ≥ 5 días de
≥ 350 $, mejor día < 50 % del beneficio desde el último cobro, saldo ≥ 154.600 $, se retira lo que pasa de 154.100 $ (mín. 500 $),
escalera 2.500/3.000/3.000/3.000/4.000/5.000 $, cierre tras el 6.º; 100 % para ti. Límite de contratos por niveles NO modelado.
Sin rupturas: M2 (con C113) y M1. Uso: python3 apex_150k_eod_real.py DIR_SCRATCH"""
import sys, numpy as np, pandas as pd
exec(open('plan_reinversion_etf.py').read().split('CAP, OBJ')[0])
base = ['yen', 'cesta_yen', 'oro_vie_1655', 'oro_D-2', 'plata_visp_1655', 'plata_viernes', 'nikkei_Q+2', 'nikkei_Q-2']
CAP = 150000; B = 20; rng = np.random.default_rng(150); ESC = [2500, 3000, 3000, 3000, 4000, 5000]
def camino(x, T): st = rng.integers(0, len(x) - B, T // B + 1); return x[(st[:, None] + np.arange(B)).ravel()[:T]] * CAP
def examen(R):
    eq = hwm = 0.0
    for t in range(21):
        r = max(R[t], -2000); eq += r; hwm = max(hwm, eq)
        piso = 9000 if hwm >= 13000 else hwm - 4000
        if eq <= piso: return False, t + 1
        if eq >= 9000: return True, t + 1
    return False, 21
def fondeada(R):
    bal = 0.0; hwm = 0.0; dias = 0; mx = 0.0; b0 = 0.0; cob = []
    for t, r in enumerate(R):
        r = max(r, -2500); bal += r; hwm = max(hwm, bal)
        piso = 100 if hwm >= 4100 else hwm - 4000
        if bal <= piso: return cob, t + 1
        if r >= 350: dias += 1
        mx = max(mx, r); ben = bal - b0
        if bal >= 4600 and dias >= 5 and ben > 0 and mx < 0.5 * ben:
            q = min(ESC[len(cob)], bal - 4100)
            if q >= 500:
                bal -= q; cob.append(q); dias = 0; mx = 0.0; b0 = bal
                if len(cob) == 6: return cob, t + 1
    return cob, len(R)
for nom, cols in (('M2 (con oro de madrugada)', base + ['c113']), ('M1 (sin oro de madrugada)', base)):
    P = C[cols].sum(axis=1); pv = P.rolling(60, min_periods=40).std().shift(1); S0 = (P * (P.std() / pv).clip(0.5, 2)).dropna().loc['2018-11-05':].values
    for hair, et in ((0.6, 'PRUDENTE'), (1.0, 'BACKTEST')):
        for re, rf in ((0.65, 0.5), (0.8, 0.5), (1.0, 0.5), (1.25, 0.5), (1.0, 0.65)):
            xe = (S0 - S0.mean() * (1 - hair)) * re / 0.5; xf = (S0 - S0.mean() * (1 - hair)) * rf / 0.5
            ok = 0; F = []
            for _ in range(4000):
                a, _t = examen(camino(xe, 30))
                if a: ok += 1; F.append(fondeada(camino(xf, 1500)))
            pa = ok / 4000; tot = np.array([sum(f[0]) for f in F]); vida = np.array([f[1] for f in F]) / 21; nc = np.array([len(f[0]) for f in F])
            print(f'{nom:27s} {et:8s} examen {re} / fondeada {rf} | aprueba en 30 días {pa*100:3.0f} % → {1/pa:4.1f} exámenes por cuenta | cobros por cuenta {nc.mean():.1f} '
                  f'(6 cobros {np.mean(nc==6)*100:3.0f} %) | cada {vida.sum()/max(nc.sum(),1):.1f} m | cobrado por cuenta {tot.mean():7,.0f} $ | vida {vida.mean():.1f} m | '
                  f'20 plazas {20*tot.mean()/vida.mean():7,.0f} $/mes con {20/vida.mean()/pa:4.1f} exámenes al mes', flush=True)
