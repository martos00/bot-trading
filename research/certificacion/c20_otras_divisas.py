"""C20: USD/xxx de 07:00 Londres a 08:00 NY en SEK, NOK, PLN, HUF, ZAR, TRY (PREREGISTRO_C20_breedon_ranaldo_otras_divisas.md).
Uso: python3 c20_otras_divisas.py DIR_HISTDATA"""
import sys
import numpy as np
import pandas as pd
from c1_certificacion import t_nw
from c3_breedon_ranaldo import cargar_histdata, precio, instantes

PARES = ['USDSEK', 'USDNOK', 'USDPLN', 'USDHUF', 'USDZAR', 'USDTRY']
COSTE_REF = {'USDSEK': 3, 'USDNOK': 3, 'USDPLN': 4, 'USDHUF': 5, 'USDZAR': 6, 'USDTRY': 15}


def holm(ps):
    orden = np.argsort(ps); m = len(ps); ok = np.zeros(m, bool)
    for k, i in enumerate(orden):
        if ps[i] <= 0.05 / (m - k): ok[i] = True
        else: break
    return ok


if __name__ == '__main__':
    d = sys.argv[1]
    dias = pd.bdate_range('2010-01-04', '2026-09-30')
    T0, T1 = instantes(dias, 'LON', 7), instantes(dias, 'NY', 8)
    series = {}
    for p in PARES:
        mv = cargar_histdata(d, p)
        if mv is None:
            print('sin datos', p); continue
        m, v = mv
        r = pd.Series(np.log(precio(m, v, T1) / precio(m, v, T0)), index=dias)
        r[(r.abs() > 0.05)] = np.nan                     # saltos imposibles en 9 h (datos erróneos)
        series[p] = r
    x = pd.DataFrame(series)
    f = x.mean(axis=1, skipna=False).dropna()
    from scipy import stats
    print('== FACTOR (media de los 6 pares) ==')
    for a, b in (('2010', '2017'), ('2018', '2026')):
        y = f.loc[a:b]; an = y.groupby(y.index.year).mean()
        print(f'  {a}-{b}: n {len(y)} media {y.mean()*1e4:5.2f} pb/día (t {t_nw(y):.2f}) años+ {(an > 0).sum()}/{len(an)}')
    y = f.loc['2018':]; an = y.groupby(y.index.year).mean()
    crit = {'D>0': f.loc['2010':'2017'].mean() > 0, '1 t>=2': y.mean() > 0 and t_nw(y) >= 2, '2 años>=60%': (an > 0).mean() >= 0.6}
    print('  confirmación por año (pb/día):', (an * 1e4).round(2).to_dict())
    print('\n== PARES (informativo; Holm en confirmación) ==')
    ps, filas = [], []
    for p in x:
        y0, y1 = x[p].loc['2010':'2017'].dropna(), x[p].loc['2018':].dropna()
        t1 = t_nw(y1); ps.append(1 - stats.norm.cdf(t1))
        an = y1.groupby(y1.index.year).mean()
        filas.append(f'  {p}: 2010-17 {y0.mean()*1e4:5.2f} pb (t {t_nw(y0):.2f}) | 2018-26 {y1.mean()*1e4:5.2f} pb (t {t1:.2f}) '
                     f'años+ {(an > 0).sum()}/{len(an)} | coste ref {COSTE_REF[p]} pb → bruto/coste {y1.mean()*1e4/COSTE_REF[p]:.2f}')
    for fl, ok in zip(filas, holm(np.array(ps))):
        print(fl, '| Holm', 'SÍ' if ok else 'no')
    if 'USDTRY' in x:
        y = x['USDTRY'].loc['2018':]; y = y[~y.index.year.isin([2018, 2021, 2023])]
        print(f'  USDTRY sin 2018/2021/2023: {y.mean()*1e4:.2f} pb (t {t_nw(y.dropna()):.2f})')
    print('\nCRITERIOS FACTOR:', crit, '→ CERTIFICADA' if all(crit.values()) else '→ NO CERTIFICADA')
