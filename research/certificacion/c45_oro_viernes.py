"""C45: confirmación independiente (HistData contado, BID) de oro largo viernes 16:00 → 16:58 NY. Ver PREREGISTRO_C45.
Uso: python3 c45_oro_viernes.py DIR_XAU DIR_XAG"""
import glob, os, sys
import numpy as np, pandas as pd
from c1_certificacion import t_nw
def carga(d):
    x = pd.concat([pd.read_csv(f, sep=';', header=None, names=['t', 'o', 'h', 'l', 'c', 'v']) for f in sorted(glob.glob(os.path.join(d, '*.csv')))])
    t = pd.to_datetime(x.t, format='%Y%m%d %H%M%S') + pd.Timedelta(hours=5)          # EST fijo → UTC
    s = pd.Series(x.c.values, index=t.dt.tz_localize('UTC').dt.tz_convert('America/New_York')).sort_index()
    return s[~s.index.duplicated()]
def tramo(s, h0, m0, h1, m1):
    """cierre del minuto anterior a h0:m0 → cierre del último minuto ≤ h1:m1, por día."""
    df = pd.DataFrame({'c': s.values, 'dia': s.index.tz_localize(None).normalize(), 'mm': s.index.hour * 60 + s.index.minute})
    a = df[(df.mm < h0 * 60 + m0) & (df.mm >= h0 * 60 + m0 - 10)].groupby('dia').c.last()
    b = df[(df.mm <= h1 * 60 + m1) & (df.mm >= h1 * 60 + m1 - 10)].groupby('dia').c.last()
    return np.log(b / a).dropna()
if __name__ == "__main__":
    for nom, d in (('ORO', sys.argv[1]), ('PLATA (informativo)', sys.argv[2])):
        s = carga(d).loc['2010-06-01':'2026-09-30']
        r = tramo(s, 16, 0, 16, 58); v = r[r.index.weekday == 4]; an = v.groupby(v.index.year).sum()
        print(f'{nom}: viernes n {len(v)} {v.mean()*1e4:.2f} pb (t {t_nw(v.values):.2f}) años+ {(an>0).sum()}/{len(an)} | '
              f'2010-17 {v.loc[:"2017"].mean()*1e4:.2f} pb (t {t_nw(v.loc[:"2017"].values):.2f}) | 2018-26 {v.loc["2018":].mean()*1e4:.2f} pb (t {t_nw(v.loc["2018":].values):.2f})')
        for wd, n in enumerate(['lun', 'mar', 'mié', 'jue']):
            q = r[r.index.weekday == wd]; print(f'   informativo {n} 16:00-16:58: {q.mean()*1e4:.2f} pb (t {t_nw(q.values):.2f})')
        for a_, b_ in (((16, 0), (16, 29)), ((16, 30), (16, 58))):
            q = tramo(s, *a_, *b_); q = q[q.index.weekday == 4]; print(f'   informativo viernes {a_}→{b_}: {q.mean()*1e4:.2f} pb (t {t_nw(q.values):.2f})')
        if nom == 'ORO':
            print('   por año (pb):', (an * 1e4).round(0).to_dict())
            crit = {'1 t>=2': v.mean() > 0 and t_nw(v.values) >= 2, '2 años>=60%': (an > 0).mean() >= 0.6, '3 2018-26>0': v.loc['2018':].mean() > 0}
            print('CRITERIOS:', crit, '→ CONFIRMADA' if all(crit.values()) else '→ NO CONFIRMADA')

