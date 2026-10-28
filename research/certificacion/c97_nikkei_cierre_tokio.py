"""C97 — última media hora de Tokio y ETF apalancados (ver PREREGISTRO_C97). Uso: python3 c97_nikkei_cierre_tokio.py DIR_SCRATCH"""
import sys, glob
import numpy as np, pandas as pd
from c1_certificacion import t_nw
from c45_oro_viernes import carga
SP = sys.argv[1]

def regla(s, tz, cierre_fn):
    s = s.tz_convert(tz); loc = s.index.tz_localize(None); mm = loc.hour * 60 + loc.minute; dia = loc.normalize()
    df = pd.DataFrame({'c': s.values, 'mm': mm}, index=dia)
    C = np.array([cierre_fn(d) for d in df.index]); df['C'] = C
    pc = df[(df.mm <= df.C) & (df.mm > df.C - 10)].groupby(level=0).c.last()
    pa = df[(df.mm <= df.C - 30) & (df.mm > df.C - 40)].groupby(level=0).c.last()
    j = pd.DataFrame({'a': pa, 'c': pc}).dropna(); j = j[j.index.dayofweek < 5]
    r = np.log(j.a / j.c.shift(1)); return (np.sign(r) * np.log(j.c / j.a) * 1e4).dropna(), r

def info(nom, x):
    a, b = x.loc[:'2017'], x.loc['2018':]; an = b.groupby(b.index.year).mean()
    print(f'{nom}: n {len(x)} {x.mean():+.2f} pb (t {t_nw(x.values):.2f}) | 2010-17 {a.mean():+.2f} (t {t_nw(a.values):.2f}) | 2018-26 n {len(b)} {b.mean():+.2f} (t {t_nw(b.values):.2f}) años+ {(an>0).sum()}/{len(an)}')
    return a, b, an

if __name__ == '__main__':
    cierre_jp = lambda d: 900 if d < pd.Timestamp('2024-11-05') else 930
    x, r = regla(carga(f'{SP}/hd_new/JPXJPY').loc['2010-06-01':'2026-09-30'], 'Asia/Tokyo', cierre_jp)
    a, b, an = info('Nikkei HistData', x)
    print('   por año:', x.groupby(x.index.year).mean().round(1).to_dict())
    q = pd.qcut(r.abs().reindex(x.index), 3, labels=False); print('   terciles |r|:', x.groupby(q).mean().round(2).to_dict())
    h = pd.concat([pd.read_csv(f) for f in sorted(glob.glob(f'{SP}/databento/h1/NKD_[0-9]*.csv'))])
    h.index = pd.to_datetime(h.ts_event).dt.tz_convert('UTC'); h = h[~h.index.duplicated()].sort_index()
    b5 = h[h.index.hour == 5]; b5.index = b5.index.tz_localize(None).normalize()
    g = (np.sign(np.log(b5.open / b5.close.shift(1))) * np.log(b5.close / b5.open) * 1e4).dropna()
    g = g[g.index.dayofweek < 5].loc['2010-06-01':'2026-09-30']; _, gb, _ = info('NKD Databento 14-15 JST', g)
    c = {'2010-17>0': a.mean() > 0, '2018-26 t>=2': b.mean() > 0 and t_nw(b.values) >= 2, 'años>=60%': (an > 0).mean() >= 0.6,
         '>2,5 pb': b.mean() > 2.5, 'NKD 2018-26 t>=2': gb.mean() > 0 and t_nw(gb.values) >= 2}
    print('CRITERIOS:', c, '→ PASA' if all(c.values()) else '→ NO PASA')
    for nom, d, tz in (('control ASX 200', 'AUXAUD', 'Australia/Sydney'), ('control Hang Seng', 'HKXHKD', 'Asia/Hong_Kong')):
        info(nom, regla(carga(f'{SP}/hd_new/{d}').loc['2010-06-01':'2026-09-30'], tz, lambda d: 960)[0])
