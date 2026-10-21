"""B1 — familia F2: sesión de contado de cada índice (PREREGISTRO_B1_barrido_fondeo.md).
(a) largo de apertura a cierre; (b) momentum intradía: última media hora en el sentido de la primera.
Uso: python3 b1_motor_f2.py DIR_HISTDATA SIMBOLO SALIDA_CSV"""
import os, sys
import numpy as np
import pandas as pd

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'fase72'))
import h80_motor as M  # noqa: E402

SESION = {  # zona local, apertura (h, min), cierre (h, min)
    'GRXEUR': ('Europe/Berlin', (9, 0), (17, 30)), 'FRXEUR': ('Europe/Paris', (9, 0), (17, 30)),
    'ETXEUR': ('Europe/Berlin', (9, 0), (17, 30)), 'UKXGBP': ('Europe/London', (8, 0), (16, 30)),
    'JPXJPY': ('Asia/Tokyo', (9, 0), (15, 0)), 'AUXAUD': ('Australia/Sydney', (10, 0), (16, 0)),
    'HKXHKD': ('Asia/Hong_Kong', (9, 30), (16, 0)),
}


def instantes(dias, zona, hm, extra_min=0):
    t = pd.DatetimeIndex([d + pd.Timedelta(hours=hm[0], minutes=hm[1] + extra_min) for d in dias])
    return t.tz_localize(zona, ambiguous='NaT', nonexistent='NaT')


if __name__ == '__main__':
    d, sim, salida = sys.argv[1:4]
    zona, ap, ci = SESION[sim]
    m, aud = M.cargar(d, sim)
    ct = pd.DatetimeIndex(m.t) + pd.Timedelta(minutes=1)
    cv = m.c.to_numpy(float)
    dias = pd.bdate_range('2010-01-01', '2026-09-30')
    p = lambda hm, extra=0: M.precio_en(ct, cv, instantes(dias, zona, hm, extra))
    p_ap, p_ap30, p_ci30, p_ci = p(ap), p(ap, 30), p(ci, -30), p(ci)
    out = pd.DataFrame(index=dias)
    out['f2a_apertura_cierre'] = np.log(p_ci / p_ap)
    out['f2b_momentum_intradia'] = np.sign(np.log(p_ap30 / p_ap)) * np.log(p_ci / p_ci30)
    hueco = np.zeros(len(out), bool)
    for g in aud.huecos:
        hueco |= (out.index >= g['inicio'] - pd.Timedelta(days=1)) & (out.index <= g['fin'] + pd.Timedelta(days=1))
    out.loc[hueco] = np.nan
    out.index.name = 'dia'
    out.to_csv(salida)
    print(sim, 'días F2a', int(out.f2a_apertura_cierre.notna().sum()), 'F2b', int(out.f2b_momentum_intradia.notna().sum()))
