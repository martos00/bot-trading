"""B17: (a) lead-lag horario entre 12 futuros; (b) día extremo (momentum/reversión) en 12 futuros + 13 pares FXCM. Ver PREREGISTRO_B17."""
import glob, os, sys
import numpy as np, pandas as pd
from scipy import stats
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'certificacion'))
from c1_certificacion import t_nw
H = '/tmp/claude-0/-home-user-bot-trading/682335b1-28ae-5d18-9355-ce7f0f968722/scratchpad/databento/'
COSTE = dict(ES=0.73, NQ=0.3, ZN=1.8, ZB=2.7, CL=2.0, GC=0.74, SI=2.3, HG=1.65, **{'6E': 0.75, '6J': 1.2, '6A': 1.3, '6B': 1.3})
def horario(s):
    if s == 'ES':
        x = pd.read_pickle(H + 'ES_1m.pkl'); t = pd.to_datetime(x.ts_event).dt.tz_convert('America/New_York').dt.tz_localize(None) + pd.Timedelta(minutes=1)
        return x.assign(t=t.dt.ceil('h')).groupby('t').agg(c=('close', 'last'), id=('instrument_id', 'last'))
    x = pd.concat([pd.read_csv(f) for f in sorted(glob.glob(H + f'h1/{s}_*.csv'))])
    x['close'] = pd.to_numeric(x.close, errors='coerce'); x['ts_event'] = pd.to_datetime(x.ts_event, utc=True, errors='coerce')
    x = x[x.close.notna() & x.ts_event.notna() & (x.close > 0)].drop_duplicates('ts_event')
    fin = x.ts_event.dt.tz_convert('America/New_York').dt.tz_localize(None) + pd.Timedelta(hours=1)
    return pd.DataFrame({'c': x.close.values, 'id': x.instrument_id.values}, index=fin).sort_index()
R = {}
for s in COSTE:
    h = horario(s).loc['2010-06-01':'2026-09-30']; h = h[h.index.weekday < 5]
    full = pd.date_range(h.index.min().floor('h'), h.index.max(), freq='h'); h = h.reindex(full)
    r = np.log(h.c / h.c.shift(1)); r[h.id != h.id.shift(1)] = np.nan; R[s] = r
R = pd.DataFrame(R); hora = R.index.hour
ok_h = ~np.isin(hora, [16, 17, 18])
filas = []
for L in COSTE:
    for F in COSTE:
        if L == F: continue
        q = (np.sign(R[L].shift(1)) * R[F])[ok_h & (R.index.normalize() == (R.index - pd.Timedelta(hours=1)).normalize())].dropna(); q = q[q != 0]
        d, c = q.loc[:'2017'], q.loc['2018':]
        filas.append(dict(regla=f'{L}→{F}', m_d=d.mean() * 1e4, t_d=t_nw(d.values), m_c=c.mean() * 1e4, t_c=t_nw(c.values),
                          años=(np.sign(c.groupby(c.index.year).mean()) == np.sign(d.mean())).mean(), coste=COSTE[F]))
def informe(nom, t):
    sel = t[t.t_d.abs() >= 3.0].copy(); k = max(len(sel), 1); u = stats.norm.ppf(1 - 0.05 / k)
    sel['t_c_s'] = sel.t_c * np.sign(sel.m_d); sel['m_c_s'] = sel.m_c * np.sign(sel.m_d)
    sel['pasa'] = (sel.t_c_s >= u) & (sel.años >= 0.6) & (sel.m_c_s >= 3 * sel.coste)
    print(f'== {nom}: {len(t)} reglas; seleccionadas {len(sel)}; umbral {u:.2f}')
    print(sel.sort_values('t_c_s', ascending=False).round(2).to_string(index=False) if len(sel) else '   (ninguna seleccionada)')
A = pd.DataFrame(filas); A.to_csv('b17a_todas.csv', index=False); informe('(a) lead-lag horario', A)
# (b) días extremos
diario = {}
for s in COSTE:
    x = horario(s).loc['2010-06-01':'2026-09-30']; x = x[(x.index.hour == 16) & (x.index.minute == 0) & (x.index.weekday < 5)]
    x.index = x.index.normalize(); r = np.log(x.c / x.c.shift(1)); r[x.id != x.id.shift(1)] = np.nan; diario[s] = (r, COSTE[s], '2017', '2018')
from c1_certificacion import fxcm, en
from datetime import datetime
from zoneinfo import ZoneInfo
NY = ZoneInfo('America/New_York'); SF = '/tmp/claude-0/-home-user-bot-trading/682335b1-28ae-5d18-9355-ce7f0f968722/scratchpad/fxcm/'
for p in ['EURUSD', 'GBPUSD', 'USDJPY', 'USDCHF', 'AUDUSD', 'USDCAD', 'EURGBP', 'EURCHF', 'EURJPY', 'GBPJPY', 'EURAUD', 'EURNZD', 'GBPCAD']:
    b, a = {}, {}
    for f in sorted(glob.glob(SF + f'{p}/{p}_*.csv.gz')):
        bb, aa = fxcm(f); b.update(bb); a.update(aa)
    v, sp = {}, {}
    for d in pd.bdate_range('2012-01-02', '2026-09-30'):
        t = datetime(d.year, d.month, d.day, 16, tzinfo=NY); x0, y0 = en(b, t), en(a, t)
        if not np.isnan([x0, y0]).any(): v[d] = (x0 + y0) / 2; sp[d] = (y0 - x0) / ((x0 + y0) / 2)
    v = pd.Series(v); diario[p] = (np.log(v / v.shift(1)), pd.Series(sp).loc['2019':].mean() * 1e4 + 0.45, '2018', '2019')
filas = []
for s, (r, c, fd, ic) in diario.items():
    sd = r.rolling(60, min_periods=40).std().shift(1); ev = r.abs() > 2 * sd
    q = (np.sign(r) * r.shift(-1))[ev].dropna(); d, cf = q.loc[:fd], q.loc[ic:]
    if len(d) < 30 or len(cf) < 30: continue
    filas.append(dict(regla=f'{s} día extremo', n_d=len(d), m_d=d.mean() * 1e4, t_d=t_nw(d.values), n_c=len(cf), m_c=cf.mean() * 1e4, t_c=t_nw(cf.values),
                      años=(np.sign(cf.groupby(cf.index.year).mean()) == np.sign(d.mean())).mean(), coste=c))
Bt = pd.DataFrame(filas); Bt.to_csv('b17b_todas.csv', index=False); informe('(b) día extremo (+ = momentum, − = reversión)', Bt)
print('\n(b) informativo, todas:'); print(Bt.round(2).to_string(index=False))
