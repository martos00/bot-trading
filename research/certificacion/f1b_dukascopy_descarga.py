"""Descarga velas M1 BID/ASK del CFD de gas natural de Dukascopy (GASCMDUSD) solo los jueves (para F1b, comprobación con otra fuente).
Uso: python3 f1b_dukascopy_descarga.py AAAA-MM-DD AAAA-MM-DD DIR_SALIDA"""
import os, sys, time, datetime as dt
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'fase69'))
from descargar_dukascopy_m1 import pedir, URL
ini, fin, out = sys.argv[1:4]
d, d1 = dt.date.fromisoformat(ini), dt.date.fromisoformat(fin)
while d.weekday() != 3: d += dt.timedelta(days=1)
while d <= d1:
    for lado in ('BID', 'ASK'):
        f = os.path.join(out, f'GASCMDUSD_{lado}_{d.isoformat()}.bi5')
        if not os.path.exists(f):
            datos = pedir(URL.format(s='GASCMDUSD', y=d.year, m=d.month - 1, d=d.day, lado=lado))
            open(f + '.tmp', 'wb').write(datos); os.replace(f + '.tmp', f); time.sleep(1.2)
    d += dt.timedelta(days=7)
print('fin', flush=True)
