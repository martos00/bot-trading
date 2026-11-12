"""C116 — mejoras de la cartera CFD (preregistro PREREGISTRO_C116_mejoras_cartera_cfd.md). Uso: python3 c116_mejoras_cartera_cfd.py DIR_SCRATCH"""
import sys, os, glob, io, zipfile, numpy as np, pandas as pd, holidays
SP = sys.argv[1]
C = pd.read_csv(f'{SP}/componentes_A.csv', index_col=0, parse_dates=True).loc['2018-03-26':]
CB = pd.read_csv(f'{SP}/componentes_B.csv', index_col=0, parse_dates=True).loc['2018-03-26':]
AJ = {'yen': (0.02, 10, 1), 'cesta_yen': (0.31, 10, 1 / 3), 'oro_vie_1645': (0.58, 18, 1), 'oro_D-2': (0.55, 33, 1),
      'nikkei_Q+2': (-1.90, 40, 1), 'nikkei_Q-2': (-1.90, 48, 1), 'oro_video_C93': (0.55, 80, 0.2), 'oro_asia_C99': (0.55, 90, 0.2),
      'nikkei_asia_C101': (-1.45, 120, 0.2)}
X = C[list(AJ)].copy()
for c, (dc, sg, w) in AJ.items():
    m = X[c] != 0; X.loc[m, c] -= 0.005 * w * dc / sg
idx = X.index
def volctl(P): pv = P.rolling(60, min_periods=40).std().shift(1); return (P * (P.std() / pv).clip(0.5, 2)).dropna()
sh = lambda s: s.mean() / s.std() * np.sqrt(252)
def comp(r, coste, w):   # r: log-rendimiento por operación (fecha = día del índice), coste en fracción
    r = r.loc['2018-03-26':]; p = w * 0.005 * (r - coste) / r.std(); return p.groupby(p.index).sum().reindex(idx).fillna(0)
def tstat(x): x = x.dropna(); return x.mean() / x.std() * np.sqrt(len(x)), len(x)

# K1 bitcoin 21-23 UTC
rows = []
for f in sorted(glob.glob(f'{SP}/bn/1h/BTCUSDT-1h-*.zip')):
    with zipfile.ZipFile(f) as z: rows.append(pd.read_csv(io.BytesIO(z.read(z.namelist()[0])), header=None, usecols=[0, 1]))
b = pd.concat(rows); t = b[0].astype('int64'); t = np.where(t > 1e14, t // 1000, t)
o = pd.Series(b[1].astype(float).values, index=pd.to_datetime(t, unit='ms')); o = o[~o.index.duplicated()]
o21 = o[o.index.hour == 21]; o23 = o[o.index.hour == 23]; o21.index = o21.index.normalize(); o23.index = o23.index.normalize()
btc = np.log(o23 / o21).dropna(); btc = btc[btc.index.dayofweek < 5]
# K2 euro 06-08 NY corto
E = pd.read_csv('c1_precios.csv', parse_dates=['dia']).drop_duplicates('dia').set_index('dia')
eur = -np.log(E.mid8 / E.mid6).dropna(); eur = eur[eur != 0]
fest = set()
for y in range(2017, 2028):
    p = pd.Timestamp(holidays.easter.easter(y) if hasattr(holidays, 'easter') else __import__('dateutil.easter', fromlist=['easter']).easter(y))
    fest |= {pd.Timestamp(y, 1, 1), pd.Timestamp(y, 5, 1), pd.Timestamp(y, 12, 25), pd.Timestamp(y, 12, 26), p - pd.Timedelta(days=2), p + pd.Timedelta(days=1)}
    fest |= {pd.Timestamp(d) for d in holidays.UK(subdiv='ENG', years=y)}
eur = eur[[d.weekday() < 5 and d not in fest for d in eur.index]]
# K3 C113 oro Asia (GC 1 h)
import c94_ruptura_otros_futuros as c94
from c112_momentum_sesiones import sesiones
c94.SP = SP; h, ex = c94.carga_h1('GC'); asia = sesiones(h, pd.Timedelta(hours=1), ex).asia / 1e4   # pb → fracción (bruto)
asia.index = pd.DatetimeIndex(asia.index)
# K4 oro viernes 16:55 vs 16:45 (GC 1 min de los viernes)
gc = {}
for f in sorted(glob.glob(f'{SP}/gc_vie/*.csv')):
    x = pd.read_csv(f)
    if len(x) < 30 or x.instrument_id.nunique() > 1: continue
    x.index = pd.to_datetime(x.ts_event, utc=True).dt.tz_convert('America/New_York'); mm = x.index.hour * 60 + x.index.minute
    def px(m):
        y = x.close[(mm < m) & (mm >= m - 10)]; return y.iloc[-1] if len(y) else np.nan
    gc[pd.Timestamp(os.path.basename(f)[:10])] = (px(960), px(1005), px(1015))
g = pd.DataFrame(gc, index=['a', 'b', 'c']).T; o45 = np.log(g.b / g.a).dropna(); o55 = np.log(g.c / g.a).dropna(); inc = np.log(g.c / g.b).dropna()

cand = {
    'K1 bitcoin (1,2 pb, peso 0,2)': (btc, 1.2e-4, 0.2, None),
    'K2 euro E2 (0,95 pb)': (eur, 0.95e-4, 1.0, None),
    'K3 C113 oro Asia (1,36 pb, peso 0,2)': (asia, 1.36e-4, 0.2, None),
    'K4 oro viernes 16:55': (o55, (0.74 + 0.58 + 0.10) * 1e-4, 1.0, 'oro_vie_1645'),
}
P0 = X.sum(axis=1); V0 = volctl(P0)
print(f'BASE CFD Upcomers: Sharpe {sh(V0):.2f} | 2018-21 {sh(V0.loc[:"2021"]):.2f} | 2022-26 {sh(V0.loc["2022":]):.2f} | datos hasta {idx[-1].date()}')
pasan = {}
for nom, (r, c, w, quita) in cand.items():
    a = comp(r, c, w); P = P0 + a - (X[quita] if quita else 0); V = volctl(P)
    d = (sh(V) - sh(V0), sh(V.loc[:'2021']) - sh(V0.loc[:'2021']), sh(V.loc['2022':]) - sh(V0.loc['2022':]))
    if quita: rr = (inc.loc['2018-03-26':] - 0.10e-4); tt, n = tstat(rr); ok2 = rr.mean() > 0; extra = f'tramo 16:45-16:55 neto {rr.mean()*1e4:+.2f} pb (t {tt:.2f}, n {n})'
    else: rr = (r.loc['2018-03-26':] - c); tt, n = tstat(rr); ok2 = tt >= 2.24; extra = f'neta {rr.mean()*1e4:+.2f} pb/op (t {tt:.2f}, n {n})'
    ok1 = d[0] >= 0.05 and d[1] > 0 and d[2] > 0
    print(f'{nom:38s} ΔSharpe {d[0]:+.2f} (18-21 {d[1]:+.2f}, 22-26 {d[2]:+.2f}) | {extra} | {"PASA" if ok1 and ok2 else "NO PASA"}')
    if ok1 and ok2: pasan[nom] = (a, quita)
# informativo: euro con 0,52 pb
a = comp(eur, 0.52e-4, 1.0); V = volctl(P0 + a); rr = eur.loc['2018-03-26':] - 0.52e-4; tt, n = tstat(rr)
print(f'  (informativo) K2 euro con 0,52 pb: ΔSharpe {sh(V)-sh(V0):+.2f} | neta {rr.mean()*1e4:+.2f} pb (t {tt:.2f})')
P = P0.copy()
for nom, (a, quita) in pasan.items(): P = P + a - (X[quita] if quita else 0)
V = volctl(P)
print(f'\nCARTERA CON LAS QUE PASAN ({", ".join(k.split()[0] for k in pasan) or "ninguna"}): Sharpe {sh(V):.2f} | 2018-21 {sh(V.loc[:"2021"]):.2f} | 2022-26 {sh(V.loc["2022":]):.2f}')
for rk in (0.5, 0.65):
    for nm, S in (('base', V0), ('nueva', V)):
        p = S * rk / 0.5; e = p.cumsum(); m = p.resample('ME').sum()
        print(f'   {nm:5s} riesgo {rk}: {p.mean()*252*100:.1f} %/año (al 60 % ≈ {0.6*p.mean()*252*100:.1f}) | caída máx {(e-e.cummax()).min()*100:.1f} % | meses negativos {(m<0).mean()*100:.0f} %')
