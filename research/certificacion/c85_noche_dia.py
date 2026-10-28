"""C85: noche frente a dia en futuros de materias primas (PREREGISTRO_C85). Uso: python3 c85_noche_dia.py DIR_H1"""
import glob, os, sys
import numpy as np, pandas as pd
from scipy import stats
from c1_certificacion import t_nw
H = sys.argv[1]
COSTE = dict(GC=0.74, SI=2.3, PL=3.5, PA=6.0, HG=1.65, CL=2.0, HO=2.5, RB=3.0, ZC=6.6, ZS=2.5, ZW=4.5, ZL=3.0, ZM=3.0)
GRANO = {'ZC', 'ZS', 'ZW', 'ZL', 'ZM'}
filas = []
for s, coste in COSTE.items():
    x = pd.concat([pd.read_csv(f, parse_dates=['ts_event']) for f in sorted(glob.glob(os.path.join(H, f'{s}_*.csv')))]).drop_duplicates('ts_event')
    fin = x.ts_event.dt.tz_convert('America/New_York').dt.tz_localize(None) + pd.Timedelta(hours=1)
    h = pd.DataFrame({'c': x.close.values, 'id': x.instrument_id.values}, index=fin).sort_index().loc['2010-06-01':'2026-09-30']
    t = pd.DataFrame({'c': h.c.values, 'id': h.id.values, 'dia': h.index.normalize(), 'hora': h.index.hour})
    C = t.pivot_table(index='dia', columns='hora', values='c', aggfunc='last'); I = t.pivot_table(index='dia', columns='hora', values='id', aggfunc='last')
    hn, hf = (21, 14) if s in GRANO else (19, 16)
    dias = C.index[C.index.weekday < 5]
    prev = {}
    for d in dias:
        p = d - pd.Timedelta(days=1)
        while p not in C.index and (d - p).days < 4: p -= pd.Timedelta(days=1)
        prev[d] = p
    def ret(a_d, a_h, b_d, b_h):
        try:
            ca, cb, ia, ib = C.at[a_d, a_h], C.at[b_d, b_h], I.at[a_d, a_h], I.at[b_d, b_h]
        except KeyError:
            return np.nan
        return np.log(cb / ca) * 1e4 if (ia == ib and not np.isnan(ca) and not np.isnan(cb)) else np.nan
    noche = pd.Series({d: ret(prev[d], hn, d, 9) for d in dias if prev[d] in C.index}).dropna()
    dia_ = pd.Series({d: ret(d, 9, d, hf) for d in dias}).dropna()
    for tramo, r in (('NOCHE', noche), ('DIA', dia_)):
        a, b = r.loc[:'2017'], r.loc['2018':]
        filas.append(dict(mercado=s, tramo=tramo, n_d=len(a), m_d=a.mean(), t_d=t_nw(a.values), n_c=len(b), m_c=b.mean(), t_c=t_nw(b.values),
                          años=(np.sign(b.groupby(b.index.year).mean()) == np.sign(a.mean())).mean(), coste=coste))
T = pd.DataFrame(filas); T.to_csv('c85_todas.csv', index=False)
sel = T[T.t_d.abs() >= 3.0].copy(); k = max(len(sel), 1); u = stats.norm.ppf(1 - 0.05 / k)
sel['t_c_s'] = sel.t_c * np.sign(sel.m_d); sel['m_c_s'] = sel.m_c * np.sign(sel.m_d)
sel['pasa'] = (sel.t_c_s >= u) & (sel.años >= 0.6) & (sel.m_c_s >= 3 * sel.coste)
print(T.round(2).to_string(index=False)); print(f'\nseleccionadas |t_d|>=3: {len(sel)}; umbral confirmacion t >= {u:.2f}')
print(sel[['mercado', 'tramo', 'm_d', 't_d', 'm_c', 't_c', 'años', 'coste', 'pasa']].round(2).to_string(index=False))
