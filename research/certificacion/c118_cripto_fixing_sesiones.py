"""C118 (PREREGISTRO_C118_cripto_fixing_y_sesiones.md). Uso: python3 c118_cripto_fixing_sesiones.py DIR_SCRATCH"""
import sys, io, glob, zipfile, numpy as np, pandas as pd, holidays
SP = sys.argv[1]
def carga(pat):
    rows = []
    for f in sorted(glob.glob(pat)):
        with zipfile.ZipFile(f) as z: rows.append(pd.read_csv(io.BytesIO(z.read(z.namelist()[0])), header=None, usecols=[0, 1]))
    b = pd.concat(rows); t = b[0].astype('int64'); t = np.where(t > 1e14, t // 1000, t)
    o = pd.Series(b[1].astype(float).values, index=pd.to_datetime(t, unit='ms', utc=True)); return o[~o.index.duplicated()].sort_index()
def tst(x): x = x.dropna(); return x.mean() * 1e4, x.mean() / x.std() * np.sqrt(len(x)), len(x)
btc = carga(f'{SP}/bn/1h/BTCUSDT-1h-*.zip'); eth = carga(f'{SP}/bn/eth1h/ETHUSDT-1h-*.zip')
# F1: apertura de la vela de las 15:00 NY y de las 16:00 NY
ny = btc.copy(); ny.index = ny.index.tz_convert('America/New_York')
fest = holidays.financial_holidays('NYSE', years=range(2020, 2027))
p15 = ny[ny.index.hour == 15]; p16 = ny[ny.index.hour == 16]
p15.index = p15.index.normalize(); p16.index = p16.index.normalize()
d = pd.DataFrame({'p15': p15, 'p16': p16}).dropna()
d = d[[x.weekday() < 5 and x.date() not in fest for x in d.index]]
d['prev16'] = d.p16.shift(1)                       # 16:00 del día hábil anterior
d['senal'] = np.sign(np.log(d.p15 / d.prev16)); d['r'] = np.log(d.p16 / d.p15)
d['neto'] = d.senal * d.r - 1.2e-4
for nom, a, b_ in (('F1 2024-01-11 → final (PRINCIPAL)', '2024-01-11', None), ('F1 informativo 2021-2023 (antes de los ETF)', '2021-01-01', '2023-12-31')):
    m, t, n = tst(d.neto.loc[a:b_]); print(f'{nom:45s} neto {m:+.2f} pb (t {t:.2f}, n {n}) {"PASA" if "PRINCIPAL" in nom and t >= 2.13 and m > 0 else ""}')
# R1 / R2: sesiones de 12 h
def sesiones(o, h0, coste, regla_noche):
    p = o[o.index.hour.isin([h0, (h0 + 12) % 24])]
    r = np.log(p / p.shift(1)).dropna()                  # cada fila: rentabilidad de la sesión que TERMINA a esa hora
    r = r[(r.index.to_series().diff().dt.total_seconds() == 43200).values]
    ini = (r.index - pd.Timedelta(hours=12)).hour
    dia = ini == h0                                      # sesión de día empieza a h0
    prev = r.shift(1)
    pos = pd.Series(np.where(dia, -np.sign(prev), (-np.sign(prev) if regla_noche == 'rev' else 1.0)), index=r.index)
    ok = r.index.to_series().diff().dt.total_seconds().values == 43200
    return (pos * r - coste)[ok]
for nom, o, h0, c, rn in (('R1 BTC rev/rev 08:00 UTC', btc, 8, 1.2e-4, 'rev'), ('R2 ETH día rev / noche largo 05:00 UTC', eth, 5, 1.5e-4, 'largo')):
    x = sesiones(o, h0, c, rn)
    m, t, n = tst(x.loc['2025-10-01':]); m2, t2, n2 = tst(x.loc['2017-01-01':'2025-09-30'])
    print(f'{nom:45s} FUERA de muestra 2025-10 →: neto {m:+.2f} pb/sesión (t {t:.2f}, n {n}) {"PASA" if t >= 2.13 and m > 0 else "NO PASA"} | informativo 2017-2025: {m2:+.2f} pb (t {t2:.2f})')
print('datos BTC hasta', btc.index[-1], 'ETH hasta', eth.index[-1])
