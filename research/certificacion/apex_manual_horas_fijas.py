"""Apex 150K operando A MANO solo las estrategias de hora fija (sin rupturas). Mismas reglas que apex_rotacion.py.
M1: yen E9/E11, oro viernes 16:55, oro D-2, plata víspera y plata viernes, Nikkei Q+2 y Q-2 (sin C113: madrugada en España).
M2: M1 + C113 (oro 18:00→03:00 NY = 00:00→09:00 España, domingo a jueves).
M3: M1 sin Nikkei Q-2 (20:00 NY = 02:00 España). Riesgo 0,65 %. Uso: python3 apex_manual_horas_fijas.py DIR_SCRATCH"""
import sys, numpy as np, pandas as pd
src = open('plan_reinversion_etf.py').read().split('CAP, OBJ')[0]
base = ['yen', 'cesta_yen', 'oro_vie_1655', 'oro_D-2', 'plata_visp_1655', 'plata_viernes', 'nikkei_Q+2', 'nikkei_Q-2']
VAR = {'M1 horas fijas sin C113': base, 'M2 horas fijas + C113': base + ['c113'], 'M3 M1 sin Nikkei de madrugada': [c for c in base if c != 'nikkei_Q-2']}
ap = open('apex_rotacion.py').read(); motor = ap[ap.index('CAP = 150000'):ap.index('for hair, et in')]; bucle = ap[ap.index('for hair, et in'):]
exec(src)
sh = lambda s: s.mean() / s.std() * np.sqrt(252)
for nom, cols in VAR.items():
    P = C[cols].sum(axis=1); pv = P.rolling(60, min_periods=40).std().shift(1); S_ = (P * (P.std() / pv).clip(0.5, 2)).dropna().loc['2018-11-05':]
    SER = S_.values * 0.65 / 0.5
    m = pd.Series(SER, index=S_.index); dmes = m.resample('ME').apply(lambda v: v.max() / v.sum() if v.sum() > 0 else np.nan).dropna()
    print(f'\n================ {nom}: {SER.mean()*252*100:.1f} %/año a 0,65 % | Sharpe {sh(S_):.2f} | meses + con mejor día ≥ 50 % del mes: {(dmes>=0.5).mean()*100:.0f} %')
    exec(motor); exec(bucle)
