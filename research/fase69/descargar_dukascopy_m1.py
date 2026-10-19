"""Descarga velas M1 (BID y ASK) de Dukascopy, un fichero .bi5 por día.

Uso: python3 descargar_dukascopy_m1.py SIMBOLO AAAA-MM-DD AAAA-MM-DD DIR_SALIDA [BID,ASK]

- Fuente: https://datafeed.dukascopy.com/datafeed/<SIM>/<AAAA>/<MM-1>/<DD>/<LADO>_candles_min_1.bi5
  (mes indexado desde 0, timestamps en UTC exacto, sin inferir offset de servidor).
- El servidor limita la frecuencia (HTTP 429): se pide de forma secuencial, con pausa base
  y espera creciente ante 429/errores. Reanudable: no vuelve a pedir ficheros ya guardados.
- Solo días laborables (lunes-viernes); un fichero vacío (0 bytes) se guarda como marcador
  de "sin datos ese día" para no volver a pedirlo.
"""
import os, sys, time, datetime as dt, urllib.request, urllib.error

URL = 'https://datafeed.dukascopy.com/datafeed/{s}/{y}/{m:02d}/{d:02d}/{lado}_candles_min_1.bi5'


def pedir(url, intentos=8):
    espera = 20
    n503 = 0
    for _ in range(intentos):
        try:
            req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
            with urllib.request.urlopen(req, timeout=40) as r:
                return r.read()
        except urllib.error.HTTPError as e:
            if e.code == 404:
                return b''
            if e.code == 503:
                n503 += 1
                if n503 >= 3:  # Dukascopy responde 503 persistente antes del inicio del histórico
                    print(f'  503 persistente, se marca sin datos: {url}', flush=True)
                    return b''
            print(f'  HTTP {e.code}, espero {espera}s', flush=True)
        except Exception as e:  # cortes de conexión del proxy/servidor
            print(f'  error {type(e).__name__}, espero {espera}s', flush=True)
        time.sleep(espera)
        espera = min(espera * 2, 300)
    raise RuntimeError(f'No se pudo descargar {url}')


def main():
    sim, ini, fin, out = sys.argv[1:5]
    lados = (sys.argv[5] if len(sys.argv) > 5 else 'BID,ASK').split(',')
    d, d1 = dt.date.fromisoformat(ini), dt.date.fromisoformat(fin)
    os.makedirs(out, exist_ok=True)
    n = 0
    while d <= d1:
        if d.weekday() < 5:
            for lado in lados:
                f = os.path.join(out, f'{sim}_{lado}_{d.isoformat()}.bi5')
                if os.path.exists(f):
                    continue
                datos = pedir(URL.format(s=sim, y=d.year, m=d.month - 1, d=d.day, lado=lado))
                with open(f + '.tmp', 'wb') as fh:
                    fh.write(datos)
                os.replace(f + '.tmp', f)
                n += 1
                time.sleep(1.2)
            if d.day == 1:
                print(f'{sim} {d} ({n} ficheros nuevos)', flush=True)
        d += dt.timedelta(days=1)
    print('FIN', sim, n, flush=True)


if __name__ == '__main__':
    main()
