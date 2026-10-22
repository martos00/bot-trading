"""E6: ¿E1 sigue el reloj de Frankfurt o el de NY en las semanas de desfase? Ver PREREGISTRO_E6. Datos FXCM M1 (mid)."""
import glob
from datetime import datetime
from zoneinfo import ZoneInfo
import numpy as np, pandas as pd
from c1_certificacion import fxcm, en, t_nw
NY, FRA = ZoneInfo('America/New_York'), ZoneInfo('Europe/Berlin')
S = '/tmp/claude-0/-home-user-bot-trading/682335b1-28ae-5d18-9355-ce7f0f968722/scratchpad/fxcm/EURUSD/'
b, a = {}, {}
for f in sorted(glob.glob(S + 'EURUSD_*.csv.gz')):
    bb, aa = fxcm(f); b.update(bb); a.update(aa)
def mid(t):
    x, y = en(b, t), en(a, t); return (x + y) / 2
filas = []
for d in pd.bdate_range('2012-01-03', '2026-09-30'):
    t = lambda h: datetime(d.year, d.month, d.day, h, tzinfo=NY)
    gap = (t(6).utcoffset() - t(6).astimezone(FRA).utcoffset()).total_seconds() / 3600 == -5
    p = [mid(t(h)) for h in (6, 7, 8, 9)]
    if np.isnan(p).any(): continue
    A, C, B = -np.log(p[1] / p[0]), -np.log(p[2] / p[1]), -np.log(p[3] / p[2])
    filas.append(dict(dia=d, gap=gap, A=A, C=C, B=B, D=B - A))
X = pd.DataFrame(filas).set_index('dia')
for nom, y in (('desfase', X[X.gap]), ('normales', X[~X.gap])):
    print(f'{nom}: n {len(y)} | corto A 06-07 NY {y.A.mean()*1e4:.2f} pb (t {t_nw(y.A.values):.2f}) | común 07-08 {y.C.mean()*1e4:.2f} pb (t {t_nw(y.C.values):.2f}) '
          f'| B 08-09 NY {y.B.mean()*1e4:.2f} pb (t {t_nw(y.B.values):.2f}) | D = B−A {y.D.mean()*1e4:.2f} pb (t {t_nw(y.D.values):.2f})')
g = X[X.gap]; tD = t_nw(g.D.values)
dec = 'reloj de Frankfurt' if tD >= 1.65 else ('reloj de NY' if tD <= -1.65 else 'sin evidencia → se mantiene el reloj de NY')
print('DECISIÓN:', dec)
