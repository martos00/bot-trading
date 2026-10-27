"""E8b: oro largo viernes 16:00 -> 16:45 NY (PREREGISTRO_E8b, commit b7a99fc). Uso: python3 e8b_oro_viernes_1645.py DIR_GC_VIERNES DIR_HISTDATA_XAU"""
import glob, os, sys
import numpy as np, pandas as pd
from c1_certificacion import t_nw
from c45_oro_viernes import carga, tramo
COSTE = 1.45
gc = {}
for f in sorted(glob.glob(os.path.join(sys.argv[1], '*.csv'))):
    x = pd.read_csv(f)
    if len(x) < 30 or x.instrument_id.nunique() > 1: continue
    x.index = pd.to_datetime(x.ts_event, utc=True).dt.tz_convert('America/New_York'); mm = x.index.hour * 60 + x.index.minute
    def px(m):
        y = x.close[(mm < m) & (mm >= m - 10)]; return y.iloc[-1] if len(y) else np.nan
    gc[pd.Timestamp(os.path.basename(f)[:10])] = {'a': px(960), 'b': px(16 * 60 + 45), 'c': px(16 * 60 + 55)}
gc = pd.DataFrame(gc).T.loc['2010-06-01':'2026-09-30']
def informe(nom, v):
    an = v.groupby(v.index.year).sum()
    print(f'{nom}: n {len(v)} {v.mean()*1e4:+.2f} pb (t {t_nw(v.values):.2f}) años+ {(an>0).sum()}/{len(an)} | '
          f'2010-17 {v.loc[:"2017"].mean()*1e4:+.2f} pb (t {t_nw(v.loc[:"2017"].values):.2f}) | 2018-26 {v.loc["2018":].mean()*1e4:+.2f} pb (t {t_nw(v.loc["2018":].values):.2f})')
    return an
r = np.log(gc.b / gc.a).dropna()
an = informe('FUTURO GC 16:00->16:45', r)
print('   por año (pb):', (an * 1e4).round(1).to_dict())
q = np.log(gc.c / gc.b).dropna(); informe('   informativo GC 16:45->16:55', q)
s = carga(sys.argv[2]).loc['2010-06-01':'2026-09-30']
h = tramo(s, 16, 0, 16, 44); h = h[h.index.weekday == 4]
informe('CONTADO HistData 16:00->16:45', h)
crit = {'futuro t>=2': r.mean() > 0 and t_nw(r.values) >= 2, 'años>=60%': (an > 0).mean() >= 0.6,
        '2018-26>0': r.loc['2018':].mean() > 0, f'2018-26 > coste {COSTE} pb': r.loc['2018':].mean() * 1e4 > COSTE,
        'contado t>=2': h.mean() > 0 and t_nw(h.values) >= 2, 'contado 2018-26>0': h.loc['2018':].mean() > 0}
print('CRITERIOS:', crit, '-> PASA: reactivar E8 en FTMO con salida 16:45' if all(crit.values()) else '-> NO PASA')
