"""C7: cambio de mes y víspera de festivo en el S&P 500 (PREREGISTRO_C7_cambio_mes_festivos.md).
Uso: python3 c7_cambio_mes_festivos.py DIR_YAHOO"""
import json, os, sys
import numpy as np
import pandas as pd

SPREAD, FIN_NOCHE = 0.5e-4, 2.0e-4
NO_PROGRAMADOS = pd.to_datetime(['2001-09-11', '2001-09-12', '2001-09-13', '2001-09-14', '2012-10-29', '2012-10-30',
                                 '2004-06-11', '2007-01-02', '2018-12-05', '2025-01-09'])


def yahoo(d, s):
    r = json.load(open(os.path.join(d, f'{s}.json')))['chart']['result'][0]
    idx = pd.to_datetime(r['timestamp'], unit='s', utc=True).tz_convert('America/New_York').tz_localize(None).normalize()
    x = pd.Series(r['indicators']['quote'][0]['close'], index=idx).dropna()
    return x[~x.index.duplicated(keep='last')]


def operaciones(p):
    """Devuelve (lista de operaciones R1, lista R2, máscara diaria R1, máscara diaria R2)."""
    p = p[p.index <= '2026-09-30']
    s = p.index
    r = np.log(p).diff()
    mes = s.to_period('M')
    ult = np.where(mes[:-1] != mes[1:])[0]            # posición de la última sesión de cada mes
    r1, m1 = [], pd.Series(False, index=s)
    for i in ult:
        a, b = i - 2, i + 3                               # cierre −2 → cierre +3
        if a < 0 or b >= len(s):
            continue
        r1.append((s[a], s[b])); m1.iloc[a + 1:b + 1] = True
    r2, m2 = [], pd.Series(False, index=s)
    sesiones = set(s)
    for i in range(1, len(s) - 1):
        sig = s[i] + pd.offsets.BDay(1)
        if sig in sesiones or sig in NO_PROGRAMADOS or s[i] + pd.Timedelta(days=1) in NO_PROGRAMADOS:
            continue
        if sig > s[-1]:
            continue
        r2.append((s[i - 1], s[i])); m2.iloc[i] = True
    return p, r, r1, r2, m1, m2


def tabla(p, ops):
    t = pd.DataFrame(ops, columns=['ini', 'fin'])
    t['bruto'] = np.log(p.loc[t.fin].values / p.loc[t.ini].values)
    t['noches'] = (t.fin - t.ini).dt.days
    t['coste'] = SPREAD + FIN_NOCHE * t.noches
    t['neto'] = t.bruto - t.coste
    return t.set_index('fin')


def t_simple(x):
    x = np.asarray(x, float); x = x[~np.isnan(x)]
    return x.mean() / (x.std(ddof=1) / np.sqrt(len(x)))


def t_dif(a, b):
    a, b = a.dropna(), b.dropna()
    return (a.mean() - b.mean()) / np.sqrt(a.var() / len(a) + b.var() / len(b))


def evaluar(nombre, p, e1):
    p, r, r1, r2, m1, m2 = operaciones(p)
    res = {}
    print(f'\n######## {nombre} ########')
    for regla, ops, m in (('R1 cambio de mes', r1, m1), ('R2 víspera de festivo', r2, m2)):
        t = tabla(p, ops)
        print(f'\n== {regla}: {len(t)} operaciones; coste medio {t.coste.mean()*1e4:.1f} pb ({t.noches.mean():.1f} noches)')
        for tramo, a, b in (('Descubrimiento 1990-2007', '1990', '2007'), ('Confirmación 2008-2026', '2008', '2026')):
            tt, rr, mm = t.loc[a:b], r.loc[a:b], m.loc[a:b]
            dif = rr[mm].mean() - rr[~mm].mean()
            anual = tt.neto.groupby(tt.index.year).sum()
            print(f'  {tramo}: n {len(tt)}  bruto {tt.bruto.mean()*1e4:6.1f} pb (t {t_simple(tt.bruto):.2f})  '
                  f'neto {tt.neto.mean()*1e4:6.1f} pb (t {t_simple(tt.neto):.2f})  bruto/coste {tt.bruto.mean()/tt.coste.mean():.2f}')
            print(f'     media diaria ventana {rr[mm].mean()*1e4:.2f} pb vs resto {rr[~mm].mean()*1e4:.2f} pb  dif {dif*1e4:.2f} pb  '
                  f't {t_dif(rr[mm], rr[~mm]):.2f}   años netos + {int((anual > 0).sum())}/{len(anual)}')
            res[(regla, tramo)] = dict(tt=tt, dif_t=t_dif(rr[mm], rr[~mm]), dif=dif, anual=anual)
        c = res[(regla, 'Confirmación 2008-2026')]['tt']
        eq = c.neto.cumsum()
        print(f'  confirmación: peor operación {c.bruto.min()*100:.1f}%  caída máx. acumulada (1× capital) {(eq - eq.cummax()).min()*100:.1f}%')
        print('  neto por año (%):', (res[(regla, 'Confirmación 2008-2026')]['anual'] * 100).round(1).to_dict())
        if e1 is not None:
            v = [e1[(e1.index > i) & (e1.index <= f)].sum() for i, f in zip(c.ini, c.index)]
            print(f'  correlación con E1 en la misma ventana: {np.corrcoef(c.neto, v)[0, 1]:.3f}')
    return res


if __name__ == '__main__':
    d = sys.argv[1]
    e1 = None
    if os.path.exists('e1_franjas.csv'):
        x = pd.read_csv('e1_franjas.csv', index_col=0, parse_dates=True)
        e1 = (-np.log(x.mid8 / x.mid6)).dropna()
    res = evaluar('S&P 500 (^GSPC) — PRUEBA PRINCIPAL', yahoo(d, 'GSPC'), e1)
    evaluar('Nasdaq 100 (^NDX) — informativo', yahoo(d, 'NDX'), None)
    print('\n======== CRITERIOS (S&P 500) ========')
    for regla in ('R1 cambio de mes', 'R2 víspera de festivo'):
        dsc, cnf = res[(regla, 'Descubrimiento 1990-2007')], res[(regla, 'Confirmación 2008-2026')]
        tt = cnf['tt']
        crit = {'D: dif>0 t>=2': dsc['dif'] > 0 and dsc['dif_t'] >= 2,
                'C1: neto>0 t>=2,24': tt.neto.mean() > 0 and t_simple(tt.neto) >= 2.24,
                'C2: dif>0 t>=1,645': cnf['dif'] > 0 and cnf['dif_t'] >= 1.645,
                'C3: años>=60%': (cnf['anual'] > 0).mean() >= 0.6,
                'C4: bruto>=3x coste': tt.bruto.mean() >= 3 * tt.coste.mean()}
        print(regla, crit, '→ CERTIFICADA' if all(crit.values()) else '→ NO CERTIFICADA')
