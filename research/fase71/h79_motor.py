"""H79 — ORB de 15 min en MNQ (bot del usuario). Motor PRINCIPAL. Reglas en PREREGISTRO_H79_orb15_mnq_usuario.md.
Uso: python3 h79_motor.py DIR_HISTDATA_NSX SALIDA_CSV [tick_desliz comision_rt] [semilla_dir_aleatoria]"""
import glob, os, sys
import numpy as np
import pandas as pd
import pandas_market_calendars as mcal

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..'))
import calidad_datos  # noqa: E402

NY = 'America/New_York'
CUENTA, RIESGO, PV = 50_000.0, 0.005, 2.0
K_RANGO, K_CIERRE = 15, 375          # velas 0-14 = 09:30-09:44; vela 375 = 15:45


def cargar(directorio):
    fs = sorted(glob.glob(os.path.join(directorio, 'DAT_ASCII_NSXUSD_M1_*.csv')))
    m = pd.concat([pd.read_csv(f, sep=';', header=None, names=['ts', 'o', 'h', 'l', 'c', 'v']) for f in fs], ignore_index=True)
    m['t'] = pd.to_datetime(m.ts, format='%Y%m%d %H%M%S').dt.tz_localize(NY, ambiguous='NaT', nonexistent='NaT')
    m = m.dropna(subset=['t']).drop_duplicates('t').sort_values('t')
    m['dia'] = m.t.dt.tz_localize(None).dt.normalize()
    d = m.groupby('dia').agg(Open=('o', 'first'), High=('h', 'max'), Low=('l', 'min'), Close=('c', 'last')).reset_index()
    aud = calidad_datos.auditar_historico(d[d.dia.dt.weekday < 5], 'NSXUSD HistData M1')
    aud.imprimir()
    m['k'] = (m.t.dt.hour - 9) * 60 + m.t.dt.minute - 30
    return m[(m.k >= 0) & (m.k <= K_CIERRE)], aud


def dias_validos(ini, fin):
    cal = mcal.get_calendar('NYSE')
    s = cal.schedule(ini, fin)
    return set(pd.DatetimeIndex(s.index).difference(cal.early_closes(s).index))


def operar(o, h, l, c, desliz, comision, lado_azar=None):
    """o,h,l,c: arrays de 376 velas (0 = 09:30). Devuelve (lado, contratos, pts_netos, pnl, peor_pnl) o None."""
    hi, lo = h[:K_RANGO].max(), l[:K_RANGO].min()
    sl = (hi - lo) / 2
    if not sl > 0:
        return None
    bs, ss = hi + 2, lo - 2
    for k in range(K_RANGO, K_CIERRE):
        tb, ts = h[k] >= bs, l[k] <= ss
        if not (tb or ts):
            continue
        if tb and ts:
            lado = 1 if abs(o[k] - bs) <= abs(o[k] - ss) else -1
        else:
            lado = 1 if tb else -1
        base = max(o[k], bs) if lado == 1 else min(o[k], ss)
        if lado_azar is not None:
            lado = lado_azar
        break
    else:
        return None
    n = max(1, int(CUENTA * RIESGO / (sl * PV)))
    stop, obj = base - lado * sl, base + lado * 2 * sl
    ent = base + lado * desliz
    peor, salida = 0.0, None
    for j in range(k, K_CIERRE):
        adv = l[j] if lado == 1 else h[j]
        fav = h[j] if lado == 1 else l[j]
        peor = min(peor, (adv - ent) * lado)
        if (adv - stop) * lado <= 0:
            px = stop if j == k else (min(o[j], stop) if lado == 1 else max(o[j], stop))
            salida = px - lado * desliz
            break
        if (fav - obj) * lado >= 0 and (j > k or (c[j] - obj) * lado >= 0):
            salida = obj if j == k else (max(o[j], obj) if lado == 1 else min(o[j], obj))
            break
    if salida is None:
        salida = (o[K_CIERRE] if not np.isnan(o[K_CIERRE]) else c[K_CIERRE - 1]) - lado * desliz
    pts = (salida - ent) * lado
    pnl = n * (pts * PV - comision)
    return lado, n, pts, pnl, min(n * (min(peor, pts) * PV - comision), pnl)


def simular(m1, desliz, comision, semilla=None):
    rng = np.random.default_rng(semilla) if semilla is not None else None
    validos = dias_validos(m1.dia.min(), m1.dia.max())
    filas = []
    for dia, g in m1.groupby('dia'):
        if dia not in validos or len(g) < 370:
            continue
        g = g.set_index('k').reindex(range(K_CIERRE + 1))
        if g.loc[0:K_RANGO, ['h', 'l']].isna().any().any():
            continue
        o_ult = g.at[K_CIERRE, 'o']
        g = g.ffill()
        o, h, l, c = (g[x].to_numpy() for x in 'ohlc')
        o = o.copy(); o[K_CIERRE] = o_ult
        r = operar(o, h, l, c, desliz, comision, None if rng is None else rng.choice([-1, 1]))
        filas.append((dia,) + (r if r else (0, 0, np.nan, 0.0, 0.0)))
    df = pd.DataFrame(filas, columns=['dia', 'lado', 'contratos', 'pts', 'pnl', 'peor']).set_index('dia')
    df['ret'], df['min_intradia'] = df.pnl / CUENTA, df.peor / CUENTA
    return df


if __name__ == '__main__':
    d, out = sys.argv[1:3]
    desl = float(sys.argv[3]) if len(sys.argv) > 3 else 0.25
    com = float(sys.argv[4]) if len(sys.argv) > 4 else 1.50
    sem = int(sys.argv[5]) if len(sys.argv) > 5 else None
    m1, aud = cargar(d)
    df = simular(m1, desl, com, sem)
    df.to_csv(out)
    x = df[df.lado != 0]
    print(f'días {len(df)}  operaciones {len(x)}  pnl total {df.pnl.sum():,.0f} $  media/día {df.pnl.mean():.1f} $')
