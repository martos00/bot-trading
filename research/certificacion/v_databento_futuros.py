"""Verificación con fuente independiente (Databento, CME, contrato continuo por volumen, sin rentabilidades entre contratos
distintos) de C12 (fin de mes en bonos), C16 (ventana FOMC en bonos) y C15-N (gas natural los jueves). Reglas sin cambios.
Uso: python3 v_databento_futuros.py DIR_DATABENTO FOMC_CSV"""
import os, sys
import numpy as np, pandas as pd
from c1_certificacion import t_nw
D, FF = sys.argv[1:3]
COSTE = {'ZN': 1.8e-4, 'ZF': 1.09e-4, 'ZB': 2.94e-4, 'NG': 5e-4}
def serie(s):
    x = pd.read_csv(os.path.join(D, f'{s}.v.0.csv'), parse_dates=['ts_event'])
    x['dia'] = x.ts_event.dt.tz_localize(None).dt.normalize()
    x = x[x.dia.dt.weekday < 5].drop_duplicates('dia').set_index('dia').sort_index()
    r = np.log(x.close).diff()
    r[x.instrument_id != x.instrument_id.shift()] = np.nan      # cambio de contrato: sin rentabilidad
    return r.loc[:'2026-09-30']
def linea(nom, x, c):
    ne = x - c; an = ne.groupby(ne.index.year).sum()
    return f'{nom}: n {len(x)} bruto {x.mean()*1e4:6.2f} pb (t {t_nw(x.dropna()):.2f}) neto {ne.mean()*1e4:6.2f} pb (t {t_nw(ne.dropna()):.2f}) años+ {(an>0).sum()}/{len(an)}'
fomc = pd.to_datetime(pd.read_csv(FF).fomc)
print('== C12: último día hábil del mes, largo (cierre penúltimo → cierre último) ==')
for s in ('ZN', 'ZF', 'ZB'):
    r = serie(s); s_ = r.index.to_series(); m = s_.dt.to_period('M'); ult = (m != m.shift(-1)); ult.iloc[-1] = False
    x = r[ult.values].dropna()
    for a, b in (('2010', '2018'), ('2019', '2026')): print(' ', s, a + '-' + b, linea('', x.loc[a:b], COSTE[s]))
print('== C16: ventana FOMC (cierre día −2 → cierre día +1), largo ==')
for s in ('ZN', 'ZB'):
    r = serie(s); ix = r.index; v = []
    for f in fomc:
        if f in ix:
            i = ix.get_loc(f)
            if i >= 1 and i + 1 < len(ix): v.append((f, r.iloc[i-1:i+2].sum(min_count=3)))
    w = pd.Series(dict(v)).dropna()
    for a, b in (('2010', '2019'), ('2020', '2026')): print(' ', s, a + '-' + b, linea('', w.loc[a:b], COSTE[s]))
print('== C15-N: gas natural, jueves (cierre miércoles → cierre jueves), largo ==')
r = serie('NG'); prev_ok = (r.index.to_series().diff().dt.days == 1).values
x = r[(r.index.weekday == 3) & prev_ok].dropna(); o = r[~((r.index.weekday == 3) & prev_ok)].dropna()
for a, b in (('2010', '2016'), ('2017', '2026')): print('  NG', a + '-' + b, linea('', x.loc[a:b], COSTE['NG']), f'| resto de días {o.loc[a:b].mean()*1e4:.1f} pb')
