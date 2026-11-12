"""Apex 300K a mano (horas fijas M1/M2) frente a 150K. Reglas 300K SUPUESTAS (sin verificar): objetivo 20.000 $, pérdida máx. 7.500 $
arrastrada que se fija en el saldo inicial + 100 $, mismas condiciones de cobro que la 150K escaladas (colchón y mínimo ×2, días con
≥ 350 $ ×2 = 700 $, ningún día ≥ 50 % del beneficio), escalera de cobros ×2 (5.000/6.000/6.000/6.000/8.000/10.000 $), se cierra tras 6.
Riesgo 0,5 y 0,65. Uso: python3 apex_300k_manual.py DIR_SCRATCH"""
import sys, numpy as np, pandas as pd
src = open('plan_reinversion_etf.py').read().split('CAP, OBJ')[0]; exec(src)
ap = open('apex_rotacion.py').read(); motor = ap[ap.index('rng = np.random'):ap.index('for hair, et in')]; bucle = ap[ap.index('for hair, et in'):]
base = ['yen', 'cesta_yen', 'oro_vie_1655', 'oro_D-2', 'plata_visp_1655', 'plata_viernes', 'nikkei_Q+2', 'nikkei_Q-2']
for nom, cols in (('M1', base), ('M2', base + ['c113'])):
    P = C[cols].sum(axis=1); pv = P.rolling(60, min_periods=40).std().shift(1); S0 = (P * (P.std() / pv).clip(0.5, 2)).dropna().loc['2018-11-05':].values
    for cap, obj, dd, esc in ((150000, 9000, 5000, [2500, 3000, 3000, 3000, 4000, 5000]), (300000, 20000, 7500, [5000, 6000, 6000, 6000, 8000, 10000])):
        for r in (0.5, 0.65):
            SER = S0 * r / 0.5
            CAP, OBJ, DD = cap, obj, dd; RED = cap + 4100 * cap / 150000; B = 20; MINC = cap + 4600 * cap / 150000; ESC = esc
            print(f'\n================ {nom} | Apex {cap//1000}K | riesgo {r}')
            exec(motor.replace('if r >= 350', f'if r >= {350 * cap / 150000:.0f}')); exec(bucle)
            
