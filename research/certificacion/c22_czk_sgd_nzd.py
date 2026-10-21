"""C22: efecto de horario local en USDCZK (Europa), USDSGD (Singapur) y NZDUSD (Wellington). Ver PREREGISTRO_C22."""
import sys
import numpy as np, pandas as pd
from scipy import stats
from c1_certificacion import t_nw
import c3_breedon_ranaldo as C3
C3.TZ.update({'SGP': 'Asia/Singapore', 'WLG': 'Pacific/Auckland'})
S = sys.argv[1]
dias = pd.bdate_range('2010-01-04', '2026-09-30')
# (par, carpeta, zona inicio, hora inicio, zona fin, hora fin, sentido previsto: +1, -1 o 0 = bilateral)
P = [('USDCZK', 'hd_c20', 'LON', 7, 'NY', 8, +1), ('USDSGD', 'hd_c20', 'SGP', 9, 'SGP', 17, 0),
     ('NZDUSD', 'hd_new', 'WLG', 10, 'WLG', 17, 0)]
e = pd.read_csv('e1_franjas.csv', index_col=0, parse_dates=True); e1 = -np.log(e.mid8 / e.mid6)
ps, crit = [], {}
for par, carp, z0, h0, z1, h1, sentido in P:
    m, v = C3.cargar_histdata(S + carp, par)
    T0, T1 = C3.instantes(dias, z0, h0), C3.instantes(dias, z1, h1)
    p0, p1 = C3.precio(m, v, T0), C3.precio(m, v, T1)
    r = pd.Series(np.log(p1 / p0), index=dias); r[r.abs() > 0.05] = np.nan
    resto = pd.Series(np.log(np.r_[p0[1:], np.nan] / p1), index=dias); resto[resto.abs() > 0.05] = np.nan
    d, c = r.loc['2010':'2017'].dropna(), r.loc['2018':].dropna()
    sg = sentido if sentido else np.sign(d.mean())
    t = t_nw(c) * sg; an = (c.groupby(c.index.year).mean() * sg > 0).mean()
    ps.append(1 - stats.norm.cdf(t))
    print(f'{par} ({z0} {h0}:00 → {z1} {h1}:00): 2010-17 {d.mean()*1e4:5.2f} pb (t {t_nw(d):.2f}) | 2018-26 {c.mean()*1e4:5.2f} pb '
          f'(t {t_nw(c):.2f}) | sentido usado {"+" if sg > 0 else "-"} | años con ese signo {an*100:.0f}% | '
          f'resto del día 2018-26 {resto.loc["2018":].mean()*1e4:.2f} pb | corr E1 {c.corr(e1.reindex(c.index)):.2f}')
    crit[par] = dict(signo_D=bool(sentido == 0 or np.sign(d.mean()) == sentido), t=t, años=an)
orden = np.argsort(ps); ok = {}
for k, i in enumerate(orden):
    ok[P[i][0]] = ps[i] <= 0.05 / (3 - k) and all(ok.values()) if k else ps[i] <= 0.05 / 3
for par, c in crit.items():
    cert = c['signo_D'] and ok[par] and c['años'] >= 0.6
    print(f'CRITERIOS {par}: {c} Holm {ok[par]} → {"CERTIFICADA" if cert else "NO CERTIFICADA"}')
