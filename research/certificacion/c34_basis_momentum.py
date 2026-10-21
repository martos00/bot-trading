"""C34: basis-momentum (Boons-Prado 2019) en 16 futuros de materias primas del CME. Ver PREREGISTRO_C34.
Uso: python3 c34_basis_momentum.py DIR_CURVA"""
import glob, os, sys
import numpy as np, pandas as pd
from c1_certificacion import t_nw
D = sys.argv[1]
SIMS = ['CL', 'HO', 'RB', 'NG', 'GC', 'SI', 'HG', 'PL', 'ZC', 'ZS', 'ZW', 'ZL', 'ZM', 'KE', 'LE', 'HE']
COSTE = 3e-4
r0, r1, nivel0, nivel1 = {}, {}, {}, {}
for s in SIMS:
    x = pd.concat([pd.read_csv(f, parse_dates=['ts_event']) for f in sorted(glob.glob(os.path.join(D, f'{s}_*.csv'))) if os.path.getsize(f) > 100])
    x['dia'] = x.ts_event.dt.tz_localize(None).dt.normalize()
    x = x[x.dia.dt.weekday < 5]
    for k, dest in ((0, r0), (1, r1)):
        y = x[x.symbol == f'{s}.c.{k}'].drop_duplicates('dia').set_index('dia').sort_index()
        r = np.log(y.close).diff(); r[y.instrument_id != y.instrument_id.shift()] = np.nan
        dest[s] = r
R0, R1 = pd.DataFrame(r0).loc[:'2026-09-30'], pd.DataFrame(r1).loc[:'2026-09-30']
M0 = R0.fillna(0).groupby(R0.index.to_period('M')).sum(); M1 = R1.fillna(0).groupby(R1.index.to_period('M')).sum()
n0 = R0.notna().groupby(R0.index.to_period('M')).sum()
M1[n0 < 10] = np.nan; M0[n0 < 10] = np.nan
BM = M0.rolling(12).sum() - M1.rolling(12).sum()            # basis-momentum a fin de mes
MOM = M0.rolling(12).sum()
def cartera(senal, ret):
    out, pos_ant = {}, None
    for i in range(12, len(senal) - 1):
        sg = senal.iloc[i].dropna(); nxt = ret.iloc[i + 1]
        sg = sg[nxt.reindex(sg.index).notna()]
        if len(sg) < 9: continue
        k = len(sg) // 3; orden = sg.sort_values()
        pos = pd.Series(0.0, index=SIMS); pos[orden.index[-k:]] = 1 / k; pos[orden.index[:k]] = -1 / k
        giro = (pos - (pos_ant if pos_ant is not None else 0)).abs().sum()
        out[ret.index[i + 1]] = (pos * nxt.reindex(SIMS).fillna(0)).sum() - giro * COSTE
        pos_ant = pos
    return pd.Series(out)
res = {'BM basis-momentum (principal)': cartera(BM, M1), 'MOM momentum 12m (informativo)': cartera(MOM, M1)}
for nom, x in res.items():
    x.index = x.index.to_timestamp()
    print(f'== {nom} ==')
    for a, b in (('2011', '2014'), ('2015', '2026')):
        y = x.loc[a:b]; an = y.groupby(y.index.year).sum()
        print(f'  {a}-{b}: n {len(y)} meses, media {y.mean()*100:.2f}%/mes (t {t_nw(y.values, 3):.2f}), Sharpe anual {y.mean()/y.std()*np.sqrt(12):.2f}, años+ {(an>0).sum()}/{len(an)}')
    print('  por año (%):', (x.groupby(x.index.year).sum() * 100).round(1).to_dict())
x = res['BM basis-momentum (principal)']; c = x.loc['2015':]; an = c.groupby(c.index.year).sum()
crit = {'réplica>0': x.loc['2011':'2014'].mean() > 0, '1 t>=2': c.mean() > 0 and t_nw(c.values, 3) >= 2, '2 años>=60%': (an > 0).mean() >= 0.6}
print('\nCRITERIOS BM:', crit, '→ CERTIFICADA' if all(crit.values()) else '→ NO CERTIFICADA')
