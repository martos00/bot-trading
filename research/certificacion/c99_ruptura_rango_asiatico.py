"""C99 — ruptura del rango asiático (PREREGISTRO_C98_C99). Uso: python3 c99_ruptura_rango_asiatico.py DIR_SCRATCH"""
import sys
import numpy as np, pandas as pd
from multiprocessing import Pool
from c1_certificacion import t_nw
from c93_oro_ruptura_dia_anterior import carga
from c94_ruptura_otros_futuros import carga_h1
SP = sys.argv[1] if len(sys.argv) > 1 else '.'
import c94_ruptura_otros_futuros as c94; c94.SP = SP

def simula(x, excluir=()):
    n = x.index.tz_localize(None); mm = n.hour * 60 + n.minute
    ses = (n + pd.Timedelta(hours=5)).normalize()                      # día = 19:00 NY anterior → 19:00 NY
    o, h, l, c = (x[k].values for k in 'ohlc'); out = []
    sv = ses.values; dias = pd.DatetimeIndex(np.unique(sv))
    ini, fin = np.searchsorted(sv, dias.values), np.searchsorted(sv, dias.values, 'right')
    for d, a, b in zip(dias, ini, fin):
        if d.weekday() > 4 or d in excluir: continue
        m = mm[a:b]; idx = np.arange(a, b)
        rg = idx[(m >= 19 * 60) | (m < 180)]; en = idx[(m >= 180) & (m < 660)]; hasta = idx[(m >= 180) & (m < 1005)]
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

M = [('ORO', 'hd2/XAUUSD', 'GC', 0.74), ('EURUSD', 'hd_all/EURUSD', '6E', 0.6), ('GBPUSD', 'hd_all/GBPUSD', '6B', 0.8), ('USDJPY', 'hd_all/USDJPY', '6J', 0.8)]
def uno(m):
    nom, d, fut, coste = m
    z = simula(carga(f'{SP}/{d}').loc['2010-06-01':'2026-09-30'])
    hh, ex = carga_h1(fut); w = simula(hh, ex)
    return nom, fut, coste, z, w
if __name__ == '__main__':
    with Pool(4) as p: res = p.map(uno, M)
    for nom, fut, coste, r, q in res:
        an = r.groupby(r.index.year).sum(); t = t_nw(r.values); a, b = r.loc[:'2019'], r.loc['2020':]; tq = t_nw(q.values)
        c = {'t>=2.50': r.mean() > 0 and t >= 2.5, 'años>=60%': (an > 0).mean() >= 0.6, '2010-19>0': a.mean() > 0, '2020-26>0': b.mean() > 0,
             '>coste': r.mean() > coste, 'Databento': q.mean() > coste and tq >= 2}
        print(f'{nom}: HistData n {len(r)} {r.mean():+.2f} pb (t {t:.2f}) años+ {(an>0).sum()}/{len(an)} | 2010-19 {a.mean():+.2f} | 2020-26 {b.mean():+.2f} '
              f'|| {fut} 1h n {len(q)} {q.mean():+.2f} (t {tq:.2f}) → ' + ('PASA' if all(c.values()) else 'no pasa: ' + ','.join(k for k, v in c.items() if not v)))
