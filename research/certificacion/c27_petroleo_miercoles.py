"""C27: corto del crudo (CL) el miércoles del informe EIA (cierre martes → cierre miércoles). Ver PREREGISTRO_C27.
Uso: python3 c27_petroleo_miercoles.py DIR_OIL (ficheros SIM_AAAA.csv de Databento)"""
import glob, os, sys
import numpy as np, pandas as pd
from c1_certificacion import t_nw
D = sys.argv[1]
def serie(s):
    x = pd.concat([pd.read_csv(f, parse_dates=['ts_event']) for f in sorted(glob.glob(os.path.join(D, f'{s}_*.csv')))])
    x['dia'] = x.ts_event.dt.tz_localize(None).dt.normalize()
    x = x[x.dia.dt.weekday < 5].drop_duplicates('dia').set_index('dia').sort_index()
    r = np.log(x.close).diff(); r[x.instrument_id != x.instrument_id.shift()] = np.nan
    return r.loc[:'2026-09-30']
def tdif(a, b): return (a.mean() - b.mean()) / np.sqrt(a.var() / len(a) + b.var() / len(b))
COSTE = {'CL': 2e-4, 'RB': 3e-4, 'HO': 3e-4}; crit = None
for s in ('CL', 'RB', 'HO'):
    r = serie(s); ok = (r.index.to_series().diff().dt.days == 1).values
    mie = -r[(r.index.weekday == 2) & ok].dropna(); resto = -r[~((r.index.weekday == 2) & ok)].dropna()
    print(f'== {s}: corto los miércoles ==')
    for a, b in (('2010', '2017'), ('2018', '2026')):
        x = mie.loc[a:b]; ne = x - COSTE[s]; an = ne.groupby(ne.index.year).sum(); o = resto.loc[a:b]
        print(f'  {a}-{b}: n {len(x)} bruto {x.mean()*1e4:6.1f} pb (t {t_nw(x):.2f}) neto {ne.mean()*1e4:6.1f} pb años+ {(an>0).sum()}/{len(an)} | corto resto de días {o.mean()*1e4:.1f} pb, dif t {tdif(x,o):.2f}')
        if s == 'CL':
            if a == '2010': d0 = x.mean() > 0
            else: crit = {'D>0': d0, '1 t>=2': ne.mean() > 0 and t_nw(ne) >= 2, '2 bruto>=3x': x.mean() >= 3 * COSTE[s], '3 años>=60%': (an > 0).mean() >= 0.6, '4 dif t>=1,645': tdif(x, o) >= 1.645}
    print('  por día de la semana (precio, pb, 2010-2026):', {n: round(r[r.index.weekday == w].mean()*1e4, 1) for w, n in enumerate('LMXJV')})
print('\nCRITERIOS CL:', crit, '→ CERTIFICADA' if all(crit.values()) else '→ NO CERTIFICADA')
