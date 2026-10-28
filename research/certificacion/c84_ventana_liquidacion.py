"""C84: minutos previos a la liquidacion diaria (PREREGISTRO_C84). Uso: python3 c84_ventana_liquidacion.py DIR_M1 ES_1m.pkl"""
import glob, os, sys
import numpy as np, pandas as pd
from c1_certificacion import t_nw
def cargar(files=None, pkl=None):
    if pkl:
        x = pd.read_pickle(pkl)[['ts_event', 'instrument_id', 'close']]
    else:
        x = pd.concat([pd.read_csv(f, usecols=['ts_event', 'instrument_id', 'close']) for f in files])
    x.index = pd.to_datetime(x.ts_event, utc=True).dt.tz_convert('America/New_York').dt.tz_localize(None)
    return x[~x.index.duplicated()].sort_index()
def ventana(x, h0, m0, h1, m1):
    df = pd.DataFrame({'c': x.close.values, 'i': x.instrument_id.values, 'dia': x.index.normalize(), 'm': x.index.hour * 60 + x.index.minute})
    a0, a1 = h0 * 60 + m0, h1 * 60 + m1
    A = df[(df.m < a0) & (df.m >= a0 - 10)].groupby('dia').last(); B = df[(df.m < a1) & (df.m >= a1 - 10)].groupby('dia').last()
    j = A.join(B, lsuffix='a', rsuffix='b', how='inner'); j = j[j.ia == j.ib]
    r = np.log(j.cb / j.ca) * 1e4; return r[r.index.dayofweek < 5].loc['2010-06-01':'2026-09-30']
def d0(idx):
    s = pd.Series(idx, index=idx); return pd.DatetimeIndex([g.max() for _, g in s.groupby([idx.year, idx.month])])
M, ES = sys.argv[1:3]
for nom, x, w, coste in (('Oro GC 13:25->13:30', cargar(sorted(glob.glob(os.path.join(M, 'GC_*.csv')))), (13, 25, 13, 30), 0.74),
                         ('Plata SI 13:20->13:25', cargar(sorted(glob.glob(os.path.join(M, 'SI_*.csv')))), (13, 20, 13, 25), 2.3),
                         ('S&P ES 15:55->16:00', cargar(pkl=ES), (15, 55, 16, 0), 0.73)):
    r = ventana(x, *w)
    for tipo, v in (('todos', r), ('fin de mes D0', r.reindex(d0(r.index)).dropna())):
        a, b = v.loc[:'2017'], v.loc['2018':]; ta = t_nw(a.values); s = int(np.sign(a.mean())) if abs(ta) >= 2 else 0
        if s == 0:
            print(f'{nom} [{tipo}]: n {len(v)} | 2010-17 {a.mean():+.2f} pb (t {ta:+.2f}) -> sin signo, NO PASA | inf. 2018-26 {b.mean():+.2f} (t {t_nw(b.values):+.2f})'); continue
        tb = t_nw(b.values) * s; an = b.groupby(b.index.year).mean()
        pasa = tb >= 2.39 and (np.sign(an) == s).mean() >= 0.6 and b.mean() * s >= 2 * coste
        print(f'{nom} [{tipo}]: n {len(v)} | 2010-17 {a.mean():+.2f} pb (t {ta:+.2f}) signo {s} | 2018-26 {b.mean():+.2f} pb (t con signo {tb:+.2f}) años {(np.sign(an)==s).sum()}/{len(an)} -> {"PASA" if pasa else "NO PASA"}')
