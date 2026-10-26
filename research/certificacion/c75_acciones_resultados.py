"""C75: acciones de FTMO alrededor de la publicacion de resultados (reglas en PREREGISTRO_C75, commit 4c80015).
Uso: python3 c75_acciones_resultados.py DIR_PRECIOS_YAHOO 'fechas_*.csv'"""
import glob
import json
import os
import sys

import numpy as np
import pandas as pd

# RTN (Raytheon antigua) se excluye: Yahoo da para RTX la historia de UTX, no la de RTN (ver resultados).
ALIAS = {'FB': 'META', 'GOOGL': 'GOOG', 'UTX': 'RTX', 'BRK.B': 'BRK-B'}
COSTE = {'A1': 8e-4, 'A2': 8e-4, 'B': 20e-4}
T_EXITO = 2.13


def cargar_px(carpeta):
    px = {}
    for f in glob.glob(os.path.join(carpeta, '*.json')):
        j = json.load(open(f))['chart']['result'][0]
        q = j['indicators']['quote'][0]
        idx = pd.to_datetime(j['timestamp'], unit='s', utc=True).tz_convert('America/New_York').normalize()
        idx = idx.tz_localize(None)
        d = pd.DataFrame({'o': q['open'], 'c': q['close']}, index=idx).dropna()
        px[os.path.basename(f)[:-5]] = d[~d.index.duplicated()]
    return px


def cargar_eventos(patron):
    ev = []
    for f in glob.glob(patron):
        for l in open(f):
            p = l.rstrip('\n').split(';')
            if len(p) < 3 or p[1] != 'OK' or not p[2]:
                continue
            for x in p[2].split(','):
                s = x.split(':')[0]
                if s == 'RTN':
                    continue
                ev.append((pd.Timestamp(p[0]), ALIAS.get(s, s)))
    ev = pd.DataFrame(ev, columns=['F', 'sim']).drop_duplicates().sort_values(['sim', 'F'])
    return ev


def eventos_con_rentabilidades(px, ev):
    spy = px['SPY']
    filas, base = [], []
    for sim, g in ev.groupby('sim'):
        if sim not in px:
            continue
        d = px[sim].join(spy, rsuffix='_m', how='inner')
        idx = d.index
        o, c, om, cm = d.o.values, d.c.values, d.o_m.values, d.c_m.values
        ex1 = np.full(len(d), np.nan)
        ex1[1:] = c[1:] / c[:-1] - cm[1:] / cm[:-1]
        gap = np.full(len(d), np.nan)
        gap[1:] = (o[1:] / c[:-1] - 1) - (om[1:] / cm[:-1] - 1)
        Rs, ultimo = [], -999
        for F in g.F:
            if F not in idx:
                continue
            k = idx.get_loc(F)
            if k < 3 or k + 7 >= len(d) or np.isnan(gap[k]) or np.isnan(gap[k + 1]):
                continue
            R = k if abs(gap[k]) >= abs(gap[k + 1]) else k + 1
            if R - ultimo <= 10:                 # mismo anuncio repetido en el calendario
                continue
            ultimo = R
            Rs.append(R)
        if not Rs:
            continue
        fuera = np.ones(len(d), bool)
        for R in Rs:
            fuera[max(0, R - 10): R + 11] = False
        ex5 = np.full(len(d), np.nan)
        ex5[:-5] = c[5:] / c[:-5] - cm[5:] / cm[:-5]
        b1 = np.nanmean(ex1[fuera])
        b5 = np.nanmean(ex5[fuera])
        for R in Rs:
            a1 = ex1[R - 1]
            a2 = ex1[R]
            sgn = np.sign(a2)
            b = sgn * ex5[R]
            filas.append({'sim': sim, 'R': idx[R],
                          'A1': a1 - b1, 'A2': a2 - b1, 'B': b - sgn * b5,
                          'A1_bruta': c[R - 1] / c[R - 2] - 1, 'A2_bruta': c[R] / c[R - 1] - 1,
                          'B_bruta': sgn * (c[R + 5] / c[R] - 1)})
    return pd.DataFrame(filas)


def t_agrupado(x, fechas):
    m = pd.Series(x.values, index=fechas.values).groupby(level=0).mean()
    n = len(m)
    return x.mean(), m.mean() / m.std(ddof=1) * np.sqrt(n), n


def main():
    px = cargar_px(sys.argv[1])
    ev = cargar_eventos(sys.argv[2])
    e = eventos_con_rentabilidades(px, ev)
    e.to_csv('c75_eventos.csv', index=False)
    lin = [f'Eventos: {len(e)} en {e.sim.nunique()} acciones; {e.R.min().date()} a {e.R.max().date()}', '']
    for regla in ['A1', 'A2', 'B']:
        lin.append(f'== {regla} (coste supuesto {COSTE[regla] * 1e4:.0f} pb) ==')
        res = {}
        for nombre, sub in [('2012-2018', e[e.R < '2019-01-01']), ('2019-2026', e[e.R >= '2019-01-01']),
                            ('todo', e)]:
            m, t, nd = t_agrupado(sub[regla], sub.R)
            bruta = sub[regla + '_bruta'].mean()
            res[nombre] = (m, t)
            lin.append(f'  {nombre}: n {len(sub)} ({nd} fechas)  exceso ajustado {m * 1e4:+.1f} pb (t {t:+.2f})  '
                       f'neto {(m - COSTE[regla]) * 1e4:+.1f} pb   [rentab. bruta sin ajustar {bruta * 1e4:+.1f} pb]')
        anios = e.groupby(e.R.dt.year)[regla].mean() * 1e4
        lin.append('  por año (pb): ' + ', '.join(f'{a}:{v:+.0f}' for a, v in anios.items()))
        pasa = res['2019-2026'][1] >= T_EXITO and res['2012-2018'][0] > 0 and res['2019-2026'][0] > COSTE[regla]
        lin.append(f'  VEREDICTO {regla}: {"PASA (candidata)" if pasa else "NO PASA"}')
        lin.append('')
    txt = '\n'.join(lin)
    print(txt)
    open('c75_resultados.txt', 'w').write(txt + '\n')


if __name__ == '__main__':
    main()
