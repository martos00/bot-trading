"""B20: últimas medias horas antes del cierre (viernes y vísperas) en 16 futuros a 1 minuto. Ver PREREGISTRO_B20."""
import glob, os, sys
import numpy as np, pandas as pd
import holidays
from scipy import stats
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'certificacion'))
from c1_certificacion import t_nw
D = '/tmp/claude-0/-home-user-bot-trading/682335b1-28ae-5d18-9355-ce7f0f968722/scratchpad/b20/'
COSTE = {'PL': 3.5, 'PA': 6.0, 'HG': 1.65, 'CL': 2.0, 'NG': 4.7, 'HO': 2.5, 'RB': 3.0, 'ZN': 1.8, 'ZB': 2.7, '6J': 1.2, '6S': 1.4, '6E': 0.75, '6A': 1.3, 'NQ': 0.3, 'YM': 0.8, 'RTY': 1.2}
FEST = {pd.Timestamp(d) for d in holidays.financial_holidays('NYSE', years=range(2009, 2028))}
HAB = pd.bdate_range('2009-01-01', '2027-12-31'); HAB = HAB[~HAB.isin(list(FEST))]
PRE = {HAB[HAB.searchsorted(f) - 1] for f in FEST if 0 < HAB.searchsorted(f) < len(HAB)}
SL = [900, 930, 960, 990, 1020]                                   # 15:00 15:30 16:00 16:30 17:00 (minutos)
filas, PLV = [], None
for s, c in COSTE.items():
    r = {}
    for f in glob.glob(D + f'{s}_*.csv'):
        x = pd.read_csv(f)
        if len(x) < 20: continue
        x.index = pd.to_datetime(x.ts_event, utc=True).dt.tz_convert('America/New_York'); mm = x.index.hour * 60 + x.index.minute
        def px(m):
            y = x[(mm < m) & (mm >= m - 10)]; return (y.close.iloc[-1], y.instrument_id.iloc[-1]) if len(y) else (np.nan, None)
        p = [px(m) for m in SL]
        r[pd.Timestamp(os.path.basename(f)[len(s) + 1:len(s) + 11])] = {SL[k]: (np.log(p[k + 1][0] / p[k][0]) if p[k][1] is not None and p[k][1] == p[k + 1][1] else np.nan) for k in range(4)}
    R = pd.DataFrame(r).T.sort_index()
    if s == 'PL': PLV = R
    for tipo in ('VIE', 'PRE'):
        msk = np.array([d in PRE for d in R.index]) if tipo == 'PRE' else np.array([(d.weekday() == 4) and (d not in PRE) for d in R.index])
        for k in SL[:4]:
            q = R.loc[msk, k].dropna(); dsc, cf = q.loc[:'2017'], q.loc['2018':]
            if len(dsc) < 30 or len(cf) < 30: continue
            filas.append(dict(mercado=s, dia=tipo, inicio=f'{k//60}:{k%60:02d}', n_d=len(dsc), m_d=dsc.mean() * 1e4, t_d=t_nw(dsc.values), n_c=len(cf), m_c=cf.mean() * 1e4,
                              t_c=t_nw(cf.values), años=(np.sign(cf.groupby(cf.index.year).mean()) == np.sign(dsc.mean())).mean(), coste=c))
# prueba principal: platino largo viernes normales 16:30-17:00
v = PLV.loc[[(d.weekday() == 4) and (d not in PRE) for d in PLV.index], 990].dropna(); an = v.groupby(v.index.year).sum(); t = t_nw(v.values)
print(f'PRINCIPAL platino VIE 16:30-17:00 largo 2010-26: n {len(v)} {v.mean()*1e4:.2f} pb (t {t:.2f}) años+ {(an>0).sum()}/{len(an)} → {"PASA" if v.mean() > 0 and t >= 2 and (an > 0).mean() >= 0.6 else "NO PASA"}')
T = pd.DataFrame(filas); T.to_csv('b20_todas.csv', index=False)
sel = T[T.t_d.abs() >= 3.0].copy(); k = max(len(sel), 1); u = stats.norm.ppf(1 - 0.05 / k)
sel['t_c_s'] = sel.t_c * np.sign(sel.m_d); sel['m_c_s'] = sel.m_c * np.sign(sel.m_d)
sel['pasa'] = (sel.t_c_s >= u) & (sel.años >= 0.6) & (sel.m_c_s >= 3 * sel.coste)
print(f'BARRIDO: {len(T)} reglas; seleccionadas (|t| >= 3): {len(sel)}; umbral Bonferroni {u:.2f}')
pd.set_option('display.width', 220)
print(sel.sort_values('t_c_s', ascending=False)[['mercado', 'dia', 'inicio', 'n_d', 'm_d', 't_d', 'n_c', 'm_c', 't_c', 'años', 'coste', 'pasa']].round(2).to_string(index=False))
