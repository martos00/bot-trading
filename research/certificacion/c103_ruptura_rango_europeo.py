"""C103 — ruptura del rango europeo (PREREGISTRO_C103). Uso: python3 c103_ruptura_rango_europeo.py DIR_SCRATCH"""
import sys
import numpy as np, pandas as pd
from multiprocessing import Pool
from c1_certificacion import t_nw
from c93_oro_ruptura_dia_anterior import carga
SP = sys.argv[1] if len(sys.argv) > 1 else '.'
def simula_eu(x, excluir=()):
    n = x.index.tz_localize(None); mm = n.hour * 60 + n.minute
    ses = n.normalize()
    o, h, l, c = (x[k].values for k in 'ohlc'); out = []
    sv = ses.values; dias = pd.DatetimeIndex(np.unique(sv))
    ini, fin = np.searchsorted(sv, dias.values), np.searchsorted(sv, dias.values, 'right')
    for d, a, b in zip(dias, ini, fin):
        if d.weekday() > 4 or d in excluir: continue
        m = mm[a:b]; idx = np.arange(a, b)
        rg = idx[(m >= 180) & (m < 570)]; en = idx[(m >= 570) & (m < 810)]; hasta = idx[(m >= 570) & (m < 955)]
        if len(rg) < 3 or len(en) == 0 or len(hasta) == 0: continue
        H, L = h[rg].max(), l[rg].min(); W = H - L
        if W <= 0: continue
        up = np.nonzero(h[en] > H)[0]; dn = np.nonzero(l[en] < L)[0]
        iu = up[0] if len(up) else 10**9; idn = dn[0] if len(dn) else 10**9
        if iu == idn: continue
        sg = 1 if iu < idn else -1; i0 = en[min(iu, idn)]
        p0 = max(H, o[i0]) if sg == 1 else min(L, o[i0]); st = L if sg == 1 else H; tg = p0 + sg * W
        res = None
        for i in hasta[hasta >= i0]:
            hs = l[i] <= st if sg == 1 else h[i] >= st
            ht = (h[i] >= tg if sg == 1 else l[i] <= tg) and i != i0
            if hs: res = st; break
            if ht: res = tg; break
        if res is None: res = c[hasta[-1]]
        out.append((d, sg * np.log(res / p0) * 1e4))
    return pd.Series(dict(out)).sort_index()


M = [('DAX', 'GRXEUR', 1.0), ('CAC', 'FRXEUR', 1.5), ('FTSE', 'UKXGBP', 1.0), ('EUROSTOXX (informativo)', 'ETXEUR', 1.0)]
def uno(m): return m, simula_eu(carga(f'{SP}/hd_new/{m[1]}').loc['2010-06-01':'2026-09-30'])
if __name__ == '__main__':
    with Pool(4) as p: res = p.map(uno, M)
    for (nom, d, co), r in res:
        an = r.groupby(r.index.year).sum(); t = t_nw(r.values); a, b = r.loc[:'2019'], r.loc['2020':]
        c = {'t>=2.39': r.mean() > 0 and t >= 2.39, 'años>=60%': (an > 0).mean() >= 0.6, '2010-19>0': a.mean() > 0, '2020-26>0': b.mean() > 0, '>coste': r.mean() > co}
        print(f'{nom}: n {len(r)} {r.mean():+.2f} pb (t {t:.2f}) años+ {(an>0).sum()}/{len(an)} | 2010-19 {a.mean():+.2f} | 2020-26 {b.mean():+.2f} → '
              + ('pasa la principal' if all(c.values()) else 'no pasa: ' + ','.join(k for k, v in c.items() if not v)))
        print('   por año:', r.groupby(r.index.year).mean().round(1).to_dict())
