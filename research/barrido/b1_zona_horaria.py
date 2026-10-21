"""B1 — verificación de la zona horaria de HistData por instrumento: actividad media (|rentabilidad| de 1 min) por hora de NY.
La apertura del mercado de referencia debe verse como el mayor salto de actividad a la hora prevista.
Uso: python3 b1_zona_horaria.py DIR_HISTDATA SIMBOLO"""
import os, sys
import numpy as np
import pandas as pd
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'fase72'))
import h80_motor as M  # noqa: E402

m, _ = M.cargar(sys.argv[1], sys.argv[2])
m = m[m.t.dt.year >= 2015]
r = np.log(m.c / m.c.shift(1)).abs()
g = r.groupby([m.t.dt.hour, m.t.dt.minute // 30 * 30]).mean() * 1e4
salto = (g - g.shift(1)).sort_values(ascending=False).head(4)
print(sys.argv[2], 'mayores saltos de actividad (hora NY, media hora): ', ', '.join(f'{h:02d}:{mm:02d} (+{v:.2f} pb)' for (h, mm), v in salto.items()))
