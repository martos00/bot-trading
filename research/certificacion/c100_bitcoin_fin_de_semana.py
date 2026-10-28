"""C100 — continuación del fin de semana en BTC con Bitstamp 1 h (PREREGISTRO_C100). Uso: python3 c100_bitcoin_fin_de_semana.py bitstamp_1h.json"""
import json, sys
import numpy as np, pandas as pd
from c1_certificacion import t_nw
d = json.load(open(sys.argv[1]))
x = pd.DataFrame(d).astype(float); x.index = pd.DatetimeIndex(pd.to_datetime(x.timestamp.astype('int64'), unit='s', utc=True)).tz_convert('America/New_York')
x = x[~x.index.duplicated()].sort_index().rename(columns={'open': 'o', 'high': 'h', 'low': 'l'})
x = x[x.volume > 0]                                   # horas sin operaciones = sin precio
out = []
for v in x.index[(x.index.dayofweek == 4) & (x.index.hour == 17)]:
    dom = v.normalize() + pd.Timedelta(days=2, hours=18); lun = v.normalize() + pd.Timedelta(days=3, hours=16)
    if dom not in x.index or lun not in x.index: continue
    p0, p1, p2 = x.o[v], x.o[dom], x.o[lun]; g = np.log(p1 / p0)
    if g == 0: continue
    w = x.loc[dom:lun - pd.Timedelta(hours=1)]
    vuelve = (w.l <= p0).any() if g > 0 else (w.h >= p0).any()
    out.append((v.tz_localize(None).normalize(), np.sign(g) * np.log((p0 if vuelve else p2) / p1) * 1e4))
s = pd.Series(dict(out)).sort_index()
def info(nom, q):
    an = q.groupby(q.index.year).mean()
    print(f'{nom}: n {len(q)} {q.mean():+.2f} pb (t {t_nw(q.values):.2f}) años+ {(an>0).sum()}/{len(an)} | por año {an.round(1).to_dict()}'); return an
a = s.loc[:'2017-07-31']; an = info('PRUEBA Bitstamp 2012-01 → 2017-07', a)
c = {'t>=2': a.mean() > 0 and t_nw(a.values) >= 2, 'años>=4/6': (an > 0).sum() >= 4, '>3pb': a.mean() > 3}
print('CRITERIOS:', c, '→ PASA' if all(c.values()) else '→ NO PASA')
info('informativo Bitstamp 2017-08 → 2026-09 (muestra de C98)', s.loc['2017-08-01':'2026-09-30'])
