"""C113 — efecto de añadir el oro largo en Asia (futuros GC 1 h, coste 0,74 pb) a la cartera de 150K. Uso: python3 c113_cartera.py DIR_SCRATCH"""
import sys, numpy as np, pandas as pd
import c94_ruptura_otros_futuros as c94
from c112_momentum_sesiones import sesiones
SP = sys.argv[1]; c94.SP = SP
h, ex = c94.carga_h1('GC'); r = sesiones(h, pd.Timedelta(hours=1), ex).asia
C = pd.read_csv(f'{SP}/componentes_B.csv', index_col=0, parse_dates=True).loc['2018-03-26':]
base = ['yen', 'cesta_yen', 'oro_vie_1655', 'oro_D-2', 'plata_visp_1655', 'plata_viernes', 'nikkei_Q+2', 'nikkei_Q-2']
def volctl(P): pv = P.rolling(60, min_periods=40).std().shift(1); return (P * (P.std() / pv).clip(0.5, 2)).dropna()
sh = lambda s: s.mean() / s.std() * np.sqrt(252)
rr = r.loc['2018-03-26':]; sig = rr.rolling(250, min_periods=60).std().shift(1).fillna(rr.std())
print(f'sigma media por operación {rr.std():.1f} pb → R esperado al 60 %: {0.6*(rr-0.74).mean()/rr.std():+.3f}')
print(f'oro Asia futuros 2018-26: media neta {(rr-0.74).mean():+.2f} pb, correlación con la cartera actual {C[base].sum(axis=1).corr((rr-0.74).reindex(C.index).fillna(0)):+.2f}, con C99 {C["oro_asia_C99"].corr((rr-0.74).reindex(C.index).fillna(0)):+.2f}')
for w in (0, 0.2, 0.5, 1.0):
    a = (0.005 * w * (rr - 0.74) / sig).reindex(C.index).fillna(0)
    T = volctl(C[base].sum(axis=1) + a); e = (T / T.std()).cumsum()
    print(f'peso {w:.1f}: Sharpe {sh(T):.2f} | 2018-21 {sh(T.loc[:"2021"]):.2f} | 2022-26 {sh(T.loc["2022":]):.2f} | caída {(e-e.cummax()).min():.1f} desv.')
