"""B19: calendario × 30 min en 13 pares FXCM con BID/ASK reales. Ver PREREGISTRO_B19."""
import glob, os, sys
import numpy as np, pandas as pd
import holidays
FEST = {pd.Timestamp(d) for d in holidays.financial_holidays('NYSE', years=range(2011, 2028))}
HAB = pd.bdate_range('2011-01-01', '2027-12-31'); HAB = HAB[~HAB.isin(list(FEST))]
from scipy import stats
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'certificacion'))
from c1_certificacion import t_nw
S = '/tmp/claude-0/-home-user-bot-trading/682335b1-28ae-5d18-9355-ce7f0f968722/scratchpad/fxcm/'
PARES = ['EURUSD', 'GBPUSD', 'USDJPY', 'USDCHF', 'AUDUSD', 'USDCAD', 'EURGBP', 'EURCHF', 'EURJPY', 'GBPJPY', 'EURAUD', 'EURNZD', 'GBPCAD']
COM = 0.45
SEMANA = {'lun': 0, 'mar': 1, 'mié': 2, 'jue': 3, 'vie': 4}
filas = []
for p in PARES:
    trozos = []
    for f in sorted(glob.glob(S + f'{p}/{p}_*.csv.gz')):
        x = pd.read_csv(f, compression='gzip', usecols=['DateTime', 'BidClose', 'AskClose'])
        t = pd.to_datetime(x.DateTime, format='%m/%d/%Y %H:%M:%S.%f')
        x = x[t.dt.minute.isin([29, 59])].assign(t=t[t.dt.minute.isin([29, 59])] + pd.Timedelta(minutes=1))
        trozos.append(x)
    x = pd.concat(trozos).drop_duplicates('t')
    x.index = x.t.dt.tz_localize('UTC').dt.tz_convert('America/New_York').dt.tz_localize(None)
    x = x[x.index.weekday < 5].sort_index()
    x['BidClose'] = pd.to_numeric(x.BidClose, errors='coerce'); x['AskClose'] = pd.to_numeric(x.AskClose, errors='coerce'); x = x[(x.BidClose > 0) & (x.AskClose > 0)]
    mid = (x.BidClose + x.AskClose) / 2; spr = (x.AskClose - x.BidClose) / mid * 1e4
    df = pd.DataFrame({'mid': mid.values, 'spr': spr.values, 'dia': x.index.normalize(), 'h': x.index.hour * 100 + x.index.minute})
    M = df.pivot_table(index='dia', columns='h', values='mid', aggfunc='last'); P = df.pivot_table(index='dia', columns='h', values='spr', aggfunc='last')
    dias = M.index; mes = dias.to_period('M')
    pos = pd.Series(np.arange(len(dias)), index=dias).groupby(mes).cumcount().values + 1
    fin = pd.Series(np.arange(len(dias)), index=dias).groupby(mes).cumcount(ascending=False).values + 1
    T1 = pd.Series('', index=dias); T1[fin == 3] = 'D-2'; T1[fin == 2] = 'D-1'; T1[fin == 1] = 'D0'; T1[pos == 1] = 'D+1'; T1[pos == 2] = 'D+2'
    T2 = pd.Series('', index=dias)
    qm = np.isin(dias.month, [3, 6, 9, 12]); qn = np.isin(dias.month, [1, 4, 7, 10])
    TQ = pd.Series('', index=dias); TQ[(fin == 3) & qm] = 'Q-2'; TQ[(fin == 2) & qm] = 'Q-1'; TQ[(fin == 1) & qm] = 'Q0'; TQ[(pos == 1) & qn] = 'Q+1'; TQ[(pos == 2) & qn] = 'Q+2'
    for f in FEST:
        i = HAB.searchsorted(f)
        if 0 < i < len(HAB):
            if HAB[i - 1] in T2.index: T2[HAB[i - 1]] = 'PRE'
            if HAB[i] in T2.index: T2[HAB[i]] = 'POST'
    for m in pd.period_range('2012-01', '2026-09', freq='M'):
        vie = pd.date_range(m.start_time, m.end_time, freq='W-FRI')[2]
        while vie not in HAB: vie -= pd.Timedelta(days=1)
        lun = vie + pd.Timedelta(days=3)
        if vie in T2.index and T2[vie] == '': T2[vie] = 'OPEX'
        if lun in T2.index and T2[lun] == '': T2[lun] = 'POSTOPEX'
        d15 = HAB[HAB.searchsorted(m.start_time + pd.Timedelta(days=14))]
        if d15 in T2.index and T2[d15] == '': T2[d15] = 'D15'
    SL = [h * 100 + m for h in range(24) for m in (0, 30)]
    for h0, h1 in zip(SL[:-1], SL[1:]):
        if 1600 <= h0 < 1800 or h0 >= 2300 or h0 not in M or h1 not in M: continue
        r = np.log((M[h1] / M[h0]).astype(float)); c = (P[h0] + P[h1]) / 2 + COM; ok = r.notna() & c.notna(); r, c = r[ok], c[ok]
        for nd in ('lun', 'mar', 'mié', 'jue', 'vie', 'D-2', 'D-1', 'D0', 'D+1', 'D+2', 'Q-2', 'Q-1', 'Q0', 'Q+1', 'Q+2', 'PRE', 'POST', 'OPEX', 'POSTOPEX', 'D15'):
            if nd in SEMANA: msk = r.index.weekday == SEMANA[nd]
            elif nd.startswith('Q'): msk = TQ.reindex(r.index).values == nd
            else:
                TT = T1 if nd.startswith('D') and nd != 'D15' else T2
                msk = TT.reindex(r.index).values == nd
            q = r[msk]; cq = c[msk]
            dsc, cf = q.loc['2012':'2018'], q.loc['2019':'2026']
            if len(dsc) < {'lun': 200, 'mar': 200, 'mié': 200, 'jue': 200, 'vie': 200, 'D-2': 80, 'D-1': 80, 'D0': 80, 'D+1': 80, 'D+2': 80, 'Q-2': 25, 'Q-1': 25, 'Q0': 25, 'Q+1': 25, 'Q+2': 25}.get(nd, 60) or len(cf) < 20: continue
            filas.append(dict(par=p, dia=nd, inicio=h0, n_d=len(dsc), m_d=dsc.mean() * 1e4, t_d=t_nw(dsc.values), n_c=len(cf), m_c=cf.mean() * 1e4,
                              t_c=t_nw(cf.values), años=(np.sign(cf.groupby(cf.index.year).mean()) == np.sign(dsc.mean())).mean(), coste=cq.loc['2019':].mean()))
    pass
t = pd.DataFrame(filas); t.to_csv('b19_todas.csv', index=False)
print(f'reglas evaluadas: {len(t)}')
sel = t[t.t_d.abs() >= 4.0].copy(); k = max(len(sel), 1); umbral = stats.norm.ppf(1 - 0.05 / k)
sel['t_c_s'] = sel.t_c * np.sign(sel.m_d); sel['m_c_s'] = sel.m_c * np.sign(sel.m_d)
sel['pasa'] = (sel.t_c_s >= umbral) & (sel.años >= 0.6) & (sel.m_c_s >= 3 * sel.coste)
print(f'seleccionadas en 2012-18 (|t| >= 4,0): {len(sel)}; umbral Bonferroni 2019-26: t >= {umbral:.2f}')
pd.set_option('display.width', 220)
print(sel.sort_values('t_c_s', ascending=False)[['par', 'dia', 'inicio', 'm_d', 't_d', 'm_c', 't_c', 'años', 'coste', 'pasa']].round(2).to_string(index=False))
