"""Descarga automática de velas M1 ASCII de HistData.com (sin intervención manual).

Uso: python3 descargar_histdata_m1.py SIMBOLO AÑO_INI AÑO_FIN DIR_SALIDA

HistData sirve un zip por año completo y, para el año en curso, un zip por mes. La descarga
es un POST a /get.php con el token 'tk' que aparece en la página del año/mes.
Formato: 'AAAAMMDD HHMMSS;O;H;L;C;V', horario EST FIJO (UTC-5 todo el año, sin horario de
verano), precio BID. Se guarda también el informe de huecos (.txt) que publica HistData.
"""
import os, re, sys, time, zipfile, io, hashlib, urllib.request, urllib.parse, http.cookiejar

BASE = 'https://www.histdata.com'


def bajar(sim, periodo, out, op):
    ruta = f'/download-free-forex-historical-data/?/ascii/1-minute-bar-quotes/{sim.lower()}/{periodo}'
    html = op.open(urllib.request.Request(BASE + ruta, headers={'User-Agent': 'Mozilla/5.0'}), timeout=60).read().decode('utf8', 'ignore')
    tk = re.search(r'name="tk" id="tk" value="([^"]+)"', html)
    if not tk:
        return None
    campos = {k: re.search(rf'name="{k}" id="{k}" value="([^"]*)"', html).group(1)
              for k in ('date', 'datemonth', 'platform', 'timeframe', 'fxpair')}
    campos['tk'] = tk.group(1)
    req = urllib.request.Request(BASE + '/get.php', data=urllib.parse.urlencode(campos).encode(),
                                 headers={'User-Agent': 'Mozilla/5.0', 'Referer': BASE + ruta})
    datos = op.open(req, timeout=300).read()
    if not datos.startswith(b'PK'):
        return None
    z = zipfile.ZipFile(io.BytesIO(datos))
    z.extractall(out)
    return hashlib.sha256(datos).hexdigest(), z.namelist()


def main():
    sim, a0, a1, out = sys.argv[1], int(sys.argv[2]), int(sys.argv[3]), sys.argv[4]
    os.makedirs(out, exist_ok=True)
    op = urllib.request.build_opener(urllib.request.HTTPCookieProcessor(http.cookiejar.CookieJar()))
    for a in range(a0, a1 + 1):
        r = bajar(sim, str(a), out, op)
        if r:
            print(sim, a, r[0], r[1], flush=True)
        else:  # año en curso: un fichero por mes
            for m in range(1, 13):
                r = bajar(sim, f'{a}/{m}', out, op)
                print(sim, f'{a}/{m}', r[0] if r else 'sin datos', r[1] if r else '', flush=True)
                time.sleep(2)
        time.sleep(2)


if __name__ == '__main__':
    main()
