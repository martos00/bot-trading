"""C92: presion antes del pago de funding (PREREGISTRO_C92). Uso: python3 c92_funding.py DIR_FUNDING DIR_BINANCE_1H"""
import glob, io, os, sys, zipfile
import numpy as np, pandas as pd
from c1_certificacion import t_nw
F, B = sys.argv[1:3]
def leer_px(sym):
    rows = []
    for f in sorted(glob.glob(os.path.join(B, f'{sym}-1h-*.zip'))):
        with zipfile.ZipFile(f) as z: rows.append(pd.read_csv(io.BytesIO(z.read(z.namelist()[0])), header=None, usecols=[0, 1]))
    b = pd.concat(rows); t = b[0].astype('int64'); t = np.where(t > 1e14, t // 1000, t)
    s = pd.Series(b[1].astype(float).values, index=pd.to_datetime(t, unit='ms')); return s[~s.index.duplicated()].sort_index()
def leer_f(sym):
    rows = []
    for f in sorted(glob.glob(os.path.join(F, f'{sym}-fundingRate-*.zip'))):
        with zipfile.ZipFile(f) as z: rows.append(pd.read_csv(io.BytesIO(z.read(z.namelist()[0]))))
    d = pd.concat(rows); t = pd.to_datetime(d.calc_time.astype('int64'), unit='ms').dt.round('h')
    return pd.Series(d.last_funding_rate.astype(float).values, index=t).groupby(level=0).last().sort_index()
for sym in ('BTCUSDT', 'ETHUSDT'):
    px, fr = leer_px(sym), leer_f(sym)
    for hora in (0, 8, 16):
        T = fr.index[fr.index.hour == hora]; out, inf = {}, {}
        for t in T:
            prev = t - pd.Timedelta(hours=8)
            if prev not in fr.index: continue
            f = fr[prev]
            s = -1 if f > 0.0001 else (1 if f < 0 else 0)
            if s == 0: continue
            a, b, c = t - pd.Timedelta(hours=1), t, t + pd.Timedelta(hours=1)
            if a in px.index and b in px.index: out[t] = s * np.log(px[b] / px[a]) * 1e4
            if b in px.index and c in px.index: inf[t] = s * np.log(px[c] / px[b]) * 1e4
        r = pd.Series(out).sort_index(); r2 = pd.Series(inf).sort_index()
        d_, c_ = r.loc[:'2022-12-31'], r.loc['2023-01-01':'2026-09-30']; an = c_.groupby(c_.index.year).mean(); tc = t_nw(c_.values)
        pasa = d_.mean() > 0 and c_.mean() > 0 and tc >= 2.39 and (an > 0).mean() >= 0.6 and c_.mean() > 3
        print(f'{sym[:3]} {hora:02d}:00 UTC: n {len(r)} (cortos {int((r.index.isin(r.index))[0]) and 0}) desc 2019-22 {d_.mean():+.2f} pb (t {t_nw(d_.values):+.2f}, n {len(d_)}) | conf 2023-26 {c_.mean():+.2f} (t {tc:+.2f}, n {len(c_)}) años+ {(an>0).sum()}/{len(an)} | inf. hora siguiente {r2.mean():+.2f} -> {"PASA" if pasa else "NO PASA"}')
