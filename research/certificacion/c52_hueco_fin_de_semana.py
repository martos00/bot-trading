"""C52: corto oro/plata durante el cierre del fin de semana. Ver PREREGISTRO_C52. Uso: python3 c52... DIR_H1"""
import sys
import numpy as np, pandas as pd
from c1_certificacion import t_nw
from c51_metales_reapertura import barras
G = {}
for s in ('GC', 'SI'):
    x = barras(s); vie = x[(x.index.weekday == 4) & (x.index.hour == 16)]; dom = x[(x.index.weekday == 6) & (x.index.hour == 18)]
    r = {}
    for t, f in vie.iterrows():
        k = t.normalize() + pd.Timedelta(days=2, hours=18)
        if k in dom.index and dom.instrument_id[k] == f.instrument_id: r[t.normalize().tz_localize(None)] = -np.log(dom.close[k] / f.close)
    G[s] = pd.Series(r)
y = pd.DataFrame(G).dropna(); m = y.mean(axis=1); an = m.groupby(m.index.year).sum()
print(f'hueco fin de semana (corto): n {len(m)} {m.mean()*1e4:.2f} pb (t {t_nw(m.values):.2f}) | GC {y.GC.mean()*1e4:.2f} (t {t_nw(y.GC.values):.2f}) | SI {y.SI.mean()*1e4:.2f} (t {t_nw(y.SI.values):.2f}) '
      f'| 2010-17 {m.loc[:"2017"].mean()*1e4:.2f} | 2018-26 {m.loc["2018":].mean()*1e4:.2f} | años+ {(an>0).sum()}/{len(an)}')
crit = {'1 t>=2': m.mean() > 0 and t_nw(m.values) >= 2, '2 años>=60%': (an > 0).mean() >= 0.6, '3 2018-26>0': m.loc['2018':].mean() > 0, '4 bruto>=3·coste': m.mean() >= 4.5e-4}
print('CRITERIOS:', crit, '→ PASA' if all(crit.values()) else '→ NO PASA')
