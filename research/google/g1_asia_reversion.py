"""G1 — reversión a la media en la sesión asiática con Bollinger (20, 2) en velas de 15 min (PREREGISTRO_G1_G2.md).
Uso: python3 g1_asia_reversion.py DIR_HISTDATA_PAR SIMBOLO SALIDA_CSV"""
import os, sys
import numpy as np
import pandas as pd

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'fase72'))
import h80_motor as M  # noqa: E402

d, sim, salida = sys.argv[1:4]
m, aud = M.cargar(d, sim)
t = m.t.dt.tz_localize(None)                                  # hora local de NY
b = m.assign(t=t).set_index('t').resample('15min', label='left').agg({'o': 'first', 'c': 'last'}).dropna()
sma = b.c.rolling(20).mean()
sd = b.c.rolling(20).std(ddof=0)
sup, inf = sma + 2 * sd, sma - 2 * sd
ini = b.index.to_numpy()
o, c = b.o.to_numpy(), b.c.to_numpy()
S, U, L = sma.to_numpy(), sup.to_numpy(), inf.to_numpy()
cierre = b.index + pd.Timedelta(minutes=15)
mins = (cierre.hour * 60 + cierre.minute).to_numpy()
ventana = (mins >= 19 * 60) | (mins <= 60)                    # vela que cierra entre las 19:00 y la 01:00
huecos = [(g['inicio'], g['fin'] + pd.Timedelta(days=1)) for g in aud.huecos]

ops = []
pos, px_ent, t_ent, limite, salir = 0, 0.0, None, None, False
for i in range(len(b) - 1):
    ti = pd.Timestamp(ini[i])
    if pos != 0:
        # cierre forzoso a las 02:00 NY: a la apertura de la primera vela que empieza a esa hora o después
        if ti >= limite or salir:
            ops.append((t_ent, ti, pos, pos * np.log(o[i] / px_ent)))
            pos, salir = 0, False
    if pos != 0:
        if (pos == 1 and c[i] >= S[i]) or (pos == -1 and c[i] <= S[i]):
            salir = True                                     # se ejecuta a la apertura de la vela siguiente
        continue
    if not ventana[i] or np.isnan(U[i]) or any(a <= ti <= z for a, z in huecos):
        continue
    if c[i] < L[i] or c[i] > U[i]:
        pos = 1 if c[i] < L[i] else -1
        t_ent = pd.Timestamp(ini[i + 1])
        px_ent = o[i + 1]
        dia = t_ent.normalize() + (pd.Timedelta(days=1) if t_ent.hour >= 19 else pd.Timedelta(0))
        limite = dia + pd.Timedelta(hours=2)
        salir = False
        # la vela de entrada es la i+1: se evalúa en la siguiente iteración
r = pd.DataFrame(ops, columns=['entrada', 'salida', 'lado', 'r'])
r.to_csv(salida, index=False)
print(sim, 'operaciones', len(r), 'media bruta', round(r.r.mean() * 1e4, 3), 'pb; duración media',
      (r.salida - r.entrada).mean())
