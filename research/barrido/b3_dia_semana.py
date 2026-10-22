"""B3: barrido de día de la semana en 27 futuros del CME. Ver PREREGISTRO_B3. Uso: python3 b3_dia_semana.py DIR_DATABENTO"""
import glob, os, sys
import numpy as np, pandas as pd
from scipy import stats
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'certificacion'))
from c1_certificacion import t_nw
B = sys.argv[1]
COM = ['CL', 'HO', 'RB', 'NG', 'GC', 'SI', 'HG', 'PL', 'ZC', 'ZS', 'ZW', 'ZL', 'ZM', 'KE', 'LE', 'HE']
def diaria(x, sym=None):
    x = x.copy(); x['close'] = pd.to_numeric(x.close, errors='coerce'); x = x[x.close.notna()]
    x['ts'] = pd.to_datetime(x.ts_event, utc=True, errors='coerce').dt.tz_localize(None); x = x[x.ts.notna()]
    if sym is not None: x = x[x.symbol == sym]
    x['dia'] = x.ts.dt.normalize(); x = x.sort_values('ts').groupby('dia').last()
    x = x[x.index.weekday < 5]
    with np.errstate(invalid='ignore', divide='ignore'):
        r = np.log(x.close.where(x.close > 0)).diff()
    r[x.instrument_id != x.instrument_id.shift()] = np.nan
    return r
R, coste = {}, {}
for s in COM:
    x = pd.concat([pd.read_csv(f) for f in glob.glob(os.path.join(B, 'curva', f'{s}_*.csv')) if os.path.getsize(f) > 100])
    R[s] = diaria(x, f'{s}.c.0'); coste[s] = 3e-4
for s in ('ZN', 'ZB', 'ZF'):
    R[s] = diaria(pd.read_csv(os.path.join(B, f'{s}.v.0.csv'))); coste[s] = 1.5e-4
for s in ('6A', '6B', '6E', '6J', 'NQ', 'RTY', 'YM'):
    R[s] = diaria(pd.concat([pd.read_csv(f) for f in sorted(glob.glob(os.path.join(B, 'h1', f'{s}_*.csv')))])); coste[s] = 1.5e-4
R['ES'] = diaria(pd.read_pickle(os.path.join(B, 'ES_1m.pkl'))); coste['ES'] = 1.5e-4
R = pd.DataFrame(R).loc['2010-06-07':'2026-09-30']
DN = ['lun', 'mar', 'mié', 'jue', 'vie']
filas = []
for s in R:
    for d in range(5):
        y = R[s][R.index.weekday == d].dropna()
        a, b = y.loc[:'2017'], y.loc['2018':]
        filas.append(dict(mercado=s, dia=DN[d], n_d=len(a), m_d=a.mean() * 1e4, t_d=t_nw(a.values), n_c=len(b), m_c=b.mean() * 1e4,
                          t_c=t_nw(b.values), coste=coste[s] * 1e4, anos=b.groupby(b.index.year).sum()))
T = pd.DataFrame(filas)
sel = T[T.t_d.abs() >= 3.0].copy(); k = len(sel)
print(f'reglas {len(T)}; seleccionadas en 2010-2017 (|t| >= 3): {k}')
if k:
    umbral = stats.norm.ppf(1 - 0.05 / k)
    print(f'umbral Bonferroni unilateral en 2018-2026: t >= {umbral:.2f}')
    for _, f in sel.iterrows():
        sg = np.sign(f.t_d); tc = sg * f.t_c; an = f.anos; ok_an = ((sg * an) > 0).mean()
        bruto = sg * f.m_c; cert = tc >= umbral and ok_an >= 0.6 and bruto >= 3 * f.coste
        print(f'  {f.mercado:4s} {f.dia}: 2010-17 {f.m_d:7.2f} pb (t {f.t_d:5.2f}) | 2018-26 {f.m_c:7.2f} pb (t {f.t_c:5.2f}) '
              f'años con signo {ok_an*100:.0f}% bruto/coste {bruto/f.coste:.1f}× → {"CERTIFICADA" if cert else "no"}')
T.drop(columns='anos').round(2).to_csv('b3_todas.csv', index=False)
print('\nMayores |t| en 2018-2026 (informativo, sin selección):')
print(T.reindex(T.t_c.abs().sort_values(ascending=False).index).head(10)[['mercado', 'dia', 'm_d', 't_d', 'm_c', 't_c']].round(2).to_string(index=False))
