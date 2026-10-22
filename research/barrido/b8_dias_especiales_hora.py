"""B8: barrido día especial × hora en 30 futuros. Ver PREREGISTRO_B8_dias_especiales_hora.md.
Uso: python3 b8_dias_especiales_hora.py DIR_H1 ES_1m.pkl"""
import glob, os, sys
import numpy as np, pandas as pd
import holidays
FEST = {pd.Timestamp(d) for d in holidays.financial_holidays('NYSE', years=range(2009, 2028))}
HAB = pd.bdate_range('2009-01-01', '2027-12-31'); HAB = HAB[~HAB.isin(list(FEST))]
from scipy import stats
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'certificacion'))
from c1_certificacion import t_nw
H, ES = sys.argv[1:3]
COSTE = dict(ES=0.73, NQ=0.3, ZN=1.8, ZB=2.7, CL=2.0, NG=4.7, GC=0.74, SI=2.3, HG=1.65, ZS=2.5, ZC=6.6, **{'6E': 0.75, '6J': 1.2, '6B': 1.3, '6A': 1.3},
             **{'6C': 1.4, '6S': 1.4, '6N': 1.6, '6M': 2.0, 'PL': 3.5, 'PA': 6.0, 'HO': 2.5, 'RB': 3.0, 'ZW': 4.5, 'ZL': 3.0, 'ZM': 3.0, 'LE': 2.5, 'HE': 4.0, 'YM': 0.8, 'RTY': 1.2})
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
for s in COSTE:
    h = horario(s).loc[:'2026-09-30']
    h = h[h.index.weekday < 5]
    dia = h.index.normalize(); hora = h.index.hour
    tabla = pd.DataFrame({'c': h.c.values, 'id': h.id.values, 'dia': dia, 'hora': hora})
    piv_c = tabla.pivot_table(index='dia', columns='hora', values='c', aggfunc='last')
    piv_i = tabla.pivot_table(index='dia', columns='hora', values='id', aggfunc='last')
    dias = piv_c.index; tipo = pd.Series('', index=dias)
    for f in FEST:
        i = HAB.searchsorted(f)
        if 0 < i < len(HAB):
            if HAB[i - 1] in tipo.index: tipo[HAB[i - 1]] = 'PRE'
            if HAB[i] in tipo.index: tipo[HAB[i]] = 'POST'
    for m in pd.period_range('2010-01', '2026-09', freq='M'):
        vie = pd.date_range(m.start_time, m.end_time, freq='W-FRI')[2]
        while vie not in HAB: vie -= pd.Timedelta(days=1)
        lun = vie + pd.Timedelta(days=3)
        if vie in tipo.index and tipo[vie] == '': tipo[vie] = 'OPEX'
        if lun in tipo.index and tipo[lun] == '': tipo[lun] = 'POSTOPEX'
        d15 = HAB[HAB.searchsorted(m.start_time + pd.Timedelta(days=14))]
        if d15 in tipo.index and tipo[d15] == '': tipo[d15] = 'D15'
    for h0 in range(23):
        h1 = h0 + 1
        if h0 == 17 or h1 == 18 or h0 not in piv_c or h1 not in piv_c: continue
        r = np.log(piv_c[h1] / piv_c[h0]); r[piv_i[h1] != piv_i[h0]] = np.nan; r = r.dropna()
        for nd in ('PRE', 'POST', 'OPEX', 'POSTOPEX', 'D15'):
            q = r[tipo.reindex(r.index).values == nd]; dsc, cf = q.loc['2010':'2017'], q.loc['2018':'2026']
            if len(dsc) < 60 or len(cf) < 60: continue
            filas.append(dict(mercado=s, dia=nd, inicio=h0, n_d=len(dsc), m_d=dsc.mean() * 1e4, t_d=t_nw(dsc.values),
                              n_c=len(cf), m_c=cf.mean() * 1e4, t_c=t_nw(cf.values),
                              años=(np.sign(cf.groupby(cf.index.year).mean()) == np.sign(dsc.mean())).mean(), coste=COSTE[s]))
t = pd.DataFrame(filas); t.to_csv('b8_todas.csv', index=False)
print(f'reglas evaluadas: {len(t)}')
sel = t[t.t_d.abs() >= 3.5].copy(); k = max(len(sel), 1); umbral = stats.norm.ppf(1 - 0.05 / k)
sel['t_c_sentido'] = sel.t_c * np.sign(sel.m_d); sel['m_c_sentido'] = sel.m_c * np.sign(sel.m_d)
sel['pasa'] = (sel.t_c_sentido >= umbral) & (sel.años >= 0.6) & (sel.m_c_sentido - sel.coste > 0) & (sel.m_c_sentido >= 3 * sel.coste)
print(f'seleccionadas en descubrimiento (|t| >= 3.5): {k}; umbral de Bonferroni en confirmación: t >= {umbral:.2f}')
pd.set_option('display.width', 220)
print(sel.sort_values('t_c_sentido', ascending=False)[['mercado', 'dia', 'inicio', 'm_d', 't_d', 'm_c', 't_c', 'años', 'coste', 'pasa']].round(2).to_string(index=False))
print('\nmayores |t| en 2010-17 (informativo):'); print(t.reindex(t.t_d.abs().sort_values(ascending=False).index).head(12)[['mercado','dia','inicio','m_d','t_d','m_c','t_c','años','coste']].round(2).to_string(index=False))
