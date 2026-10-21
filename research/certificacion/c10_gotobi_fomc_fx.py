"""C10: gotobi del yen y prima del dólar en días de la Fed (PREREGISTRO_C10_gotobi_fomc_fx.md).
Uso: python3 c10_gotobi_fomc_fx.py DIR_FXCM DIR_HISTDATA FOMC_CSV"""
import calendar, glob, os, sys
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo
import holidays
import numpy as np
import pandas as pd
from c1_certificacion import fxcm, en, t_nw
from c6_fin_de_mes_fixing import histdata

TOK, NY = ZoneInfo('Asia/Tokyo'), ZoneInfo('America/New_York')
COM, DESL, NOCHE = 0.45e-4, 0.1e-4, 0.5e-4
CESTA = {'EURUSD': +1, 'GBPUSD': +1, 'AUDUSD': +1, 'USDJPY': -1, 'USDCHF': -1}   # signo de "corto en USD"
JP = holidays.Japan(years=range(2003, 2027))


def gotobi(a0, a1):
    out = set()
    for y in range(a0, a1 + 1):
        for m in range(1, 13):
            for d in (5, 10, 15, 20, 25, calendar.monthrange(y, m)[1]):
                f = datetime(y, m, d).date()
                while f.weekday() >= 5 or f in JP:
                    f -= timedelta(days=1)
                out.add(f)
    return sorted(out)


def tramo(px, signo, t0, t1):
    """(rent. precio medio, rent. ejecutable) de una posición con signo (+1 compra del par) entre t0 y t1."""
    b, a = px
    b0, b1 = en(b, t0), en(b, t1)
    if a is None:                                     # HistData: solo BID
        return signo * np.log(b1 / b0), np.nan
    a0, a1 = en(a, t0), en(a, t1)
    m = signo * np.log(((b1 + a1) / 2) / ((b0 + a0) / 2))
    ej = np.log(b1 / a0) if signo > 0 else np.log(b0 / a1)
    return m, ej


def regla_G(px, dias, h0=3, m0=0):
    filas = []
    for f in dias:
        t1 = datetime(f.year, f.month, f.day, 9, 55, tzinfo=TOK)
        t0 = datetime(f.year, f.month, f.day, h0, m0, tzinfo=TOK)
        m, ej = tramo(px, +1, t0, t1)
        filas.append(dict(dia=pd.Timestamp(f), medio=m, ejec=ej - COM - 2 * DESL - NOCHE * (h0 < 8)))
    return pd.DataFrame(filas).set_index('dia').dropna(subset=['medio'])


def regla_F(pxs, fechas):
    filas = []
    for f in fechas:
        t1 = datetime(f.year, f.month, f.day, 16, tzinfo=NY)
        prev = f - pd.offsets.BDay(1)
        t0 = datetime(prev.year, prev.month, prev.day, 16, tzinfo=NY)
        rs = {p: tramo(pxs[p], s, t0, t1) for p, s in CESTA.items() if p in pxs}
        ms = [v[0] for v in rs.values() if not np.isnan(v[0])]
        if len(ms) < len(rs):
            continue
        ejs = [v[1] for v in rs.values()]
        noches = (t1 - t0).days
        fila = dict(dia=f, medio=np.mean(ms), ejec=np.mean(ejs) - COM - 2 * DESL - NOCHE * noches)
        fila.update({p: v[0] for p, v in rs.items()})
        filas.append(fila)
    return pd.DataFrame(filas).set_index('dia')


def resumen(x, nombre, conf):
    anual = (x.ejec if conf else x.medio).groupby(x.index.year).sum()
    s = f'  {nombre}: n {len(x)}  medio {x.medio.mean()*1e4:6.2f} pb (t {t_nw(x.medio):.2f})'
    if conf:
        coste = (x.medio - x.ejec).mean()
        s += f'  ejecutable {x.ejec.mean()*1e4:6.2f} pb (t {t_nw(x.ejec):.2f})  coste {coste*1e4:.2f} pb  medio/coste {x.medio.mean()/coste:.2f}'
    print(s + f'  años+ {int((anual > 0).sum())}/{len(anual)}')
    return anual


def carga_fxcm(d, par):
    b, a = {}, {}
    for f in sorted(glob.glob(os.path.join(d, par, f'{par}_*.csv.gz'))):
        bb, aa = fxcm(f); b.update(bb); a.update(aa)
    return b, a


if __name__ == '__main__':
    dfx, dhd, ffomc = sys.argv[1:4]
    fomc = pd.to_datetime(pd.read_csv(ffomc).fomc)
    e1 = None
    if os.path.exists('e1_franjas.csv'):
        z = pd.read_csv('e1_franjas.csv', index_col=0, parse_dates=True); e1 = (-np.log(z.mid8 / z.mid6)).dropna()
    hd = {p: (histdata(dhd, p), None) for p in CESTA if os.path.isdir(os.path.join(dhd, p))}
    fx = {p: carga_fxcm(dfx, p) for p in CESTA}
    crit = {}
    print('===== G: gotobi USD/JPY 03:00 → 09:55 Tokio =====')
    gd = regla_G(hd['USDJPY'], gotobi(2003, 2011)); resumen(gd, 'Descubrimiento HistData 2003-2011', False)
    gc = regla_G(fx['USDJPY'], [f for f in gotobi(2012, 2026) if f <= datetime(2026, 9, 30).date()])
    an = resumen(gc, 'Confirmación FXCM 2012-2026', True)
    print('     ejecutable por año (pb):', (an * 1e4).round(0).to_dict())
    g8 = regla_G(fx['USDJPY'], [f for f in gotobi(2012, 2026) if f <= datetime(2026, 9, 30).date()], 8, 0)
    resumen(g8, 'Informativo 08:00 → 09:55 (sin rollover)', True)
    if e1 is not None:
        print('     correlación con E1 (mismo día):', round(gc.medio.corr(e1.reindex(gc.index)), 3))
    coste = (gc.medio - gc.ejec).mean()
    crit['G'] = {'D: bruto>0': gd.medio.mean() > 0, '1: ejec>0 t>=2,24': gc.ejec.mean() > 0 and t_nw(gc.ejec) >= 2.24,
                 '2: medio>=3x coste': gc.medio.mean() >= 3 * coste, '3: años>=60%': (an > 0).mean() >= 0.6}

    print('\n===== F: corto USD contra la cesta, 16:00 NY del día anterior → 16:00 NY del día del FOMC =====')
    fd = regla_F(hd, [f for f in fomc if 2003 <= f.year <= 2011]); resumen(fd, f'Descubrimiento HistData 2003-2011 ({len(hd)} pares)', False)
    fc = regla_F(fx, [f for f in fomc if 2012 <= f.year and f <= pd.Timestamp('2026-09-30')])
    an = resumen(fc, 'Confirmación FXCM 2012-2026', True)
    print('     ejecutable por año (pb):', (an * 1e4).round(0).to_dict())
    print('     por par (medio, pb):', {p: round(fc[p].mean() * 1e4, 2) for p in CESTA})
    coste = (fc.medio - fc.ejec).mean()
    crit['F'] = {'D: bruto>0': fd.medio.mean() > 0, '1: ejec>0 t>=2,24': fc.ejec.mean() > 0 and t_nw(fc.ejec) >= 2.24,
                 '2: medio>=3x coste': fc.medio.mean() >= 3 * coste, '3: años>=60%': (an > 0).mean() >= 0.6}
    print('\nCRITERIOS:')
    for k, v in crit.items():
        print(' ', k, v, '→ CERTIFICADA' if all(v.values()) else '→ NO CERTIFICADA')
