"""C3 — réplica fiel de Breedon & Ranaldo (2013) con FXCM 2012-2026 (PREREGISTRO_C3_breedon_ranaldo.md).
Uso: python3 c3_breedon_ranaldo.py DIR_FXCM DIR_HISTDATA SALIDA_CSV"""
import glob, os, sys
import numpy as np
import pandas as pd
from scipy import stats
from c1_certificacion import t_nw

TZ = {'NY': 'America/New_York', 'LON': 'Europe/London', 'TOK': 'Asia/Tokyo', 'SYD': 'Australia/Sydney'}
# (par, sesión, (zona, h inicio), (zona, h fin), zona que define el día, signo previsto)
SESIONES = [
    ('EURUSD', 'Europa', ('LON', 7), ('NY', 8), 'LON', -1), ('EURUSD', 'EEUU', ('NY', 8), ('NY', 16), 'NY', +1),
    ('GBPUSD', 'Europa', ('LON', 7), ('NY', 8), 'LON', -1), ('GBPUSD', 'EEUU', ('NY', 8), ('NY', 16), 'NY', +1),
    ('USDCHF', 'Europa', ('LON', 7), ('NY', 8), 'LON', +1), ('USDCHF', 'EEUU', ('NY', 8), ('NY', 16), 'NY', -1),
    ('USDJPY', 'Japon', ('TOK', 8), ('TOK', 15), 'TOK', +1), ('USDJPY', 'EEUU', ('NY', 8), ('NY', 16), 'NY', -1),
    ('EURJPY', 'Europa', ('LON', 7), ('LON', 15), 'LON', -1), ('EURJPY', 'Japon', ('TOK', 8), ('TOK', 15), 'TOK', +1),
    ('AUDUSD', 'Australia', ('SYD', 10), ('SYD', 16), 'SYD', -1), ('AUDUSD', 'EEUU', ('NY', 8), ('NY', 16), 'NY', +1),
]
TOL = 5


def cargar_fxcm(d, par):
    partes = []
    for f in sorted(glob.glob(os.path.join(d, par, f'{par}_*.csv.gz'))):
        x = pd.read_csv(f, compression='gzip', usecols=['DateTime', 'BidClose', 'AskClose'])
        m = (pd.to_datetime(x.DateTime, format='%m/%d/%Y %H:%M:%S.%f') - pd.Timestamp('1970-01-01')) // pd.Timedelta(minutes=1)
        partes.append(pd.DataFrame({'m': m.to_numpy(), 'mid': ((x.BidClose + x.AskClose) / 2).to_numpy()}))
    s = pd.concat(partes).drop_duplicates('m').sort_values('m')
    return s.m.to_numpy(np.int64), s.mid.to_numpy(float)


def cargar_histdata(d, par):
    fs = sorted(glob.glob(os.path.join(d, par, f'DAT_ASCII_{par}_M1_*.csv')))
    if not fs:
        return None
    x = pd.concat([pd.read_csv(f, sep=';', header=None, names=['ts', 'o', 'h', 'l', 'c', 'v']) for f in fs])
    t = pd.to_datetime(x.ts, format='%Y%m%d %H%M%S').dt.tz_localize(TZ['NY'], ambiguous='NaT', nonexistent='NaT')
    x = x.assign(t=t).dropna(subset=['t'])
    m = (x.t.dt.tz_convert('UTC').dt.tz_localize(None) - pd.Timestamp('1970-01-01')) // pd.Timedelta(minutes=1)
    s = pd.DataFrame({'m': m.to_numpy(), 'p': x.c.to_numpy(float)}).drop_duplicates('m').sort_values('m')
    return s.m.to_numpy(np.int64), s.p.to_numpy(float)


def precio(mins, vals, T):
    """cierre de la vela que empieza en [T−TOL, T−1] minutos (termina en o antes de T)."""
    pos = np.searchsorted(mins, T - 1, side='right') - 1
    pc = np.clip(pos, 0, None)
    ok = (pos >= 0) & (T - 1 - mins[pc] <= TOL - 1)
    return np.where(ok, vals[pc], np.nan)


def instantes(dias, zona, h):
    loc = pd.DatetimeIndex([d + pd.Timedelta(hours=h) for d in dias]).tz_localize(TZ[zona], ambiguous='NaT', nonexistent='NaT')
    return ((loc.tz_convert('UTC').tz_localize(None) - pd.Timestamp('1970-01-01')) // pd.Timedelta(minutes=1)).to_numpy()


if __name__ == '__main__':
    dir_fx, dir_hd, salida = sys.argv[1:4]
    dias = pd.bdate_range('2012-01-02', '2026-09-30')
    filas, series = [], {}
    cache_fx, cache_hd = {}, {}
    for par, ses, (z0, h0), (z1, h1), zdia, signo in SESIONES:
        if par not in cache_fx:
            cache_fx[par] = cargar_fxcm(dir_fx, par)
            cache_hd[par] = cargar_histdata(dir_hd, par)
        m, v = cache_fx[par]
        T0, T1 = instantes(dias, z0, h0), instantes(dias, z1, h1)
        # si el fin cae antes del inicio en UTC (no ocurre con estas sesiones), se descarta
        r = pd.Series(np.log(precio(m, v, T1) / precio(m, v, T0)), index=dias) * signo
        r[T1 <= T0] = np.nan
        r = r.dropna()
        series[f'{par}_{ses}'] = r
        anual = r.groupby(r.index.year).mean()
        corr = np.nan
        if cache_hd[par] is not None:
            mh, vh = cache_hd[par]
            rh = pd.Series(np.log(precio(mh, vh, T1) / precio(mh, vh, T0)), index=dias) * signo
            j = pd.concat([r, rh], axis=1, join='inner').dropna()
            corr = j.corr().iat[0, 1]
        t = t_nw(r.values)
        filas.append({'par': par, 'sesion': ses, 'signo': '+' if signo > 0 else '−', 'n': len(r), 'media_pb': r.mean() * 1e4,
                      't': t, 'p_unilateral': 1 - stats.norm.cdf(t), 'años_signo_previsto': f'{(anual > 0).sum()}/{len(anual)}',
                      'n_años_ok': (anual > 0).sum(), 'corr_histdata': corr,
                      'sharpe_bruto': r.mean() / r.std() * np.sqrt(252)})
    f = pd.DataFrame(filas).sort_values('p_unilateral').reset_index(drop=True)
    k = len(f)
    f['umbral_holm_p'] = [0.05 / (k - i) for i in range(k)]
    pasa_holm, sigue = [], True
    for p, u in zip(f.p_unilateral, f.umbral_holm_p):
        sigue = sigue and p <= u
        pasa_holm.append(sigue)
    f['holm'] = pasa_holm
    f['certificada'] = f.holm & (f.n_años_ok >= 9) & ((f.corr_histdata >= 0.9) | f.corr_histdata.isna())
    pd.set_option('display.width', 250); pd.set_option('display.max_columns', 30)
    print(f.drop(columns=['n_años_ok']).round(4).to_string(index=False))
    pd.DataFrame(series).to_csv(salida)
    print('\nCorrelaciones entre sesiones (rentabilidad en el sentido previsto):')
    print(pd.DataFrame(series).corr().round(2).to_string())
