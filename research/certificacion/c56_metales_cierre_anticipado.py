"""C56: oro y plata en la última hora antes de un cierre anticipado. Ver PREREGISTRO_C56. Uso: python3 c56... DIR_H1"""
import sys
import numpy as np, pandas as pd
from c1_certificacion import t_nw
from c51_metales_reapertura import barras
R = {}
for s in ('GC', 'SI'):
    x = barras(s); x['fin'] = x.index + pd.Timedelta(hours=1)
    x['dia'] = x.index.tz_localize(None).normalize(); x = x[(x.index.weekday < 5) & (x.index.hour >= 8) & (x.index.hour < 17)]
    r = {}
    for d, g in x.groupby('dia'):
        if len(g) < 4 or g.fin.iloc[-1].hour > 14 or (g.fin.iloc[-1].hour == 14 and g.fin.iloc[-1].minute > 0): continue
        if g.instrument_id.iloc[-1] != g.instrument_id.iloc[-2]: continue
        r[d] = np.log(g.close.iloc[-1] / g.close.iloc[-2])
    R[s] = pd.Series(r)
X = pd.DataFrame(R); print('días de cierre anticipado:', ', '.join(d.strftime('%Y-%m-%d') for d in X.index[:6]), '...', len(X), 'en total')
for s in X: y = X[s].dropna(); print(f'{s}: n {len(y)} {y.mean()*1e4:.2f} pb (t {t_nw(y.values, 2):.2f}) positivos {(y>0).mean()*100:.0f}%')
m = X.mean(axis=1).dropna(); t = t_nw(m.values, 2)
print(f'PRINCIPAL media GC+SI: n {len(m)} {m.mean()*1e4:.2f} pb (t {t:.2f}) → {"PASA" if m.mean() > 0 and t >= 1.65 else "NO PASA"}')
