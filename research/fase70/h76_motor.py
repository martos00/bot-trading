"""H76 — ORB de 5 minutos (Zarattini & Aziz 2023). Motor PRINCIPAL. Reglas en PREREGISTRO_H76_orb5.md.

Uso: python3 h76_motor.py DIR_HISTDATA SIMBOLO SALIDA_CSV [coste_pts deslizamiento_stop_pts] [aleatorio_semilla]
Salida: una fila por sesión NYSE completa con la operación (dirección, R en puntos, resultado en R bruto y
neto, rentabilidad sobre capital, peor flotante intradía en fracción del capital).
"""
import glob, os, sys
import numpy as np
import pandas as pd
import pandas_market_calendars as mcal

NY = 'America/New_York'
CAPITAL_INICIAL = 25_000.0


def cargar(directorio, sim):
    fs = sorted(glob.glob(os.path.join(directorio, f'DAT_ASCII_{sim}_M1_*.csv')))
    m1 = pd.concat([pd.read_csv(f, sep=';', header=None, names=['ts', 'o', 'h', 'l', 'c', 'v']) for f in fs], ignore_index=True)
    t = pd.to_datetime(m1['ts'], format='%Y%m%d %H%M%S').dt.tz_localize(NY, ambiguous='NaT', nonexistent='NaT')
    m1['t'] = t
    m1 = m1.dropna(subset=['t']).drop_duplicates('t').sort_values('t')
    hm = m1['t'].dt.hour * 100 + m1['t'].dt.minute
    m1 = m1[(hm >= 930) & (hm < 1600)].copy()
    m1['dia'] = m1['t'].dt.tz_localize(None).dt.normalize()
    m1['k'] = (m1['t'].dt.hour - 9) * 60 + m1['t'].dt.minute - 30
    return m1


def sesiones(ini, fin):
    cal = mcal.get_calendar('NYSE')
    s = cal.schedule(ini, fin)
    return set(pd.DatetimeIndex(s.index).difference(cal.early_closes(s).index))


def simular(m1, coste_pts, desliz_pts, semilla=None):
    rng = np.random.default_rng(semilla) if semilla is not None else None
    validos = sesiones(m1['dia'].min(), m1['dia'].max())
    cap = CAPITAL_INICIAL
    filas = []
    for dia, g in m1.groupby('dia'):
        if dia not in validos or len(g) < 380:
            continue
        g = g.set_index('k').reindex(range(390))
        if g.loc[0:4, 'o'].isna().any() or g.loc[[0, 4, 5]].isna().any().any():
            continue
        g = g.ffill()
        o1, c1 = g.at[0, 'o'], g.at[4, 'c']
        h1, l1 = g.loc[0:4, 'h'].max(), g.loc[0:4, 'l'].min()
        if rng is None:
            if c1 == o1:
                filas.append((dia, 0, np.nan, np.nan, np.nan, 0.0, 0.0, cap))
                continue
            lado = 1 if c1 > o1 else -1
        else:
            lado = rng.choice([-1, 1])
        ent = g.at[5, 'o']
        stop = l1 if lado == 1 else h1
        R = (ent - stop) * lado
        if not R > 0:   # la apertura de la segunda vela ya está más allá del stop
            filas.append((dia, lado, R, np.nan, np.nan, 0.0, 0.0, cap))
            continue
        obj = ent + lado * 10 * R
        unidades = min(0.01 * cap / R, 4 * cap / ent)
        salida, peor = None, 0.0
        for k in range(5, 390):
            o, h, l = g.at[k, 'o'], g.at[k, 'h'], g.at[k, 'l']
            adverso = l if lado == 1 else h
            peor = min(peor, (adverso - ent) * lado)
            toca_stop = (l <= stop) if lado == 1 else (h >= stop)
            toca_obj = (h >= obj) if lado == 1 else (l <= obj)
            if toca_stop:   # si coinciden stop y objetivo en la misma vela, se asume el stop
                px = min(o, stop) if lado == 1 else max(o, stop)
                salida = px - lado * desliz_pts
                break
            if toca_obj:
                salida = max(o, obj) if lado == 1 else min(o, obj)
                break
        if salida is None:
            salida = g.at[389, 'c']
        bruto_pts = (salida - ent) * lado
        neto_pts = bruto_pts - coste_pts
        pnl = unidades * neto_pts
        peor_eq = unidades * (min(peor, bruto_pts) - coste_pts)
        filas.append((dia, lado, R, bruto_pts / R, neto_pts / R, pnl / cap, min(peor_eq, pnl) / cap, cap))
        cap += pnl
    return pd.DataFrame(filas, columns=['dia', 'lado', 'R_pts', 'R_bruto', 'R_neto', 'ret', 'min_intradia', 'capital']).set_index('dia')


if __name__ == '__main__':
    directorio, sim, salida = sys.argv[1:4]
    coste = float(sys.argv[4]) if len(sys.argv) > 4 else 0.0
    desl = float(sys.argv[5]) if len(sys.argv) > 5 else 0.0
    sem = int(sys.argv[6]) if len(sys.argv) > 6 else None
    m1 = cargar(directorio, sim)
    df = simular(m1, coste, desl, sem)
    df.to_csv(salida)
    x = df.dropna(subset=['R_bruto'])
    print(sim, 'ops', len(x), 'R bruto medio %.3f' % x.R_bruto.mean(), 'R neto medio %.3f' % x.R_neto.mean(),
          'aciertos %.1f%%' % ((x.R_bruto > 0).mean() * 100), 'capital final %.0f' % (df.capital.iloc[-1] * (1 + df.ret.iloc[-1])))
