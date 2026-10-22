"""B4: barrido día de la semana × franja de 1 h (hora NY) en los futuros de B2. Ver PREREGISTRO_B4.
Uso: python3 b4_dia_hora_futuros.py DIR_H1 ES_1m.pkl"""
import glob, os, sys
import numpy as np, pandas as pd
from scipy import stats
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'certificacion'))
from c1_certificacion import t_nw
H, ES = sys.argv[1:3]
COSTE = dict(ES=0.73, NQ=0.3, ZN=1.8, ZB=2.7, CL=2.0, NG=4.7, GC=0.74, SI=2.3, HG=1.65, ZS=2.5, ZC=6.6, **{'6E': 0.75, '6J': 1.2, '6B': 1.3, '6A': 1.3})
def horario(s):
    """cierres horarios (índice = fin de la barra, hora NY) con contrato."""
    if s == 'ES':
        x = pd.read_pickle(ES); t = pd.to_datetime(x.ts_event).dt.tz_convert('America/New_York').dt.tz_localize(None) + pd.Timedelta(minutes=1)
        x = x.assign(t=t.dt.ceil('h')).groupby('t').agg(c=('close', 'last'), id=('instrument_id', 'last'))
        return x
    x = pd.concat([pd.read_csv(f, parse_dates=['ts_event']) for f in sorted(glob.glob(os.path.join(H, f'{s}_*.csv')))]).drop_duplicates('ts_event')
    fin = x.ts_event.dt.tz_convert('America/New_York').dt.tz_localize(None) + pd.Timedelta(hours=1)
    return pd.DataFrame({'c': x.close.values, 'id': x.instrument_id.values}, index=fin).sort_index()
filas = []
for s in COSTE:
    h = horario(s).loc[:'2026-09-30']
    h = h[h.index.weekday < 5]
    dia = h.index.normalize(); hora = h.index.hour
    tabla = pd.DataFrame({'c': h.c.values, 'id': h.id.values, 'dia': dia, 'hora': hora})
    piv_c = tabla.pivot_table(index='dia', columns='hora', values='c', aggfunc='last')
    piv_i = tabla.pivot_table(index='dia', columns='hora', values='id', aggfunc='last')
    for h0 in range(23):
        h1 = h0 + 1
        if h0 == 17 or h1 == 18 or h0 not in piv_c or h1 not in piv_c: continue
        r = np.log(piv_c[h1] / piv_c[h0]); r[piv_i[h1] != piv_i[h0]] = np.nan; r = r.dropna()
        for wd, nd in enumerate(['lun', 'mar', 'mié', 'jue', 'vie']):
            q = r[r.index.weekday == wd]; dsc, cf = q.loc['2010':'2017'], q.loc['2018':'2026']
            if len(dsc) < 200 or len(cf) < 200: continue
            filas.append(dict(mercado=s, dia=nd, inicio=h0, n_d=len(dsc), m_d=dsc.mean() * 1e4, t_d=t_nw(dsc.values),
                              n_c=len(cf), m_c=cf.mean() * 1e4, t_c=t_nw(cf.values),
                              años=(np.sign(cf.groupby(cf.index.year).mean()) == np.sign(dsc.mean())).mean(), coste=COSTE[s]))
t = pd.DataFrame(filas); t.to_csv('b4_todas.csv', index=False)
print(f'reglas evaluadas: {len(t)}')
sel = t[t.t_d.abs() >= 3.5].copy(); k = max(len(sel), 1); umbral = stats.norm.ppf(1 - 0.05 / k)
sel['t_c_sentido'] = sel.t_c * np.sign(sel.m_d); sel['m_c_sentido'] = sel.m_c * np.sign(sel.m_d)
sel['pasa'] = (sel.t_c_sentido >= umbral) & (sel.años >= 0.6) & (sel.m_c_sentido - sel.coste > 0) & (sel.m_c_sentido >= 3 * sel.coste)
print(f'seleccionadas en descubrimiento (|t| >= 3.5): {k}; umbral de Bonferroni en confirmación: t >= {umbral:.2f}')
pd.set_option('display.width', 220)
print(sel.sort_values('t_c_sentido', ascending=False)[['mercado', 'dia', 'inicio', 'm_d', 't_d', 'm_c', 't_c', 'años', 'coste', 'pasa']].round(2).to_string(index=False))
ctl = t[(t.mercado == 'NG') & (t.dia == 'jue') & (t.inicio == 9)]
print('\ncontrol conocido (F1b, no cuenta):'); print(ctl.round(2).to_string(index=False))
print('\nmayores |t| en 2010-17 (informativo):'); print(t.reindex(t.t_d.abs().sort_values(ascending=False).index).head(12)[['mercado','dia','inicio','m_d','t_d','m_c','t_c','años','coste']].round(2).to_string(index=False))
