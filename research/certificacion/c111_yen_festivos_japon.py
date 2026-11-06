"""C111 — USDJPY largo 08:00-09:55 JST el último día hábil japonés antes de un festivo de Japón (PREREGISTRO_C111).
Uso: python3 c111_yen_festivos_japon.py DIR_SCRATCH"""
import sys, glob, os, numpy as np, pandas as pd, holidays
from c1_certificacion import t_nw, fxcm, en
from c93_oro_ruptura_dia_anterior import carga
SP = sys.argv[1]; COSTE = 0.8
jp = holidays.Japan(years=range(2009, 2028))
fest = lambda d: d.weekday() >= 5 or d.date() in jp
def sig_lab(d):
    s = d + pd.Timedelta(days=1)
    while s.weekday() >= 5: s += pd.Timedelta(days=1)
    return s
def sig_habil(d):
    s = d + pd.Timedelta(days=1)
    while fest(s): s += pd.Timedelta(days=1)
    return s
dias = pd.date_range('2010-01-01', '2026-09-30', freq='B')
D = [d for d in dias if not fest(d) and sig_lab(d).date() in jp]
def gotobi(d):
    h = sig_habil(d); g = pd.date_range(d, h - pd.Timedelta(days=1))
    return any(x.day in (5, 10, 15, 20, 25) for x in g) or any(x.month != (x + pd.Timedelta(days=1)).month for x in g)
x = carga(f'{SP}/hd_all/USDJPY'); c = x.c.copy(); c.index = c.index.tz_convert('Asia/Tokyo')
def px(t):   # cierre de la última vela que empieza antes de t (≤ 10 min)
    k = c.index.searchsorted(t) - 1
    return c.iloc[k] if k >= 0 and (t - c.index[k]) <= pd.Timedelta(minutes=10) else np.nan
def ret_hd(d):
    t0 = pd.Timestamp(d.date()).tz_localize('Asia/Tokyo') + pd.Timedelta(hours=8); t1 = t0 + pd.Timedelta(minutes=115)
    return np.log(px(t1) / px(t0)) * 1e4
bid = {}
for f in sorted(glob.glob(f'{SP}/fxcm/USDJPY/USDJPY_*.csv.gz')):
    b, _ = fxcm(f); bid.update(b)
def ret_fx(d):
    t0 = (pd.Timestamp(d.date()).tz_localize('Asia/Tokyo') + pd.Timedelta(hours=8)).tz_convert('UTC'); t1 = t0 + pd.Timedelta(minutes=115)
    a, b = en(bid, t0), en(bid, t1); return np.log(b / a) * 1e4
R = pd.DataFrame([(d, gotobi(d), ret_hd(d), ret_fx(d)) for d in D], columns=['d', 'gotobi', 'hd', 'fx']).set_index('d')
def linea(nom, r):
    r = r.dropna(); an = r.groupby(r.index.year).mean()
    return f'{nom}: n {len(r)} media {r.mean():+.2f} pb (t {t_nw(r.values):.2f}) | 2010-17 {r.loc[:"2017"].mean():+.2f} | 2018-26 {r.loc["2018":].mean():+.2f} | desde 2023 {r.loc["2023":].mean():+.2f} | años+ {(an>0).sum()}/{len(an)}'
s = R[~R.gotobi]
print(linea('PRINCIPAL HistData (sin gotobi)', s.hd)); print(linea('Confirmación FXCM (sin gotobi)', s.fx)); print(linea('Informativo HistData con gotobi', R.hd))
# control: resto de días hábiles japoneses no festivos ni gotobi, misma franja
ctrl = pd.Series({d: ret_hd(d) for d in dias[::3] if not fest(d) and d not in D and not gotobi(d)}); print(linea('Control (otros días, 1 de cada 3)', ctrl))
r = s.hd.dropna(); q = s.fx.dropna(); an = r.groupby(r.index.year).mean()
crit = {'t>=2.24': r.mean() > 0 and t_nw(r.values) >= 2.24, '2010-17>0': r.loc[:'2017'].mean() > 0, '2018-26>0': r.loc['2018':].mean() > 0,
        'años>=60%': (an > 0).mean() >= 0.6, '>coste': r.mean() > COSTE, 'FXCM': q.mean() > COSTE and t_nw(q.values) >= 2.0, 'desde 2023>0': r.loc['2023':].mean() > 0}
print('RESULTADO:', 'PASA' if all(crit.values()) else 'NO PASA: falla ' + ', '.join(k for k, v in crit.items() if not v))
