"""C69: víspera de festivo en 16 futuros de materias primas, día completo. Ver PREREGISTRO_C69."""
import glob, os
import numpy as np, pandas as pd
import holidays
from c1_certificacion import t_nw
D = '/tmp/claude-0/-home-user-bot-trading/682335b1-28ae-5d18-9355-ce7f0f968722/scratchpad/databento/curva/'
FEST = {pd.Timestamp(d) for d in holidays.financial_holidays('NYSE', years=range(2009, 2028))}
HAB = pd.bdate_range('2009-01-01', '2027-12-31'); HAB = HAB[~HAB.isin(list(FEST))]
PRE = pd.DatetimeIndex(sorted({HAB[HAB.searchsorted(f) - 1] for f in FEST if 0 < HAB.searchsorted(f) < len(HAB)}))
r = {}
for s in ['CL', 'HO', 'RB', 'NG', 'ZC', 'ZS', 'ZW', 'ZL', 'ZM', 'KE', 'LE', 'HE', 'GC', 'SI', 'HG', 'PL']:
    x = pd.concat([pd.read_csv(f) for f in glob.glob(D + f'{s}_*.csv') if os.path.getsize(f) > 100])
    x = x[x.symbol == f'{s}.c.0']; x['dia'] = pd.to_datetime(x.ts_event).dt.tz_localize(None).dt.normalize()
    y = x.drop_duplicates('dia').set_index('dia').sort_index(); y = y[(y.index.weekday < 5) & (y.close > 0)]
    q = np.log(y.close).diff(); q[y.instrument_id != y.instrument_id.shift()] = np.nan; r[s] = q
R = pd.DataFrame(r).loc['2010-06-01':'2026-09-30']
# las barras diarias de Databento cierran a las 00:00 UTC: el día PRE es la barra con fecha PRE
NM = ['CL', 'HO', 'RB', 'NG', 'ZC', 'ZS', 'ZW', 'ZL', 'ZM', 'KE', 'LE', 'HE']; MET = ['GC', 'SI', 'HG', 'PL']
for nom, cols, principal in (('No metálicas (principal)', NM, True), ('Metales (inf.)', MET, False)):
    m = R[cols].mean(axis=1); v = m.reindex(PRE).dropna(); resto = m.drop(v.index, errors='ignore').dropna()
    an = v.groupby(v.index.year).sum(); t = t_nw(v.values, 2)
    print(f'{nom}: PRE n {len(v)} {v.mean()*1e4:.2f} pb (t {t:.2f}) años+ {(an>0).sum()}/{len(an)} | resto {resto.mean()*1e4:.2f} pb | neto {v.mean()*1e4-3:.2f} pb'
          + (f' → {"PASA" if v.mean() > 0 and t >= 2 and (an > 0).mean() >= 0.6 else "NO PASA"}' if principal else ''))
print('por mercado PRE (pb):', (R.reindex(PRE).mean() * 1e4).round(1).to_dict())
