"""C49: plata (y oro) en la última hora antes de un festivo de la NYSE. Ver PREREGISTRO_C49.
Uso: python3 c49_plata_vispera.py DIR_XAU DIR_XAG DIR_H1"""
import glob, os, sys
import numpy as np, pandas as pd
import holidays
from c1_certificacion import t_nw
from c45_oro_viernes import carga, tramo
FEST = {pd.Timestamp(d) for d in holidays.financial_holidays('NYSE', years=range(2009, 2028))}
HAB = pd.bdate_range('2009-01-01', '2027-12-31'); HAB = HAB[~HAB.isin(list(FEST))]
PRE = sorted({HAB[HAB.searchsorted(f) - 1] for f in FEST if 0 < HAB.searchsorted(f) < len(HAB)})
PRE = pd.DatetimeIndex([d for d in PRE if pd.Timestamp('2010-06-01') <= d <= pd.Timestamp('2026-09-30')])
def informe(nom, r, principal=False):
    v = r.reindex(PRE).dropna(); an = v.groupby(v.index.year).sum()
    vi, nv = v[v.index.weekday == 4], v[v.index.weekday != 4]
    print(f'{nom}: PRE n {len(v)} {v.mean()*1e4:.2f} pb (t {t_nw(v.values):.2f}) años+ {(an>0).sum()}/{len(an)} | 2018-26 {v.loc["2018":].mean()*1e4:.2f} pb '
          f'| PRE viernes n {len(vi)} {vi.mean()*1e4:.2f} pb (t {t_nw(vi.values):.2f}) | PRE no viernes n {len(nv)} {nv.mean()*1e4:.2f} pb (t {t_nw(nv.values):.2f})')
    if principal:
        crit = {'1 t>=2': v.mean() > 0 and t_nw(v.values) >= 2, '2 años>=60%': (an > 0).mean() >= 0.6}
        print('CRITERIOS (a):', crit, '→ CONFIRMADA' if all(crit.values()) else '→ NO CONFIRMADA')
xag = carga(sys.argv[2]).loc['2010-06-01':'2026-09-30']; xau = carga(sys.argv[1]).loc['2010-06-01':'2026-09-30']
informe('XAGUSD contado 16:00-16:58', tramo(xag, 16, 0, 16, 58), principal=True)
informe('XAUUSD contado 16:00-16:58 (inf.)', tramo(xau, 16, 0, 16, 58))
for s in ('SI', 'GC'):
    x = pd.concat([pd.read_csv(f) for f in sorted(glob.glob(os.path.join(sys.argv[3], f'{s}_*.csv')))])
    x['close'] = pd.to_numeric(x.close, errors='coerce'); x = x[x.close > 0]
    x.index = pd.to_datetime(x.ts_event, utc=True).dt.tz_convert('America/New_York') + pd.Timedelta(hours=1); x = x[~x.index.duplicated()].sort_index()
    a = x[x.index.hour == 16]; b = x[x.index.hour == 17]; a.index = a.index.tz_localize(None).normalize(); b.index = b.index.tz_localize(None).normalize()
    j = a[['close', 'instrument_id']].join(b[['close', 'instrument_id']], lsuffix='0', rsuffix='1', how='inner'); j = j[j.instrument_id0 == j.instrument_id1]
    informe(f'{s} futuro 16:00-17:00 (inf.)', np.log(j.close1 / j.close0))
