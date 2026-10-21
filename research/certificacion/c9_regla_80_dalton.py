"""C9: regla del 80% del Market Profile (Dalton) en S&P 500 / Nasdaq 100 (PREREGISTRO_C9_regla_80_dalton.md).
Uso: python3 c9_regla_80_dalton.py DIR_HISTDATA"""
import glob, os, sys
import numpy as np
import pandas as pd

COSTE, ESTRES = 1.0e-4, 2.0e-4


def cargar(d, sim):
    fs = sorted(glob.glob(os.path.join(d, sim, f'DAT_ASCII_{sim}_M1_*.csv')))
    x = pd.concat([pd.read_csv(f, sep=';', header=None, names=['ts', 'o', 'h', 'l', 'c', 'v']) for f in fs])
    x['t'] = pd.to_datetime(x.ts, format='%Y%m%d %H%M%S')
    x = x.drop_duplicates('t').set_index('t').sort_index()
    m = x.index.hour * 60 + x.index.minute
    x = x[(m >= 570) & (m < 960) & (x.index.weekday < 5)]          # 09:30-16:00 NY
    x['dia'] = x.index.normalize()
    x['per'] = (x.index.hour * 60 + x.index.minute - 570) // 30      # período de 30 min (0..12)
    return x


def zona_valor(s):
    """VAL, VAH del perfil TPO de la sesión s (velas M1)."""
    paso = s.c.iloc[-1] * 0.0005
    g = s.groupby('per').agg(h=('h', 'max'), l=('l', 'min'))
    lo = np.floor(g.l.min() / paso); hi = np.floor(g.h.max() / paso)
    niveles = np.arange(lo, hi + 1)
    cuenta = np.zeros(len(niveles))
    for _, p in g.iterrows():
        cuenta[(niveles >= np.floor(p.l / paso)) & (niveles <= np.floor(p.h / paso))] += 1
    centro = (len(niveles) - 1) / 2
    cand = np.flatnonzero(cuenta == cuenta.max())
    poc = cand[np.argmin(np.abs(cand - centro))]
    a = b = poc; total = cuenta[poc]
    while total < 0.7 * cuenta.sum():
        arriba = cuenta[b + 1] if b + 1 < len(cuenta) else -1
        abajo = cuenta[a - 1] if a - 1 >= 0 else -1
        if arriba >= abajo: b += 1; total += arriba
        else: a -= 1; total += abajo
    return niveles[a] * paso, (niveles[b] + 1) * paso


def operar(x):
    dias = [d for d, s in x.groupby('dia') if len(s) >= 350]
    sesiones = {d: s for d, s in x.groupby('dia')}
    ops = []
    for ayer, hoy in zip(dias[:-1], dias[1:]):
        if (hoy - ayer).days > 4:
            continue
        val, vah = zona_valor(sesiones[ayer])
        s = sesiones[hoy]
        ap = s.o.iloc[0]
        if val <= ap <= vah:
            continue
        lado = -1 if ap > vah else +1                               # −1 venta (abrió arriba), +1 compra
        cierres = s.groupby('per').c.last()
        dentro = (cierres >= val) & (cierres <= vah)
        ent_per = next((p for p in cierres.index[1:] if dentro.get(p) and dentro.get(p - 1)), None)
        if ent_per is None or 570 + (ent_per + 1) * 30 > 14 * 60:
            continue
        hasta = s[s.per <= ent_per]
        precio = cierres[ent_per]
        stop = hasta.h.max() if lado < 0 else hasta.l.min()
        obj = val if lado < 0 else vah
        if (stop - precio) * lado >= 0:                             # stop del lado equivocado: no hay operación
            continue
        resto = s[s.per > ent_per]
        salida, motivo = resto.c.iloc[-1] if len(resto) else precio, 'cierre'
        for _, v in resto.iterrows():
            if (lado < 0 and v.h >= stop) or (lado > 0 and v.l <= stop):
                salida, motivo = stop, 'stop'; break
            if (lado < 0 and v.l <= obj) or (lado > 0 and v.h >= obj):
                salida, motivo = obj, 'objetivo'; break
        bruto = lado * np.log(salida / precio)
        riesgo = abs(np.log(stop / precio))
        ops.append(dict(dia=hoy, lado=lado, bruto=bruto, neto=bruto - COSTE, estres=bruto - ESTRES,
                        R=(bruto - COSTE) / riesgo, motivo=motivo))
    return pd.DataFrame(ops).set_index('dia')


def t_simple(v):
    v = np.asarray(v, float)
    return v.mean() / (v.std(ddof=1) / np.sqrt(len(v)))


def informe(t, nombre):
    print(f'\n##### {nombre}: {len(t)} operaciones #####')
    for tramo, a, b in (('Descubrimiento 2010-2017', '2010', '2017'), ('Confirmación 2018-2026', '2018', '2026')):
        x = t.loc[a:b]
        anual = x.neto.groupby(x.index.year).sum()
        print(f'  {tramo}: n {len(x)}  bruto {x.bruto.mean()*1e4:6.2f} pb  neto {x.neto.mean()*1e4:6.2f} pb (t {t_simple(x.neto):.2f})  '
              f'estrés {x.estres.mean()*1e4:6.2f} pb  bruto/coste {x.bruto.mean()/COSTE:.2f}  R medio {x.R.mean():.3f}  '
              f'años+ {int((anual > 0).sum())}/{len(anual)}')
        print(f'     llegan al objetivo {(x.motivo == "objetivo").mean()*100:.0f}%  stop {(x.motivo == "stop").mean()*100:.0f}%  '
              f'cierre 16:00 {(x.motivo == "cierre").mean()*100:.0f}%   ventas/compras {(x.lado < 0).sum()}/{(x.lado > 0).sum()}')
    c = t.loc['2018':'2026']
    print('  confirmación, neto por año (pb):', (c.neto.groupby(c.index.year).sum() * 1e4).round(0).to_dict())
    return c


if __name__ == '__main__':
    d = sys.argv[1]
    spx = operar(cargar(d, 'SPXUSD')); spx.to_csv('c9_spx.csv')
    c = informe(spx, 'S&P 500 (principal)')
    nsx = operar(cargar(d, 'NSXUSD')); nsx.to_csv('c9_nsx.csv')
    informe(nsx, 'Nasdaq 100 (informativo)')
    dsc = spx.loc['2010':'2017']
    anual = c.neto.groupby(c.index.year).sum()
    crit = {'D: neto > 0': dsc.neto.mean() > 0, '1: neto > 0, t >= 2': c.neto.mean() > 0 and t_simple(c.neto) >= 2,
            '2: bruto >= 3x coste': c.bruto.mean() >= 3 * COSTE, '3: años >= 60%': (anual > 0).mean() >= 0.6}
    print('\nCRITERIOS (S&P 500):', crit, '→ CERTIFICADA' if all(crit.values()) else '→ NO CERTIFICADA')
