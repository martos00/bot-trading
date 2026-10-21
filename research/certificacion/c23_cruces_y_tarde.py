"""C23: cruces EUR/PLN-HUF-CZK en sesión europea y USD/PLN-HUF-CZK en horario de EE. UU. Ver PREREGISTRO_C23."""
import sys
import numpy as np, pandas as pd
from scipy import stats
from c1_certificacion import t_nw
import c3_breedon_ranaldo as C3
S = sys.argv[1]
dias = pd.bdate_range('2010-01-04', '2026-09-30')
P = [('EURPLN', 'LON', 7, 'NY', 8, +1), ('EURHUF', 'LON', 7, 'NY', 8, +1), ('EURCZK', 'LON', 7, 'NY', 8, +1),
     ('USDPLN', 'NY', 8, 'NY', 16, -1), ('USDHUF', 'NY', 8, 'NY', 16, -1), ('USDCZK', 'NY', 8, 'NY', 16, -1)]
e = pd.read_csv('e1_franjas.csv', index_col=0, parse_dates=True); e1 = -np.log(e.mid8 / e.mid6)
cache, filas, ps, series = {}, [], [], {}
for par, z0, h0, z1, h1, sg in P:
    if par not in cache: cache[par] = C3.cargar_histdata(S, par)
    m, v = cache[par]
    r = pd.Series(np.log(C3.precio(m, v, C3.instantes(dias, z1, h1)) / C3.precio(m, v, C3.instantes(dias, z0, h0))), index=dias)
    r[r.abs() > 0.05] = np.nan
    d, c = r.loc['2010':'2017'].dropna(), r.loc['2018':].dropna()
    t = t_nw(c) * sg; an = (c.groupby(c.index.year).mean() * sg > 0).mean()
    ps.append(1 - stats.norm.cdf(t)); series[par + ('_tarde' if h0 == 8 and z0 == 'NY' else '')] = r * sg
    filas.append((par, z0, h0, z1, h1, sg, d.mean(), t_nw(d), c.mean(), t_nw(c), an, c.corr(e1.reindex(c.index))))
orden = np.argsort(ps); ok = [False] * len(P); seguir = True
for k, i in enumerate(orden):
    seguir = seguir and ps[i] <= 0.05 / (len(P) - k); ok[i] = seguir
for f, o in zip(filas, ok):
    par, z0, h0, z1, h1, sg, dm, dt, cm, ct, an, ce = f
    cert = (np.sign(dm) == sg) and o and an >= 0.6
    print(f'{par} {z0} {h0}:00→{z1} {h1}:00 (signo previsto {"+" if sg > 0 else "-"}): 2010-17 {dm*1e4:5.2f} pb (t {dt:.2f}) | '
          f'2018-26 {cm*1e4:5.2f} pb (t {ct:.2f}) años ok {an*100:.0f}% corr E1 {ce:.2f} | Holm {o} → {"CERTIFICADA" if cert else "no"}')
x = pd.DataFrame(series).loc['2018':]
print('\ncorrelaciones 2018-26 (en el sentido previsto):'); print(x.corr().round(2))
