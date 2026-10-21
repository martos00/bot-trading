"""C33: ruptura del rango del día anterior (R) y reversión después de noticias de las 08:30 (N). Ver PREREGISTRO_C33."""
import sys
import numpy as np, pandas as pd
from scipy import stats
from c1_certificacion import t_nw
from c21_box_story import cargar
COM, DESL = 0.45e-4, 0.1e-4
D = '/tmp/claude-0/-home-user-bot-trading/682335b1-28ae-5d18-9355-ce7f0f968722/scratchpad/fxcm'


def simular(h, l, c, spr, k0, lado, entrada, stop, obj, fin):
    for j in range(k0, fin):
        if (lado > 0 and l[j] <= stop) or (lado < 0 and h[j] >= stop):
            return stop, spr[j]
        if j > k0 and ((lado > 0 and h[j] >= obj) or (lado < 0 and l[j] <= obj)):
            return obj, spr[j]
    return c[fin - 1], spr[fin - 1]


R, N = {}, {}
for par in ('EURUSD', 'GBPUSD'):
    m = cargar(D, par)
    mins = m.index.hour * 60 + m.index.minute
    m = m.assign(mins=mins)
    dias = sorted(m.dia.unique()); g = {d: s for d, s in m.groupby('dia')}
    ventana_abs = []
    for ayer, hoy in zip(dias[:-1], dias[1:]):
        a, s = g[ayer], g[hoy]
        if len(a) < 600 or len(s) < 600 or pd.Timestamp(hoy).weekday() >= 5: continue
        h, l, c, sp, mm, o = s.h.values, s.l.values, s.c.values, s.spr.values, s.mins.values, s.o.values
        fin = np.searchsorted(mm, 16 * 60 + 55) if False else None
        cal = (s.index.normalize() == pd.Timestamp(hoy))          # minutos del día natural de hoy (el día FX empieza a las 17:00 de ayer)
        idx = np.flatnonzero(np.asarray(cal))
        if len(idx) < 300: continue
        # ---- R
        H, L = a.h.max(), a.l.min(); rango = H - L
        hoy_min = mm[idx]
        ent_ok = idx[(hoy_min >= 180) & (hoy_min < 720)]
        fin_i = idx[hoy_min < 16 * 60 + 55]
        if rango > 0 and len(ent_ok) and len(fin_i):
            fin = fin_i[-1] + 1
            for k in ent_ok:
                lado = +1 if h[k] >= H else (-1 if l[k] <= L else 0)
                if lado:
                    # orden stop: si la vela abre ya más allá del nivel, se ejecuta a la apertura (corrección 21-oct-2026)
                    ent = max(H, o[k]) if lado > 0 else min(L, o[k])
                    sal, sp_s = simular(h, l, c, sp, k, lado, ent, (H + L) / 2, ent + lado * rango, fin)
                    bruto = lado * np.log(sal / ent); coste = (sp[k] + sp_s) / 2 / ent + COM + 2 * DESL
                    R.setdefault(pd.Timestamp(hoy), []).append((bruto, bruto - coste)); break
        # ---- N
        def en_min(t):
            j = idx[(hoy_min <= t) & (hoy_min > t - 5)]
            return j[-1] if len(j) else None
        k0, k1, k2 = en_min(8 * 60 + 29), en_min(8 * 60 + 45), en_min(10 * 60)
        if None in (k0, k1, k2): continue
        mov = np.log(c[k1] / c[k0]); hist = ventana_abs[-60:]
        if len(hist) == 60 and abs(mov) > 3 * np.median(hist):
            lado = -np.sign(mov)
            tramo = slice(k0, k1 + 1)
            stop = h[tramo].max() if lado < 0 else l[tramo].min()
            sal, sp_s = simular(h, l, c, sp, k1 + 1, lado, c[k1], stop, np.inf * lado, k2 + 1)
            bruto = lado * np.log(sal / c[k1]); coste = (sp[k1] + sp_s) / 2 / c[k1] + COM + 2 * DESL
            N.setdefault(pd.Timestamp(hoy), []).append((bruto, bruto - coste))
        ventana_abs.append(abs(mov))
res = {}
for nom, dd in (('R ruptura del día anterior', R), ('N reversión post-noticia', N)):
    x = pd.DataFrame({d: np.mean(v, axis=0) for d, v in dd.items()}, index=['bruto', 'neto']).T.sort_index()
    res[nom] = x
ps, filas = [], []
for nom, x in res.items():
    d, c = x.loc['2012':'2018'], x.loc['2019':'2026']; an = c.neto.groupby(c.index.year).sum(); t = t_nw(c.neto.values)
    ps.append(1 - stats.norm.cdf(t)); filas.append((nom, d, c, an, t))
orden = np.argsort(ps); ok = [False] * 2; seguir = True
for k, i in enumerate(orden):
    seguir = seguir and ps[i] <= 0.05 / (2 - k); ok[i] = seguir
for (nom, d, c, an, t), o in zip(filas, ok):
    coste = (c.bruto - c.neto).mean()
    cert = o and (an > 0).mean() >= 0.6 and c.bruto.mean() >= 3 * coste
    print(f'{nom}: 2012-18 n {len(d)} neto {d.neto.mean()*1e4:6.2f} pb (t {t_nw(d.neto.values):.2f}) | 2019-26 n {len(c)} bruto {c.bruto.mean()*1e4:6.2f} '
          f'neto {c.neto.mean()*1e4:6.2f} pb (t {t:.2f}) coste {coste*1e4:.2f} años+ {(an>0).sum()}/{len(an)} | Holm {o} → {"CERTIFICADA" if cert else "no"}')
