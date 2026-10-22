"""E13: afinar a 30 min las ventanas de E1, E9, E11, E8 y E10. Ver PREREGISTRO_E13."""
import glob, os
from datetime import datetime
from zoneinfo import ZoneInfo
import numpy as np, pandas as pd
from dateutil.easter import easter
from c1_certificacion import fxcm, en, t_nw
NY = ZoneInfo('America/New_York'); S = '/tmp/claude-0/-home-user-bot-trading/682335b1-28ae-5d18-9355-ce7f0f968722/scratchpad/'
COM = 0.45e-4
def fx(p):
    b, a = {}, {}
    for f in sorted(glob.glob(S + f'fxcm/{p}/{p}_*.csv.gz')):
        bb, aa = fxcm(f); b.update(bb); a.update(aa)
    return b, a
def t_ny(d, hm): return datetime(d.year, d.month, d.day, hm // 100, hm % 100, tzinfo=NY)
def neto_fx(b, a, d, h0, h1, lado):
    b0, a0, b1, a1 = en(b, t_ny(d, h0)), en(a, t_ny(d, h0)), en(b, t_ny(d, h1)), en(a, t_ny(d, h1))
    if np.isnan([b0, a0, b1, a1]).any(): return np.nan
    return (np.log(b1 / a0) if lado > 0 else np.log(b0 / a1)) - COM
def medida(x): x = x.dropna(); return x.mean() / x.std() if len(x) > 5 else np.nan
def decidir(nom, series, actual, d0, d1, c0):
    filas = []
    for k, s in series.items():
        filas.append(dict(ventana=k, med_d=medida(s.loc[d0:d1]), med_c=medida(s.loc[c0:]), t_c=t_nw(s.loc[c0:].dropna().values), media_c=s.loc[c0:].mean() * 1e4, n_c=s.loc[c0:].notna().sum()))
    T = pd.DataFrame(filas).set_index('ventana'); mejor = T.med_d.idxmax()
    adopta = mejor != actual and T.med_c[mejor] >= T.med_c[actual] and T.t_c[mejor] >= 2
    print(f'== {nom}: mejor en descubrimiento {mejor} | actual {actual} → {"ADOPTAR " + mejor if adopta else "SE QUEDA " + actual}')
    print(T.round(3).sort_values('med_d', ascending=False).to_string())
    return T
dias = pd.bdate_range('2012-01-02', '2026-09-30')
# E1
def target(d):
    e = pd.Timestamp(easter(d.year)); return (d.month, d.day) in ((1, 1), (5, 1), (12, 25), (12, 26)) or d in (e - pd.Timedelta(days=2), e + pd.Timedelta(days=1))
b, a = fx('EURUSD'); dE1 = [d for d in dias if not target(d)]
ser = {f'{i:04d}-{f:04d}': pd.Series({d: neto_fx(b, a, d, i, f, -1) for d in dE1}) for i in (500, 530, 600, 630) for f in (730, 800, 830)}
decidir('E1 EURUSD corto', ser, '0600-0800', '2012', '2018', '2019')
# calendario D−2 y Q0 con días con datos de USDJPY
b, a = fx('USDJPY'); dd = pd.DatetimeIndex([d for d in dias if not np.isnan(en(b, t_ny(d, 700)))])
k = pd.Series(range(len(dd)), index=dd); fin = k.groupby(k.index.to_period('M')).cumcount(ascending=False) + 1
D2 = dd[fin.values == 3]; Q0 = dd[(fin.values == 1) & np.isin(dd.month, [3, 6, 9, 12])]
ser = {f'{i:04d}-{f:04d}': pd.Series({d: neto_fx(b, a, d, i, f, 1) for d in D2}) for i in (630, 700, 730) for f in (730, 800, 830) if f > i}
decidir('E9 USDJPY largo D−2', ser, '0700-0800', '2012', '2018', '2019')
FXJ = {p: fx(p) for p in ('USDJPY', 'EURJPY', 'GBPJPY')}
ser = {}
for i in (0, 30, 100, 130):
    for f in (130, 200, 230, 300):
        if f <= i: continue
        ser[f'{i:04d}-{f:04d}'] = pd.Series({d: np.nanmean([neto_fx(*FXJ[p], d, i, f, -1) for p in FXJ]) for d in Q0})
decidir('E11 cesta yen fuerte Q0', ser, '0100-0200', '2012', '2018', '2019')
# futuros a minuto
def fut(dirc, coste):
    out = {}
    for f in sorted(glob.glob(dirc + '*.csv')):
        x = pd.read_csv(f)
        if len(x) < 30 or x.instrument_id.nunique() > 1: continue
        x.index = pd.to_datetime(x.ts_event, utc=True).dt.tz_convert('America/New_York'); mm = x.index.hour * 60 + x.index.minute
        def px(m):
            y = x.close[(mm < m) & (mm >= m - 10)]; return y.iloc[-1] if len(y) else np.nan
        p = {m: px(m) for m in (930, 960, 990, 1015)}
        out[pd.Timestamp(os.path.basename(f)[:10])] = {f'{m//60:02d}{m%60:02d}-1655': np.log(p[1015] / p[m]) - coste for m in (930, 960, 990)}
    return pd.DataFrame(out).T
G = fut(S + 'gc_vie/', 0.74e-4); decidir('E8 oro viernes', {c: G[c] for c in G}, '1600-1655', '2010', '2017', '2018')
P = fut(S + 'si_pre/', 2.3e-4); decidir('E10 plata víspera', {c: P[c] for c in P}, '1600-1655', '2010', '2017', '2018')
