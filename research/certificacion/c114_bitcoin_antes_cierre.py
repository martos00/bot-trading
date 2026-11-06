"""C114 — BTC 21:00→22:00 UTC solo con NY en horario de invierno (PREREGISTRO_C114). Uso: python3 c114_bitcoin_antes_cierre.py DIR_SCRATCH"""
import sys, glob, io, zipfile, numpy as np, pandas as pd
from c1_certificacion import t_nw
SP = sys.argv[1]; COSTE = 3.0
rows = []
for f in sorted(glob.glob(f'{SP}/bn/1h/BTCUSDT-1h-*.zip')):
    with zipfile.ZipFile(f) as z: rows.append(pd.read_csv(io.BytesIO(z.read(z.namelist()[0])), header=None, usecols=[0, 1]))
b = pd.concat(rows); t = b[0].astype('int64'); t = np.where(t > 1e14, t // 1000, t)
o = pd.Series(b[1].astype(float).values, index=pd.to_datetime(t, unit='ms')); o = o[~o.index.duplicated()].sort_index()
def hora(h0, h1):
    a = o[o.index.hour == h0]; c = o[o.index.hour == h1]; a.index = a.index.normalize(); c.index = c.index.normalize()
    r = (np.log(c / a) * 1e4).dropna(); return r[r.index.dayofweek < 5]
ny = lambda d: pd.Timestamp(d).tz_localize('UTC').tz_convert('America/New_York')
def invierno(idx): return np.array([ny(d + pd.Timedelta(hours=21)).utcoffset().total_seconds() == -5 * 3600 for d in idx])
def linea(nom, r):
    an = r.groupby(r.index.year).mean()
    return (f'{nom}: n {len(r)} neto {r.mean():+.2f} pb (t {t_nw(r.values):.2f}) | 2018-21 {r.loc["2018":"2021"].mean():+.2f} | 2022-26 {r.loc["2022":].mean():+.2f} '
            f'| desde 2023 {r.loc["2023":].mean():+.2f} | años+ {(an>0).sum()}/{len(an)}'), an
r = hora(21, 22); w = invierno(r.index); p = r[w] - COSTE
l, an = linea('PRINCIPAL 21-22 UTC en invierno (16:00-16:59 NY)', p); print(l)
print(linea('Informativo 21-22 UTC en verano (17:00-18:00 NY, no operable)', r[~w] - COSTE)[0])
v = hora(20, 21); print(linea('Informativo 20-21 UTC en verano (16:00-17:00 NY)', v[~invierno(v.index)] - COSTE)[0])
print(linea('Referencia C2 21-23 UTC todo el año', hora(21, 23) - COSTE)[0])
c = {'t>=2.0': p.mean() > 0 and t_nw(p.values) >= 2.0, '2018-21>0': p.loc['2018':'2021'].mean() > 0, '2022-26>0': p.loc['2022':].mean() > 0,
     'desde 2023>0': p.loc['2023':].mean() > 0, 'años>=60%': (an > 0).mean() >= 0.6}
print('RESULTADO:', 'PASA' if all(c.values()) else 'NO PASA: falla ' + ', '.join(k for k, v in c.items() if not v))
