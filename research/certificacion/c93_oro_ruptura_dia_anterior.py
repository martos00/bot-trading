"""C93 — oro, ruptura del máximo/mínimo de la sesión anterior (ver PREREGISTRO_C93). Uso: python3 c93_oro_ruptura_dia_anterior.py DIR_HISTDATA_XAUUSD"""
import sys, glob, os
import numpy as np, pandas as pd
from c1_certificacion import t_nw

def carga(d):
    x = pd.concat([pd.read_csv(f, sep=';', header=None, names=['t', 'o', 'h', 'l', 'c', 'v']) for f in sorted(glob.glob(os.path.join(d, '*.csv')))])
    t = pd.to_datetime(x.t, format='%Y%m%d %H%M%S').dt.tz_localize('America/New_York', ambiguous='NaT', nonexistent='NaT')
    x.index = t; x = x[x.index.notna()].sort_index()
    return x[~x.index.duplicated()][['o', 'h', 'l', 'c']]

def simula(x, v0, v1, cierre, k, conStop=True, excluir=()):
    n = x.index.tz_localize(None)
    ses = (n + pd.Timedelta(hours=7)).normalize()               # sesión 17:00 NY → 17:00 NY
    mm = n.hour * 60 + n.minute
    d = pd.DataFrame({'h': x.h.values, 'l': x.l.values, 'c': x.c.values}, index=ses)
    dia = d.groupby(level=0).agg(h=('h', 'max'), l=('l', 'min'), c=('c', 'last'))
    tr = pd.concat([dia.h - dia.l, (dia.h - dia.c.shift()).abs(), (dia.l - dia.c.shift()).abs()], axis=1).max(axis=1)
    atr = tr.rolling(14).mean().shift(); H = dia.h.shift(); L = dia.l.shift()
    arr = {'o': x.o.values, 'h': x.h.values, 'l': x.l.values, 'c': x.c.values}
    sesv = ses.values; out = []
    lims = np.searchsorted(sesv, dia.index.values), np.searchsorted(sesv, dia.index.values, 'right')
    for j, s in enumerate(dia.index):
        if np.isnan(atr.iloc[j]) or np.isnan(H.iloc[j]) or s.weekday() > 4 or s in excluir: continue
        a, b = lims[0][j], lims[1][j]; m = mm[a:b]; idx = np.arange(a, b)
        en = idx[(m >= v0) & (m < v1)]; fin = idx[m < cierre]
        if len(en) == 0 or len(fin) == 0: continue
        hh, ll = arr['h'][en], arr['l'][en]
        up = np.nonzero(hh > H.iloc[j])[0]; dn = np.nonzero(ll < L.iloc[j])[0]
        iu = up[0] if len(up) else 10**9; idn = dn[0] if len(dn) else 10**9
        if iu == idn == 10**9: continue
        if iu == idn: continue                                    # rompe los dos en el mismo minuto: ambiguo, sin operación
        sg = 1 if iu < idn else -1; i0 = en[min(iu, idn)]
        lvl = H.iloc[j] if sg == 1 else L.iloc[j]; o = arr['o'][i0]
        p0 = max(lvl, o) if sg == 1 else min(lvl, o)
        A = atr.iloc[j]; st = p0 - sg * k * A; tg = p0 + sg * 3 * k * A
        res, tipo = None, 'cierre'
        resto = np.arange(i0, fin[-1] + 1)
        if conStop:
            for i in resto:
                hs = arr['l'][i] <= st if sg == 1 else arr['h'][i] >= st
                ht = arr['h'][i] >= tg if sg == 1 else arr['l'][i] <= tg
                if i == i0:                                         # en el minuto de entrada solo cuenta el stop
                    ht = False
                if hs: res, tipo = st, 'stop'; break
                if ht: res, tipo = tg, 'objetivo'; break
        if res is None: res = arr['c'][fin[-1]]
        out.append((s, sg * np.log(res / p0), sg * (res - p0) / (k * A), tipo, sg))
    return pd.DataFrame(out, columns=['dia', 'r', 'R', 'tipo', 'sg']).set_index('dia')

def informe(nom, z, coste=1.5):
    r = z.r * 1e4; an = r.groupby(r.index.year).sum(); t = t_nw(r.values)
    a, b = r.loc[:'2019'], r.loc['2020':]
    print(f'{nom}: n {len(r)} media {r.mean():.2f} pb (t {t:.2f}) años+ {(an>0).sum()}/{len(an)} | 2010-19 {a.mean():.2f} (t {t_nw(a.values):.2f}) '
          f'| 2020-26 {b.mean():.2f} (t {t_nw(b.values):.2f}) | R medio {z.R.mean():.3f}, 2020-26 {z.R.loc["2020":].mean():.3f} '
          f'| reparto {dict((z.tipo.value_counts(normalize=True)*100).round(1))}')
    return {'t>=2.24': r.mean() > 0 and t >= 2.24, 'años>=60%': (an > 0).mean() >= 0.6, '2010-19>0': a.mean() > 0, '2020-26>0': b.mean() > 0, 'media>1.5': r.mean() > coste}

if __name__ == '__main__':
    x = carga(sys.argv[1]).loc['2010-06-01':'2026-09-30']
    for nom, v0, v1, ci in (('A servidor 07-14 NY, cierre 16:00', 420, 840, 960), ('B España 08-15 NY, cierre 17:00', 480, 900, 1020)):
        z = simula(x, v0, v1, ci, 1.0); c = informe(nom, z)
        print('   por año (pb):', (z.r.groupby(z.index.year).sum() * 1e4).round(0).to_dict())
        print('   CRITERIOS:', c, '→ PASA' if all(c.values()) else '→ NO PASA')
        for k in (0.5, 2.0): informe(f'   informativo k={k}', simula(x, v0, v1, ci, k))
        informe('   informativo sin stop ni objetivo', simula(x, v0, v1, ci, 1.0, conStop=False))
    informe('informativo B con salida 16:45 (futuros)', simula(x, 480, 900, 1005, 1.0))
