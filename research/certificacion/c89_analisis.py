"""C89 — análisis de los eventos exportados de QuantConnect (c89_eventos_quantconnect.txt: X aammdd signo GEX rendimiento_pb ES 15-16 NY)."""
import numpy as np, pandas as pd
from c1_certificacion import t_nw
x = pd.read_csv('c89_eventos_quantconnect.txt', sep=' ', header=None, names=['X', 'd', 's', 'g', 'r']).query("X == 'X'")
x.index = pd.to_datetime(x.d.astype(int).astype(str), format='%y%m%d'); x = x[~x.index.duplicated()].sort_index()
x['regla'] = np.where(x.g < 0, x.s, -x.s) * x.r; x['control'] = x.s * x.r
h = x.index[len(x) // 2]
def lin(nom, v): return f'{nom}: n {len(v)} {v.mean():+.2f} pb (t {t_nw(v.values):.2f})'
print(lin('REGLA', x.regla), '|', lin('1.ª mitad', x.regla[:h]), '|', lin('2.ª mitad', x.regla[h:]))
print(lin('control (siempre a favor de s)', x.control), '| GEX<0 días', (x.g < 0).sum())
for nom, q in (('GEX<0 continuación', x[x.g < 0].control), ('GEX>0 reversión', -x[x.g > 0].control)): print('  ', lin(nom, q))
print('   por año:', x.regla.groupby(x.index.year).mean().round(1).to_dict())
c = {'t>=2.24': x.regla.mean() > 0 and t_nw(x.regla.values) >= 2.24, 'mitades>0': x.regla[:h].mean() > 0 and x.regla[h:].mean() > 0,
     '2.ª mitad>0,73': x.regla[h:].mean() > 0.73, 'mejor que control': x.regla.mean() > x.control.mean()}
print('CRITERIOS:', c, '→ PASA' if all(c.values()) else '→ NO PASA')
