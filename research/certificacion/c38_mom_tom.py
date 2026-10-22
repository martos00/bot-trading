"""C38: MOM-TOM (Van Hemert 2014) en 16 futuros de materias primas. Ver PREREGISTRO_C38. Uso: python3 c38_mom_tom.py DIR_CURVA"""
import glob, os, sys
import numpy as np, pandas as pd
from c1_certificacion import t_nw
D = sys.argv[1]
SIMS = ['CL', 'HO', 'RB', 'NG', 'GC', 'SI', 'HG', 'PL', 'ZC', 'ZS', 'ZW', 'ZL', 'ZM', 'KE', 'LE', 'HE']
COSTE = 3e-4
r = {}
for s in SIMS:
    x = pd.concat([pd.read_csv(f, parse_dates=['ts_event']) for f in sorted(glob.glob(os.path.join(D, f'{s}_*.csv'))) if os.path.getsize(f) > 100])
    x['dia'] = x.ts_event.dt.tz_localize(None).dt.normalize()
    y = x[(x.symbol == f'{s}.c.0') & (x.dia.dt.weekday < 5)].drop_duplicates('dia').set_index('dia').sort_index()
    with np.errstate(invalid='ignore', divide='ignore'):
        q = np.log(y.close.where(y.close > 0)).diff()
    q[y.instrument_id != y.instrument_id.shift()] = np.nan
    r[s] = q
R = pd.DataFrame(r).loc[:'2026-09-30']
dias = R.index; mes = dias.to_period('M')
desde_fin = pd.Series(np.arange(len(dias)), index=dias).groupby(mes).cumcount(ascending=False).values + 1
bd = pd.Series(np.arange(len(dias)), index=dias).groupby(mes).cumcount().values + 1
mom = R.fillna(0).rolling(252).sum().where(R.notna().rolling(252).sum() >= 200)
vol = R.rolling(60, min_periods=40).std()
tom_m, otro_m = {}, {}
pos_tom = pd.DataFrame(0.0, index=dias, columns=SIMS); pos_otro = pos_tom.copy()
ent = np.flatnonzero(desde_fin == 3)
for i in ent:
    sg = np.sign(mom.iloc[i]); iv = 1 / vol.iloc[i]
    ok = sg.notna() & iv.notna() & (sg != 0)
    if ok.sum() < 8: continue
    w = (iv[ok] / iv[ok].sum()) * sg[ok]
    tramo = R.iloc[i + 1:i + 4]                         # 2 últimos días del mes + 1.º del siguiente
    if i + 3 >= len(dias) or len(tramo) < 3 or bd[i + 3] != 1: continue
    g = (tramo[w.index].fillna(0) * w).sum().sum()
    tom_m[dias[i].to_period('M')] = (g, g - 2 * COSTE * w.abs().sum())
    # informativo: la misma cartera en los días no-TOM del mes siguiente (DH2 hasta el 4.º antes del fin)
    j0 = i + 4; fin_sig = np.flatnonzero((desde_fin == 3) & (np.arange(len(dias)) > i))
    if len(fin_sig):
        otros = R.iloc[j0:fin_sig[0] + 1]
        otro_m[dias[i].to_period('M')] = ((otros[w.index].fillna(0) * w).sum().sum(), len(otros))
T = pd.DataFrame(tom_m, index=['bruto', 'neto']).T; T.index = T.index.to_timestamp()
O = pd.DataFrame(otro_m, index=['bruto', 'n']).T; O.index = O.index.to_timestamp()
for a, b in (('2011', '2014'), ('2015', '2026')):
    y = T.loc[a:b]; an = y.neto.groupby(y.index.year).sum(); o = O.loc[a:b]
    print(f'{a}-{b}: TOM n {len(y)} bruto {y.bruto.mean()*1e4:.1f} pb/mes neto {y.neto.mean()*1e4:.1f} pb (t {t_nw(y.neto.values, 3):.2f}) '
          f'Sharpe {y.neto.mean()/y.neto.std()*np.sqrt(12):.2f} años+ {(an>0).sum()}/{len(an)} | por día: TOM {y.bruto.mean()/3*1e4:.2f} pb, '
          f'no-TOM {(o.bruto.sum()/o.n.sum())*1e4:.2f} pb')
    print('   por año TOM neto (%):', (an * 100).round(2).to_dict())
c = T.loc['2015':]; an = c.neto.groupby(c.index.year).sum()
crit = {'1 t>=2': c.neto.mean() > 0 and t_nw(c.neto.values, 3) >= 2, '2 años>=60%': (an > 0).mean() >= 0.6}
print('CRITERIOS:', crit, '→ CERTIFICADA' if all(crit.values()) else '→ NO CERTIFICADA')
