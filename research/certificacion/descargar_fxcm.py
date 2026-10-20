"""Descarga velas M1 (BID y ASK) públicas de FXCM: candledata.fxcorporate.com/m1/SIMBOLO/AÑO/SEMANA.csv.gz
Uso: python3 descargar_fxcm.py SIMBOLO AÑO_INI AÑO_FIN DIR_SALIDA   (registra en DIR/disponibilidad.txt qué semanas existen)"""
import os, sys, time, urllib.request, urllib.error

sim, a0, a1, out = sys.argv[1], int(sys.argv[2]), int(sys.argv[3]), sys.argv[4]
os.makedirs(out, exist_ok=True)
log = open(os.path.join(out, 'disponibilidad.txt'), 'a')
for y in range(a0, a1 + 1):
    for w in range(1, 54):
        f = os.path.join(out, f'{sim}_{y}_{w:02d}.csv.gz')
        if os.path.exists(f):
            continue
        url = f'https://candledata.fxcorporate.com/m1/{sim}/{y}/{w}.csv.gz'
        for intento in range(4):
            try:
                datos = urllib.request.urlopen(urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'}), timeout=60).read()
                open(f, 'wb').write(datos)
                log.write(f'{y} {w} ok\n')
                break
            except urllib.error.HTTPError as e:
                if e.code == 404:
                    log.write(f'{y} {w} 404\n')
                    break
                time.sleep(2 ** intento)
            except Exception:
                time.sleep(2 ** intento)
        log.flush()
        time.sleep(0.2)
print('FIN')
