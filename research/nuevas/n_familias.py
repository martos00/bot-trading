"""N1-N3 según PREREGISTRO_N1_N3.md. Uso: python3 n_familias.py DIR_DATOS DIR_HD_USDCAD DIR_HD_AUDUSD"""
import json, os, sys
import numpy as np
import pandas as pd
from scipy import stats

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'fase72'))
import h80_motor as M  # noqa: E402
from h80_evaluacion import t_nw  # noqa: E402

d, hd_cad, hd_aud = sys.argv[1:4]


def yahoo(f):
    r = json.load(open(os.path.join(d, f)))['chart']['result'][0]
    tz = r['meta'].get('exchangeTimezoneName', 'America/New_York')
    idx = pd.to_datetime(r['timestamp'], unit='s', utc=True).tz_convert(tz).tz_localize(None).normalize()
    return pd.Series(r['indicators']['quote'][0]['close'], index=idx).dropna()


def cboe(f):
    x = pd.read_csv(os.path.join(d, f))
    return pd.Series(x.CLOSE.values, index=pd.to_datetime(x.DATE, format='%m/%d/%Y'))


def sharpe(x):
    return x.mean() / x.std() * np.sqrt(252)


spx = yahoo('y_%5EGSPC.json')
r_spx = np.log(spx / spx.shift(1)).dropna()            # r_t = cierre t-1 → cierre t

# ---------- N1 ----------
print('=== N1: VIX/VIX3M → S&P 500 al día siguiente ===')
q = (cboe('VIX_History.csv') / cboe('VIX3M_History.csv')).dropna()
sig = q.reindex(r_spx.index).shift(1)                   # cociente al cierre del día anterior
x = pd.DataFrame({'r': r_spx, 'inv': sig > 1}).loc[sig.notna()]
reglas = {}
for nom, sl in (('descubrimiento 2006-2015', slice('2006-07', '2015')), ('confirmación 2016-2026', slice('2016', '2026'))):
    y = x.loc[sl]
    a, b = y[y.inv].r, y[~y.inv].r
    t, _ = stats.ttest_ind(a, b, equal_var=False)
    reglas[nom] = (a.mean(), b.mean(), t)
    print(f'  {nom}: inversión {a.mean() * 1e4:+.2f} pb/día (n {len(a)}) | normal {b.mean() * 1e4:+.2f} pb/día (n {len(b)}) | t diferencia {t:+.2f}')
ma, mb, td = reglas['descubrimiento 2006-2015']
estado_bueno_inv = ma > mb
print(f'  Criterio descubrimiento |t| ≥ 2,5: {"CUMPLE" if abs(td) >= 2.5 else "NO CUMPLE"} → estado bueno: {"inversión" if estado_bueno_inv else "normal"}')
y = x.loc['2016':]
pos = (y.inv == estado_bueno_inv).astype(float)
cambios = pos.diff().abs().fillna(pos.iloc[0])
neto_regla = pos * (y.r - 2.0e-4) - cambios * 0.5e-4
neto_largo = y.r - 2.0e-4
mc, mbc, tc = reglas['confirmación 2016-2026']
print(f'  Confirmación: regla neta Sharpe {sharpe(neto_regla):.2f} (exposición {pos.mean():.0%}) frente a siempre largo {sharpe(neto_largo):.2f}; '
      f'diferencia mismo signo y t ≥ 2: {"SÍ" if (mc - mbc) * (ma - mb) > 0 and abs(tc) >= 2 else "NO"}')
eq = neto_regla.cumsum()
print(f'  DD máx. regla {(eq - eq.cummax()).min() * 100:.0f}% | veredicto:',
      'CONFIRMADA' if abs(td) >= 2.5 and (mc - mbc) * (ma - mb) > 0 and abs(tc) >= 2 and sharpe(neto_regla) > sharpe(neto_largo) else 'NO CONFIRMADA')

# ---------- N2 ----------
print('\n=== N2: S&P 500 el día del anuncio del FOMC ===')
fomc = pd.to_datetime(pd.read_csv(os.path.join(d, 'fomc.csv')).fomc)
es = r_spx.index.isin(fomc)
for nom, sl in (('descubrimiento 1994-2009', slice('1994', '2009')), ('confirmación 2010-2026', slice('2010', '2026'))):
    y, e = r_spx.loc[sl], es[r_spx.index.slice_indexer(sl.start, sl.stop)]
    f, o = y[e], y[~e]
    neto = f - 2.5e-4
    t_dif, _ = stats.ttest_ind(f, o, equal_var=False)
    an = neto.groupby(neto.index.year).mean()
    print(f'  {nom}: días FOMC n {len(f)}, media {f.mean() * 1e4:+.1f} pb (t {f.mean() / f.std() * np.sqrt(len(f)):.2f}), neta {neto.mean() * 1e4:+.1f} pb '
          f'(t {neto.mean() / neto.std() * np.sqrt(len(neto)):.2f}) | resto de días {o.mean() * 1e4:+.2f} pb | t diferencia {t_dif:.2f} | '
          f'años netos + {(an > 0).sum()}/{len(an)}')

# ---------- N3 ----------
print('\n=== N3: materias primas → divisas al día siguiente (16:00 NY → 16:00 NY) ===')
for par, mat, dirmat, hd, signo in (('USDCAD', 'petróleo', 'y_CL%3DF.json', hd_cad, -1), ('AUDUSD', 'cobre', 'y_HG%3DF.json', hd_aud, +1)):
    c = yahoo(dirmat)
    rc = np.sign(np.log(c / c.shift(1))).dropna()
    m, _ = M.cargar(hd, par)
    ct = pd.DatetimeIndex(m.t) + pd.Timedelta(minutes=1); cv = m.c.to_numpy(float)
    dias = pd.bdate_range('2010-01-01', '2026-09-30')
    T = pd.DatetimeIndex([x + pd.Timedelta(hours=16) for x in dias]).tz_localize(M.NY)
    p = pd.Series(M.precio_en(ct, cv, T), index=dias)
    rfx = np.log(p.shift(-1) / p)                       # 16:00 de t → 16:00 del día hábil siguiente
    s = rc.reindex(dias)
    tr = (signo * s * rfx).dropna()
    tr = tr[s.reindex(tr.index) != 0]
    for nom, sl in (('descubrimiento 2010-2017', slice('2010', '2017')), ('confirmación 2018-2026', slice('2018', '2026'))):
        y = tr.loc[sl]; neto = y - 1.5e-4
        an = neto.groupby(neto.index.year).mean()
        print(f'  {par} según {mat} {nom}: n {len(y)}, bruto {y.mean() * 1e4:+.2f} pb (t {t_nw(y.values):.2f}), neto {neto.mean() * 1e4:+.2f} pb '
              f'(t {t_nw(neto.values):.2f}), años netos + {(an > 0).sum()}/{len(an)}')
