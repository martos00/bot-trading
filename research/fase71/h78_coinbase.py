"""H78 — comprobación con otra bolsa: velas de 1 h de Coinbase Exchange (API pública, sin clave).
Uso: python3 h78_coinbase.py AAAA-MM-DD AAAA-MM-DD SALIDA_CSV"""
import json, sys, time, urllib.request
import pandas as pd

ini, fin, out = pd.Timestamp(sys.argv[1], tz='UTC'), pd.Timestamp(sys.argv[2], tz='UTC'), sys.argv[3]
filas, t = [], ini
while t < fin:
    t2 = min(t + pd.Timedelta(hours=300), fin)
    u = f'https://api.exchange.coinbase.com/products/BTC-USD/candles?granularity=3600&start={t.isoformat()}&end={t2.isoformat()}'
    for intento in range(5):
        try:
            filas += json.load(urllib.request.urlopen(urllib.request.Request(u, headers={'User-Agent': 'investigacion'}), timeout=30))
            break
        except Exception as e:
            print(t, e, flush=True); time.sleep(2 ** intento)
    t = t2
    time.sleep(0.35)
k = pd.DataFrame(filas, columns=['t', 'l', 'h', 'o', 'c', 'v']).drop_duplicates('t')
op = pd.Series(k.o.values, index=pd.to_datetime(k.t, unit='s', utc=True)).sort_index()
e = op[op.index.hour == 21]
s = op.reindex(e.index + pd.Timedelta(hours=2))
pd.DataFrame({'regla_1m': s.values / e.values - 1}, index=e.index.normalize().tz_localize(None).rename('dia')).dropna().to_csv(out)
print('días', len(e))
