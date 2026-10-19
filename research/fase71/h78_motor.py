"""H78 — BTC largo 21:00 → 23:00 UTC (PREREGISTRO_H78_btc_21_23utc.md). Motor PRINCIPAL (velas de 1 h, vectorizado).
Uso: python3 h78_motor.py DIR_1H SALIDA_CSV
Salida: por día UTC, rentabilidad simple bruta de la regla y de las 24 ventanas de 2 h (para el control aleatorio)."""
import glob, sys
import numpy as np
import pandas as pd

COLS = ['ot', 'o', 'h', 'l', 'c', 'v', 'ct', 'qv', 'n', 'tb', 'tq', 'x']


def cargar(directorio):
    k = pd.concat([pd.read_csv(f, header=None, names=COLS) for f in sorted(glob.glob(f'{directorio}/*.zip'))])
    k = k[pd.to_numeric(k.ot, errors='coerce').notna()]
    ot = k.ot.astype('int64')
    ot = np.where(ot > 10**14, ot // 1000, ot)   # desde 2025 Binance publica microsegundos
    return pd.Series(k.o.astype(float).values, index=pd.to_datetime(ot, unit='ms', utc=True)).sort_index().loc[lambda s: ~s.index.duplicated()]


def ventanas(op):
    """op: apertura por hora. Devuelve DataFrame dia x hora_inicio con la rentabilidad de 2 h."""
    rej = op.reindex(pd.date_range(op.index.min().normalize(), op.index.max().normalize() + pd.Timedelta(hours=26), freq='h'))
    r2 = rej.shift(-2) / rej - 1
    df = pd.DataFrame({'r': r2.values, 'dia': rej.index.normalize(), 'hora': rej.index.hour})
    return df.pivot(index='dia', columns='hora', values='r')


if __name__ == '__main__':
    op = cargar(sys.argv[1])
    v = ventanas(op)
    v.columns = [f'h{c:02d}' for c in v.columns]
    v['regla'] = v['h21']
    v.dropna(subset=['regla']).to_csv(sys.argv[2])
    print('días', v.regla.notna().sum(), 'desde', v.regla.first_valid_index(), 'hasta', v.regla.last_valid_index())
