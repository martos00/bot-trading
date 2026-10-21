"""C11: impulso de la última media hora del S&P 500 condicionado a GEX < 0 (PREREGISTRO_C11_gamma_momentum.md).
Uso: python3 c11_gamma_momentum.py DIR_HISTDATA DIX_CSV"""
import glob, os, sys
import numpy as np
import pandas as pd
from c1_certificacion import t_nw

COSTE = 1.0e-4


def cierres(d):
    fs = sorted(glob.glob(os.path.join(d, 'SPXUSD', 'DAT_ASCII_SPXUSD_M1_*.csv')))
    x = pd.concat([pd.read_csv(f, sep=';', header=None, names=['ts', 'o', 'h', 'l', 'c', 'v']) for f in fs])
    t = pd.to_datetime(x.ts, format='%Y%m%d %H%M%S')
    s = pd.Series(x.c.values, index=t + pd.Timedelta(minutes=1)).sort_index()   # índice = fin de la vela
    s = s[~s.index.duplicated()]
    s = s[s.index.weekday < 5]
    out = {}
    for h, m in ((15, 30), (16, 0)):
        k = s[(s.index.hour * 60 + s.index.minute <= h * 60 + m) & (s.index.hour * 60 + s.index.minute > h * 60 + m - 5)]
        out[f'{h}{m:02d}'] = k.groupby(k.index.normalize()).last()
    return pd.DataFrame(out).dropna()


if __name__ == '__main__':
    p = cierres(sys.argv[1])
    g = pd.read_csv(sys.argv[2], index_col=0, parse_dates=True).gex
    p['prev'] = p['1600'].shift(1)
    p = p[(p.index.to_series().diff().dt.days <= 4)]
    p['gex_ant'] = g.shift(1).reindex(p.index)
    p = p.dropna()
    señal = np.sign(np.log(p['1530'] / p['prev']))
    p['bruto'] = señal * np.log(p['1600'] / p['1530'])
    p['neto'] = p.bruto - COSTE
    p.to_csv('c11_dias.csv')
    print(f'días {len(p)}; con GEX < 0: {(p.gex_ant < 0).sum()} ({(p.gex_ant < 0).mean()*100:.1f}%)')
    res = {}
    for nom, m in (('GEX < 0 (REGLA)', p.gex_ant < 0), ('GEX >= 0', p.gex_ant >= 0), ('sin condición', p.gex_ant == p.gex_ant)):
        for tramo, a, b in (('2011-2018', '2011', '2018'), ('2019-2026', '2019', '2026')):
            x = p[m].loc[a:b]
            an = x.neto.groupby(x.index.year).agg(['sum', 'size']); an = an[an['size'] >= 5]['sum']
            print(f'{nom:16s} {tramo}: n {len(x):4d}  bruto {x.bruto.mean()*1e4:6.2f} pb  neto {x.neto.mean()*1e4:6.2f} pb '
                  f'(t {t_nw(x.neto):5.2f})  bruto/coste {x.bruto.mean()/COSTE:5.2f}  años+ {int((an > 0).sum())}/{len(an)}')
            res[(nom, tramo)] = (x, an)
    c, an = res[('GEX < 0 (REGLA)', '2019-2026')]
    print('confirmación, neto por año (pb):', (c.neto.groupby(c.index.year).sum() * 1e4).round(0).to_dict())
    d = res[('GEX < 0 (REGLA)', '2011-2018')][0]
    crit = {'D: bruto>0': d.bruto.mean() > 0, '1: neto>0 t>=2': c.neto.mean() > 0 and t_nw(c.neto) >= 2,
            '2: bruto>=3x coste': c.bruto.mean() >= 3 * COSTE, '3: años>=60%': (an > 0).mean() >= 0.6}
    print('CRITERIOS:', crit, '→ CERTIFICADA' if all(crit.values()) else '→ NO CERTIFICADA')
    if os.path.exists('c9_spx.csv'):
        r = pd.read_csv('c9_spx.csv', index_col=0, parse_dates=True)
        r['gex_ant'] = g.shift(1).reindex(r.index)
        for nom, m in (('GEX >= 0', r.gex_ant >= 0), ('GEX < 0', r.gex_ant < 0)):
            x = r[m]
            print(f'C9 (regla del 80%) con {nom}: n {len(x)}  neto {x.neto.mean()*1e4:.2f} pb (t {t_nw(x.neto):.2f})')
