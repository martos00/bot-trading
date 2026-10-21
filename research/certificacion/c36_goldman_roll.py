"""C36: adelantarse al Goldman roll en diferenciales de calendario de energía. Ver PREREGISTRO_C36.
Uso: python3 c36_goldman_roll.py DIR_CURVA"""
import glob, os, sys
import numpy as np, pandas as pd
from scipy import stats
from c1_certificacion import t_nw
D = sys.argv[1]
COSTE = 4e-4
spr = {}
for s in ('CL', 'HO', 'RB', 'NG'):
    x = pd.concat([pd.read_csv(f, parse_dates=['ts_event']) for f in sorted(glob.glob(os.path.join(D, f'{s}_*.csv'))) if os.path.getsize(f) > 100])
    x['dia'] = x.ts_event.dt.tz_localize(None).dt.normalize()
    x = x[x.dia.dt.weekday < 5]
    r = {}
    for k in (0, 1):
        y = x[x.symbol == f'{s}.c.{k}'].drop_duplicates('dia').set_index('dia').sort_index()
        q = np.log(y.close).diff(); q[y.instrument_id != y.instrument_id.shift()] = np.nan
        r[k] = q
    spr[s] = r[1] - r[0]
S = pd.DataFrame(spr).loc['2010-06-01':'2026-09-30']
dias = S.index
mes = dias.to_period('M')
bd = pd.Series(dias, index=dias).groupby(mes).cumcount() + 1            # día hábil 1, 2, ...
desde_fin = pd.Series(dias, index=dias).groupby(mes).cumcount(ascending=False) + 1   # 1 = último día hábil del mes
mes_obj = pd.Series(mes, index=dias)
mes_obj[desde_fin.values <= 5] = (mes[desde_fin.values <= 5] + 1)       # últimos 5 días cuentan para el mes siguiente
W = {'W1 adelantamiento (5 últimos + DH1-4)': ((desde_fin.values <= 5) | (bd.values <= 4)),
     'W2 periodo de roll (DH5-9)': ((bd.values >= 5) & (bd.values <= 9))}
res = {}
for nom, m in W.items():
    sub = S[m]; g = sub.groupby(mes_obj[m].values)
    tot = g.sum(min_count=3)                       # al menos 3 días válidos por mercado y mes
    bruto = tot.mean(axis=1); neto = (tot - COSTE).mean(axis=1)
    x = pd.DataFrame({'bruto': bruto, 'neto': neto}).dropna(); x.index = x.index.to_timestamp()
    res[nom] = x
ps, filas = [], []
for nom, x in res.items():
    d, c = x.loc['2010':'2014'], x.loc['2015':'2026']; an = c.neto.groupby(c.index.year).sum(); t = t_nw(c.neto.values, 3)
    ps.append(1 - stats.norm.cdf(t)); filas.append((nom, d, c, an, t))
orden = np.argsort(ps); ok = [False] * 2; seguir = True
for k, i in enumerate(orden):
    seguir = seguir and ps[i] <= 0.05 / (2 - k); ok[i] = seguir
for (nom, d, c, an, t), o in zip(filas, ok):
    cert = o and (an > 0).mean() >= 0.6 and c.bruto.mean() >= 3 * COSTE
    print(f'{nom}: 2010-14 n {len(d)} neto {d.neto.mean()*1e4:6.2f} pb (t {t_nw(d.neto.values, 3):.2f}) | 2015-26 n {len(c)} bruto {c.bruto.mean()*1e4:6.2f} '
          f'neto {c.neto.mean()*1e4:6.2f} pb (t {t:.2f}) años+ {(an>0).sum()}/{len(an)} | Holm {o} → {"CERTIFICADA" if cert else "no"}')
    print('   por año (pb):', (an * 1e4).round(0).to_dict())
for nom, x in res.items():
    pass
print('Por mercado, 2015-26, bruto medio (pb):')
for nom, m in W.items():
    sub = S[m].loc['2015':]; g = sub.groupby(mes_obj[m].loc['2015':].values).sum(min_count=3)
    print('  ', nom, (g.mean() * 1e4).round(1).to_dict())
