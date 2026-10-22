"""B21 (calendario × hora en cacao y FTSE) y C72 (víspera de festivo en 8 mercados de ICE). Ver PREREGISTRO_B21_C72_ICE.md."""
import os, sys
import numpy as np, pandas as pd
import holidays
from scipy import stats
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'certificacion'))
from c1_certificacion import t_nw
D = '/tmp/claude-0/-home-user-bot-trading/682335b1-28ae-5d18-9355-ce7f0f968722/scratchpad/ice/'
def leer(f):
    x = pd.read_csv(D + f); pub = x.groupby('publisher_id').volume.sum().idxmax(); x = x[(x.publisher_id == pub) & (x.close > 0)]
    x.index = pd.to_datetime(x.ts_event, utc=True); return x[~x.index.duplicated()].sort_index()
FEST_US = {pd.Timestamp(d) for d in holidays.financial_holidays('NYSE', years=range(2018, 2028))}
FEST_UK = {pd.Timestamp(d) for d in holidays.UK(subdiv='ENG', years=range(2018, 2028))}
def pre_dias(F):
    H = pd.bdate_range('2018-01-01', '2027-12-31'); H = H[~H.isin(list(F))]
    return {H[H.searchsorted(f) - 1] for f in F if 0 < H.searchsorted(f) < len(H)}, H
# ---------- C72
print('== C72 víspera de festivo (diario, 2019-2026-09)')
R, PREs = {}, {}
for s, mercado in (('CC', 'US'), ('KC', 'US'), ('SB', 'US'), ('CT', 'US'), ('BRN', 'UK'), ('G', 'UK'), ('Z', 'UK'), ('R', 'UK')):
    x = leer(f'{s}_ohlcv-1d.csv'); x.index = x.index.tz_localize(None).normalize(); x = x[x.index.weekday < 5]
    r = np.log(x.close).diff(); r[x.instrument_id != x.instrument_id.shift()] = np.nan; R[s] = r.loc[:'2026-09-30']
    PREs[s] = pre_dias(FEST_US if mercado == 'US' else FEST_UK)[0]
for s in R:
    v = R[s].reindex(sorted(PREs[s])).dropna(); print(f'   {s}: PRE n {len(v)} {v.mean()*1e4:.1f} pb (t {t_nw(v.values, 2):.2f}) | resto {R[s].drop(v.index, errors="ignore").mean()*1e4:.1f} pb')
cesta = []
for s in ('CC', 'KC', 'SB', 'CT', 'BRN', 'G'): cesta.append(R[s].reindex(sorted(PREs[s])).rename(s))
m = pd.concat(cesta, axis=1).mean(axis=1).dropna(); t = t_nw(m.values, 2); an = m.groupby(m.index.year).sum()
print(f'PRINCIPAL cesta 6 materias primas PRE: n {len(m)} {m.mean()*1e4:.2f} pb (t {t:.2f}) años+ {(an>0).sum()}/{len(an)} → {"PASA" if m.mean() > 0 and t >= 2 else "NO PASA"}')
# ---------- B21
print('\n== B21 calendario × hora en CC y Z (descubrimiento 2019-2022, confirmación 2023-2026-09)')
COSTE = {'CC': 5.0, 'Z': 1.5}; NMIN = {'sem': 200, 'mes': 40, 'esp': 30, 'trim': 12}; filas = []
for s in COSTE:
    x = leer(f'{s}_ohlcv-1h.csv'); fin_b = x.index.tz_convert('America/New_York').tz_localize(None) + pd.Timedelta(hours=1)
    h = pd.DataFrame({'c': x.close.values, 'id': x.instrument_id.values}, index=fin_b).loc[:'2026-09-30']; h = h[h.index.weekday < 5]
    tab = pd.DataFrame({'c': h.c.values, 'id': h.id.values, 'dia': h.index.normalize(), 'hora': h.index.hour})
    piv_c = tab.pivot_table(index='dia', columns='hora', values='c', aggfunc='last'); piv_i = tab.pivot_table(index='dia', columns='hora', values='id', aggfunc='last')
    dias = piv_c.index; mes = dias.to_period('M'); idx = pd.Series(np.arange(len(dias)), index=dias)
    pos = idx.groupby(mes).cumcount().values + 1; fin = idx.groupby(mes).cumcount(ascending=False).values + 1
    qm = np.isin(dias.month, [3, 6, 9, 12]); qn = np.isin(dias.month, [1, 4, 7, 10])
    T = {nd: ('sem', dias.weekday == k) for k, nd in enumerate(['lun', 'mar', 'mié', 'jue', 'vie'])}
    for k, nd in ((3, 'D-2'), (2, 'D-1'), (1, 'D0')): T[nd] = ('mes', fin == k); T['Q' + nd[1:]] = ('trim', (fin == k) & qm)
    for k, nd in ((1, 'D+1'), (2, 'D+2')): T[nd] = ('mes', pos == k); T['Q' + nd[1:]] = ('trim', (pos == k) & qn)
    PRE, H = pre_dias(FEST_US if s == 'CC' else FEST_UK)
    POST = {H[H.searchsorted(f)] for f in (FEST_US if s == 'CC' else FEST_UK) if 0 < H.searchsorted(f) < len(H)}
    T['PRE'] = ('esp', dias.isin(list(PRE))); T['POST'] = ('esp', dias.isin(list(POST)))
    for h0 in range(23):
        h1 = h0 + 1
        if h0 not in piv_c or h1 not in piv_c: continue
        r = np.log(piv_c[h1] / piv_c[h0]); r[piv_i[h1] != piv_i[h0]] = np.nan
        for nd, (fam, msk) in T.items():
            q = r[msk].dropna(); dsc, cf = q.loc['2019':'2022'], q.loc['2023':'2026']
            if len(dsc) < NMIN[fam] or len(cf) < NMIN[fam]: continue
            filas.append(dict(mercado=s, dia=nd, inicio=h0, n_d=len(dsc), m_d=dsc.mean() * 1e4, t_d=t_nw(dsc.values), n_c=len(cf), m_c=cf.mean() * 1e4,
                              t_c=t_nw(cf.values), años=(np.sign(cf.groupby(cf.index.year).mean()) == np.sign(dsc.mean())).mean(), coste=COSTE[s]))
t = pd.DataFrame(filas); t.to_csv('b21_todas.csv', index=False)
sel = t[t.t_d.abs() >= 3.5].copy(); k = max(len(sel), 1); u = stats.norm.ppf(1 - 0.05 / k)
sel['t_c_s'] = sel.t_c * np.sign(sel.m_d); sel['m_c_s'] = sel.m_c * np.sign(sel.m_d)
sel['pasa'] = (sel.t_c_s >= u) & (sel.años >= 0.6) & (sel.m_c_s >= 3 * sel.coste)
print(f'reglas {len(t)}; seleccionadas {len(sel)}; umbral {u:.2f}')
pd.set_option('display.width', 220)
print(sel.sort_values('t_c_s', ascending=False)[['mercado', 'dia', 'inicio', 'n_d', 'm_d', 't_d', 'n_c', 'm_c', 't_c', 'años', 'coste', 'pasa']].round(2).to_string(index=False))
