"""C104 — barrido del máximo/mínimo de ayer con vela de confirmación (PREREGISTRO_C104_C105). Uso: python3 c104_barrido_pdh.py DIR_SCRATCH"""
import sys
import numpy as np, pandas as pd
from multiprocessing import Pool
from c1_certificacion import t_nw
from c93_oro_ruptura_dia_anterior import carga
SP = sys.argv[1] if len(sys.argv) > 1 else '.'

def a15(x):
    x = x.copy(); x.index = x.index.tz_localize(None)
    return x.resample('15min', label='left', closed='left').agg({'o': 'first', 'h': 'max', 'l': 'min', 'c': 'last'}).dropna()

def simula(x, excluir=()):
    b = a15(x); ses = (b.index + pd.Timedelta(hours=7)).normalize(); mm = b.index.hour * 60 + b.index.minute
    dia = b.groupby(ses).agg(h=('h', 'max'), l=('l', 'min'))
    PH, PL = dia.h.shift(), dia.l.shift()
    o, h, l, c = (b[k].values for k in 'ohlc'); sv = ses.values; out = []
    dias = dia.index; ini, fin = np.searchsorted(sv, dias.values), np.searchsorted(sv, dias.values, 'right')
    for j, (d, a, z) in enumerate(zip(dias, ini, fin)):
        if d.weekday() > 4 or np.isnan(PH.iloc[j]) or d in excluir: continue
        H, L = PH.iloc[j], PL.iloc[j]; m = mm[a:z]; idx = np.arange(a, z)
        ven = idx[(m >= 180) & (m < 900)]; hasta = idx[(m >= 180) & (m < 1005)]
        if len(ven) == 0 or len(hasta) == 0: continue
        sw = {1: None, -1: None}; ext = {1: None, -1: None}; inval = {1: False, -1: False}; trade = None
        for i in ven:
            # lado -1: barrido del máximo (venta); lado +1: barrido del mínimo (compra)
            if not inval[-1]:
                if c[i] > H: inval[-1] = True
                elif h[i] > H: sw[-1] = i; ext[-1] = h[i] if ext[-1] is None else max(ext[-1], h[i])
                elif sw[-1] is not None and c[i] < o[i] and c[i] < l[sw[-1]]: trade = (-1, i, ext[-1], L); break
            if not inval[1]:
                if c[i] < L: inval[1] = True
                elif l[i] < L: sw[1] = i; ext[1] = l[i] if ext[1] is None else min(ext[1], l[i])
                elif sw[1] is not None and c[i] > o[i] and c[i] > h[sw[1]]: trade = (1, i, ext[1], H); break
        if trade is None: continue
        sg, i0, st, tg = trade; p0 = c[i0]; riesgo = abs(p0 - st)
        if riesgo <= 0: continue
        res = None
        for i in hasta[hasta > i0]:
            if (l[i] <= st if sg == 1 else h[i] >= st): res = st; break
            if (h[i] >= tg if sg == 1 else l[i] <= tg): res = tg; break
        if res is None: res = c[hasta[-1]]
        out.append((d, sg * np.log(res / p0) * 1e4, sg * (res - p0) / riesgo, res == tg))
    return pd.DataFrame(out, columns=['d', 'r', 'R', 'gana']).set_index('d')

def db_1m(df):
    df.index = pd.DatetimeIndex(pd.to_datetime(df.ts_event, utc=True)).tz_convert('America/New_York'); df = df[~df.index.duplicated()].sort_index()
    ses = (df.index.tz_localize(None) + pd.Timedelta(hours=7)).normalize()
    g = pd.Series(df.instrument_id.values, index=ses).groupby(level=0); moda = g.agg(lambda v: v.mode().iloc[0]); mez = g.nunique() > 1
    excl = set(moda.index[(moda != moda.shift()) | mez | mez.shift(fill_value=False)])
    return df[['open', 'high', 'low', 'close']].set_axis(['o', 'h', 'l', 'c'], axis=1).loc['2010-06-01':'2026-09-30'], excl

M = [('ORO', 'hd2/XAUUSD', 0.74), ('EURUSD', 'hd_all/EURUSD', 0.6), ('USDJPY', 'hd_all/USDJPY', 0.8), ('GBPUSD', 'hd_all/GBPUSD', 0.8), ('ES', None, 0.73)]
def uno(m):
    nom, d, co = m
    if d: return nom, co, simula(carga(f'{SP}/{d}').loc['2010-06-01':'2026-09-30'])
    x, ex = db_1m(pd.read_pickle(f'{SP}/databento/ES_1m.pkl')); return nom, co, simula(x, ex)
if __name__ == '__main__':
    with Pool(5) as p: res = p.map(uno, M)
    for nom, co, z in res:
        r = z.r; an = r.groupby(r.index.year).sum(); t = t_nw(r.values); a, b = r.loc[:'2017'], r.loc['2018':]
        c = {'>coste y t>=2.58': r.mean() > co and t >= 2.58, 'años>=60%': (an > 0).mean() >= 0.6, '2010-17>0': a.mean() > 0, '2018-26>0': b.mean() > 0}
        print(f'{nom}: n {len(r)} {r.mean():+.2f} pb (t {t:.2f}) años+ {(an>0).sum()}/{len(an)} | 2010-17 {a.mean():+.2f} | 2018-26 {b.mean():+.2f} | acierto {z.gana.mean()*100:.0f} % | R medio {z.R.mean():+.3f} → '
              + ('PASA' if all(c.values()) else 'no pasa: ' + ','.join(k for k, v in c.items() if not v)))
