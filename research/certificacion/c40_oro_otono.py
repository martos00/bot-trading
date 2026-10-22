"""C40: efecto otoño del oro. Ver PREREGISTRO_C40. Uso: python3 c40_oro_otono.py DIR_CURVA"""
import glob, os, sys
import numpy as np, pandas as pd
from scipy import stats
D = sys.argv[1]
x = pd.concat([pd.read_csv(f) for f in glob.glob(os.path.join(D, 'GC_*.csv')) if os.path.getsize(f) > 100])
x = x[x.symbol == 'GC.c.0']; x['dia'] = pd.to_datetime(x.ts_event).dt.tz_localize(None).dt.normalize()
y = x.drop_duplicates('dia').set_index('dia').sort_index(); y = y[y.index.weekday < 5]
r = np.log(y.close).diff(); r[y.instrument_id != y.instrument_id.shift()] = np.nan
M = r.groupby(r.index.to_period('M')).sum(min_count=10).dropna().loc['2011-01':'2026-09']
otono = M[M.index.month.isin([9, 11])]; resto = M[~M.index.month.isin([9, 11])]
t = stats.ttest_ind(otono, resto, equal_var=False)
print(f'sep+nov: n {len(otono)} media {otono.mean()*100:.2f} %/mes | resto: n {len(resto)} media {resto.mean()*100:.2f} %/mes | diferencia {(otono.mean()-resto.mean())*100:.2f} pp (t Welch {t.statistic:.2f})')
print('por mes (%):', (M.groupby(M.index.month).mean() * 100).round(2).to_dict())
an = pd.DataFrame({'o': otono.groupby(otono.index.year).mean(), 'r': resto.groupby(resto.index.year).mean()}).dropna()
neto = otono - 3e-4
print(f'años con sep+nov > resto: {(an.o > an.r).sum()}/{len(an)} | estrategia neta futuros {neto.mean()*100:.2f} %/mes, CFD {(otono - 3e-4 - 0.004).mean()*100:.2f} %/mes')
print('sep+nov por año (%):', (otono.groupby(otono.index.year).sum() * 100).round(1).to_dict())
crit = {'1 dif t>=2': t.statistic >= 2, '2 años>=60%': (an.o > an.r).mean() >= 0.6, '3 neta>0': neto.mean() > 0}
print('CRITERIOS:', crit, '→ CERTIFICADA' if all(crit.values()) else '→ NO CERTIFICADA')
