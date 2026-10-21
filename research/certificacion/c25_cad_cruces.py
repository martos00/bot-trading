"""C25: USDCAD 08-16 NY, EURGBP y EURCHF 07 Londres → 08 NY, con BID/ASK reales de FXCM. Ver PREREGISTRO_C25."""
import glob, os, sys
from datetime import datetime
from zoneinfo import ZoneInfo
import numpy as np, pandas as pd
from scipy import stats
from c1_certificacion import fxcm, en, t_nw
LON, NY = ZoneInfo('Europe/London'), ZoneInfo('America/New_York')
COM, DESL = 0.45e-4, 0.1e-4
D = sys.argv[1]
P = [('USDCAD', NY, 8, NY, 16), ('EURGBP', LON, 7, NY, 8), ('EURCHF', LON, 7, NY, 8)]
e = pd.read_csv('e1_franjas.csv', index_col=0, parse_dates=True); e1 = -np.log(e.mid8 / e.mid6)
res, ps = [], []
for par, z0, h0, z1, h1 in P:
    b, a = {}, {}
    for f in sorted(glob.glob(os.path.join(D, par, f'{par}_*.csv.gz'))):
        bb, aa = fxcm(f); b.update(bb); a.update(aa)
    filas = []
    for d in pd.bdate_range('2012-01-03', '2026-09-30'):
        t0 = datetime(d.year, d.month, d.day, h0, tzinfo=z0); t1 = datetime(d.year, d.month, d.day, h1, tzinfo=z1)
        b0, a0, b1, a1 = en(b, t0), en(a, t0), en(b, t1), en(a, t1)
        if np.isnan([b0, a0, b1, a1]).any(): continue
        m = np.log(((b1 + a1) / 2) / ((b0 + a0) / 2))
        coste = ((a0 - b0) / ((a0 + b0) / 2) + (a1 - b1) / ((a1 + b1) / 2)) / 2 + COM + 2 * DESL
        filas.append(dict(dia=d, medio=m, coste=coste))
    x = pd.DataFrame(filas).set_index('dia')
    dsc, c = x.loc['2012':'2018'], x.loc['2019':]
    sg = np.sign(dsc.medio.mean())
    y = c.medio * sg; neto = y - c.coste; t = t_nw(y); an = (y.groupby(y.index.year).mean() > 0).mean()
    ps.append(1 - stats.norm.cdf(t))
    res.append((par, sg, dsc.medio.mean(), t_nw(dsc.medio), y.mean(), t, an, c.coste.mean(), neto.mean(), t_nw(neto), y.corr(e1.reindex(y.index))))
orden = np.argsort(ps); ok = [False] * 3; seguir = True
for k, i in enumerate(orden):
    seguir = seguir and ps[i] <= 0.05 / (3 - k); ok[i] = seguir
for r, o in zip(res, ok):
    par, sg, dm, dt, cm, ct, an, co, nm, nt, ce = r
    cert = o and an >= 0.6 and nm > 0 and cm >= 3 * co
    print(f'{par}: sentido {"+" if sg > 0 else "-"} | 2012-18 {dm*1e4:5.2f} pb (t {dt:.2f}) | 2019-26 {cm*1e4:5.2f} pb (t {ct:.2f}) años {an*100:.0f}% '
          f'| coste {co*1e4:.2f} pb neto {nm*1e4:5.2f} pb (t {nt:.2f}) | corr E1 {ce:.2f} | Holm {o} → {"CERTIFICADA" if cert else "no"}')
