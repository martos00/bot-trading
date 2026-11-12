"""Apex a mano, sin rupturas (M2: horas fijas + C113; M1 sin C113). Flota de 20 cuentas fondeadas siempre llenas: cada plaza cuando se
cierra (6 cobros o pérdida) se repone con exámenes (los que hagan falta hasta aprobar). Ingreso por plaza y mes = cobrado medio por cuenta /
(vida fondeada + tiempo de examen hasta aprobar, si no se solapan) y con solape (exámenes en paralelo: la plaza solo espera la vida fondeada).
Reglas de apex_300k_manual.py (300K supuestas). Riesgo del examen y de la fondeada por separado. Uso: python3 apex_flota_optima.py DIR_SCRATCH"""
import sys, numpy as np, pandas as pd
exec(open('plan_reinversion_etf.py').read().split('CAP, OBJ')[0])
ap = open('apex_rotacion.py').read(); motor = ap[ap.index('def camino'):ap.index('for hair, et in')]
base = ['yen', 'cesta_yen', 'oro_vie_1655', 'oro_D-2', 'plata_visp_1655', 'plata_viernes', 'nikkei_Q+2', 'nikkei_Q-2']
B = 20; rng = np.random.default_rng(31)
for nom, cols in (('M2 (con oro de madrugada)', base + ['c113']), ('M1 (sin oro de madrugada)', base)):
    P = C[cols].sum(axis=1); pv = P.rolling(60, min_periods=40).std().shift(1); S0 = (P * (P.std() / pv).clip(0.5, 2)).dropna().loc['2018-11-05':].values
    for cap, obj, dd, esc in ((300000, 20000, 7500, [5000, 6000, 6000, 6000, 8000, 10000]), (150000, 9000, 5000, [2500, 3000, 3000, 3000, 4000, 5000])):
        CAP, OBJ, DD, ESC = cap, obj, dd, esc; RED = cap + 4100 * cap / 150000; MINC = cap + 4600 * cap / 150000
        exec(motor.replace('if r >= 350', f'if r >= {350 * cap / 150000:.0f}'))
        for hair, et in ((0.6, 'PRUDENTE'), (1.0, 'BACKTEST')):
            for re, rf in ((0.5, 0.5), (0.8, 0.5), (1.0, 0.5), (0.65, 0.65)):
                xe = (S0 - S0.mean() * (1 - hair)) * re / 0.5; xf = (S0 - S0.mean() * (1 - hair)) * rf / 0.5
                ok = 0; n = 0; tex = []; F = []
                for _ in range(3000):
                    R = camino(xe, 900); a, t = evaluacion(R, 0); n += 1; tex.append(t)
                    if a: ok += 1; Rf = camino(xf, 1500); F.append(fondeada(Rf, 0))
                pa = ok / n; te = np.mean(tex) / 21; tot = np.array([sum(f[0]) for f in F]); vida = np.array([f[1] for f in F]) / 21
                ex_por = 1 / pa; mes_plaza = tot.mean() / vida.mean()
                print(f'{nom:27s} {cap//1000}K {et:8s} examen {re} / fondeada {rf} | aprueba {pa*100:3.0f} % | exámenes por cuenta fondeada {ex_por:.1f} | '
                      f'vida fondeada {vida.mean():4.1f} m | cobrado por cuenta {tot.mean():7,.0f} $ | por plaza y mes {mes_plaza:6,.0f} $ → 20 plazas {20*mes_plaza:7,.0f} $/mes | '
                      f'exámenes al mes para 20 plazas {20/vida.mean()*ex_por:.1f}', flush=True)
