"""Descarga velas mensuales de Binance spot (data.binance.vision, público y gratuito).
Uso: python3 descargar_binance.py SIMBOLO INTERVALO AAAA-MM AAAA-MM DIR_SALIDA"""
import os, sys, time, urllib.request
import pandas as pd

sim, iv, ini, fin, out = sys.argv[1:6]
os.makedirs(out, exist_ok=True)
for p in pd.period_range(ini, fin, freq='M'):
    f = f'{sim}-{iv}-{p.year}-{p.month:02d}.zip'
    dst = os.path.join(out, f)
    if os.path.exists(dst):
        continue
    url = f'https://data.binance.vision/data/spot/monthly/klines/{sim}/{iv}/{f}'
    for intento in range(4):
        try:
            urllib.request.urlretrieve(url, dst + '.tmp')
            os.replace(dst + '.tmp', dst)
            break
        except Exception as e:
            print(p, 'error', e, flush=True)
            time.sleep(2 ** (intento + 1))
    time.sleep(0.3)
print('ok', len(os.listdir(out)))
