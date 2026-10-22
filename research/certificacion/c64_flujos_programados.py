"""C64: flujos programados (MSCI, Russell, triple hechicería, VIX, dividendos japoneses). Ver PREREGISTRO_C64."""
import glob
import numpy as np, pandas as pd
import holidays
from scipy import stats
from c1_certificacion import t_nw
from c45_oro_viernes import carga
from c54_fin_trimestre import tramo
S = '/tmp/claude-0/-home-user-bot-trading/682335b1-28ae-5d18-9355-ce7f0f968722/scratchpad/'
FEST = {pd.Timestamp(d) for d in holidays.financial_holidays('NYSE', years=range(2009, 2028))}
HAB = pd.bdate_range('2009-01-01', '2027-12-31'); HAB = HAB[~HAB.isin(list(FEST))]
def habil_ant(d):
    while d not in HAB: d -= pd.Timedelta(days=1)
    return d
meses = pd.period_range('2010-06', '2026-09', freq='M')
ult_hab = {m: HAB[HAB.searchsorted(m.end_time.normalize(), side='right') - 1] for m in meses}
tercer_vie = {m: habil_ant(pd.date_range(m.start_time, m.end_time, freq='W-FRI')[2]) for m in pd.period_range('2010-06', '2026-11', freq='M')}
MSCI = [ult_hab[m] for m in meses if m.month in (2, 5, 8, 11)]
RUSSELL = [habil_ant(pd.date_range(f'{y}-06-01', f'{y}-06-30', freq='W-FRI')[-1]) for y in range(2011, 2027)]
TRIPLE = [tercer_vie[m] for m in meses if m.month in (3, 6, 9, 12)]
VIX = [habil_ant(tercer_vie[m + 1] - pd.Timedelta(days=30)) for m in meses]
# precios
es = pd.read_pickle(S + 'databento/ES_1m.pkl'); es.index = pd.to_datetime(es.ts_event, utc=True).dt.tz_convert('America/New_York').dt.tz_localize(None)
es = es.sort_index(); es = es[~es.index.duplicated()]
def es_tramo(d, h0, m0, h1, m1):
    a = es.loc[d + pd.Timedelta(hours=h0, minutes=m0) - pd.Timedelta(minutes=10): d + pd.Timedelta(hours=h0, minutes=m0) - pd.Timedelta(minutes=1)]
    b = es.loc[d + pd.Timedelta(hours=h1, minutes=m1) - pd.Timedelta(minutes=10): d + pd.Timedelta(hours=h1, minutes=m1) - pd.Timedelta(minutes=1)]
    if not len(a) or not len(b) or a.instrument_id.iloc[-1] != b.instrument_id.iloc[-1]: return np.nan
    return np.log(b.close.iloc[-1] / a.close.iloc[-1])
def h1(s):
    x = pd.concat([pd.read_csv(f) for f in sorted(glob.glob(S + f'databento/h1/{s}_*.csv'))])
    x['close'] = pd.to_numeric(x.close, errors='coerce'); x = x[x.close > 0]
    x.index = pd.to_datetime(x.ts_event, utc=True).dt.tz_convert('America/New_York').dt.tz_localize(None) + pd.Timedelta(hours=1)
    x = x[~x.index.duplicated()].sort_index(); return x
NQ, RTY = h1('NQ'), h1('RTY')
def h1_tramo(x, d, h0, h1_):
    a, b = d + pd.Timedelta(hours=h0), d + pd.Timedelta(hours=h1_)
    if a in x.index and b in x.index and x.instrument_id[a] == x.instrument_id[b]: return np.log(x.close[b] / x.close[a])
    return np.nan
P = {}
P['F1 MSCI ES/NQ/RTY 15-16'] = (pd.Series({d: np.nanmean([es_tramo(d, 15, 0, 16, 0), h1_tramo(NQ, d, 15, 16), h1_tramo(RTY, d, 15, 16)]) for d in MSCI}), 0.75)
P['F2 Russell RTY 15-16'] = (pd.Series({d: h1_tramo(RTY, d, 15, 16) for d in RUSSELL}), 1.2)
P['F3 Triple hechicería ES 15-16'] = (pd.Series({d: es_tramo(d, 15, 0, 16, 0) for d in TRIPLE}), 0.73)
P['F4 Vencimiento VIX ES 09:30-10:00'] = (pd.Series({d: es_tramo(d, 9, 30, 10, 0) for d in VIX}), 0.73)
jp = carga(S + 'hd_new/JPXJPY'); rj = tramo(jp, 1, 0, 1, 59)
dj = pd.DatetimeIndex(sorted(set(rj.index))); dj = dj[dj.weekday < 5]; k = pd.Series(range(len(dj)), index=dj)
fin = k.groupby(k.index.to_period('M')).cumcount(ascending=False) + 1
ex = dj[(fin.values == 3) & np.isin(dj.month, [3, 9])]; ex1 = dj[(fin.values == 2) & np.isin(dj.month, [3, 9])]
P['F5a Dividendos JP JPX 01-02 (último día con derecho)'] = (rj.reindex(ex), 2.0)
P['F5b Dividendos JP JPX 01-02 (día siguiente)'] = (rj.reindex(ex1), 2.0)
ps, info = {}, {}
for nom, (r, c) in P.items():
    r = r.dropna(); t = t_nw(r.values, 2); ps[nom] = 2 * (1 - stats.norm.cdf(abs(t)))
    an = r.groupby(r.index.year).sum(); info[nom] = (r, t, (np.sign(an) == np.sign(r.mean())).mean(), c)
seguir = True
for j, nom in enumerate(sorted(ps, key=ps.get)):
    r, t, anos, c = info[nom]; seguir = seguir and ps[nom] <= 0.05 / (6 - j)
    ok = seguir and anos >= 0.6 and abs(r.mean()) * 1e4 >= 3 * c
    print(f'{nom}: n {len(r)} {r.mean()*1e4:+.2f} pb (t {t:.2f}) años con el signo {anos*100:.0f}% | Holm {seguir} → {"PASA" if ok else "no"}')
