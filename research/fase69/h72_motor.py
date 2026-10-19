"""H72 — front-running del rebalanceo 60/40 (Harvey, Mazzoleni & Melone). Motor PRINCIPAL.
Reglas congeladas en PREREGISTRO_H72_rebalanceo.md.

Uso: python3 h72_motor.py DIR_RAW SALIDA_CSV   (DIR_RAW: y_%5ESP500TR.json, fred/DGS10.csv, fred/TB3MS.csv)
"""
import json, os, sys
import numpy as np
import pandas as pd

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..'))
import calidad_datos  # noqa: E402

OBJETIVO = 0.60
DELTAS = np.round(np.arange(0, 0.02501, 0.001), 4)   # 0%, 0,1%, ..., 2,5%  (26 valores)
ESCALA_THRESHOLD = 0.015
DIAS_WEEK4 = 5


def cargar(raw):
    d = json.load(open(os.path.join(raw, 'y_%5ESP500TR.json')))['chart']['result'][0]
    sp = pd.Series(d['indicators']['quote'][0]['close'], index=pd.to_datetime(d['timestamp'], unit='s').normalize()).dropna()
    sp = sp[~sp.index.duplicated(keep='last')]
    y = pd.read_csv(os.path.join(raw, 'fred', 'DGS10.csv'), index_col=0, parse_dates=True, na_values='.').iloc[:, 0].dropna()
    rf = pd.read_csv(os.path.join(raw, 'fred', 'TB3MS.csv'), index_col=0, parse_dates=True, na_values='.').iloc[:, 0].dropna()
    return sp, y, rf


def retorno_bono_diario(y, dias):
    """Bono a la par de 10 años (cupón = rendimiento del día anterior), revalorizado al rendimiento de hoy
    con vencimiento 10 - Δt años, más el cupón devengado en Δt (días naturales / 365)."""
    dt = np.diff(dias.values).astype('timedelta64[D]').astype(float) / 365.0
    c, y1 = y.values[:-1] / 100, y.values[1:] / 100
    n = 10 - dt
    precio = c * (1 - (1 + y1) ** -n) / y1 + (1 + y1) ** -n
    return pd.Series(np.r_[np.nan, precio - 1 + c * dt], index=dias)


def series(raw):
    sp, y, rf = cargar(raw)
    dias = sp.index.intersection(y.index)
    sp, y = sp.loc[dias], y.loc[dias]
    df = pd.DataFrame({'r_sp': sp.pct_change(), 'r_10y': retorno_bono_diario(y, dias)}, index=dias)
    rf_m = rf.groupby(rf.index.to_period('M')).last()
    df['rf'] = [rf_m.get(p - 1, np.nan) / 100 / 252 for p in dias.to_period('M')]
    return df.dropna(subset=['r_sp', 'r_10y']), sp, y


def desviacion(r_sp, r_b, rebalancea):
    """Desviación de la cartera respecto a 60% ANTES de rebalancear, día a día. `rebalancea(t, dev)` decide."""
    w = OBJETIVO
    out = np.empty(len(r_sp))
    for t in range(len(r_sp)):
        w = w * (1 + r_sp[t]) / (w * (1 + r_sp[t]) + (1 - w) * (1 + r_b[t]))
        out[t] = w - OBJETIVO
        if rebalancea(t, out[t]):
            w = OBJETIVO
    return out


def senales(df):
    r_sp, r_b = df['r_sp'].to_numpy(), df['r_10y'].to_numpy()
    th = np.mean([desviacion(r_sp, r_b, lambda t, dv, d=d: abs(dv) >= d) for d in DELTAS], axis=0)
    per = df.index.to_period('M')
    ultimo = np.r_[per[1:] != per[:-1], True]           # último día hábil del mes (en la muestra)
    cal = desviacion(r_sp, r_b, lambda t, dv: ultimo[t])
    # posición dentro del mes contada desde el final (0 = último día hábil)
    pos_fin = pd.Series(1, index=df.index).groupby(per).cumcount(ascending=False).to_numpy()
    primero = np.r_[True, per[1:] != per[:-1]]
    cal_mod = np.zeros(len(df))
    cal_mod[pos_fin < DIAS_WEEK4] = np.sign(-cal[pos_fin < DIAS_WEEK4])
    # primer día hábil del mes: sign(Calendar en T-4 del mes anterior)
    s = pd.Series(cal, index=df.index)
    t4 = s[pos_fin == 4].groupby(per[pos_fin == 4]).last()
    for i in np.where(primero)[0]:
        prev = per[i] - 1
        if prev in t4.index:
            cal_mod[i] = np.sign(t4[prev])
    out = df.copy()
    out['threshold'], out['calendar'], out['cal_mod'] = th, cal, cal_mod
    out['w'] = (-th / ESCALA_THRESHOLD + cal_mod) / 2
    out['estr'] = out['w'].shift(1) * (out['r_sp'] - out['r_10y'])           # H72a, dos patas
    out['estr_rv'] = out['w'].shift(1) * (out['r_sp'] - out['rf'])           # H72b, solo renta variable
    return out


if __name__ == '__main__':
    raw, salida = sys.argv[1:3]
    df, sp, y = series(raw)
    for nom, s in [('SP500TR', sp), ('DGS10', y)]:
        d = pd.DataFrame({'dia': s.index, 'Open': s.values, 'High': s.values, 'Low': s.values, 'Close': s.values})
        calidad_datos.auditar_historico(d, nom).imprimir()
    out = senales(df)
    out.index.name = 'dia'
    out.to_csv(salida)
    print(out[['threshold', 'calendar', 'w']].describe().round(4).to_string())
