"""C21: "box story" en EUR/USD y GBP/USD con FXCM M1 BID/ASK (PREREGISTRO_C21_box_story.md).
Uso: python3 c21_box_story.py DIR_FXCM"""
import glob, os, sys
import numpy as np
import pandas as pd
from c1_certificacion import t_nw

COM, DESL = 0.45e-4, 0.1e-4


def cargar(d, par):
    fs = sorted(glob.glob(os.path.join(d, par, f'{par}_*.csv.gz')))
    x = pd.concat([pd.read_csv(f, compression='gzip') for f in fs])
    t = pd.to_datetime(x.DateTime, format='%m/%d/%Y %H:%M:%S.%f').dt.tz_localize('UTC').dt.tz_convert('America/New_York').dt.tz_localize(None)
    m = pd.DataFrame({'o': (x.BidOpen + x.AskOpen).values / 2, 'h': (x.BidHigh + x.AskHigh).values / 2,
                      'l': (x.BidLow + x.AskLow).values / 2, 'c': (x.BidClose + x.AskClose).values / 2,
                      'spr': (x.AskClose - x.BidClose).values}, index=t)
    m = m[~m.index.duplicated()].sort_index()
    m['dia'] = (m.index + pd.Timedelta(hours=7)).normalize()          # día FX: 17:00 NY → 17:00 NY
    return m


def operar(m):
    ops = []
    dias = sorted(m.dia.unique())
    g = {d: s for d, s in m.groupby('dia')}
    for ayer, hoy in zip(dias[:-1], dias[1:]):
        a, s = g[ayer], g[hoy]
        if len(a) < 600 or len(s) < 600 or pd.Timestamp(hoy).weekday() >= 5:
            continue
        H, L = a.h.max(), a.l.min(); R = H - L
        if R <= 0:
            continue
        h1 = s.resample('1h', label='right', closed='left').agg({'o': 'first', 'h': 'max', 'l': 'min', 'c': 'last', 'spr': 'last'}).dropna()
        prev = None
        for t, v in h1.iterrows():
            hr = t.hour + t.minute / 60
            if prev is not None and 3 <= hr <= 15:
                rango = v.h - v.l
                lado = 0
                if rango > 0 and v.l <= L + 0.25 * R and (min(v.o, v.c) - v.l) >= 0.5 * rango and v.c > prev.h:
                    lado, stop, obj = +1, v.l, (H + L) / 2
                elif rango > 0 and v.h >= H - 0.25 * R and (v.h - max(v.o, v.c)) >= 0.5 * rango and v.c < prev.l:
                    lado, stop, obj = -1, v.h, (H + L) / 2
                if lado and (obj - v.c) * lado > 0:
                    resto = s[(s.index >= t) & (s.index < t.normalize() + pd.Timedelta(hours=16, minutes=55))]
                    salida, motivo, spr_s = (resto.c.iloc[-1], 'cierre', resto.spr.iloc[-1]) if len(resto) else (v.c, 'cierre', v.spr)
                    for tt, w in resto.iterrows():
                        if (lado > 0 and w.l <= stop) or (lado < 0 and w.h >= stop):
                            salida, motivo, spr_s = stop, 'stop', w.spr; break
                        if (lado > 0 and w.h >= obj) or (lado < 0 and w.l <= obj):
                            salida, motivo, spr_s = obj, 'objetivo', w.spr; break
                    bruto = lado * np.log(salida / v.c)
                    coste = (v.spr + spr_s) / 2 / v.c + COM + 2 * DESL
                    ops.append(dict(dia=pd.Timestamp(hoy), lado=lado, bruto=bruto, coste=coste, neto=bruto - coste,
                                    R=(bruto - coste) / abs(np.log(stop / v.c)), motivo=motivo))
                    break
            prev = v
    return pd.DataFrame(ops).set_index('dia')


if __name__ == '__main__':
    d = sys.argv[1]
    todos = []
    for par in ('EURUSD', 'GBPUSD'):
        t = operar(cargar(d, par)); t['par'] = par; todos.append(t)
        t.to_csv(f'c21b_{par}.csv')
    t = pd.concat(todos).sort_index()
    res = {}
    for nom, x0 in (('EUR+GBP', t), ('EURUSD', t[t.par == 'EURUSD']), ('GBPUSD', t[t.par == 'GBPUSD'])):
        print(f'\n== {nom} ==')
        for a, b in (('2012', '2018'), ('2019', '2026')):
            x = x0.loc[a:b]; an = x.neto.groupby(x.index.year).sum()
            print(f'  {a}-{b}: n {len(x)} bruto {x.bruto.mean()*1e4:5.2f} pb neto {x.neto.mean()*1e4:5.2f} pb (t {t_nw(x.neto):.2f}) '
                  f'coste {x.coste.mean()*1e4:.2f} pb bruto/coste {x.bruto.mean()/x.coste.mean():.2f} R {x.R.mean():.3f} años+ {(an > 0).sum()}/{len(an)} '
                  f'objetivo {(x.motivo == "objetivo").mean()*100:.0f}% stop {(x.motivo == "stop").mean()*100:.0f}%')
            res[(nom, a)] = (x, an)
    d0 = res[('EUR+GBP', '2012')][0]; c, an = res[('EUR+GBP', '2019')]
    crit = {'D>0': d0.neto.mean() > 0, '1 t>=2': c.neto.mean() > 0 and t_nw(c.neto) >= 2,
            '2 bruto>=3x': c.bruto.mean() >= 3 * c.coste.mean(), '3 años>=60%': (an > 0).mean() >= 0.6}
    print('\nCRITERIOS:', crit, '→ CERTIFICADA' if all(crit.values()) else '→ NO CERTIFICADA')
