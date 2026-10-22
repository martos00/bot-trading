"""C50: dosis-respuesta de oro y plata (16-17 NY) con la duración del cierre. Ver PREREGISTRO_C50. Uso: python3 c50... DIR_H1"""
import glob, os, sys
import numpy as np, pandas as pd
import holidays
from c1_certificacion import t_nw
FEST = {pd.Timestamp(d) for d in holidays.financial_holidays('NYSE', years=range(2009, 2028))}
HAB = pd.bdate_range('2009-01-01', '2027-12-31'); HAB = HAB[~HAB.isin(list(FEST))]
PRE = {HAB[HAB.searchsorted(f) - 1] for f in FEST if 0 < HAB.searchsorted(f) < len(HAB)}
def serie(s):
    x = pd.concat([pd.read_csv(f) for f in sorted(glob.glob(os.path.join(sys.argv[1], f'{s}_*.csv')))])
    x['close'] = pd.to_numeric(x.close, errors='coerce'); x = x[x.close > 0]
    x.index = pd.to_datetime(x.ts_event, utc=True).dt.tz_convert('America/New_York') + pd.Timedelta(hours=1); x = x[~x.index.duplicated()].sort_index()
    a = x[x.index.hour == 16]; b = x[x.index.hour == 17]; a.index = a.index.tz_localize(None).normalize(); b.index = b.index.tz_localize(None).normalize()
    j = a[['close', 'instrument_id']].join(b[['close', 'instrument_id']], lsuffix='0', rsuffix='1', how='inner'); j = j[j.instrument_id0 == j.instrument_id1]
    return np.log(j.close1 / j.close0).loc['2010-06-01':'2026-09-30']
R = pd.DataFrame({s: serie(s) for s in ('GC', 'SI')}).dropna()
cat = pd.Series([3 if d in PRE else (2 if d.weekday() == 4 else 1) for d in R.index], index=R.index)
for s in ('GC', 'SI'):
    print(s, ' | '.join(f'cat {k}: {R[s][cat == k].mean()*1e4:.2f} pb (t {t_nw(R[s][cat == k].values):.2f}, n {(cat == k).sum()})' for k in (1, 2, 3)))
y = R.mean(axis=1); xc = cat - cat.mean()
beta = (xc * y).sum() / (xc ** 2).sum(); e = y - y.mean() - beta * xc
# t de Newey-West de la pendiente (5 retardos) vía la serie xc*e
u = (xc * e).values; n = len(u); g = [u[k:] @ u[:n - k] / n for k in range(6)]
var = (g[0] + 2 * sum((1 - k / 6) * g[k] for k in range(1, 6))) * n / ((xc ** 2).sum()) ** 2
tb = beta / np.sqrt(var)
print(f'PENDIENTE media GC+SI: {beta*1e4:.2f} pb por categoría (t NW {tb:.2f}) → {"PASA" if beta > 0 and tb >= 2 else "NO PASA"}')
for a0, a1 in (('2010', '2017'), ('2018', '2026')):
    yy = y.loc[a0:a1]; cc = cat.loc[a0:a1]
    print(f'   {a0}-{a1}: ' + ' | '.join(f'cat {k} {yy[cc == k].mean()*1e4:.2f} pb' for k in (1, 2, 3)))
