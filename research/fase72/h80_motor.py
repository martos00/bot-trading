"""H80 — rentabilidad de cada franja horaria (inicio 0-23 h NY, duración 1 y 2 h) por día. Motor PRINCIPAL (vectorizado).
Reglas en PREREGISTRO_H80_franjas_horarias.md.
Uso: python3 h80_motor.py DIR_HISTDATA SIMBOLO SALIDA_CSV"""
import glob, os, sys
import numpy as np
import pandas as pd

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..'))
import calidad_datos  # noqa: E402

NY = 'America/New_York'
TOL = pd.Timedelta(minutes=5)


def franjas():
    """(inicio, duración) válidas: se excluye toda franja que toque 17:00-18:00 ET."""
    return [(h, d) for d in (1, 2) for h in range(24) if not (h < 18 and h + d > 17)]


def cargar(directorio, sim):
    fs = sorted(glob.glob(os.path.join(directorio, f'DAT_ASCII_{sim}_M1_*.csv')))
    m = pd.concat([pd.read_csv(f, sep=';', header=None, names=['ts', 'o', 'h', 'l', 'c', 'v']) for f in fs], ignore_index=True)
    m['t'] = pd.to_datetime(m.ts, format='%Y%m%d %H%M%S').dt.tz_localize(NY, ambiguous='NaT', nonexistent='NaT')
    m = m.dropna(subset=['t']).drop_duplicates('t').sort_values('t')
    m = m[(m.t >= pd.Timestamp('2010-01-01', tz=NY)) & (m.t < pd.Timestamp('2026-10-01', tz=NY))]
    d = m.assign(dia=m.t.dt.tz_localize(None).dt.normalize()).groupby('dia').agg(
        Open=('o', 'first'), High=('h', 'max'), Low=('l', 'min'), Close=('c', 'last')).reset_index()
    aud = calidad_datos.auditar_historico(d[d.dia.dt.weekday < 5], f'{sim} HistData M1')
    aud.imprimir()
    return m, aud


def precio_en(cierre_t, cierre_v, T):
    """Cierre del último minuto que termina en o antes de T (la vela con marca t cierra en t + 1 min)."""
    Tn = T.tz_convert(NY)
    pos = cierre_t.searchsorted(Tn, side='right') - 1
    pc = np.clip(pos, 0, None)
    ok = (pos >= 0) & ((Tn - cierre_t[pc]) <= TOL)
    return np.where(ok, cierre_v[pc], np.nan)


def calcular(m, aud):
    cierre_t = pd.DatetimeIndex(m.t) + pd.Timedelta(minutes=1)
    cierre_v = m.c.to_numpy(float)
    dias = pd.bdate_range('2010-01-01', '2026-09-30')
    out = pd.DataFrame(index=dias)
    for h, d in franjas():
        ini = pd.DatetimeIndex([pd.Timestamp(x) + pd.Timedelta(hours=h) for x in dias]).tz_localize(NY, ambiguous='NaT', nonexistent='NaT')
        fin = ini + pd.Timedelta(hours=d)
        out[f'h{h:02d}_d{d}'] = np.log(precio_en(cierre_t, cierre_v, fin) / precio_en(cierre_t, cierre_v, ini))
    hueco = np.zeros(len(out), bool)
    for g in aud.huecos:
        hueco |= (out.index >= g['inicio'] - pd.Timedelta(days=1)) & (out.index <= g['fin'] + pd.Timedelta(days=1))
    out.loc[hueco] = np.nan
    out.index.name = 'dia'
    return out


if __name__ == '__main__':
    d, sim, salida = sys.argv[1:4]
    m, aud = cargar(d, sim)
    r = calcular(m, aud)
    r.to_csv(salida)
    print(sim, 'días', len(r), 'franjas', r.shape[1], 'observaciones válidas', int(r.notna().sum().sum()))
