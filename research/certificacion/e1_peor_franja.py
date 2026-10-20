"""E1 — peor precio (máximo del ASK, adverso para una venta) entre 06:00 y 08:00 ET de cada día de c1_precios.csv.
FXCM: máximo de AskHigh de las velas que empiezan en [06:00, 08:00). Dukascopy: máximo del High de las velas ASK.
Uso: python3 e1_peor_franja.py DIR_FXCM DIR_DUKASCOPY c1_precios.csv SALIDA_CSV"""
import glob, lzma, os, struct, sys
from datetime import datetime, timedelta, timezone
from zoneinfo import ZoneInfo
import numpy as np
import pandas as pd

NY = ZoneInfo('America/New_York')


def minutos_fxcm(d):
    out = {}
    for f in sorted(glob.glob(os.path.join(d, 'EURUSD_*.csv.gz'))):
        x = pd.read_csv(f, compression='gzip', usecols=['DateTime', 'AskHigh'])
        m = ((pd.to_datetime(x.DateTime, format='%m/%d/%Y %H:%M:%S.%f') - pd.Timestamp('1970-01-01')) // pd.Timedelta(minutes=1)).to_numpy()
        out.update(zip(m, x.AskHigh.to_numpy(float)))
    return out


def minutos_duka(d):
    out = {}
    for f in sorted(glob.glob(os.path.join(d, 'EURUSD_ASK_*.bi5'))):
        b = open(f, 'rb').read()
        if not b:
            continue
        b = lzma.decompress(b)
        dia = datetime.strptime(os.path.basename(f).split('_')[-1][:10], '%Y-%m-%d').replace(tzinfo=timezone.utc)
        for i in range(len(b) // 24):
            t, o, c, lo, hi, v = struct.unpack('>IIIIIf', b[i * 24:(i + 1) * 24])
            out[int((dia + timedelta(seconds=t)).timestamp()) // 60] = hi / 1e5
    return out


if __name__ == '__main__':
    fx, dk = minutos_fxcm(sys.argv[1]), minutos_duka(sys.argv[2])
    x = pd.read_csv(sys.argv[3], index_col=0, parse_dates=True)
    peor = []
    for d, fuente in x.fuente.items():
        src = fx if fuente == 'FXCM' else dk
        a = int(datetime(d.year, d.month, d.day, 6, tzinfo=NY).timestamp()) // 60
        b = int(datetime(d.year, d.month, d.day, 8, tzinfo=NY).timestamp()) // 60
        v = [src[k] for k in range(a, b) if k in src]
        peor.append(max(v) if v else np.nan)
    x['ask_max'] = peor
    x[['mid6', 'mid8', 'ask_max', 'fuente']].to_csv(sys.argv[4])
    print('días con peor precio:', x.ask_max.notna().sum(), 'de', len(x))
