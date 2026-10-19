"""H78 — motor INDEPENDIENTE: velas de 1 minuto, bucle en Python puro (sin pandas en el cálculo).
Precio de entrada = apertura del minuto 21:00:00 UTC; salida = apertura del minuto 23:00:00 UTC.
Uso: python3 h78_motor_independiente.py DIR_1M SALIDA_CSV"""
import csv, datetime as dt, glob, io, sys, zipfile

aperturas = {}
for f in sorted(glob.glob(f'{sys.argv[1]}/*.zip')):
    z = zipfile.ZipFile(f)
    for fila in csv.reader(io.TextIOWrapper(z.open(z.namelist()[0]))):
        if not fila[0].isdigit():
            continue
        ms = int(fila[0])
        if ms > 10**14:
            ms //= 1000
        t = dt.datetime.fromtimestamp(ms / 1000, dt.timezone.utc)
        if t.minute == 0 and t.hour in (21, 23):
            aperturas[t] = float(fila[1])

with open(sys.argv[2], 'w', newline='') as fo:
    w = csv.writer(fo)
    w.writerow(['dia', 'regla_1m'])
    for t in sorted(aperturas):
        if t.hour == 21:
            s = t + dt.timedelta(hours=2)
            if s in aperturas:
                w.writerow([t.date().isoformat(), aperturas[s] / aperturas[t] - 1])
