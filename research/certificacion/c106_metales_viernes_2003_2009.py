"""C106 — oro y plata del viernes en 2003-2009 con Dukascopy (PREREGISTRO_C106).
Uso: python3 c106_metales_viernes_2003_2009.py xau_bid.csv xau_ask.csv xag_bid.csv xag_ask.csv
CSV de dukascopy-node (columnas timestamp, open, high, low, close[, volume]; timestamp en ms UTC o fecha ISO)."""
import sys
import numpy as np, pandas as pd, holidays
from c1_certificacion import t_nw
FEST = {pd.Timestamp(d) for d in holidays.financial_holidays('NYSE', years=range(2003, 2011))}

def lee(f):
    x = pd.read_csv(f); ts = x.iloc[:, 0]
    t = pd.to_datetime(ts, unit='ms', utc=True) if np.issubdtype(ts.dtype, np.number) else pd.to_datetime(ts, utc=True)
    s = pd.Series(x['close'].values, index=t.dt.tz_convert('America/New_York')); return s[~s.index.duplicated()].sort_index()
def medio(fb, fa):
    b, a = lee(fb), lee(fa); j = pd.concat([b, a], axis=1, keys=['b', 'a']).dropna()
    m = (j.b + j.a) / 2; m.index = m.index + pd.Timedelta(minutes=5)      # marca = cierre de la vela de 5 min
    return m, ((j.a - j.b) / m * 1e4)
def tramo(m, h0, m0, h1, m1):
    n = m.index.tz_localize(None); d = pd.DataFrame({'p': m.values, 'dia': n.normalize(), 'mm': n.hour * 60 + n.minute})
    p0 = d[d.mm == h0 * 60 + m0].groupby('dia').p.last(); p1 = d[d.mm == h1 * 60 + m1].groupby('dia').p.last()
    return (np.log(p1 / p0) * 1e4).dropna()
def info(nom, r, crit=False):
    an = r.groupby(r.index.year).mean(); t = t_nw(r.values)
    print(f'{nom}: n {len(r)} {r.mean():+.2f} pb (t {t:.2f}) años+ {(an>0).sum()}/{len(an)} | por año {an.round(1).to_dict()}')
    if crit:
        c = {'t>=2.24': r.mean() > 0 and t >= 2.24, 'años>=60%': (an > 0).mean() >= 0.6}
        print('   CRITERIOS:', c, '→ CONFIRMADA' if all(c.values()) else '→ NO CONFIRMADA')
if __name__ == '__main__':
    xau, sau = medio(sys.argv[1], sys.argv[2]); xag, sag = medio(sys.argv[3], sys.argv[4])
    xau, xag = xau.loc['2003-05-01':'2009-12-31'], xag.loc['2003-05-01':'2009-12-31']
    vie = lambda r: r[(r.index.dayofweek == 4) & ~r.index.isin(list(FEST))]
    PRE = {d for d in pd.bdate_range('2003-01-01', '2010-01-31') if d not in FEST and (d + pd.offsets.BDay(1)) in FEST}
    o = tramo(xau, 16, 0, 16, 55); p = tramo(xag, 16, 30, 16, 55)
    info('ORO viernes 16:00-16:55', vie(o), True); info('PLATA viernes 16:30-16:55', vie(p), True)
    for nom, r in (('oro', o), ('plata', p)):
        for wd, n in enumerate(['lun', 'mar', 'mié', 'jue']):
            q = r[r.index.dayofweek == wd]; print(f'   placebo {nom} {n}: {q.mean():+.2f} pb (t {t_nw(q.values):.2f})')
    info('informativo plata víspera 16:00-16:55', tramo(xag, 16, 0, 16, 55).reindex(sorted(PRE)).dropna())
    for nom, s in (('oro', sau), ('plata', sag)):
        n = s.index.tz_localize(None); print(f'   spread medio {nom} viernes 16:00-17:00: {s[(n.dayofweek == 4) & (n.hour == 16)].mean():.1f} pb')
