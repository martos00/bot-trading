"""C90: BTC 21-23 UTC recortado a la ventana operable en el CME (PREREGISTRO_C90). Uso: python3 c90_bitcoin_cme.py DIR_BN"""
import glob, io, os, sys, zipfile
import numpy as np, pandas as pd
from c1_certificacion import t_nw
D = sys.argv[1]
def leer(patron):
    rows = []
    for f in sorted(glob.glob(os.path.join(D, patron))):
        with zipfile.ZipFile(f) as z:
            rows.append(pd.read_csv(io.BytesIO(z.read(z.namelist()[0])), header=None, usecols=[0, 1]))
    b = pd.concat(rows); t = b[0].astype('int64'); t = np.where(t > 1e14, t // 1000, t)
    s = pd.Series(b[1].astype(float).values, index=pd.to_datetime(t, unit='ms')); return s[~s.index.duplicated()].sort_index()
m1 = leer('1m/BTCUSDT-1m-*.zip')
def verano(d):   # horario de verano de EE. UU. para la fecha UTC d a las 21:00
    ny = pd.Timestamp(d.date()).tz_localize('UTC') + pd.Timedelta(hours=21)
    return ny.tz_convert('America/New_York').utcoffset() == pd.Timedelta(hours=-4)
res = {}
for d in pd.date_range('2022-02-04', '2026-09-30'):
    v = verano(d); ny_dia = (pd.Timestamp(d.date()) + pd.Timedelta(hours=21) - pd.Timedelta(hours=4 if v else 5)).dayofweek
    if v:
        if ny_dia not in (6, 0, 1, 2, 3): continue
        a, b = pd.Timestamp(d.date()) + pd.Timedelta(hours=22), pd.Timestamp(d.date()) + pd.Timedelta(hours=23)
    else:
        if ny_dia > 4: continue
        a, b = pd.Timestamp(d.date()) + pd.Timedelta(hours=21), pd.Timestamp(d.date()) + pd.Timedelta(hours=21, minutes=45)
    if a in m1.index and b in m1.index: res[pd.Timestamp(d.date())] = (np.log(m1[b] / m1[a]) * 1e4, 'verano' if v else 'invierno')
r = pd.DataFrame(res, index=['r', 'tramo']).T; r['r'] = r.r.astype(float)
x = r.r; an = x.groupby(x.index.year).mean(); t = t_nw(x.values)
pasa = x.mean() > 0 and t >= 2 and (an > 0).mean() >= 0.6 and x.mean() > 3
print(f'BTC ventana CME 2022-02 -> 2026-09: n {len(x)} {x.mean():+.2f} pb (t {t:+.2f}) años+ {(an>0).sum()}/{len(an)} | neto MBT (3 pb) {x.mean()-3:+.2f} | neto BTC (1 pb) {x.mean()-1:+.2f} -> {"PASA" if pasa else "NO PASA"}')
for tr, g in r.groupby('tramo'): print(f'   {tr}: n {len(g)} {g.r.mean():+.2f} pb (t {t_nw(g.r.values):+.2f})')
print('   por año:', an.round(2).to_dict())
h1 = leer('1h/BTCUSDT-1h-*.zip')
o22 = h1[h1.index.hour == 22]; o23 = h1[h1.index.hour == 23]; o22.index = o22.index.normalize(); o23.index = o23.index.normalize()
inf = (np.log(o23 / o22) * 1e4).dropna().loc['2017-08-01':'2022-01-31']
inf = inf[[verano(d) for d in inf.index]]
print(f'Informativo 2017-08 -> 2022-01, tramo verano 22-23 UTC (todos los dias): n {len(inf)} {inf.mean():+.2f} pb (t {t_nw(inf.values):+.2f})')
