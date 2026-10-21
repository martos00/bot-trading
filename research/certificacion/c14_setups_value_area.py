"""C14: setups P (ping pong), B (breakout y test) y F (subasta fallida) sobre la zona de valor TPO del día anterior
(PREREGISTRO_C14_setups_value_area.md). Uso: python3 c14_setups_value_area.py DIR_HISTDATA"""
import sys
import numpy as np
import pandas as pd
from c9_regla_80_dalton import cargar, zona_valor, t_simple

COSTE, LIMITE = 1.0e-4, 14 * 60            # entradas hasta las 14:00


def salida(h, l, c, k, lado, stop, obj, mismo_bar_stop=True):
    """Precio de salida desde la vela k (la de entrada). Stop primero si coincide; objetivo desde la vela siguiente."""
    for j in range(k, len(c)):
        if (lado < 0 and h[j] >= stop) or (lado > 0 and l[j] <= stop):
            return stop
        if j > k and ((lado < 0 and l[j] <= obj) or (lado > 0 and h[j] >= obj)):
            return obj
    return c[-1]


def dia(s, val, vah):
    A = vah - val
    h, l, c, o = s.h.values, s.l.values, s.c.values, s.o.values
    mins = s.index.hour * 60 + s.index.minute
    per = s.per.values
    out = []
    dentro_ap = val <= o[0] <= vah
    # P: primer toque de un borde abriendo dentro
    if dentro_ap:
        for k in range(len(c)):
            if mins[k] >= LIMITE:
                break
            if h[k] >= vah:
                out.append(('P', -1, vah, salida(h, l, c, k, -1, vah + 0.25 * A, val))); break
            if l[k] <= val:
                out.append(('P', +1, val, salida(h, l, c, k, +1, val - 0.25 * A, vah))); break
    # B: cierre de período fuera y regreso al borde
    cierres = s.groupby('per').c.last()
    fin_per = {p: np.flatnonzero(per == p)[-1] for p in cierres.index}
    for p, cp in cierres.items():
        if mins[fin_per[p]] >= LIMITE:
            break
        if cp > vah or cp < val:
            lado = +1 if cp > vah else -1
            borde = vah if lado > 0 else val
            for k in range(fin_per[p] + 1, len(c)):
                if mins[k] >= LIMITE:
                    break
                if (lado > 0 and l[k] <= borde) or (lado < 0 and h[k] >= borde):
                    stop = borde - 0.25 * A if lado > 0 else borde + 0.25 * A
                    out.append(('B', lado, borde, salida(h, l, c, k, lado, stop, borde + lado * A))); break
            break
    # F: abre dentro, cotiza fuera y un período vuelve a cerrar dentro
    if dentro_ap:
        fuera = 0
        for p, cp in cierres.items():
            k = fin_per[p]
            if mins[k] >= LIMITE:
                break
            ih = np.flatnonzero(per <= p)
            if fuera == 0:
                if h[ih].max() > vah: fuera = +1
                elif l[ih].min() < val: fuera = -1
                if fuera and not (val <= cp <= vah):
                    continue
            if fuera and val <= cp <= vah and (h[ih].max() > vah if fuera > 0 else l[ih].min() < val):
                lado = -fuera
                stop = h[:k + 1].max() if lado < 0 else l[:k + 1].min()
                obj = val if lado < 0 else vah
                if (stop - cp) * lado < 0:
                    out.append(('F', lado, cp, salida(h, l, c, k + 1, lado, stop, obj) if k + 1 < len(c) else cp))
                break
    return out


def operar(x):
    dias = [d for d, s in x.groupby('dia') if len(s) >= 350]
    ses = {d: s for d, s in x.groupby('dia')}
    filas = []
    for ayer, hoy in zip(dias[:-1], dias[1:]):
        if (hoy - ayer).days > 4:
            continue
        val, vah = zona_valor(ses[ayer])
        for regla, lado, pe, ps in dia(ses[hoy], val, vah):
            b = lado * np.log(ps / pe)
            filas.append(dict(dia=hoy, regla=regla, lado=lado, bruto=b, neto=b - COSTE))
    return pd.DataFrame(filas).set_index('dia')


def informe(t, nombre):
    res = {}
    for r in ('P', 'B', 'F'):
        x0 = t[t.regla == r]
        print(f'\n== {nombre} — {r}: {len(x0)} operaciones ==')
        for tramo, a, b in (('Descubrimiento 2010-2017', '2010', '2017'), ('Confirmación 2018-2026', '2018', '2026')):
            x = x0.loc[a:b]; an = x.neto.groupby(x.index.year).sum()
            print(f'  {tramo}: n {len(x)} bruto {x.bruto.mean()*1e4:6.2f} pb neto {x.neto.mean()*1e4:6.2f} pb (t {t_simple(x.neto):.2f}) '
                  f'bruto/coste {x.bruto.mean()/COSTE:.2f} años+ {int((an > 0).sum())}/{len(an)} aciertos {(x.bruto > 0).mean()*100:.0f}%')
            res[(r, a)] = (x, an)
    return res


if __name__ == '__main__':
    d = sys.argv[1]
    spx = operar(cargar(d, 'SPXUSD')); spx.to_csv('c14_spx.csv')
    res = informe(spx, 'S&P 500 (principal)')
    nsx = operar(cargar(d, 'NSXUSD')); nsx.to_csv('c14_nsx.csv')
    informe(nsx, 'Nasdaq 100 (informativo)')
    print('\nCRITERIOS (S&P 500, t >= 2,39):')
    for r in ('P', 'B', 'F'):
        dsc, (c, an) = res[(r, '2010')][0], res[(r, '2018')]
        crit = {'D>0': dsc.neto.mean() > 0, '1 t>=2,39': c.neto.mean() > 0 and t_simple(c.neto) >= 2.39,
                '2 bruto>=3x': c.bruto.mean() >= 3 * COSTE, '3 años>=60%': (an > 0).mean() >= 0.6}
        print(' ', r, crit, '→ CERTIFICADA' if all(crit.values()) else '→ NO CERTIFICADA')
