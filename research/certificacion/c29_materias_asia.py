"""C29: largo 01:00→07:00 UTC en HG, ZS, CL, GC (horario de Shanghái). Ver PREREGISTRO_C29. Uso: python3 c29_materias_asia.py DIR_H1"""
import glob, os, sys
import numpy as np, pandas as pd
from scipy import stats
from c1_certificacion import t_nw
D = sys.argv[1]
COSTE = {'HG': 1.1e-4, 'ZS': 2e-4, 'CL': 1.5e-4, 'GC': 0.5e-4}
e = pd.read_csv('e1_franjas.csv', index_col=0, parse_dates=True); e1 = -np.log(e.mid8 / e.mid6)
def ventana(x, h0, h1):
    """rentabilidad del cierre de la barra que termina a h0 UTC al cierre de la que termina a h1 UTC, mismo contrato."""
    fin = x.index + pd.Timedelta(hours=1)
    c = pd.DataFrame({'c': x.close.values, 'id': x.instrument_id.values}, index=fin)
    a = c[c.index.hour == h0]; b = c[c.index.hour == h1]
    a.index = a.index.normalize(); b.index = b.index.normalize()
    j = a.join(b, lsuffix='0', rsuffix='1', how='inner')
    j = j[(j.id0 == j.id1) & (j.index.weekday < 5)]
    return np.log(j.c1 / j.c0)
series, us = {}, {}
for s in COSTE:
    x = pd.concat([pd.read_csv(f, parse_dates=['ts_event']) for f in sorted(glob.glob(os.path.join(D, f'{s}_*.csv')))])
    x = x.drop_duplicates('ts_event').set_index(x.ts_event.dt.tz_localize(None)).sort_index().loc[:'2026-09-30']
    series[s] = ventana(x, 1, 7); us[s] = ventana(x, 14, 20)
X = pd.DataFrame(series); f = X.mean(axis=1, skipna=False).dropna()
print('== FACTOR (media de HG, ZS, CL, GC), largo 01:00→07:00 UTC ==')
for a, b in (('2010', '2017'), ('2018', '2026')):
    y = f.loc[a:b]; an = y.groupby(y.index.year).mean()
    print(f'  {a}-{b}: n {len(y)} {y.mean()*1e4:5.2f} pb (t {t_nw(y.values):.2f}) años+ {(an>0).sum()}/{len(an)}')
y = f.loc['2018':]; an = y.groupby(y.index.year).mean(); cm = np.mean(list(COSTE.values()))
crit = {'D>0': f.loc[:'2017'].mean() > 0, '1 t>=2': y.mean() > 0 and t_nw(y.values) >= 2, '2 años>=60%': (an > 0).mean() >= 0.6,
        '3 neto>0 y bruto>=3x': y.mean() - cm > 0 and y.mean() >= 3 * cm}
print('  corr con E1:', round(f.corr(e1.reindex(f.index)), 3))
print('\n== Por materia (informativo) ==')
ps = []
for s in COSTE:
    d, c = X[s].loc[:'2017'].dropna(), X[s].loc['2018':].dropna(); u = us[s].loc['2018':].dropna()
    ps.append(1 - stats.norm.cdf(t_nw(c.values)))
    print(f'  {s}: 2010-17 {d.mean()*1e4:5.2f} pb (t {t_nw(d.values):.2f}) | 2018-26 {c.mean()*1e4:5.2f} pb (t {t_nw(c.values):.2f}) '
          f'coste {COSTE[s]*1e4:.1f} pb | EE.UU. 14-20 UTC 2018-26 {u.mean()*1e4:5.2f} pb')
print('\nCRITERIOS FACTOR:', crit, '→ CERTIFICADA' if all(crit.values()) else '→ NO CERTIFICADA')
