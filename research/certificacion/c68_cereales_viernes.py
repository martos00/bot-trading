"""C68: maíz y soja, viernes 13-14 NY, junio-agosto. Ver PREREGISTRO_C68. Uso: python3 c68... DIR_H1"""
import sys
import numpy as np, pandas as pd
import holidays
from c1_certificacion import t_nw
from c51_metales_reapertura import barras
FEST = {pd.Timestamp(d) for d in holidays.financial_holidays('NYSE', years=range(2009, 2028))}
HAB = pd.bdate_range('2009-01-01', '2027-12-31'); HAB = HAB[~HAB.isin(list(FEST))]
PRE = {HAB[HAB.searchsorted(f) - 1] for f in FEST if 0 < HAB.searchsorted(f) < len(HAB)}
R = {}
for s in ('ZC', 'ZS'):
    x = barras(s); x.index = x.index + pd.Timedelta(hours=1)          # índice = fin de la barra
    a = x[x.index.hour == 13]; b = x[x.index.hour == 14]
    a.index = a.index.tz_localize(None).normalize(); b.index = b.index.tz_localize(None).normalize()
    j = a[['close', 'instrument_id']].join(b[['close', 'instrument_id']], lsuffix='0', rsuffix='1', how='inner'); j = j[j.instrument_id0 == j.instrument_id1]
    R[s] = np.log(j.close1 / j.close0)
X = pd.DataFrame(R).dropna().loc['2010-06-01':'2026-09-30']; m = X.mean(axis=1)
cierre = pd.Series([(d.weekday() == 4) or (d in PRE) for d in m.index], index=m.index); verano = pd.Series(m.index.month.isin([6, 7, 8]), index=m.index)
def inf(nom, v, principal=False):
    an = v.groupby(v.index.year).sum(); t = t_nw(v.values)
    print(f'{nom}: n {len(v)} {v.mean()*1e4:.2f} pb (t {t:.2f}) años+ {(an>0).sum()}/{len(an)} | ZC {X.ZC.reindex(v.index).mean()*1e4:.2f} ZS {X.ZS.reindex(v.index).mean()*1e4:.2f}'
          + (f' → {"PASA" if v.mean() > 0 and t >= 2 and (an > 0).mean() >= 0.6 else "NO PASA"}' if principal else ''))
inf('Viernes/víspera en verano (principal)', m[cierre & verano], True)
inf('   inf. viernes/víspera resto del año', m[cierre & ~verano])
inf('   inf. lunes-jueves en verano', m[~cierre & verano])
