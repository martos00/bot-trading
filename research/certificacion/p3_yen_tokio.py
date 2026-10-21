"""P3: viabilidad del yen en horario de Tokio con BID/ASK reales de FXCM (PREREGISTRO_P3_yen_tokio_viabilidad.md).
Uso: python3 p3_yen_tokio.py DIR_FXCM_USDJPY"""
import glob, os, sys
from datetime import datetime
from zoneinfo import ZoneInfo
import numpy as np
import pandas as pd
from c1_certificacion import fxcm, en, t_nw

TOK = ZoneInfo('Asia/Tokyo')
COM, DESL = 0.45e-4, 0.1e-4

b, a = {}, {}
for f in sorted(glob.glob(os.path.join(sys.argv[1], 'USDJPY_*.csv.gz'))):
    bb, aa = fxcm(f); b.update(bb); a.update(aa)
filas = []
for d in pd.bdate_range('2012-01-03', '2026-09-30'):
    t0 = datetime(d.year, d.month, d.day, 8, tzinfo=TOK); t1 = t0.replace(hour=15)
    b0, a0, b1, a1 = en(b, t0), en(a, t0), en(b, t1), en(a, t1)
    if np.isnan([b0, a0, b1, a1]).any():
        continue
    m0, m1 = (b0 + a0) / 2, (b1 + a1) / 2
    filas.append(dict(dia=d, medio=-np.log(m1 / m0), ejec=np.log(b0 / a1) - COM - 2 * DESL,
                      spr0=(a0 - b0) / m0, spr1=(a1 - b1) / m1))
x = pd.DataFrame(filas).set_index('dia')
x['coste'] = x.medio - x.ejec
pb = lambda v: f'{v * 1e4:.2f} pb'
print(f'días {len(x)}')
print(f'punto medio : {pb(x.medio.mean())}  t {t_nw(x.medio):.2f}')
print(f'ejecutable  : {pb(x.ejec.mean())}  t {t_nw(x.ejec):.2f}')
print(f'coste medio : {pb(x.coste.mean())}   medio/coste {x.medio.mean() / x.coste.mean():.2f}')
print(f'spread 08:00 Tokio mediana {pb(x.spr0.median())} p90 {pb(x.spr0.quantile(.9))} | 15:00 mediana {pb(x.spr1.median())} p90 {pb(x.spr1.quantile(.9))}')
anual = x.ejec.groupby(x.index.year).mean() * 1e4
print('ejecutable por año (pb/día):', anual.round(2).to_dict(), f' positivos {(anual > 0).sum()}/{len(anual)}')
print('punto medio por año (pb/día):', (x.medio.groupby(x.index.year).mean() * 1e4).round(2).to_dict())
e1 = pd.read_csv('e1_franjas.csv', index_col=0, parse_dates=True)
r1 = -np.log(e1.mid8 / e1.mid6)
print('correlación diaria con E1 (EUR/USD 06-08 NY):', round(x.medio.corr(r1), 3))
crit = {'1 ejecutable t>=2': x.ejec.mean() > 0 and t_nw(x.ejec) >= 2,
        '2 medio >= 3x coste': x.medio.mean() >= 3 * x.coste.mean(), '3 años >= 60%': (anual > 0).mean() >= 0.6}
print('CRITERIOS:', crit, '→ PASA A FORWARD TEST' if all(crit.values()) else '→ SE CIERRA')
