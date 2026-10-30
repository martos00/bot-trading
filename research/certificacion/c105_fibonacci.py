"""C105 — retrocesos de Fibonacci frente a niveles de control (PREREGISTRO_C104_C105). Uso: python3 c105_fibonacci.py DIR_SCRATCH"""
import sys
import numpy as np, pandas as pd
from multiprocessing import Pool
from c1_certificacion import t_nw
from c93_oro_ruptura_dia_anterior import carga
SP = sys.argv[1] if len(sys.argv) > 1 else '.'
FIB = (0.382, 0.5, 0.618); CTRL = (0.30, 0.45, 0.55, 0.70)

def diario_m1(x):
    n = x.index.tz_localize(None); ses = (n + pd.Timedelta(hours=7)).normalize()
    d = pd.DataFrame({'o': x.o.values, 'h': x.h.values, 'l': x.l.values, 'c': x.c.values}, index=ses)
    d = d.groupby(level=0).agg(o=('o', 'first'), h=('h', 'max'), l=('l', 'min'), c=('c', 'last'))
    d = d[d.index.dayofweek < 5]; d['roll'] = False; return d
def diario_db(f):
    x = pd.read_csv(f); x.index = pd.to_datetime(x.ts_event).dt.tz_localize(None).dt.normalize()
    d = x[['open', 'high', 'low', 'close']].set_axis(['o', 'h', 'l', 'c'], axis=1); d['roll'] = x.instrument_id.ne(x.instrument_id.shift()).values
    return d[~d.index.duplicated()].loc['2010-06-01':'2026-09-30']

def eventos(d):
    o, h, l, c, roll = (d[k].values for k in ('o', 'h', 'l', 'c', 'roll')); n = len(d)
    tr = np.maximum(h[1:] - l[1:], np.maximum(abs(h[1:] - c[:-1]), abs(l[1:] - c[:-1]))); atr = np.r_[np.nan, pd.Series(tr).rolling(20).mean().values]
    vistos = set(); out = []
    for t in range(21, n - 12):
        w0 = t - 20; hh = h[w0:t]; ll = l[w0:t]; iH = w0 + int(hh.argmax()); iL = w0 + int(ll.argmin()); H, L = h[iH], l[iL]; A = atr[t - 1]
        if np.isnan(A) or H - L < 2 * A or roll[w0:t + 12].any(): continue
        sg = 1 if iH > iL else -1                                        # 1: tramo alcista (compra en retroceso); -1: bajista
        ext = iH if sg == 1 else iL
        for k in FIB + CTRL:
            P = H - k * (H - L) if sg == 1 else L + k * (H - L)
            clave = (ext, k, sg)
            if clave in vistos: continue
            toca = l[t] <= P if sg == 1 else h[t] >= P
            if not toca: continue
            antes = (l[ext + 1:t] <= P).any() if sg == 1 else (h[ext + 1:t] >= P).any()
            vistos.add(clave)
            if antes: continue
            e = None
            for j in (t, t + 1):
                if (c[j] > o[j] and c[j] > P) if sg == 1 else (c[j] < o[j] and c[j] < P): e = j; break
            if e is None: continue
            st = l[t] - 0.5 * A if sg == 1 else h[t] + 0.5 * A; tg = H if sg == 1 else L; p0 = c[e]; res = None; gana = False
            for j in range(e + 1, min(n, e + 11)):
                if (l[j] <= st) if sg == 1 else (h[j] >= st): res = st; break
                if (h[j] >= tg) if sg == 1 else (l[j] <= tg): res = tg; gana = True; break
            if res is None: res = c[min(n - 1, e + 10)]
            out.append((d.index[e], k, sg, sg * np.log(res / p0) * 1e4, gana))
    return pd.DataFrame(out, columns=['d', 'k', 'sg', 'r', 'gana'])

def uno(m):
    nom, src = m
    if src.startswith('hd'): d = diario_m1(carga(f'{SP}/{src}').loc['2010-06-01':'2026-09-30'])
    elif src == 'ES':
        x = pd.read_pickle(f'{SP}/databento/ES_1m.pkl'); x.index = pd.DatetimeIndex(pd.to_datetime(x.ts_event, utc=True)).tz_convert('America/New_York')
        x = x[~x.index.duplicated()].sort_index(); d = diario_m1(x[['open', 'high', 'low', 'close']].set_axis(['o', 'h', 'l', 'c'], axis=1).loc['2010-06-01':'2026-09-30'])
        iid = x.instrument_id.groupby((x.index.tz_localize(None) + pd.Timedelta(hours=7)).normalize()).agg(lambda v: v.mode().iloc[0]).reindex(d.index)
        d['roll'] = iid.ne(iid.shift()).values
    else: d = diario_db(f'{SP}/databento/{src}')
    e = eventos(d); e['mercado'] = nom; return e

M = [('oro', 'hd2/XAUUSD'), ('plata', 'hd_new/XAGUSD'), ('EURUSD', 'hd_all/EURUSD'), ('GBPUSD', 'hd_all/GBPUSD'), ('USDJPY', 'hd_all/USDJPY'),
     ('AUDUSD', 'hd_new/AUDUSD'), ('ES', 'ES'), ('crudo', 'CL.v.0.csv'), ('gas', 'NG.v.0.csv'), ('bono10', 'ZN.v.0.csv')]
if __name__ == '__main__':
    with Pool(5) as p: E = pd.concat(p.map(uno, M))
    E['d'] = pd.to_datetime(E.d); E = E.sort_values('d').set_index('d')
    for k in FIB + CTRL:
        q = E[E.k == k]; print(f'nivel {k*100:4.1f} % {"FIB" if k in FIB else "control"}: n {len(q)} {q.r.mean():+6.2f} pb (t {t_nw(q.r.values):5.2f}) | llega al objetivo {q.gana.mean()*100:4.1f} %')
    f, cc = E[E.k.isin(FIB)], E[E.k.isin(CTRL)]
    dm = f.r.mean() - cc.r.mean(); se = np.sqrt(f.r.var() / len(f) + cc.r.var() / len(cc)) * 2.5   # ×2,5: eventos solapados (prudente)
    print(f'PRUEBA CENTRAL Fibonacci − control: {dm:+.2f} pb (t aprox. {dm/se:.2f}) | objetivo {f.gana.mean()*100:.1f} % vs {cc.gana.mean()*100:.1f} %')
    a, b = f.loc[:'2017'].r, f.loc['2018':].r
    c = {'t>=2.24': f.r.mean() > 1.5 and t_nw(f.r.values) >= 2.24, '2010-17>0': a.mean() > 0, '2018-26>0': b.mean() > 0}
    print(f'ESTRATEGIA Fibonacci (38,2/50/61,8 con confirmación): n {len(f)} {f.r.mean():+.2f} pb (t {t_nw(f.r.values):.2f}) | 2010-17 {a.mean():+.2f} | 2018-26 {b.mean():+.2f} → ' + ('PASA' if all(c.values()) else 'NO PASA'))
    print('   por mercado:', f.groupby('mercado').r.mean().round(1).to_dict())
