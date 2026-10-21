"""R1 — ¿depende la ventaja C1 del régimen? (PREREGISTRO_R1_regimenes_eurusd.md)
Uso: python3 r1_regimenes_eurusd.py H80_EURUSD.csv c1_precios.csv DIR_HISTDATA_EURUSD"""
import glob, os, sys
import numpy as np
import pandas as pd
from scipy import stats
from c1_certificacion import t_nw

h80, c1f, dhd = sys.argv[1:4]
desc = (-pd.read_csv(h80, index_col=0, parse_dates=True)['h06_d2']).loc['2010':'2017']
c1 = pd.read_csv(c1f, index_col=0, parse_dates=True)
conf = (-np.log(c1.mid8 / c1.mid6)).loc['2018':'2026-09']
r = pd.concat([desc, conf]).dropna()
r = r[~r.index.duplicated()]

# cierre diario (último minuto del día de NY) de HistData
fs = sorted(glob.glob(os.path.join(dhd, 'DAT_ASCII_EURUSD_M1_*.csv')))
x = pd.concat([pd.read_csv(f, sep=';', header=None, names=['ts', 'o', 'h', 'l', 'c', 'v'], usecols=[0, 4]) for f in fs])
x['dia'] = pd.to_datetime(x.ts.str[:8], format='%Y%m%d')
cierre = x.groupby('dia').c.last()
cierre = cierre[cierre.index.weekday < 5]
sma = cierre.rolling(200).mean()
alcista = (cierre > sma).shift(1).reindex(r.index, method='ffill')

# volatilidad: σ de 60 días anteriores frente a su mediana expandida hasta el día anterior
sig = r.rolling(60).std().shift(1)
med = sig.expanding(250).median().shift(1)
alta = (sig > med).where(med.notna())
d = pd.DataFrame({'r': r, 'alta_vol': alta, 'alcista': alcista}).dropna()
d['alta_vol'] = d.alta_vol.astype(bool); d['alcista'] = d.alcista.astype(bool)


def dif(sub, var):
    a, b = sub[sub[var]].r, sub[~sub[var]].r
    t, _ = stats.ttest_ind(a, b, equal_var=False)
    return a.mean() * 1e4, b.mean() * 1e4, len(a), len(b), t


COSTE = 0.53e-4
for var, (si, no) in {'alta_vol': ('volatilidad alta', 'volatilidad baja'), 'alcista': ('tendencia alcista', 'tendencia bajista')}.items():
    print(f'\n=== {var} ===')
    res = {}
    for nom, sl in (('descubrimiento 2010-2017', slice('2010', '2017')), ('confirmación 2018-2026', slice('2018', '2026'))):
        ma, mb, na, nb, t = dif(d.loc[sl], var)
        res[nom] = (ma, mb, t)
        print(f'  {nom}: {si} {ma:+.2f} pb (n {na}) | {no} {mb:+.2f} pb (n {nb}) | diferencia t = {t:+.2f}')
    ma, mb, t = res['descubrimiento 2010-2017']
    c1_ok = abs(t) >= 2.5
    bueno = var if ma > mb else None
    cc = d.loc['2018':'2026']
    mc, mbc, tc = res['confirmación 2018-2026']
    signo_ok = (mc - mbc) * (ma - mb) > 0 and abs(tc) >= 2.0
    filtro = cc[cc[var]] if ma > mb else cc[~cc[var]]
    sr_f = ((filtro.r - COSTE).mean() / (filtro.r - COSTE).std()) * np.sqrt(252) * np.sqrt(len(filtro) / len(cc))
    sr_t = ((cc.r - COSTE).mean() / (cc.r - COSTE).std()) * np.sqrt(252)
    print(f'  Criterio 1 (|t| ≥ 2,5 en descubrimiento): {"CUMPLE" if c1_ok else "NO CUMPLE"}')
    print(f'  Criterio 2 (mismo sentido, t ≥ 2 en confirmación): {"CUMPLE" if signo_ok else "NO CUMPLE"}')
    print(f'  Criterio 3: Sharpe neto confirmación con filtro {sr_f:.2f} (anualizado sobre todos los días) frente a sin filtro {sr_t:.2f}: '
          f'{"CUMPLE" if sr_f > sr_t else "NO CUMPLE"}')
    print('  → FILTRO ADOPTADO' if c1_ok and signo_ok and sr_f > sr_t else '  → sin filtro')
print('\nInformativo: media (pb) por régimen combinado')
for nom, sl in (('2010-2017', slice('2010', '2017')), ('2018-2026', slice('2018', '2026'))):
    g = d.loc[sl].groupby(['alta_vol', 'alcista']).r.agg(['mean', 'count'])
    g['mean'] *= 1e4
    print(nom, {f"{'vol alta' if a else 'vol baja'}/{'alcista' if b else 'bajista'}": f"{v['mean']:+.2f} (n {int(v['count'])})" for (a, b), v in g.iterrows()})
