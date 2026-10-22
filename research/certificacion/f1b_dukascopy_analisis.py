"""F1b, comprobación con otra fuente (descriptiva, NO certifica): CFD de gas de Dukascopy, corto jueves 09:00→10:00 NY con BID/ASK reales.
Uso: python3 f1b_dukascopy_analisis.py DIR_DUK_GAS"""
import glob, os, sys
from datetime import datetime
from zoneinfo import ZoneInfo
import numpy as np, pandas as pd
from c1_certificacion import velas, en, t_nw
NY = ZoneInfo('America/New_York'); D = sys.argv[1]
filas = []
for f in sorted(glob.glob(os.path.join(D, 'GASCMDUSD_BID_*.bi5'))):
    dia = os.path.basename(f)[-14:-4]; g = f.replace('_BID_', '_ASK_')
    if not os.path.exists(g): continue
    b, a = velas(f, 1000), velas(g, 1000)
    if not b or not a: continue
    d = pd.Timestamp(dia); t0 = datetime(d.year, d.month, d.day, 9, tzinfo=NY); t1 = t0.replace(hour=10)
    b0, a0, b1, a1 = en(b, t0), en(a, t0), en(b, t1), en(a, t1)
    if np.isnan([b0, a0, b1, a1]).any() or a0 <= b0 * 0.999999: continue
    m0, m1 = (b0 + a0) / 2, (b1 + a1) / 2
    filas.append(dict(dia=d, bruto=-np.log(m1 / m0), neto=np.log(b0 / a1), spr0=(a0 - b0) / m0, spr1=(a1 - b1) / m1))
X = pd.DataFrame(filas).set_index('dia')
print(f'jueves con datos: {len(X)} ({X.index.min().date()} → {X.index.max().date()})')
print(f'spread a las 09:00 NY: mediana {X.spr0.median()*1e4:.1f} pb, p75 {X.spr0.quantile(.75)*1e4:.1f} pb; a las 10:00 mediana {X.spr1.median()*1e4:.1f} pb')
for a0, a1 in (('2012', '2017'), ('2018', '2026'), ('2012', '2026')):
    y = X.loc[a0:a1]
    if not len(y): continue
    an = y.bruto.groupby(y.index.year).sum()
    print(f'{a0}-{a1}: n {len(y)} bruto {y.bruto.mean()*1e4:.1f} pb (t {t_nw(y.bruto.values):.2f}) | neto CFD {y.neto.mean()*1e4:.1f} pb (t {t_nw(y.neto.values):.2f}) | años bruto>0 {(an>0).sum()}/{len(an)}')
print('spread mediano a las 09:00 por año (pb):', (X.spr0.groupby(X.index.year).median() * 1e4).round(1).to_dict())
