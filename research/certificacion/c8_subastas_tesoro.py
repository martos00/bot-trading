"""C8: ciclo de subastas del Tesoro (Lou-Yan-Zhang 2013) en futuros de bonos (PREREGISTRO_C8_subastas_tesoro.md).
Uso: python3 c8_subastas_tesoro.py DIR (con c8_subastas.json, c8_DGS2.csv, c8_DGS5.csv) RUTA_DGS10"""
import json, os, sys
import numpy as np
import pandas as pd

TICK_COM = {'5': (7.8125 + 4.0), '2': (7.8125 + 4.0), '10': (15.625 + 4.0)}   # 1 tick + comisión por ida y vuelta (USD)
NOMINAL = {'5': 100_000, '2': 200_000, '10': 100_000}
TERMINOS = {'5': ('5-Year',), '2': ('2-Year',), '10': ('10-Year', '9-Year 11-Month', '9-Year 10-Month')}


def precio_par(y, plazo):
    """Rentabilidad diaria de un bono a la par con cupón = rendimiento de ayer, revalorizado al de hoy (pagos semestrales)."""
    y = y / 100
    c = y.shift(1)
    n = int(plazo * 2)
    k = np.arange(1, n + 1)[:, None]
    precio = (c.values / 2 / (1 + y.values / 2) ** k).sum(axis=0) + 1 / (1 + y.values / 2) ** n
    return pd.Series(np.log(precio) + c.values / 252, index=y.index)   # incluye el devengo del cupón


def t_simple(x):
    x = np.asarray(x, float); x = x[~np.isnan(x)]
    return x.mean() / (x.std(ddof=1) / np.sqrt(len(x)))


def ciclo(plazo, y, subastas, e1=None, principal=False):
    r = precio_par(y, int(plazo)).dropna()
    s = r.index
    fechas = sorted({pd.Timestamp(x['auction_date']) for x in subastas if x['security_term'] in TERMINOS[plazo]
                     and x['inflation_index_security'] == 'No' and x['floating_rate'] == 'No'})
    filas, ultima = [], None
    for f in fechas:
        if f not in s:
            continue
        i = s.get_loc(f)
        if i < 5 or i + 5 >= len(s) or (ultima is not None and i - ultima < 11):
            continue
        ultima = i
        antes = r.iloc[i - 4:i + 1].sum()           # cierre −5 → cierre 0
        despues = r.iloc[i + 1:i + 6].sum()         # cierre 0 → cierre +5
        filas.append(dict(dia=f, corto_antes=-antes, largo_despues=despues))
    t = pd.DataFrame(filas).set_index('dia')
    t['bruto'] = t.corto_antes + t.largo_despues
    t['coste'] = 2 * TICK_COM[plazo] / NOMINAL[plazo]
    t['neto'] = t.bruto - t.coste
    print(f'\n===== Nota a {plazo} años ({"PRINCIPAL" if principal else "informativo"}): {len(t)} subastas; coste {t.coste.iloc[0]*1e4:.2f} pb/ciclo =====')
    for tramo, a, b in (('Réplica 1990-jun 2008', '1990-01-01', '2008-06-30'), ('Confirmación jul 2008-2026', '2008-07-01', '2026-09-30')):
        x = t.loc[a:b]
        anual = x.neto.groupby(x.index.year).sum()
        print(f'  {tramo}: n {len(x)}  bruto {x.bruto.mean()*1e4:6.2f} pb (t {t_simple(x.bruto):.2f})  neto {x.neto.mean()*1e4:6.2f} pb '
              f'(t {t_simple(x.neto):.2f})  bruto/coste {x.bruto.mean()/x.coste.mean():.1f}  años+ {int((anual>0).sum())}/{len(anual)}')
        print(f'     pata corto antes {x.corto_antes.mean()*1e4:.2f} pb (t {t_simple(x.corto_antes):.2f}) | '
              f'largo después {x.largo_despues.mean()*1e4:.2f} pb (t {t_simple(x.largo_despues):.2f})')
    c = t.loc['2008-07-01':'2026-09-30']
    print('  confirmación, neto por año (pb):', (c.neto.groupby(c.index.year).sum() * 1e4).round(0).to_dict())
    print(f'  confirmación: peor ciclo {c.bruto.min()*1e4:.0f} pb; desv. típica por ciclo {c.bruto.std()*1e4:.0f} pb')
    if e1 is not None:
        v = [e1[(e1.index > s[s.get_loc(d) - 5]) & (e1.index <= s[s.get_loc(d) + 5])].sum() for d in c.index]
        print(f'  correlación con E1 en la misma ventana: {np.corrcoef(c.neto, v)[0, 1]:.3f}')
    return t


if __name__ == '__main__':
    d, ruta10 = sys.argv[1:3]
    subastas = json.load(open(os.path.join(d, 'c8_subastas.json')))['data']
    lee = lambda f: pd.read_csv(f, index_col=0, parse_dates=True, na_values='.').iloc[:, 0].dropna()
    e1 = None
    if os.path.exists('e1_franjas.csv'):
        x = pd.read_csv('e1_franjas.csv', index_col=0, parse_dates=True)
        e1 = (-np.log(x.mid8 / x.mid6)).dropna()
    t5 = ciclo('5', lee(os.path.join(d, 'c8_DGS5.csv')), subastas, e1, principal=True)
    ciclo('2', lee(os.path.join(d, 'c8_DGS2.csv')), subastas)
    ciclo('10', lee(ruta10), subastas)
    rep, c = t5.loc['1990':'2008-06-30'], t5.loc['2008-07-01':'2026-09-30']
    anual = c.neto.groupby(c.index.year).sum()
    crit = {'réplica bruto > 0': rep.bruto.mean() > 0,
            '1 neto > 0, t >= 2': c.neto.mean() > 0 and t_simple(c.neto) >= 2,
            '2 bruto >= 3x coste': c.bruto.mean() >= 3 * c.coste.mean(),
            '3 años >= 60%': (anual > 0).mean() >= 0.6}
    print('\nCRITERIOS (5 años):', crit, '→ CERTIFICADA' if all(crit.values()) else '→ NO CERTIFICADA')
