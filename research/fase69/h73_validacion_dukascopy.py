"""H73 — validación con Dukascopy (ticks BID/ASK) de USDJPY-Tokio. PREREGISTRO_H73_usdjpy_tokio.md.

Uso:
  python3 h73_validacion_dukascopy.py descargar DIR_TICKS
  python3 h73_validacion_dukascopy.py medir DIR_TICKS H71_USDJPY_CSV SALIDA_CSV

Muestra fijada: primer día de Tokio válido (lunes-viernes, no festivo en Japón) de cada mes, 2020-01 → 2026-09.
Instantes: 17:05 ET del día anterior, 09:55 Tokio, 08:00 Frankfurt. Precio = último tick en los 5 minutos previos.
"""
import lzma, os, struct, sys, time
from datetime import date, datetime, timedelta, timezone
from zoneinfo import ZoneInfo
import holidays

NY, FRA, TOK, UTC = (ZoneInfo(z) for z in ('America/New_York', 'Europe/Berlin', 'Asia/Tokyo', 'UTC'))
URL = 'https://datafeed.dukascopy.com/datafeed/USDJPY/{y}/{m:02d}/{d:02d}/{h:02d}h_ticks.bi5'


def dias_muestra():
    fj = holidays.Japan(years=range(2020, 2027))
    out = []
    for y in range(2020, 2027):
        for m in range(1, 13):
            if (y, m) > (2026, 9):
                break
            d = date(y, m, 1)
            while d.weekday() >= 5 or d in fj:
                d += timedelta(days=1)
            out.append(d)
    return out


def instantes(d):
    return {'t1a': datetime(d.year, d.month, d.day, 17, 5, tzinfo=NY) - timedelta(days=1),
            't1b': datetime(d.year, d.month, d.day, 9, 55, tzinfo=TOK),
            't2b': datetime(d.year, d.month, d.day, 8, 0, tzinfo=FRA)}


def hora_fichero(T):
    h = (T - timedelta(minutes=1)).astimezone(UTC)
    return h.replace(minute=0, second=0, microsecond=0)


def descargar(raiz):
    sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
    import descargar_dukascopy_m1 as dk
    os.makedirs(raiz, exist_ok=True)
    for d in dias_muestra():
        for k, T in instantes(d).items():
            h = hora_fichero(T)
            f = os.path.join(raiz, f'USDJPY_{h:%Y%m%d%H}.bi5')
            if os.path.exists(f):
                continue
            datos = dk.pedir(URL.format(y=h.year, m=h.month - 1, d=h.day, h=h.hour))
            open(f, 'wb').write(datos)
            time.sleep(4)
        print(d, flush=True)
    print('FIN', flush=True)


def ticks(f, h):
    b = open(f, 'rb').read()
    if not b:
        return []
    b = lzma.decompress(b)
    out = []
    for i in range(len(b) // 20):
        ms, ask, bid, _, _ = struct.unpack('>IIIff', b[i * 20:(i + 1) * 20])
        out.append((h + timedelta(milliseconds=ms), ask / 1000, bid / 1000))
    return out


def en(raiz, T):
    h = hora_fichero(T)
    f = os.path.join(raiz, f'USDJPY_{h:%Y%m%d%H}.bi5')
    if not os.path.exists(f):
        return None
    tk = [x for x in ticks(f, h) if T - timedelta(minutes=5) <= x[0] < T]
    return tk[-1] if tk else None


def medir(raiz, h71_csv, salida):
    import numpy as np
    import pandas as pd
    hd = pd.read_csv(h71_csv, parse_dates=['dia'])
    hd = hd[(hd.estrategia == 'TOKIO') & hd.completo].set_index('dia')
    filas = []
    for d in dias_muestra():
        v = {k: en(raiz, T) for k, T in instantes(d).items()}
        if any(x is None for x in v.values()):
            continue
        mid = {k: (a + b) / 2 for k, (_, a, b) in v.items()}
        sp = {k: (a - b) / ((a + b) / 2) * 1e4 for k, (_, a, b) in v.items()}
        r_mid = np.log(mid['t1b'] / mid['t1a']) - np.log(mid['t2b'] / mid['t1b'])
        fila = dict(dia=d, r_duka_mid=r_mid, r_duka_bid=np.log(v['t1b'][2] / v['t1a'][2]) - np.log(v['t2b'][2] / v['t1b'][2]),
                    r1_mid=np.log(mid['t1b'] / mid['t1a']), **{f'spread_{k}_pb': s for k, s in sp.items()},
                    **{f'pips_{k}': (v[k][1] - v[k][2]) * 100 for k in v})
        ts = pd.Timestamp(d)
        fila['r_histdata'] = hd.loc[ts, 'r'] if ts in hd.index else np.nan
        filas.append(fila)
    df = pd.DataFrame(filas)
    df.to_csv(salida, index=False)
    x = df.dropna(subset=['r_histdata'])
    print(f'Días de muestra con los 3 instantes: {len(df)}; con dato HistData: {len(x)}')
    print(f"Corr(HistData BID, Dukascopy mid) = {x.r_histdata.corr(x.r_duka_mid):.3f}; "
          f"diferencia media = {(x.r_histdata - x.r_duka_mid).mean() * 1e4:.3f} pb/día (mediana {(x.r_histdata - x.r_duka_mid).median() * 1e4:.3f})")
    print(f"Corr(HistData BID, Dukascopy BID) = {x.r_histdata.corr(x.r_duka_bid):.3f}")
    print(f"Media bruta en la muestra: HistData {x.r_histdata.mean() * 1e4:.2f} pb, Dukascopy mid {x.r_duka_mid.mean() * 1e4:.2f} pb")
    print(df[[c for c in df if c.startswith('spread_') or c.startswith('pips_')]].describe(percentiles=[.5, .9]).round(3).to_string())


if __name__ == '__main__':
    if sys.argv[1] == 'descargar':
        descargar(sys.argv[2])
    else:
        medir(*sys.argv[2:5])
