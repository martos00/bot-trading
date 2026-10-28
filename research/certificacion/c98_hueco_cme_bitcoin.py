"""C98 — «el hueco del CME se cierra» en BTC y ETH (PREREGISTRO_C98_C99). Uso: python3 c98_hueco_cme_bitcoin.py DIR_BINANCE_1H"""
import glob, io, os, sys, zipfile
import numpy as np, pandas as pd
from c1_certificacion import t_nw
D = sys.argv[1]
def leer(sym):
    rows = []
    for f in sorted(glob.glob(os.path.join(D, f'{sym}-1h-*.zip'))):
        with zipfile.ZipFile(f) as z: rows.append(pd.read_csv(io.BytesIO(z.read(z.namelist()[0])), header=None, usecols=[0, 1, 2, 3]))
    b = pd.concat(rows); t = b[0].astype('int64'); t = np.where(t > 1e14, t // 1000, t)
    x = pd.DataFrame(b[[1, 2, 3]].astype(float).values, columns=['o', 'h', 'l'], index=pd.to_datetime(t, unit='ms', utc=True).tz_convert('America/New_York'))
    return x[~x.index.duplicated()].sort_index()
for sym, coste in (('BTCUSDT', 3), ('ETHUSDT', 4)):
    x = leer(sym); out = []
    for v in x.index[(x.index.dayofweek == 4) & (x.index.hour == 17)]:
        dom = v.normalize() + pd.Timedelta(days=2, hours=18); lun = v.normalize() + pd.Timedelta(days=3, hours=16)
        if dom not in x.index or lun not in x.index: continue
        p0, p1, p2 = x.o[v], x.o[dom], x.o[lun]; g = np.log(p1 / p0)
        if g == 0: continue
        w = x.loc[dom:lun - pd.Timedelta(hours=1)]
        toca = (w.l <= p0).any() if g > 0 else (w.h >= p0).any()
        pf = p0 if toca else p2
        semana = x.loc[dom:v.normalize() + pd.Timedelta(days=7, hours=17)]
        cerr_sem = (semana.l <= p0).any() if g > 0 else (semana.h >= p0).any()
        out.append((v.tz_localize(None).normalize(), -np.sign(g) * np.log(pf / p1) * 1e4, toca, cerr_sem))
    r = pd.DataFrame(out, columns=['d', 'r', 'toca', 'semana']).set_index('d'); s = r.r
    an = s.groupby(s.index.year).mean(); a, b = s.loc[:'2021'], s.loc['2022':]
    c = {'t>=2.24': s.mean() > 0 and t_nw(s.values) >= 2.24, 'años>=60%': (an > 0).mean() >= 0.6, f'>{coste}pb': s.mean() > coste, '2017-21>0': a.mean() > 0, '2022-26>0': b.mean() > 0}
    print(f'{sym}: n {len(s)} {s.mean():+.2f} pb (t {t_nw(s.values):.2f}) años+ {(an>0).sum()}/{len(an)} | 2017-21 {a.mean():+.2f} | 2022-26 {b.mean():+.2f} '
          f'| huecos cerrados antes del lunes 16:00 {r.toca.mean()*100:.0f} %, antes del viernes {r.semana.mean()*100:.0f} %')
    print('   por año:', an.round(1).to_dict()); print('   CRITERIOS:', c, '→ PASA' if all(c.values()) else '→ NO PASA')
