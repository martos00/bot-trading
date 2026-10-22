"""B16: calendario × hora en 6 criptomonedas (Binance 1 h, UTC). Ver PREREGISTRO_B16_cripto_calendario.md."""
import glob, io, os, sys, zipfile
import numpy as np, pandas as pd
from scipy import stats
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'certificacion'))
from c1_certificacion import t_nw
D = '/tmp/claude-0/-home-user-bot-trading/682335b1-28ae-5d18-9355-ce7f0f968722/scratchpad/binance/'
COSTE = {'BTCUSDT': 10, 'ETHUSDT': 10, 'LTCUSDT': 20, 'XRPUSDT': 20, 'BNBUSDT': 20, 'ADAUSDT': 20}
NMIN = {'sem': 100, 'mes': 30, 'trim': 10}
def carga(s):
    trozos = []
    for f in sorted(glob.glob(D + f'{s}-1h-*.zip')):
        z = zipfile.ZipFile(f); x = pd.read_csv(z.open(z.namelist()[0]), header=None, usecols=[0, 4])
        x = x[pd.to_numeric(x[0], errors='coerce').notna()]; ts = x[0].astype('int64')
        ts = np.where(ts > 1e14, ts // 1000, ts)                      # 2025+: microsegundos
        trozos.append(pd.Series(x[4].astype(float).values, index=pd.to_datetime(ts, unit='ms')))
    c = pd.concat(trozos).sort_index(); return c[~c.index.duplicated()]
filas = []
for s, coste in COSTE.items():
    c = carga(s); r = np.log(c).diff(); r = r[(r.index.to_series().diff() == pd.Timedelta(hours=1)).values]  # rentabilidad de la hora que empieza en t−1h
    r.index = r.index - pd.Timedelta(hours=1)                                                               # índice = inicio de la franja
    dia = r.index.normalize(); mes = dia.to_period('M')
    dl = pd.Series(pd.DatetimeIndex(sorted(set(dia))), dtype='datetime64[ns]')
    ult = pd.Series(dl.values, index=dl.values).groupby(pd.DatetimeIndex(dl.values).to_period('M')).transform('max')
    pri = pd.Series(dl.values, index=dl.values).groupby(pd.DatetimeIndex(dl.values).to_period('M')).transform('min')
    fin = ((ult - pd.Series(dl.values, index=dl.values)).dt.days + 1).reindex(dia).values
    pos = ((pd.Series(dl.values, index=dl.values) - pri).dt.days + 1).reindex(dia).values
    qm = np.isin(dia.month, [3, 6, 9, 12]); qn = np.isin(dia.month, [1, 4, 7, 10])
    T = {nd: ('sem', dia.weekday == k) for k, nd in enumerate(['lun', 'mar', 'mié', 'jue', 'vie', 'sáb', 'dom'])}
    for k, nd in ((3, 'D-2'), (2, 'D-1'), (1, 'D0')): T[nd] = ('mes', fin == k); T['Q' + nd[1:]] = ('trim', (fin == k) & qm)
    for k, nd in ((1, 'D+1'), (2, 'D+2')): T[nd] = ('mes', pos == k); T['Q' + nd[1:]] = ('trim', (pos == k) & qn)
    for h in range(24):
        rh = r[r.index.hour == h]; m_h = {nd: msk[r.index.hour == h] for nd, (fam, msk) in T.items()}
        for nd, (fam, _) in T.items():
            q = rh[m_h[nd]]; dsc, cf = q.loc['2018':'2021'], q.loc['2022':'2026-09']
            if len(dsc) < NMIN[fam] or len(cf) < NMIN[fam]: continue
            filas.append(dict(mercado=s, dia=nd, inicio_utc=h, n_d=len(dsc), m_d=dsc.mean() * 1e4, t_d=t_nw(dsc.values), n_c=len(cf), m_c=cf.mean() * 1e4,
                              t_c=t_nw(cf.values), años=(np.sign(cf.groupby(cf.index.year).mean()) == np.sign(dsc.mean())).mean(), coste=coste))
    print(s, 'hecho', flush=True)
t = pd.DataFrame(filas); t.to_csv('b16_todas.csv', index=False)
print(f'reglas evaluadas: {len(t)}')
sel = t[t.t_d.abs() >= 3.5].copy(); k = max(len(sel), 1); umbral = stats.norm.ppf(1 - 0.05 / k)
sel['t_c_s'] = sel.t_c * np.sign(sel.m_d); sel['m_c_s'] = sel.m_c * np.sign(sel.m_d)
sel['pasa'] = (sel.t_c_s >= umbral) & (sel.años >= 0.6) & (sel.m_c_s >= 3 * sel.coste)
print(f'seleccionadas (|t| >= 3,5): {len(sel)}; umbral Bonferroni: t >= {umbral:.2f}')
pd.set_option('display.width', 220)
print(sel.sort_values('t_c_s', ascending=False)[['mercado', 'dia', 'inicio_utc', 'n_d', 'm_d', 't_d', 'n_c', 'm_c', 't_c', 'años', 'coste', 'pasa']].round(2).to_string(index=False))
