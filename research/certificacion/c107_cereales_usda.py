"""C107 — cereales en los días de informes del USDA (PREREGISTRO_C107). Uso: python3 c107_cereales_usda.py DIR_SCRATCH"""
import sys
import numpy as np, pandas as pd
from c1_certificacion import t_nw
import c94_ruptura_otros_futuros as c94
SP = sys.argv[1]; c94.SP = SP
W = pd.to_datetime(open('datos_c107_fechas_wasde.txt').read().split())
Q = []
for y in range(2010, 2027):
    for m in (3, 6, 9):
        d = pd.Timestamp(y, m, 1) + pd.offsets.BMonthEnd(0); Q.append(d)
INF = set(W) | set(Q)
COSTE = {'ZC': 3.0, 'ZS': 2.5, 'ZW': 3.5}
for f in ('ZC', 'ZS', 'ZW'):
    h, ex = c94.carga_h1(f)
    n = h.index.tz_localize(None); h = h.copy(); h['dia'] = n.normalize(); h['hora'] = n.hour
    c = h.pivot_table(index='dia', columns='hora', values='c', aggfunc='last')
    if not all(k in c for k in (11, 12, 13)): print(f, 'faltan horas'); continue
    sesion = (pd.Series(c.index, index=c.index) + pd.Timedelta(hours=7)).dt.normalize()
    ok = ~c.index.isin(list(ex)); c = c[ok & (c.index.dayofweek < 5)]
    A = np.log(c[13] / c[13].shift(1)) * 1e4                     # 14:00 de ayer → 14:00 de hoy (cierre barra 13)
    B = np.sign(np.log(c[12] / c[11])) * np.log(c[13] / c[12]) * 1e4
    dia = A.index.isin(list(INF))
    for nom, s in (('A prima día de informe', A), ('B continuación tras el dato', B)):
        r = s[dia].dropna(); ctrl = s[~dia].dropna(); a, b = r.loc[:'2017'], r.loc['2018':]
        crit = {'>coste y t>=2,64': r.mean() > COSTE[f] and t_nw(r.values) >= 2.64, '2010-17>0': a.mean() > 0, '2018-26>0': b.mean() > 0}
        if nom.startswith('A'):
            dif = r.mean() - ctrl.mean(); se = np.sqrt(r.var() / len(r) + ctrl.var() / len(ctrl)); crit['> control (t>=2)'] = dif / se >= 2
            extra = f' | control {ctrl.mean():+.2f} (dif t {dif/se:.2f})'
        else: extra = ''
        print(f'{f} {nom}: n {len(r)} {r.mean():+.2f} pb (t {t_nw(r.values):.2f}) | 2010-17 {a.mean():+.2f} | 2018-26 {b.mean():+.2f}{extra} → '
              + ('PASA' if all(crit.values()) else 'no pasa'))
