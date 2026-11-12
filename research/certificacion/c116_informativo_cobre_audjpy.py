"""INFORMATIVO (no decide): efecto en la cartera CFD C116 de añadir C102 cobre (peso 0,2) y AUDJPY en E11, con costes CFD supuestos
(sin medir en Upcomers). Cobre: serie de futuros HG (componentes_A, coste 2 pb, sigma por operación supuesta 110 pb). AUDJPY: HistData
01-02 NY fin de trimestre (C55), peso 1/3 como los otros cruces de E11. Uso: python3 c116_informativo_cobre_audjpy.py DIR_SCRATCH"""
import sys, io, contextlib, runpy, numpy as np, pandas as pd
SP = sys.argv[1]; sys.argv = ['x', SP]
with contextlib.redirect_stdout(io.StringIO()): g = runpy.run_path('c116_mejoras_cartera_cfd.py')
P0, X, comp, volctl, sh = g['P0'], g['X'], g['comp'], g['volctl'], g['sh']; C = g['C']
P1 = P0.copy()
for nom, (a, quita) in g['pasan'].items(): P1 = P1 + a - (X[quita] if quita else 0)
V1 = volctl(P1)
def info(nom, P):
    V = volctl(P); out = []
    for r in (0.65, 0.8):
        p = V * r / 0.5; e = p.cumsum(); out.append(f'r{r}: {p.mean()*252*100:.1f} %/año, caída {(e-e.cummax()).min()*100:.1f} %')
    print(f'{nom:44s} Sharpe {sh(V):.2f} (Δ {sh(V)-sh(V1):+.2f}; 18-21 {sh(V.loc[:"2021"])-sh(V1.loc[:"2021"]):+.2f}, 22-26 {sh(V.loc["2022":])-sh(V1.loc["2022":]):+.2f}) | ' + ' | '.join(out))
info('BASE C116', P1)
cu = C['cobre_asia_C102'].reindex(P1.index).fillna(0)
for cpb in (2, 4, 6, 8):
    adj = cu.copy(); m = adj != 0; adj[m] -= 0.005 * 0.2 * (cpb - 2) / 110
    info(f'+ cobre C102, coste CFD {cpb} pb', P1 + adj)
with contextlib.redirect_stdout(io.StringIO()): h = runpy.run_path('c55_yen_fin_trimestre_cruces.py')
aj = h['R']['AUDJPY']; aj.index = pd.DatetimeIndex(aj.index)
for cpb in (1.2, 1.8, 2.5):
    info(f'+ AUDJPY en E11 (peso 1/3), coste {cpb} pb', P1 + comp(aj, cpb * 1e-4, 1 / 3))
adj = cu.copy(); m = adj != 0; adj[m] -= 0.005 * 0.2 * (4 - 2) / 110
info('+ cobre 4 pb + AUDJPY 1,8 pb', P1 + adj + comp(aj, 1.8e-4, 1 / 3))
