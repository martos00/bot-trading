"""Certificación C1 — EURUSD corto 06:00 → 08:00 ET con Dukascopy (punto medio BID/ASK). PREREGISTRO_C1_eurusd_manana_europea.md
Fuente principal FXCM (velas M1 BID/ASK, UTC); los días sin FXCM se completan con Dukascopy (apéndice 1 del pre-registro).
Uso: python3 c1_certificacion.py DIR_FXCM DIR_DUKASCOPY H80_EURUSD.csv H80_GBPUSD.csv [--faltan SALIDA_TXT]"""
import glob, lzma, os, struct, sys
from datetime import datetime, timedelta, timezone
from zoneinfo import ZoneInfo
import numpy as np
import pandas as pd

NY = ZoneInfo('America/New_York')


def velas(f, div=1e5):
    b = open(f, 'rb').read()
    if not b:
        return {}
    b = lzma.decompress(b)
    dia = datetime.strptime(os.path.basename(f).split('_')[-1][:10], '%Y-%m-%d').replace(tzinfo=timezone.utc)
    return {int((dia + timedelta(seconds=struct.unpack('>I', b[i * 24:i * 24 + 4])[0])).timestamp()) // 60:
            struct.unpack('>IIIIIf', b[i * 24:(i + 1) * 24])[2] / div for i in range(len(b) // 24)}


def fxcm(f):
    """Velas de un fichero semanal de FXCM → ({minuto: cierre BID}, {minuto: cierre ASK}); minuto = inicio de la vela (UTC)."""
    x = pd.read_csv(f, compression='gzip')
    m = ((pd.to_datetime(x.DateTime, format='%m/%d/%Y %H:%M:%S.%f') - pd.Timestamp('1970-01-01')) // pd.Timedelta(minutes=1)).to_numpy()
    return dict(zip(m, x.BidClose.to_numpy(float))), dict(zip(m, x.AskClose.to_numpy(float)))


def en(d, T):
    """Cierre del último minuto que termina en o antes de T (tolerancia 5 min), como en HistData/H80."""
    base = int(T.timestamp()) // 60
    for j in range(1, 6):
        if base - j in d:
            return d[base - j]
    return np.nan


def t_nw(x, L=5):
    x = np.asarray(x, float); x = x[~np.isnan(x)]; n = len(x); e = x - x.mean()
    g = [e[k:] @ e[:n - k] / n for k in range(L + 1)]
    return x.mean() / np.sqrt((g[0] + 2 * sum((1 - k / (L + 1)) * g[k] for k in range(1, L + 1))) / n)


if __name__ == '__main__':
    dir_fxcm, dir_duka, h80_eur, h80_gbp = sys.argv[1:5]
    fb, fa = {}, {}
    for f in sorted(glob.glob(os.path.join(dir_fxcm, 'EURUSD_*.csv.gz'))):
        b, a = fxcm(f)
        fb.update(b); fa.update(a)
    db, da = {}, {}
    for f in sorted(glob.glob(os.path.join(dir_duka, 'EURUSD_BID_*.bi5'))):
        db.update(velas(f))
    for f in sorted(glob.glob(os.path.join(dir_duka, 'EURUSD_ASK_*.bi5'))):
        da.update(velas(f))
    filas, faltan = [], []
    for d in pd.bdate_range('2018-01-01', '2026-09-30'):
        fila = {'dia': d}
        ok_fxcm = all(not np.isnan(en(fb, datetime(d.year, d.month, d.day, h, tzinfo=NY))) for h in (6, 8))
        bid, ask = (fb, fa) if ok_fxcm else (db, da)
        fila['fuente'] = 'FXCM' if ok_fxcm else 'Dukascopy'
        for h in (5, 6, 7, 8, 9):
            T = datetime(d.year, d.month, d.day, h, tzinfo=NY)
            b, a = en(bid, T), en(ask, T)
            fila[f'bid{h}'], fila[f'mid{h}'], fila[f'spr{h}'] = b, (a + b) / 2, (a - b) / ((a + b) / 2) * 1e4
        if not ok_fxcm and np.isnan(fila['mid6'] + fila['mid8']):
            faltan.append(d.date().isoformat())
        filas.append(fila)
    if '--faltan' in sys.argv:
        open(sys.argv[sys.argv.index('--faltan') + 1], 'w').write('\n'.join(faltan) + '\n')
        print(f'Días sin dato en ninguna fuente: {len(faltan)}')
        sys.exit()
    x = pd.DataFrame(filas).set_index('dia')
    print('Días por fuente:', x.fuente.value_counts().to_dict())
    corto = lambda p, h0, h1: -np.log(x[f'{p}{h1}'] / x[f'{p}{h0}'])
    mid, bidr = corto('mid', 6, 8), corto('bid', 6, 8)
    print(f'Días con dato: {mid.notna().sum()} de {len(x)}')
    m, t = mid.mean() * 1e4, t_nw(mid.dropna())
    print(f'\nC1 Dukascopy punto medio, corto 06→08 ET 2018-2026: media {m:.2f} pb, t_NW {t:.2f}  → {"CUMPLE" if m > 0 and t >= 3 else "NO CUMPLE"} (t ≥ 3)')
    anual = mid.groupby(mid.index.year).mean() * 1e4
    print('C2 media por año (pb):', anual.round(2).to_dict(), f'→ positivos {(anual > 0).sum()}/9',
          '→ CUMPLE' if (anual > 0).sum() >= 7 else '→ NO CUMPLE')
    hd = -pd.read_csv(h80_eur, index_col=0, parse_dates=True)['h06_d2']
    j = pd.concat([mid.rename('duka'), hd.rename('histdata')], axis=1, join='inner').dropna()
    c, dif = j.corr().iat[0, 1], (j.duka.mean() - j.histdata.mean()) * 1e4
    print(f'C3 concordancia con HistData: n {len(j)}, correlación {c:.3f}, diferencia de medias {dif:+.2f} pb',
          '→ CUMPLE' if c >= 0.9 and abs(dif) <= 0.3 else '→ NO CUMPLE')
    db = (mid.mean() - bidr.mean()) * 1e4
    print(f'C4 punto medio − BID: {db:+.3f} pb', '→ CUMPLE' if abs(db) <= 0.3 else '→ NO CUMPLE',
          f'| spread mediano 06:00 {x.spr6.median():.2f} pb, 08:00 {x.spr8.median():.2f} pb')
    print('\nInformativo:')
    for h0, h1 in ((5, 7), (7, 9), (6, 7), (7, 8)):
        r = corto('mid', h0, h1)
        print(f'  Dukascopy corto {h0:02d}→{h1:02d} ET: media {r.mean() * 1e4:.2f} pb, t {t_nw(r.dropna()):.2f}')
    g = -pd.read_csv(h80_gbp, index_col=0, parse_dates=True)['h06_d2'].loc['2018':'2026-09']
    print(f'  GBPUSD (HistData) corto 06→08 ET 2018-2026: media {g.mean() * 1e4:.2f} pb, t {t_nw(g.dropna()):.2f}')
    x.to_csv(os.path.join(os.path.dirname(os.path.abspath(__file__)), 'c1_precios_dukascopy.csv'))
