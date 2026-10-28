"""C91: cripto 21-23 UTC en SOL y XRP (+ LTC, ADA, BNB, BTC, ETH informativos). PREREGISTRO_C91. Uso: python3 c91_cripto_otras.py DIR_BINANCE DIR_SOL"""
import glob, io, os, sys, zipfile
import numpy as np, pandas as pd
from c1_certificacion import t_nw
def leer(files):
    rows = []
    for f in files:
        with zipfile.ZipFile(f) as z: rows.append(pd.read_csv(io.BytesIO(z.read(z.namelist()[0])), header=None, usecols=[0, 1]))
    b = pd.concat(rows); t = b[0].astype('int64'); t = np.where(t > 1e14, t // 1000, t)
    s = pd.Series(b[1].astype(float).values, index=pd.to_datetime(t, unit='ms')); return s[~s.index.duplicated()].sort_index()
B, S = sys.argv[1:3]
for sym, files, prueba in (('SOL', sorted(glob.glob(os.path.join(S, 'SOLUSDT-1h-*.zip'))), True),
                           ('XRP', sorted(glob.glob(os.path.join(B, 'XRPUSDT-1h-*.zip'))), True),
                           ('LTC', sorted(glob.glob(os.path.join(B, 'LTCUSDT-1h-*.zip'))), False),
                           ('ADA', sorted(glob.glob(os.path.join(B, 'ADAUSDT-1h-*.zip'))), False),
                           ('BNB', sorted(glob.glob(os.path.join(B, 'BNBUSDT-1h-*.zip'))), False),
                           ('BTC (ref.)', sorted(glob.glob(os.path.join(B, 'BTCUSDT-1h-*.zip'))), False),
                           ('ETH (ref.)', sorted(glob.glob(os.path.join(B, 'ETHUSDT-1h-*.zip'))), False)):
    o = leer(files); a = o[o.index.hour == 21]; b = o[o.index.hour == 23]; a.index = a.index.normalize(); b.index = b.index.normalize()
    r = (np.log(b / a) * 1e4).dropna(); p = r.loc['2022-02-04':'2026-09-30']; pre = r.loc[:'2022-02-03']
    an = p.groupby(p.index.year).mean(); t = t_nw(p.values)
    ver = (' -> ' + ('PASA' if (p.mean() > 0 and t >= 2.24 and (an > 0).mean() >= 0.6 and p.mean() > 5) else 'NO PASA')) if prueba else ' (informativo)'
    print(f'{sym}: tras publicarse n {len(p)} {p.mean():+.2f} pb (t {t:+.2f}) años+ {(an>0).sum()}/{len(an)} | antes {pre.mean():+.2f} (t {t_nw(pre.values):+.2f}, desde {pre.index.min().date() if len(pre) else "-"}) | otras horas 2h media {np.log(o.shift(-2)/o).dropna().loc["2022-02-04":].mean()*1e4:+.2f}{ver}')
