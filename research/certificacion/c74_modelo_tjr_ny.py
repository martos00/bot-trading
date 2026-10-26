"""C74: modelo "TJR" de sesion NY (barrida de Asia/Londres -> MSS en 5 min -> entrada en FVG, 2R).
Reglas congeladas en PREREGISTRO_C74_modelo_tjr_ny.md (commit 8e56287), sin parametros libres.
Uso: python3 c74_modelo_tjr_ny.py ES_1m.pkl DIR_HISTDATA_EURUSD DIR_HISTDATA_XAUUSD"""
import glob
import os
import sys

import numpy as np
import pandas as pd

COSTE_PB = {'ES': 1.0, 'EURUSD': 0.54, 'XAUUSD': 1.5}
T_EXITO = 2.39


def cargar_es(ruta):
    d = pd.read_pickle(ruta)
    ts = pd.to_datetime(d['ts_event'], utc=True).dt.tz_convert('America/New_York').dt.tz_localize(None)
    df = pd.DataFrame({'open': d['open'].values, 'high': d['high'].values, 'low': d['low'].values,
                       'close': d['close'].values, 'inst': d['instrument_id'].values}, index=ts)
    return df[~df.index.duplicated()].sort_index()


def cargar_histdata(carpeta):
    piezas = []
    for f in sorted(glob.glob(os.path.join(carpeta, '*.csv'))):
        anio = int(os.path.basename(f).split('_')[-1][:4])
        if anio < 2010:
            continue
        p = pd.read_csv(f, sep=';', header=None, names=['t', 'open', 'high', 'low', 'close', 'v'])
        piezas.append(p)
    p = pd.concat(piezas, ignore_index=True)
    ts = (pd.to_datetime(p['t'], format='%Y%m%d %H%M%S') + pd.Timedelta(hours=5)).dt.tz_localize('UTC')
    ts = ts.dt.tz_convert('America/New_York').dt.tz_localize(None)
    df = pd.DataFrame({'open': p['open'].values, 'high': p['high'].values, 'low': p['low'].values,
                       'close': p['close'].values}, index=ts)
    df['inst'] = 0
    return df[~df.index.duplicated()].sort_index()


def operaciones(m1, coste_pb):
    m5 = m1.resample('5min').agg({'open': 'first', 'high': 'max', 'low': 'min', 'close': 'last'}).dropna()
    m5['fecha'] = m5.index.normalize()
    hhmm = m5.index.hour * 100 + m5.index.minute
    m5['hhmm'] = hhmm
    m1h = m1.index.hour * 100 + m1.index.minute
    res = []
    fechas = pd.DatetimeIndex(sorted(set(m1.index.normalize())))
    fechas = fechas[(fechas >= '2011-01-01') & (fechas <= '2026-09-30') & (fechas.dayofweek < 5)]
    for D in fechas:
        ini = D - pd.Timedelta(hours=5)                       # 19:00 del dia anterior
        bloque = m1.loc[ini: D + pd.Timedelta(hours=12) - pd.Timedelta(minutes=1)]
        if len(bloque) == 0 or bloque['inst'].nunique() != 1:
            continue
        asia = bloque.loc[:D - pd.Timedelta(minutes=1)]
        lon = bloque.loc[D + pd.Timedelta(hours=2): D + pd.Timedelta(hours=5) - pd.Timedelta(minutes=1)]
        if len(asia) == 0 or len(lon) == 0:
            continue
        pre_a = bloque.loc[D: D + pd.Timedelta(hours=9, minutes=29)]
        pre_l = bloque.loc[D + pd.Timedelta(hours=5): D + pd.Timedelta(hours=9, minutes=29)]
        altos, bajos = [], []
        aH, aL, lH, lL = asia.high.max(), asia.low.min(), lon.high.max(), lon.low.min()
        if not (len(pre_a) and pre_a.high.max() > aH):
            altos.append(aH)
        if not (len(pre_a) and pre_a.low.min() < aL):
            bajos.append(aL)
        if not (len(pre_l) and pre_l.high.max() > lH):
            altos.append(lH)
        if not (len(pre_l) and pre_l.low.min() < lL):
            bajos.append(lL)
        v = m5.loc[D + pd.Timedelta(hours=9): D + pd.Timedelta(hours=11, minutes=55)]
        if len(v) < 20 or (not altos and not bajos):
            continue
        o, h, l, c, hm = v.open.values, v.high.values, v.low.values, v.close.values, v.hhmm.values
        nivH = min(altos) if altos else np.inf
        nivL = max(bajos) if bajos else -np.inf
        s = None
        for i in range(len(v)):
            if 930 <= hm[i] <= 1055:
                up, dn = h[i] > nivH, l[i] < nivL
                if up and dn:
                    s = -1
                    break
                if up or dn:
                    s, corto = i, up
                    break
        if s is None or s == -1:
            continue
        if not corto:                       # el largo es el espejo del corto
            o, h, l, c = -o, -l, -h, -c
        # referencia de estructura: ultimo minimo de swing antes de la barrida
        ref = None
        for k in range(s - 1, 0, -1):
            if k + 1 < len(v) and l[k] < l[k - 1] and l[k] < l[k + 1]:
                ref = l[k]
                break
        if ref is None:
            if s == 0:
                continue
            ref = l[:s].min()
        m = None
        for i in range(s + 1, len(v)):
            if hm[i] > 1055:
                break
            if c[i] < ref:
                m = i
                break
        if m is None:
            continue
        stop = h[s:m + 1].max()
        fvg = None
        for i in range(m, s - 1, -1):
            if i >= 2 and l[i - 2] > h[i]:
                fvg = i
                break
        if fvg is None:
            continue
        entrada = h[fvg]
        R0 = stop - entrada
        lleno = None
        for i in range(m + 1, len(v)):
            if hm[i] > 1125:
                break
            if h[i] >= entrada:
                lleno, px = i, max(entrada, o[i])
                break
            if l[i] <= entrada - 2 * R0:
                break
        if lleno is None:
            continue
        R = stop - px
        precio = abs(px)
        if R <= 0 or R < 1e-4 * precio:
            continue
        obj = px - 2 * R
        if h[lleno] >= stop:
            sal = stop
        else:
            sal = None
            for i in range(lleno + 1, len(v)):
                if h[i] >= stop:
                    sal = stop
                    break
                if l[i] <= obj:
                    sal = obj
                    break
                if hm[i] >= 1155:
                    sal = c[i]
                    break
            if sal is None:
                sal = c[-1]
        bruto = (px - sal) / R
        neto = bruto - coste_pb * 1e-4 * precio / R
        res.append({'fecha': D, 'dir': 'corto' if corto else 'largo', 'bruto': bruto, 'neto': neto,
                    'R_pb': R / precio * 1e4})
    return pd.DataFrame(res)


def resumen(x, col):
    n = len(x)
    if n < 2:
        return n, np.nan, np.nan
    return n, x[col].mean(), x[col].mean() / x[col].std(ddof=1) * np.sqrt(n)


def main():
    es, eu, xau = sys.argv[1:4]
    datos = {'ES': cargar_es(es), 'EURUSD': cargar_histdata(eu), 'XAUUSD': cargar_histdata(xau)}
    salida = []
    for nombre, m1 in datos.items():
        ops = operaciones(m1, COSTE_PB[nombre])
        ops.to_csv(f'c74_ops_{nombre}.csv', index=False)
        n, mb, tb = resumen(ops, 'bruto')
        _, mn, tn = resumen(ops, 'neto')
        d1 = ops[ops.fecha < '2019-01-01']
        d2 = ops[ops.fecha >= '2019-01-01']
        _, m1n, t1 = resumen(d1, 'neto')
        _, m2n, t2 = resumen(d2, 'neto')
        gan = (ops.bruto > 0).mean() * 100
        pasa = (mn > 0) and (tn >= T_EXITO) and (m1n > 0) and (m2n > 0)
        salida.append(f'== {nombre} (coste {COSTE_PB[nombre]} pb) ==')
        salida.append(f'operaciones {n}  aciertos {gan:.1f}%  riesgo mediano {ops.R_pb.median():.1f} pb')
        salida.append(f'bruto {mb:+.3f} R (t {tb:+.2f})   neto {mn:+.3f} R (t {tn:+.2f})')
        salida.append(f'2011-2018: n {len(d1)} neto {m1n:+.3f} R (t {t1:+.2f})   '
                      f'2019-2026: n {len(d2)} neto {m2n:+.3f} R (t {t2:+.2f})')
        for dirn, g in ops.groupby('dir'):
            salida.append(f'  {dirn}: n {len(g)} neto {g.neto.mean():+.3f} R')
        por_anio = ops.groupby(ops.fecha.dt.year).neto.agg(['count', 'mean'])
        salida.append('  por año (n, R neta media): ' + ', '.join(
            f'{a}:{int(r["count"])}/{r["mean"]:+.2f}' for a, r in por_anio.iterrows()))
        salida.append(f'VEREDICTO {nombre}: {"PASA (candidata)" if pasa else "NO PASA"}')
        salida.append('')
    texto = '\n'.join(salida)
    print(texto)
    with open('c74_resultados.txt', 'w') as f:
        f.write(texto + '\n')


if __name__ == '__main__':
    main()
