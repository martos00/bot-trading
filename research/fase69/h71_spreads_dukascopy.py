"""H71 — spread ASK-BID medido en Dukascopy (M1) en los 4 instantes de cada estrategia, sobre la muestra
fijada (primer día laborable de cada mes). Devuelve la mediana por par, estrategia e instante, en pb.

Uso: python3 h71_spreads_dukascopy.py DIR_DUKASCOPY SALIDA_CSV
"""
import glob, lzma, os, struct, sys
from datetime import datetime, timedelta, timezone
from zoneinfo import ZoneInfo
import numpy as np
import pandas as pd

NY, FRA, LON, TOK = (ZoneInfo(z) for z in ('America/New_York', 'Europe/Berlin', 'Europe/London', 'Asia/Tokyo'))
DIVISOR = {'EURUSD': 1e5, 'GBPUSD': 1e5, 'USDJPY': 1e3}


def velas(f, div):
    b = open(f, 'rb').read()
    if not b:
        return {}
    b = lzma.decompress(b)
    dia = datetime.strptime(os.path.basename(f).split('_')[-1][:10], '%Y-%m-%d').replace(tzinfo=timezone.utc)
    out = {}
    for i in range(len(b) // 24):
        t, o, c, lo, hi, v = struct.unpack('>IIIIIf', b[i * 24:(i + 1) * 24])
        out[int((dia + timedelta(seconds=t)).timestamp()) // 60] = c / div
    return out


def en(d, k, T):
    base = int(T.timestamp()) // 60
    for j in range(1, 6):
        if base - j in d:
            return d[base - j]
    return None


def main():
    raiz, salida = sys.argv[1:3]
    filas = []
    for par, div in DIVISOR.items():
        for fb in sorted(glob.glob(os.path.join(raiz, par, f'{par}_BID_*.bi5'))):
            fecha = fb.split('_')[-1][:10]
            fa = fb.replace('_BID_', '_ASK_')
            if not os.path.exists(fa):
                continue
            # cada fichero cubre un día UTC; se cargan también el día anterior/siguiente si existen
            bid, ask = velas(fb, div), velas(fa, div)
            if not bid:
                continue
            d = datetime.strptime(fecha, '%Y-%m-%d').date()
            inst = {('EUROPA', 't1a'): datetime(d.year, d.month, d.day, 8, 0, tzinfo=FRA),
                    ('EUROPA', 't1b'): datetime(d.year, d.month, d.day, 14, 15, tzinfo=FRA),
                    ('EUROPA', 't2a'): datetime(d.year, d.month, d.day, 16, 0, tzinfo=LON),
                    ('EUROPA', 't2b'): datetime(d.year, d.month, d.day, 16, 55, tzinfo=NY),
                    ('TOKIO', 't1b'): datetime(d.year, d.month, d.day, 9, 55, tzinfo=TOK)}
            for (est, k), T in inst.items():
                b_, a_ = en(bid, k, T), en(ask, k, T)
                if b_ is not None and a_ is not None:
                    filas.append(dict(par=par, fecha=fecha, estrategia=est, instante=k, spread_pb=(a_ - b_) / ((a_ + b_) / 2) * 1e4))
    df = pd.DataFrame(filas)
    res = df.groupby(['par', 'estrategia', 'instante']).spread_pb.agg(['median', 'mean', 'count', lambda s: s.quantile(.9)])
    res.columns = ['mediana_pb', 'media_pb', 'n_dias', 'p90_pb']
    print(res.round(3).to_string())
    res.to_csv(salida)


if __name__ == '__main__':
    main()
