"""Exporta las series diarias (riesgo 0,5 %, con control de volatilidad, mismas fechas) para el simulador de planes:
U = cartera CFD Upcomers (C116); F = cartera CFD con costes de FTMO (cartera_cfd_ftmo.py, con diarias; proxy de FTMO y firmas parecidas);
T = futuros con la configuración del bot en Tradeify/Lucid; O = futuros cartera completa (cuenta propia: Nikkei, cobre, bitcoin 0,2, E12, C113).
Uso: python3 series_planes_10k.py DIR_SCRATCH  → DIR_SCRATCH/series_planes_10k.csv"""
import sys, io, contextlib, runpy, numpy as np, pandas as pd
SP = sys.argv[1]; sys.path.insert(0, '.'); sys.argv = ['x', SP]
volctl = lambda P: (P * (P.std() / P.rolling(60, min_periods=40).std().shift(1)).clip(0.5, 2)).dropna()
with contextlib.redirect_stdout(io.StringIO()): g = runpy.run_path('c116_mejoras_cartera_cfd.py')
P1 = g['P0'].copy()
for nom, (a, quita) in g['pasan'].items(): P1 = P1 + a - (g['X'][quita] if quita else 0)
U = volctl(P1)
exec(open('cartera_cfd_ftmo.py').read().split('for nom, cols in')[0].replace('sys.argv[1]', 'SP'))
F = volctl(X[list(AJ)].sum(axis=1))
CB = pd.read_csv(f'{SP}/componentes_B.csv', index_col=0, parse_dates=True).loc['2018-03-26':]
import c94_ruptura_otros_futuros as c94
from c112_momentum_sesiones import sesiones
c94.SP = SP; h, ex = c94.carga_h1('GC'); rr = sesiones(h, pd.Timedelta(hours=1), ex).asia.loc['2018-03-26':]; rr.index = pd.DatetimeIndex(rr.index)
sig = rr.rolling(250, min_periods=60).std().shift(1).fillna(rr.std()); c113 = (0.005 * 0.2 * (rr - 0.74) / sig).reindex(CB.index).fillna(0)
T = volctl(CB[['yen', 'cesta_yen', 'oro_vie_1655', 'oro_D-2', 'plata_visp_1655', 'plata_viernes', 'oro_video_C93', 'oro_asia_C99']].sum(axis=1) + c113)
cB = CB.copy(); cB['bitcoin'] *= 0.2
O = volctl(cB.sum(axis=1) + c113)
D = pd.DataFrame({'U': U, 'F': F, 'T': T, 'O': O}).dropna()
sh = lambda s: s.mean() / s.std() * np.sqrt(252)
for c in D: print(f'{c}: {D[c].mean()*252*100:5.1f} %/año a riesgo 0,5 | Sharpe {sh(D[c]):.2f} | desv. diaria {D[c].std()*100:.2f} %')
print('correlaciones\n', D.corr().round(2)); D.to_csv(f'{SP}/series_planes_10k.csv'); print(len(D), 'días', D.index[0].date(), '→', D.index[-1].date())
