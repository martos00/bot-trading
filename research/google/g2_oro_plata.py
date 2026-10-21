"""G2 — pares oro/plata: z de 60 días de ln(oro/plata), entrada |z| > 2, salida al cruzar 0 o a los 20 días (PREREGISTRO_G1_G2.md).
Uso: python3 g2_oro_plata.py DIR_XAUUSD DIR_XAGUSD SALIDA_CSV"""
import glob, os, sys
import numpy as np
import pandas as pd


def cierres(d, sim):
    fs = sorted(glob.glob(os.path.join(d, f'DAT_ASCII_{sim}_M1_*.csv')))
    x = pd.concat([pd.read_csv(f, sep=';', header=None, names=['ts', 'o', 'h', 'l', 'c', 'v'], usecols=[0, 4]) for f in fs])
    x['dia'] = pd.to_datetime(x.ts.str[:8], format='%Y%m%d')
    s = x.groupby('dia').c.last()
    return s[s.index.weekday < 5]


oro, plata = cierres(sys.argv[1], 'XAUUSD'), cierres(sys.argv[2], 'XAGUSD')
p = pd.concat([oro.rename('oro'), plata.rename('plata')], axis=1, join='inner').dropna().loc['2010':]
L = np.log(p.oro / p.plata)
z = ((L - L.rolling(60).mean().shift(1)) / L.rolling(60).std().shift(1)).to_numpy()
lo, lp = np.log(p.oro.to_numpy()), np.log(p.plata.to_numpy())
ops, pos, i0 = [], 0, None
for i in range(len(p)):
    if pos != 0:
        dur = i - i0
        if (pos == -1 and z[i] <= 0) or (pos == 1 and z[i] >= 0) or dur >= 20:
            # pos = −1: venta de oro / compra de plata ; pos = +1: compra de oro / venta de plata (mismo nominal)
            r = pos * ((lo[i] - lo[i0]) - (lp[i] - lp[i0])) / 2          # rentabilidad sobre el nominal total (2 patas)
            ops.append((p.index[i0], p.index[i], pos, dur, r))
            pos = 0
        continue
    if np.isnan(z[i]):
        continue
    if z[i] > 2:
        pos, i0 = -1, i
    elif z[i] < -2:
        pos, i0 = 1, i
pd.DataFrame(ops, columns=['entrada', 'salida', 'lado', 'dias', 'r']).to_csv(sys.argv[3], index=False)
print('operaciones', len(ops), 'media bruta', round(np.mean([o[4] for o in ops]) * 1e4, 2), 'pb sobre el nominal total; días medios',
      round(np.mean([o[3] for o in ops]), 1))
