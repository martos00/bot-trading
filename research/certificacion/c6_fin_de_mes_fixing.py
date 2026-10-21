"""C6: cobertura de renta variable en el fixing de Londres de fin de mes (PREREGISTRO_C6_fin_de_mes_fixing.md).
Uso: python3 c6_fin_de_mes_fixing.py DIR_FXCM DIR_HISTDATA DIR_YAHOO"""
import glob, json, os, sys
from datetime import datetime
from zoneinfo import ZoneInfo
import numpy as np
import pandas as pd
from c1_certificacion import fxcm, en

LON, NY = ZoneInfo('Europe/London'), ZoneInfo('America/New_York')
# par: (índice extranjero, signo de "comprar USD" sobre el precio del par)
PARES = {'EURUSD': ('STOXX50E', -1), 'GBPUSD': ('FTSE', -1), 'USDJPY': ('N225', +1),
         'USDCHF': ('SSMI', +1), 'AUDUSD': ('AXJO', -1)}
COMISION, DESLIZ = 0.45e-4, 0.1e-4


def yahoo(d, s):
    r = json.load(open(os.path.join(d, f'{s}.json')))['chart']['result'][0]
    tz = r['meta'].get('exchangeTimezoneName', 'America/New_York')
    idx = pd.to_datetime(r['timestamp'], unit='s', utc=True).tz_convert(tz).tz_localize(None).normalize()
    x = pd.Series(r['indicators']['quote'][0]['close'], index=idx).dropna()
    return x[~x.index.duplicated(keep='last')]


def rent_mes(p, dia):
    """Rentabilidad desde el último cierre del mes anterior hasta el último cierre ANTERIOR a 'dia'."""
    ini = p[p.index < dia.replace(day=1)]
    fin = p[p.index < dia]
    if len(ini) == 0 or len(fin) == 0 or fin.index[-1] < dia.replace(day=1):
        return np.nan
    return fin.iloc[-1] / ini.iloc[-1] - 1


def histdata(d, par):
    fs = [f for f in sorted(glob.glob(os.path.join(d, par, f'DAT_ASCII_{par}_M1_*.csv')))
          if 2003 <= int(os.path.basename(f).split('_')[-1][:4]) <= 2011]
    x = pd.concat([pd.read_csv(f, sep=';', header=None, names=['ts', 'o', 'h', 'l', 'c', 'v']) for f in fs])
    t = pd.to_datetime(x.ts, format='%Y%m%d %H%M%S').dt.tz_localize(NY, ambiguous='NaT', nonexistent='NaT')
    ok = t.notna()
    m = ((t[ok].dt.tz_convert('UTC').dt.tz_localize(None) - pd.Timestamp('1970-01-01')) // pd.Timedelta(minutes=1)).to_numpy()
    return dict(zip(m, x.c[ok].to_numpy(float)))


def ultimos_dias(bid, a0, a1):
    """Último día laborable de cada mes con precio a las 14:00 y 16:00 de Londres."""
    out = []
    for mes in pd.period_range(f'{a0}-01', f'{a1}', freq='M'):
        for d in sorted(pd.bdate_range(mes.start_time, mes.end_time), reverse=True):
            t0 = datetime(d.year, d.month, d.day, 14, tzinfo=LON); t1 = t0.replace(hour=16)
            if not np.isnan(en(bid, t0)) and not np.isnan(en(bid, t1)):
                out.append(d); break
    return out


def t_simple(x):
    x = np.asarray(x, float); x = x[~np.isnan(x)]
    return x.mean() / (x.std(ddof=1) / np.sqrt(len(x))), len(x)


def evaluar(fuente, precios, dias, idx, coste_fijo=None):
    filas = []
    for par, (ind, sgn) in PARES.items():
        mid, spr = precios[par]
        for d in dias[par]:
            s = rent_mes(idx[ind], d) - rent_mes(idx['GSPC'], d)
            if np.isnan(s) or s == 0:
                continue
            pos = sgn * np.sign(s)          # +1 = comprar el par, −1 = venderlo
            t0 = datetime(d.year, d.month, d.day, 14, tzinfo=LON)
            p0, p1, p2 = en(mid, t0), en(mid, t0.replace(hour=16)), en(mid, t0.replace(hour=17))
            bruto = pos * np.log(p1 / p0)
            if coste_fijo is None:
                c = (en(spr, t0) + en(spr, t0.replace(hour=16))) / 2 + COMISION + 2 * DESLIZ
            else:
                c = coste_fijo[par]
            filas.append(dict(fuente=fuente, par=par, dia=d, señal=s, pos=pos, bruto=bruto, coste=c,
                              neto=bruto - c, reversion=-pos * np.log(p2 / p1)))
    return pd.DataFrame(filas)


def informe(x, titulo):
    print(f'\n===== {titulo} =====')
    f = x.groupby(x.dia.dt.to_period('M'))[['bruto', 'neto', 'coste', 'reversion']].mean()
    for c in ('bruto', 'neto', 'reversion'):
        t, n = t_simple(f[c])
        print(f'factor {c:9s}: media {f[c].mean()*1e4:6.2f} pb  t {t:5.2f}  meses {n}')
    print(f'coste medio {f.coste.mean()*1e4:.2f} pb   bruto/coste {f.bruto.mean()/f.coste.mean():.2f}')
    anual = f.neto.groupby(f.index.year).sum() * 1e4
    print('neto por año (pb):', {int(k): round(v, 1) for k, v in anual.items()},
          f' positivos {int((anual > 0).sum())}/{len(anual)}')
    print('por par (bruto pb, t, n):')
    for par, g in x.groupby('par'):
        t, n = t_simple(g.bruto)
        print(f'  {par}: {g.bruto.mean()*1e4:6.2f}  t {t:5.2f}  n {n}  acierto {(g.bruto > 0).mean():.2f}')
    return f


if __name__ == '__main__':
    dir_fxcm, dir_hd, dir_y = sys.argv[1:4]
    idx = {s: yahoo(dir_y, s) for s in ['GSPC'] + [v[0] for v in PARES.values()]}
    precios, dias = {}, {}
    for par in PARES:
        b, a = {}, {}
        for f in sorted(glob.glob(os.path.join(dir_fxcm, par, f'{par}_*.csv.gz'))):
            bb, aa = fxcm(f); b.update(bb); a.update(aa)
        mid = {k: (v + a[k]) / 2 for k, v in b.items() if k in a}
        spr = {k: (a[k] - v) / ((a[k] + v) / 2) for k, v in b.items() if k in a}
        precios[par] = (mid, spr)
        dias[par] = ultimos_dias(mid, 2012, '2026-09')
    fx = evaluar('FXCM', precios, dias, idx)
    fx.to_csv('c6_fxcm.csv', index=False)
    f1 = informe(fx, 'FXCM 2012-01 → 2026-09 (prueba principal)')
    coste_par = fx.groupby('par').coste.median().to_dict()
    print('mediana del coste por par (pb):', {k: round(v * 1e4, 2) for k, v in coste_par.items()})

    precios, dias = {}, {}
    for par in PARES:
        if not os.path.isdir(os.path.join(dir_hd, par)):
            print('sin HistData', par); continue
        bid = histdata(dir_hd, par)
        precios[par] = (bid, None)
        dias[par] = ultimos_dias(bid, 2003, '2011-12')
    pares_hd = {p: PARES[p] for p in precios}
    PARES_ORIG = PARES; PARES = pares_hd
    hd = evaluar('HistData', precios, dias, idx, coste_fijo=coste_par)
    PARES = PARES_ORIG
    hd.to_csv('c6_histdata.csv', index=False)
    f2 = informe(hd, 'HistData 2003-01 → 2011-12 (confirmación, BID)')

    t1, _ = t_simple(f1.neto); t2, _ = t_simple(f2.bruto)
    anual = f1.neto.groupby(f1.index.year).sum()
    crit = {'1 FXCM neto t>=2': f1.neto.mean() > 0 and t1 >= 2,
            '2 bruto >= 3x coste': f1.bruto.mean() >= 3 * f1.coste.mean(),
            '3 años positivos >= 60%': (anual > 0).mean() >= 0.6,
            '4 HistData bruto t>=1,645': f2.bruto.mean() > 0 and t2 >= 1.645}
    print('\nCRITERIOS:', crit, '\nCERTIFICADA' if all(crit.values()) else '\nNO CERTIFICADA')
