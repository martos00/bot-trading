"""H75 — estrategias de timing de Connors & Alvarez (2009) sobre SPY diario. Motor PRINCIPAL.
Reglas congeladas en PREREGISTRO_H75_connors.md.

Uso: python3 h75_motor.py DIR_YAHOO TB3MS_CSV SALIDA_DIR
"""
import json, os, sys
import numpy as np
import pandas as pd

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..'))
import calidad_datos  # noqa: E402

MARKUP_CFD = 0.025
SPREAD_CFD_PB = 1.0            # ida y vuelta, en pb del precio
COSTE_ETF_ACCION = 0.0045      # $ por acción y lado


def yahoo(f):
    r = json.load(open(f))['chart']['result'][0]
    q = r['indicators']['quote'][0]
    df = pd.DataFrame({k: q[k] for k in ['open', 'high', 'low', 'close']},
                      index=pd.to_datetime(r['timestamp'], unit='s').normalize())
    if 'adjclose' in r['indicators']:
        df['adj'] = r['indicators']['adjclose'][0]['adjclose']
    return df[~df.index.duplicated(keep='last')].dropna(subset=['close'])


def rsi_wilder(c, n=2):
    d = c.diff()
    up = d.clip(lower=0).ewm(alpha=1 / n, adjust=False).mean()
    dn = (-d.clip(upper=0)).ewm(alpha=1 / n, adjust=False).mean()
    return 100 - 100 / (1 + up / dn)


def senales(spy, vix):
    c = spy['close']
    sma200, sma5 = c.rolling(200).mean(), c.rolling(5).mean()
    r2 = rsi_wilder(c)
    v = vix.reindex(spy.index)
    vc, vo = v['close'], v['open']
    estirado = vc >= 1.05 * vc.rolling(10).mean()
    racha_vix = estirado.astype(int).groupby((~estirado).cumsum()).cumsum()
    sube = c > c.shift(1)
    racha_sube = sube.astype(int).groupby((~sube).cumsum()).cumsum()
    arriba, abajo = c > sma200, c < sma200
    reglas = {
        'H75a_VIX_stretches': (1, arriba & (racha_vix >= 3), r2 > 65),
        'H75b_VIX_RSI': (1, arriba & (rsi_wilder(vc) > 90) & (vo > vc.shift(1)) & (r2 < 30), r2 > 65),
        'H75c_cumulative_RSI': (1, arriba & (r2 + r2.shift(1) < 45), r2 > 65),
        'H75d_SP_short': (-1, abajo & (racha_sube >= 4), c < sma5),
        'H75e_double7': (1, arriba & (c <= c.rolling(7).min()), c >= c.rolling(7).max()),
        'H75f_RSI2_lt5': (1, arriba & (r2 < 5), c > sma5),
    }
    return reglas


def ejecutar(spy, lado, entrada, salida):
    """Posición mantenida desde el cierre de entrada hasta el cierre de salida (señales al cierre)."""
    pos = np.zeros(len(spy))
    ent, sal = entrada.fillna(False).to_numpy(), salida.fillna(False).to_numpy()
    en = False
    for i in range(len(spy)):
        if en and sal[i]:
            en = False
        elif not en and ent[i]:
            en = True
        pos[i] = lado if en else 0
    return pd.Series(pos, index=spy.index)  # posición al CIERRE del día i (aplica al rendimiento de i+1)


def resultados(spy, pos, rf_diario):
    r_tot = spy['adj'].pct_change()
    p = pos.shift(1).fillna(0)
    cambio = pos.diff().abs().fillna(pos.abs())
    bruto = p * r_tot
    coste_etf = cambio * COSTE_ETF_ACCION / spy['close']
    noches = spy.index.to_series().diff().dt.days.fillna(1)
    fin_cfd = np.where(p > 0, (rf_diario + MARKUP_CFD) / 360, np.where(p < 0, -(rf_diario - MARKUP_CFD) / 360, 0)) * noches
    coste_cfd = cambio * SPREAD_CFD_PB / 2 * 1e-4 + np.abs(p) * 0 + fin_cfd
    return pd.DataFrame({'pos': p, 'bruto': bruto, 'neto_etf': bruto - coste_etf, 'neto_cfd': bruto - coste_cfd, 'r_spy': r_tot})


def operaciones(spy, pos, serie):
    ops, ini = [], None
    pv = pos.to_numpy()
    for i in range(1, len(pv)):
        if pv[i] != 0 and pv[i - 1] == 0:
            ini = i
        if pv[i] == 0 and pv[i - 1] != 0 and ini is not None:
            r = (1 + serie.iloc[ini + 1:i + 1]).prod() - 1
            ops.append((spy.index[ini], spy.index[i], i - ini, r))
            ini = None
    return pd.DataFrame(ops, columns=['entrada', 'salida', 'dias', 'ret'])


if __name__ == '__main__':
    dy, tb, out = sys.argv[1:4]
    os.makedirs(out, exist_ok=True)
    spy, vix = yahoo(os.path.join(dy, 'y_SPY.json')), yahoo(os.path.join(dy, 'y_%5EVIX.json'))
    for nom, s in (('SPY', spy), ('VIX', vix)):
        calidad_datos.auditar_historico(s.rename(columns=str.capitalize).reset_index().rename(columns={'index': 'dia'}), nom).imprimir()
    rf = pd.read_csv(tb, index_col=0, parse_dates=True, na_values='.').iloc[:, 0] / 100
    rf = rf.shift(1)  # la media mensual del mes M solo se conoce al acabar M
    rf_d = rf.reindex(spy.index, method='ffill').bfill().to_numpy()
    for nom, (lado, e, s) in senales(spy, vix).items():
        pos = ejecutar(spy, lado, e, s)
        res = resultados(spy, pos, rf_d)
        res.to_csv(os.path.join(out, f'{nom}_diario.csv'))
        for col in ('bruto', 'neto_etf', 'neto_cfd'):
            operaciones(spy, pos, res[col]).to_csv(os.path.join(out, f'{nom}_ops_{col}.csv'), index=False)
    print('ok')
