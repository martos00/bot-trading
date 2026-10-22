"""C41: corto CL miércoles 09:00→10:00 NY (hora previa al informe EIA). Ver PREREGISTRO_C41. Uso: python3 c41... DIR_H1"""
import glob, os, sys
import numpy as np, pandas as pd
from c1_certificacion import t_nw
x = pd.concat([pd.read_csv(f) for f in sorted(glob.glob(os.path.join(sys.argv[1], 'CL_*.csv')))])
x['close'] = pd.to_numeric(x.close, errors='coerce'); x = x[x.close > 0]
x.index = pd.to_datetime(x.ts_event, utc=True).dt.tz_convert('America/New_York'); x = x[~x.index.duplicated()].sort_index()
x['dia'] = x.index.tz_localize(None).normalize(); x['h'] = x.index.hour
a = x[x.h == 8][['dia', 'close', 'instrument_id']].set_index('dia'); b = x[x.h == 9][['dia', 'close', 'instrument_id']].set_index('dia')
j = a.join(b, lsuffix='0', rsuffix='1', how='inner'); j = j[j.instrument_id0 == j.instrument_id1]
j['r'] = -np.log(j.close1 / j.close0); j['neto'] = j.r - 2e-4
w = j[j.index.weekday == 2]; an = w.neto.groupby(w.index.year).sum()
print(f'miércoles: n {len(w)} bruto {w.r.mean()*1e4:.2f} pb neto {w.neto.mean()*1e4:.2f} pb (t {t_nw(w.neto.values):.2f}) años+ {(an>0).sum()}/{len(an)}')
for a0, a1 in (('2010', '2017'), ('2018', '2026')):
    y = w.loc[a0:a1]; print(f'   {a0}-{a1}: bruto {y.r.mean()*1e4:.2f} pb (t {t_nw(y.r.values):.2f})')
for d, n in enumerate(['lun', 'mar', 'mié', 'jue', 'vie']):
    y = j[j.index.weekday == d]; print(f'   informativo {n}: bruto {y.r.mean()*1e4:.2f} pb (t {t_nw(y.r.values):.2f})')
print('por año neto (pb):', (an * 1e4).round(0).to_dict())
crit = {'1 t>=2': w.neto.mean() > 0 and t_nw(w.neto.values) >= 2, '2 años>=60%': (an > 0).mean() >= 0.6}
print('CRITERIOS:', crit, '→ PASA' if all(crit.values()) else '→ NO PASA')
