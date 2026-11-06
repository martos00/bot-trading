"""C110 — variantes de configuración de la cartera de 150K (PREREGISTRO_C110). Uso: python3 c110_configuracion_150k.py componentes_B.csv"""
import sys, numpy as np, pandas as pd
C = pd.read_csv(sys.argv[1], index_col=0, parse_dates=True).loc['2018-03-26':]
base = ['yen', 'cesta_yen', 'oro_vie_1655', 'oro_D-2', 'plata_visp_1655', 'plata_viernes', 'nikkei_Q+2', 'nikkei_Q-2']
def volctl(P): pv = P.rolling(60, min_periods=40).std().shift(1); return (P * (P.std() / pv).clip(0.5, 2)).dropna()
def paridad(X):
    s = X.rolling(252, min_periods=120).std().shift(1); w = (1 / s); w = w.div(w.mean(axis=1), axis=0)   # misma vol por componente, media de pesos 1
    return (X * w).dropna(how='all').fillna(0)
sh = lambda s: s.mean() / s.std() * np.sqrt(252)
def dd(s): k = s / s.std(); e = k.cumsum(); return (e - e.cummax()).min()   # caída a misma volatilidad
V = {'V0 actual': volctl(C[base].sum(axis=1)), 'V1 sin control de vol.': C[base].sum(axis=1),
     'V2 paridad de riesgo': volctl(paridad(C[base]).sum(axis=1)), 'V3 + cobre': volctl(C[base + ['cobre_asia_C102']].sum(axis=1)),
     'V4 + cobre con paridad': volctl(paridad(C[base + ['cobre_asia_C102']]).sum(axis=1))}
ini = V['V2 paridad de riesgo'].index[0]
r0 = None
for k, s in V.items():
    s = s.loc[ini:]; a, b = s.loc[:'2021'], s.loc['2022':]
    if r0 is None: r0 = (sh(s), sh(a), sh(b), dd(s))
    ok = sh(s) > r0[0] and sh(a) > r0[1] and sh(b) > r0[2] and dd(s) >= 1.1 * r0[3]
    print(f'{k:24s} Sharpe {sh(s):.2f} | 2018-21 {sh(a):.2f} | 2022-26 {sh(b):.2f} | caída (en desv. diarias) {dd(s):6.1f} | ' + ('referencia' if k.startswith('V0') else ('MEJORA' if ok else 'no mejora')))
print('periodo común desde', ini.date())
