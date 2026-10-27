"""C76: continuacion 5 minutos despues de noticias (PREREGISTRO_C76, commit 654ecb7).
Uso: python3 c76_continuacion_noticias.py FOMC_CSV DIR_GC_M1 ES_1m.pkl DIR_HISTDATA_EURUSD"""
import glob
import os
import sys

import numpy as np
import pandas as pd

from c1_certificacion import t_nw
from c74_modelo_tjr_ny import cargar_histdata

COSTE = {'oro': 2.9, 'EURUSD': 1.1}
T_EXITO = 2.64


def precio(s, t):
    """cierre del ultimo minuto que empieza antes de t (busca hasta 10 minutos atras)"""
    y = s.loc[t - pd.Timedelta(minutes=10): t - pd.Timedelta(minutes=1)]
    return y.iloc[-1] if len(y) else np.nan


def fechas_nfp(es):
    cierre = es['close']
    dias = pd.DatetimeIndex(sorted(set(cierre.index.normalize())))
    out = []
    for (y, m), _ in pd.Series(0, index=pd.date_range('2010-07-01', '2026-09-30')).groupby(lambda d: (d.year, d.month)):
        vie = [d for d in pd.date_range(f'{y}-{m:02d}-01', f'{y}-{m:02d}-14') if d.dayofweek == 4]
        cand = list(vie)
        for v in vie:                                   # jueves anterior si el viernes es festivo (4 de julio)
            if (v.month == 7 and v.day in (3, 4)) or (v.month == 1 and v.day == 1) or (v.month == 12 and v.day == 25):
                cand.append(v - pd.Timedelta(days=1))
        mejor, mov = None, -1
        for d in cand:
            if d not in dias:
                continue
            a, b = precio(cierre, d + pd.Timedelta(hours=8, minutes=29)), precio(cierre, d + pd.Timedelta(hours=8, minutes=31))
            if np.isnan(a) or np.isnan(b):
                continue
            if abs(np.log(b / a)) > mov:
                mejor, mov = d, abs(np.log(b / a))
        if mejor is not None:
            out.append(mejor)
    return pd.DatetimeIndex(out)


def cargar_gc(carpeta, dias):
    piezas = []
    quiero = set(dias)
    for f in sorted(glob.glob(os.path.join(carpeta, 'GC_*.csv'))):
        x = pd.read_csv(f, usecols=['ts_event', 'instrument_id', 'close'])
        t = pd.to_datetime(x.ts_event, utc=True).dt.tz_convert('America/New_York').dt.tz_localize(None)
        x.index = t
        x = x[t.dt.normalize().isin(quiero).values]
        piezas.append(x[['instrument_id', 'close']])
    g = pd.concat(piezas).sort_index()
    return g[~g.index.duplicated()]


def operaciones(serie, inst, eventos, hora):
    filas = []
    for d in eventos:
        T = d + pd.Timedelta(hours=hora[0], minutes=hora[1])
        if inst is not None:
            ventana = inst.loc[T - pd.Timedelta(minutes=10): T + pd.Timedelta(minutes=30)]
            if len(ventana) == 0 or ventana.nunique() != 1:
                continue
        p0, p5, p30 = precio(serie, T), precio(serie, T + pd.Timedelta(minutes=5)), precio(serie, T + pd.Timedelta(minutes=30))
        if np.isnan(p0) or np.isnan(p5) or np.isnan(p30):
            continue
        sg = np.sign(np.log(p5 / p0))
        if sg == 0:
            continue
        filas.append((d, sg * np.log(p30 / p5) * 1e4))
    return pd.Series([v for _, v in filas], index=pd.DatetimeIndex([d for d, _ in filas]))


def main():
    fomc_csv, dir_gc, es_pkl, dir_eu = sys.argv[1:5]
    fomc = pd.DatetimeIndex(pd.read_csv(fomc_csv).iloc[:, 0])
    es = pd.read_pickle(es_pkl)
    es.index = pd.to_datetime(es['ts_event'], utc=True).dt.tz_convert('America/New_York').dt.tz_localize(None)
    es = es[~es.index.duplicated()].sort_index()
    nfp = fechas_nfp(es)
    ev = {'FOMC comunicado 14:00': (fomc[(fomc >= '2013-03-01') & (fomc <= '2026-09-30')], (14, 0), '2020-01-01'),
          'FOMC rueda de prensa 14:30': (fomc[(fomc >= '2019-01-01') & (fomc <= '2026-09-30')], (14, 30), '2023-01-01'),
          'Empleo NFP 08:30': (nfp, (8, 30), '2020-01-01')}
    todas = sorted(set().union(*[set(v[0]) for v in ev.values()]))
    gc = cargar_gc(dir_gc, todas)
    eu = cargar_histdata(dir_eu)
    lin = [f'Fechas NFP identificadas: {len(nfp)} (viernes {np.mean(nfp.dayofweek == 4)*100:.0f} %); ejemplo 2019-2020: '
           + ', '.join(d.strftime('%Y-%m-%d') for d in nfp[(nfp >= '2019-10-01') & (nfp < '2020-08-01')]), '']
    for nom, (fechas, hora, corte) in ev.items():
        for mk, serie, inst in (('oro', gc['close'], gc['instrument_id']), ('EURUSD', eu['close'], None)):
            r = operaciones(serie, inst, fechas, hora)
            a, b = r[r.index < corte], r[r.index >= corte]
            t = t_nw(r.values)
            pasa = r.mean() > 0 and t >= T_EXITO and a.mean() > 0 and b.mean() > 0 and b.mean() > COSTE[mk]
            lin.append(f'{nom} | {mk}: n {len(r)}  continuacion {r.mean():+.2f} pb (t {t:+.2f}), aciertos {(r > 0).mean()*100:.0f} %  | '
                       f'antes de {corte[:4]} {a.mean():+.2f} (n {len(a)})  desde {corte[:4]} {b.mean():+.2f} (n {len(b)})  | coste {COSTE[mk]} pb  '
                       f'-> {"PASA" if pasa else "no pasa"}   [informativo reversion: {-r.mean():+.2f} pb]')
    txt = '\n'.join(lin)
    print(txt)
    open('c76_resultados.txt', 'w').write(txt + '\n')


if __name__ == '__main__':
    main()
