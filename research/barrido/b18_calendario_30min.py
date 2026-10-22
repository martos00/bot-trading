"""B18: calendario × 30 min en GC, SI (1 min Databento) y ES. Ver PREREGISTRO_B18_calendario_30min.md."""
import glob, os, sys
import numpy as np, pandas as pd
import holidays
from scipy import stats
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'certificacion'))
from c1_certificacion import t_nw
S = '/tmp/claude-0/-home-user-bot-trading/682335b1-28ae-5d18-9355-ce7f0f968722/scratchpad/'
COSTE = {'GC': 0.74, 'SI': 2.3, 'ES': 0.73}
NMIN = {'sem': 200, 'mes': 80, 'esp': 60, 'trim': 25}
FEST = {pd.Timestamp(d) for d in holidays.financial_holidays('NYSE', years=range(2009, 2028))}
HAB = pd.bdate_range('2009-01-01', '2027-12-31'); HAB = HAB[~HAB.isin(list(FEST))]
def minutos(s):
    if s == 'ES':
        x = pd.read_pickle(S + 'databento/ES_1m.pkl')
    else:
        x = pd.concat([pd.read_csv(f, usecols=['ts_event', 'instrument_id', 'close']) for f in sorted(glob.glob(S + f'm1/{s}_*.csv'))])
    t = pd.to_datetime(x.ts_event, utc=True).dt.tz_convert('America/New_York').dt.tz_localize(None)
    y = pd.DataFrame({'c': pd.to_numeric(x.close, errors='coerce').values, 'id': x.instrument_id.values}, index=t + pd.Timedelta(minutes=1))   # índice = fin del minuto
    y = y[y.c > 0]; y = y[~y.index.duplicated()].sort_index()
    return y.groupby(y.index.ceil('30min')).last()                   # precio en cada frontera de 30 min = último cierre del tramo previo
filas = []
for s in COSTE:
    b = minutos(s).loc['2010-06-01':'2026-09-30']; b = b[b.index.weekday < 5]
    tab = pd.DataFrame({'c': b.c.values, 'id': b.id.values, 'dia': b.index.normalize(), 'slot': b.index.hour * 100 + b.index.minute})
    piv_c = tab.pivot_table(index='dia', columns='slot', values='c', aggfunc='last'); piv_i = tab.pivot_table(index='dia', columns='slot', values='id', aggfunc='last')
    dias = piv_c.index; mes = dias.to_period('M'); idx = pd.Series(np.arange(len(dias)), index=dias)
    pos = idx.groupby(mes).cumcount().values + 1; fin = idx.groupby(mes).cumcount(ascending=False).values + 1
    qm = np.isin(dias.month, [3, 6, 9, 12]); qn = np.isin(dias.month, [1, 4, 7, 10])
    T = {nd: ('sem', dias.weekday == k) for k, nd in enumerate(['lun', 'mar', 'mié', 'jue', 'vie'])}
    for k, nd in ((3, 'D-2'), (2, 'D-1'), (1, 'D0')): T[nd] = ('mes', fin == k); T['Q' + nd[1:]] = ('trim', (fin == k) & qm)
    for k, nd in ((1, 'D+1'), (2, 'D+2')): T[nd] = ('mes', pos == k); T['Q' + nd[1:]] = ('trim', (pos == k) & qn)
    esp = pd.Series('', index=dias)
    for f in FEST:
        i = HAB.searchsorted(f)
        if 0 < i < len(HAB):
            if HAB[i - 1] in esp.index: esp[HAB[i - 1]] = 'PRE'
            if HAB[i] in esp.index: esp[HAB[i]] = 'POST'
    for m in pd.period_range('2010-06', '2026-09', freq='M'):
        vie = pd.date_range(m.start_time, m.end_time, freq='W-FRI')[2]
        while vie not in HAB: vie -= pd.Timedelta(days=1)
        lun = vie + pd.Timedelta(days=3)
        if vie in esp.index and esp[vie] == '': esp[vie] = 'OPEX'
        if lun in esp.index and esp[lun] == '': esp[lun] = 'POSTOPEX'
        d15 = HAB[HAB.searchsorted(m.start_time + pd.Timedelta(days=14))]
        if d15 in esp.index and esp[d15] == '': esp[d15] = 'D15'
    for nd in ('PRE', 'POST', 'OPEX', 'POSTOPEX', 'D15'): T[nd] = ('esp', (esp == nd).values)
    slots = [h * 100 + m for h in range(24) for m in (0, 30)]
    for a, b2 in zip(slots[:-1], slots[1:]):
        if 1700 <= a < 1800 or a >= 2300 or a not in piv_c or b2 not in piv_c: continue
        r = np.log(piv_c[b2] / piv_c[a]); r[piv_i[b2] != piv_i[a]] = np.nan
        for nd, (fam, msk) in T.items():
            q = r[msk].dropna(); dsc, cf = q.loc['2010':'2017'], q.loc['2018':'2026']
            if len(dsc) < NMIN[fam] or len(cf) < NMIN[fam] // 2: continue
            filas.append(dict(mercado=s, dia=nd, inicio=f'{a:04d}', n_d=len(dsc), m_d=dsc.mean() * 1e4, t_d=t_nw(dsc.values), n_c=len(cf), m_c=cf.mean() * 1e4,
                              t_c=t_nw(cf.values), años=(np.sign(cf.groupby(cf.index.year).mean()) == np.sign(dsc.mean())).mean(), coste=COSTE[s]))
    print(s, 'hecho', flush=True)
t = pd.DataFrame(filas); t.to_csv('b18_todas.csv', index=False)
CONTROL = lambda f: (f.mercado == 'GC' and f.dia == 'vie' and f.inicio in ('1600', '1630')) or (f.mercado in ('GC', 'SI') and f.dia == 'PRE' and f.inicio in ('1600', '1630'))
print(f'reglas evaluadas: {len(t)}')
sel = t[t.t_d.abs() >= 4.0].copy(); k = max(len(sel), 1); umbral = stats.norm.ppf(1 - 0.05 / k)
sel['t_c_s'] = sel.t_c * np.sign(sel.m_d); sel['m_c_s'] = sel.m_c * np.sign(sel.m_d)
sel['pasa'] = (sel.t_c_s >= umbral) & (sel.años >= 0.6) & (sel.m_c_s >= 3 * sel.coste)
sel['control'] = sel.apply(CONTROL, axis=1)
print(f'seleccionadas (|t| >= 4,0): {len(sel)}; umbral Bonferroni: t >= {umbral:.2f}')
pd.set_option('display.width', 230)
print(sel.sort_values('t_c_s', ascending=False)[['mercado', 'dia', 'inicio', 'n_d', 'm_d', 't_d', 'n_c', 'm_c', 't_c', 'años', 'coste', 'pasa', 'control']].round(2).to_string(index=False))
