"""C31: confirmación de candidatas en vigilancia con mercados no usados (ver PREREGISTRO_C31)."""
import glob, json, os, numpy as np, pandas as pd
from scipy import stats
from c1_certificacion import t_nw
S = '/tmp/claude-0/-home-user-bot-trading/682335b1-28ae-5d18-9355-ce7f0f968722/scratchpad/'
D = S + 'databento/'
def diario(s):
    x = pd.concat([pd.read_csv(f, parse_dates=['ts_event']) for f in sorted(glob.glob(D + f'agro/{s}_*.csv'))] + ([pd.read_csv(D + f'{s}.v.0.csv', parse_dates=['ts_event'])] if os.path.exists(D + f'{s}.v.0.csv') else []))
    x['dia'] = x.ts_event.dt.tz_localize(None).dt.normalize()
    x = x[x.dia.dt.weekday < 5].drop_duplicates('dia').set_index('dia').sort_index()
    r = np.log(x.close).diff(); r[x.instrument_id != x.instrument_id.shift()] = np.nan; return r.loc[:'2026-09-30']
def resumen(nombre, series, desde, hasta):
    m = pd.concat(series, axis=1).loc[desde:hasta]; f = m.mean(axis=1).dropna()
    for c in m: y = m[c].dropna(); print(f'   {c}: {y.mean()*1e4:6.2f} pb (t {t_nw(y.values):.2f}) n {len(y)}')
    t = t_nw(f.values); ok = (m.mean() > 0).all() and t >= 1.645
    print(f'  {nombre} media: {f.mean()*1e4:.2f} pb (t {t:.2f}) → {"CONFIRMADA" if ok else "NO confirmada"}')
fomc = pd.to_datetime(pd.read_csv(S + 'n/fomc.csv').fomc)
print('== V1 ventana FOMC (largo cierre −2 → cierre +1) ==')
ser = []
for s in ('ZT', 'ZF'):
    r = diario(s); ix = r.index; v = {}
    for f in fomc:
        if f in ix:
            i = ix.get_loc(f)
            if i >= 1 and i + 1 < len(ix): v[f] = r.iloc[i - 1:i + 2].sum(min_count=3)
    ser.append(pd.Series(v, name=s).dropna())
resumen('V1', ser, '2018', '2026')
print('== V2 madrugada 01:00 → 03:00 NY (largo) ==')
ser = []
for s in ('YM', 'RTY'):
    x = pd.concat([pd.read_csv(f, parse_dates=['ts_event']) for f in sorted(glob.glob(D + f'h1/{s}_*.csv')) if os.path.getsize(f) > 200]).drop_duplicates('ts_event')
    fin = x.ts_event.dt.tz_convert('America/New_York').dt.tz_localize(None) + pd.Timedelta(hours=1)
    h = pd.DataFrame({'c': x.close.values, 'id': x.instrument_id.values}, index=fin).sort_index(); h = h[h.index.weekday < 5]
    pc = pd.DataFrame({'c': h.c.values, 'id': h.id.values, 'dia': h.index.normalize(), 'hora': h.index.hour})
    a = pc.pivot_table(index='dia', columns='hora', values='c', aggfunc='last'); i = pc.pivot_table(index='dia', columns='hora', values='id', aggfunc='last')
    r = np.log(a[3] / a[1]); r[i[3] != i[1]] = np.nan; ser.append(r.dropna().rename(s))
resumen('V2', ser, '2018', '2026')
print('== V3 antes del BCE (largo cierre D−2 → cierre D−1) ==')
raw = pd.read_excel(S + 'eampd.xlsx', sheet_name='Press Conference Window').date
ev = pd.Series([pd.Timestamp(v) if not isinstance(v, str) else pd.to_datetime(v, dayfirst=True) for v in raw]).dt.normalize().sort_values()
ser = []
for t in ('%5EFCHI', '%5EIBEX', 'FTSEMIB.MI'):
    r0 = json.load(open(S + f'c31_{t}.json'))['chart']['result'][0]
    idx = pd.to_datetime(r0['timestamp'], unit='s', utc=True).tz_convert(r0['meta'].get('exchangeTimezoneName', 'Europe/Paris')).tz_localize(None).normalize()
    p = pd.Series(r0['indicators']['quote'][0]['close'], index=idx).dropna(); p = p[~p.index.duplicated(keep='last')].sort_index()
    r = np.log(p).diff().dropna(); s_ = r.index; v = {}
    for d in ev:
        i = s_.searchsorted(d)
        if 2 <= i < len(s_): v[d] = r.iloc[i - 1]
    ser.append(pd.Series(v, name=t.replace('%5E', '')).dropna())
resumen('V3', ser, '2013', '2025')
