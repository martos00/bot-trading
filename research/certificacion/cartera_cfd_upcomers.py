"""Cartera de CFD en Upcomers con los costes medidos en su cuenta pública de MT5 (12-nov-2026, research/costes_cfd/upcomers_*.csv).
Mismo método que cartera_cfd_ftmo.py: Δ coste Upcomers − futuros = Δ FTMO + (coste Upcomers − coste FTMO), ida y vuelta mediana.
Comisión: Upcomers 5 $/lote en divisas y metales (igual que FTMO); índices solo diferencial.
  yen USDJPY 0,10 vs 0,28 pb (−0,18) | cesta yen media 0,58 vs 0,66 (−0,09) | oro ≈ igual (0,72–1,24, solo 2 semanas de historial: se deja como FTMO)
  Nikkei JPCJPY.c 0,61 vs ~1,55 (−0,95; C101 igual −0,95, conservador).
Sin plata (7–9 pb), sin cesta E12, sin bitcoin (comisión cripto sin confirmar) y sin C113 (no está en componentes_A).
Uso: python3 cartera_cfd_upcomers.py DIR_SCRATCH"""
import sys, numpy as np, pandas as pd
C = pd.read_csv(f'{sys.argv[1]}/componentes_A.csv', index_col=0, parse_dates=True).loc['2018-03-26':]
AJ = {'yen': (0.02, 10, 1), 'cesta_yen': (0.31, 10, 1 / 3), 'oro_vie_1645': (0.58, 18, 1), 'oro_D-2': (0.55, 33, 1),
      'nikkei_Q+2': (-1.90, 40, 1), 'nikkei_Q-2': (-1.90, 48, 1), 'oro_video_C93': (0.55, 80, 0.2), 'oro_asia_C99': (0.55, 90, 0.2),
      'nikkei_asia_C101': (-1.45, 120, 0.2)}
def volctl(P): pv = P.rolling(60, min_periods=40).std().shift(1); return (P * (P.std() / pv).clip(0.5, 2)).dropna()
sh = lambda s: s.mean() / s.std() * np.sqrt(252)
X = C[list(AJ)].copy()
for c, (dc, sg, w) in AJ.items():
    m = X[c] != 0; X.loc[m, c] -= 0.005 * w * dc / sg
for nom, cols in (('CFD Upcomers (sin diarias)', ['yen', 'cesta_yen', 'oro_vie_1645', 'oro_D-2', 'nikkei_Q+2', 'nikkei_Q-2']),
                  ('CFD Upcomers (con diarias C93, C99, C101)', list(AJ))):
    S = volctl(X[cols].sum(axis=1)); S0 = volctl(C[cols].sum(axis=1))
    print(f'{nom:42s} Sharpe {sh(S):.2f} (con costes de futuros sería {sh(S0):.2f}) | 2018-21 {sh(S.loc[:"2021"]):.2f} | 2022-26 {sh(S.loc["2022":]):.2f}')
    for r in (0.5, 0.65, 0.8, 1.0):
        p = S * r / 0.5; e = p.cumsum(); m = p.resample('ME').sum()
        print(f'    riesgo {r} %: rent. {p.mean()*252*100:.1f} %/año (al 60 % ≈ {0.6*p.mean()*252*100:.1f} %) | mes medio {m.mean()*100:.2f} % | caída máx {(e-e.cummax()).min()*100:.1f} % | meses negativos {(m<0).mean()*100:.0f} %')
