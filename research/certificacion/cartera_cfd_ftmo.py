"""Estimación de la cartera de CFD en FTMO con los costes medidos (12-nov-2026, costes_cartera_resumen.csv + comisiones de su web).
Parte de componentes_A (salidas 16:45; ya netos del coste de futuros) y resta la diferencia de coste FTMO − futuros por operación,
pasada a unidades de la serie con la sigma típica de cada operación (aproximada de los registros del bot). Sin plata, sin cesta E12,
sin bitcoin y sin C113 (en FTMO el oro reabre hacia las 18:15 y ahí ya no compensa). Uso: python3 cartera_cfd_ftmo.py DIR_SCRATCH"""
import sys, numpy as np, pandas as pd
C = pd.read_csv(f'{sys.argv[1]}/componentes_A.csv', index_col=0, parse_dates=True).loc['2018-03-26':]
#            columna:            (Δ coste pb, sigma pb, peso)
AJ = {'yen': (0.20, 10, 1), 'cesta_yen': (0.40, 10, 1 / 3), 'oro_vie_1645': (0.58, 18, 1), 'oro_D-2': (0.55, 33, 1),
      'nikkei_Q+2': (-0.95, 40, 1), 'nikkei_Q-2': (-0.95, 48, 1), 'oro_video_C93': (0.55, 80, 0.2), 'oro_asia_C99': (0.55, 90, 0.2),
      'nikkei_asia_C101': (-0.5, 120, 0.2)}
def volctl(P): pv = P.rolling(60, min_periods=40).std().shift(1); return (P * (P.std() / pv).clip(0.5, 2)).dropna()
sh = lambda s: s.mean() / s.std() * np.sqrt(252)
X = C[list(AJ)].copy()
for c, (dc, sg, w) in AJ.items():
    m = X[c] != 0; X.loc[m, c] -= 0.005 * w * dc / sg
for nom, cols in (('CFD FTMO (sin diarias)', ['yen', 'cesta_yen', 'oro_vie_1645', 'oro_D-2', 'nikkei_Q+2', 'nikkei_Q-2']),
                  ('CFD FTMO (con diarias C93, C99, C101)', list(AJ))):
    S = volctl(X[cols].sum(axis=1)); S0 = volctl(C[cols].sum(axis=1))
    print(f'{nom:40s} Sharpe {sh(S):.2f} (con costes de futuros sería {sh(S0):.2f}) | 2018-21 {sh(S.loc[:"2021"]):.2f} | 2022-26 {sh(S.loc["2022":]):.2f}')
    for r in (0.5, 0.65):
        p = S * r / 0.5; e = p.cumsum(); m = p.resample('ME').sum()
        print(f'    riesgo {r} %: rent. {p.mean()*252*100:.1f} %/año (al 60 % ≈ {0.6*p.mean()*252*100:.1f} %) | mes medio {m.mean()*100:.2f} % | caída máx {(e-e.cummax()).min()*100:.1f} % | meses negativos {(m<0).mean()*100:.0f} %')
