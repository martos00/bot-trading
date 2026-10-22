"""B14: calendario × hora (4 familias) en NKD, BTC, ZT, ZF, 6Z, 6L. Ver PREREGISTRO_B14.
Uso: python3 b14_mercados_nuevos.py DIR_H1 ES_1m.pkl"""
import glob, os, sys
import numpy as np, pandas as pd
import holidays
FEST = {pd.Timestamp(d) for d in holidays.financial_holidays('NYSE', years=range(2009, 2028))}
HAB = pd.bdate_range('2009-01-01', '2027-12-31'); HAB = HAB[~HAB.isin(list(FEST))]
from scipy import stats
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'certificacion'))
from c1_certificacion import t_nw
H, ES = sys.argv[1:3]
COSTE = {'NKD': 2.5, 'BTC': 2.0, 'ZT': 0.8, 'ZF': 1.2, '6Z': 3.0, '6L': 4.0}
def horario(s):
    """cierres horarios (índice = fin de la barra, hora NY) con contrato."""
    if s == 'ES':
        x = pd.read_pickle(ES); t = pd.to_datetime(x.ts_event).dt.tz_convert('America/New_York').dt.tz_localize(None) + pd.Timedelta(minutes=1)
        x = x.assign(t=t.dt.ceil('h')).groupby('t').agg(c=('close', 'last'), id=('instrument_id', 'last'))
        return x
    x = pd.concat([pd.read_csv(f) for f in sorted(glob.glob(os.path.join(H, f'{s}_*.csv')))])
    x['close'] = pd.to_numeric(x.close, errors='coerce'); x['ts_event'] = pd.to_datetime(x.ts_event, utc=True, errors='coerce')
    x = x[x.close.notna() & x.ts_event.notna() & (x.close > 0)].drop_duplicates('ts_event')
    fin = x.ts_event.dt.tz_convert('America/New_York').dt.tz_localize(None) + pd.Timedelta(hours=1)
    return pd.DataFrame({'c': x.close.values, 'id': x.instrument_id.values}, index=fin).sort_index()
filas = []
NMIN = {'sem': 200, 'mes': 80, 'esp': 60, 'trim': 25}
for s in COSTE:
    h = horario(s).loc[:'2026-09-30']; h = h[h.index.weekday < 5]
    tabla = pd.DataFrame({'c': h.c.values, 'id': h.id.values, 'dia': h.index.normalize(), 'hora': h.index.hour})
    piv_c = tabla.pivot_table(index='dia', columns='hora', values='c', aggfunc='last')
    piv_i = tabla.pivot_table(index='dia', columns='hora', values='id', aggfunc='last')
    dias = piv_c.index; mes = dias.to_period('M'); idx = pd.Series(np.arange(len(dias)), index=dias)
    pos = idx.groupby(mes).cumcount().values + 1; fin = idx.groupby(mes).cumcount(ascending=False).values + 1
    qm = np.isin(dias.month, [3, 6, 9, 12]); qn = np.isin(dias.month, [1, 4, 7, 10])
    T = {}
    for wd, nd in enumerate(['lun', 'mar', 'mié', 'jue', 'vie']): T[nd] = ('sem', dias.weekday == wd)
    for k, nd in ((3, 'D-2'), (2, 'D-1'), (1, 'D0')): T[nd] = ('mes', fin == k)
    for k, nd in ((1, 'D+1'), (2, 'D+2')): T[nd] = ('mes', pos == k)
    for k, nd in ((3, 'Q-2'), (2, 'Q-1'), (1, 'Q0')): T[nd] = ('trim', (fin == k) & qm)
    for k, nd in ((1, 'Q+1'), (2, 'Q+2')): T[nd] = ('trim', (pos == k) & qn)
    esp = pd.Series('', index=dias)
    for f in FEST:
        i = HAB.searchsorted(f)
        if 0 < i < len(HAB):
            if HAB[i - 1] in esp.index: esp[HAB[i - 1]] = 'PRE'
            if HAB[i] in esp.index: esp[HAB[i]] = 'POST'
    for m in pd.period_range('2010-01', '2026-09', freq='M'):
        vie = pd.date_range(m.start_time, m.end_time, freq='W-FRI')[2]
        while vie not in HAB: vie -= pd.Timedelta(days=1)
        lun = vie + pd.Timedelta(days=3)
        if vie in esp.index and esp[vie] == '': esp[vie] = 'OPEX'
        if lun in esp.index and esp[lun] == '': esp[lun] = 'POSTOPEX'
        d15 = HAB[HAB.searchsorted(m.start_time + pd.Timedelta(days=14))]
        if d15 in esp.index and esp[d15] == '': esp[d15] = 'D15'
    for nd in ('PRE', 'POST', 'OPEX', 'POSTOPEX', 'D15'): T[nd] = ('esp', (esp == nd).values)
    d0, d1, c0 = ('2018', '2021', '2022') if s == 'BTC' else ('2010', '2017', '2018')
    for h0 in range(23):
        h1 = h0 + 1
        if h0 == 17 or h1 == 18 or h0 not in piv_c or h1 not in piv_c: continue
        r = np.log(piv_c[h1] / piv_c[h0]); r[piv_i[h1] != piv_i[h0]] = np.nan
        for nd, (fam, msk) in T.items():
            q = r[msk].dropna(); dsc, cf = q.loc[d0:d1], q.loc[c0:'2026']
            if len(dsc) < NMIN[fam] or len(cf) < NMIN[fam] // 2: continue
            filas.append(dict(mercado=s, dia=nd, inicio=h0, n_d=len(dsc), m_d=dsc.mean() * 1e4, t_d=t_nw(dsc.values), n_c=len(cf), m_c=cf.mean() * 1e4,
                              t_c=t_nw(cf.values), años=(np.sign(cf.groupby(cf.index.year).mean()) == np.sign(dsc.mean())).mean(), coste=COSTE[s]))
t = pd.DataFrame(filas); t.to_csv('b14_todas.csv', index=False)
print(f'reglas evaluadas: {len(t)}')
sel = t[t.t_d.abs() >= 3.5].copy(); k = max(len(sel), 1); umbral = stats.norm.ppf(1 - 0.05 / k)
sel['t_c_s'] = sel.t_c * np.sign(sel.m_d); sel['m_c_s'] = sel.m_c * np.sign(sel.m_d)
sel['pasa'] = (sel.t_c_s >= umbral) & (sel.años >= 0.6) & (sel.m_c_s >= 3 * sel.coste)
print(f'seleccionadas (|t| >= 3,5): {len(sel)}; umbral Bonferroni: t >= {umbral:.2f}')
pd.set_option('display.width', 220)
print(sel.sort_values('t_c_s', ascending=False)[['mercado', 'dia', 'inicio', 'n_d', 'm_d', 't_d', 'n_c', 'm_c', 't_c', 'años', 'coste', 'pasa']].round(2).to_string(index=False))
