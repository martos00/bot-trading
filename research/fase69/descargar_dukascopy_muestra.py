"""Descarga Dukascopy M1 BID+ASK solo para una lista fija de días (muestra para medir spreads).

Uso: python3 descargar_dukascopy_muestra.py SIM1,SIM2 AAAA-MM AAAA-MM DIR_SALIDA
Muestra fijada: el primer día laborable (lunes-viernes, distinto de 1-ene y 25-dic) de cada mes.
"""
import os, sys, time, datetime as dt
import descargar_dukascopy_m1 as d

sims, ini, fin, out = sys.argv[1].split(','), sys.argv[2], sys.argv[3], sys.argv[4]
y, m = map(int, ini.split('-'))
y1, m1 = map(int, fin.split('-'))
dias = []
while (y, m) <= (y1, m1):
    x = dt.date(y, m, 1)
    while x.weekday() >= 5 or (x.month, x.day) in ((1, 1), (12, 25)):
        x += dt.timedelta(days=1)
    dias.append(x)
    y, m = (y + 1, 1) if m == 12 else (y, m + 1)
for x in dias:
    for sim in sims:
        os.makedirs(os.path.join(out, sim), exist_ok=True)
        for lado in ('BID', 'ASK'):
            f = os.path.join(out, sim, f'{sim}_{lado}_{x.isoformat()}.bi5')
            if os.path.exists(f):
                continue
            datos = d.pedir(d.URL.format(s=sim, y=x.year, m=x.month - 1, d=x.day, lado=lado))
            open(f, 'wb').write(datos)
            time.sleep(1.2)
    print(x, flush=True)
print('FIN')
