"""Forma más rápida: comprarlo todo el primer día con dinero propio y reponer con los cobros.
- Apex: 24 evaluaciones de 150K (200 $ c/u, supuesto) → hasta 20 fondeadas.
- CFD tipo FTMO: N cuentas de 100.000 $ (examen 540 $, devuelto con el 1.er cobro; fases +10 % y +5 %, pérdida fija 10 %, diaria 5 %,
  cobro cada 10 días del 80 %); si se pierde, se repone.
Misma cartera (con C113) y mismas operaciones en todo. Riesgo 0,65 %. ¿Cuándo llega la media de 3 meses a 10.000 $ cobrados y a 14.300 $
(≈ 10.000 $ limpios)? Uso: python3 todo_a_la_vez_10k.py DIR_SCRATCH"""
import sys, numpy as np, pandas as pd
exec(open('apex_rotacion.py').read().split('rng = np.random')[0])
rng = np.random.default_rng(47); T = 252 * 3; PRECIO = 200; EXAMEN = 540
def corre(x, ncfd):
    st = rng.integers(0, len(x) - B, T // B + 1); Rf = x[(st[:, None] + np.arange(B)).ravel()[:T]]; R = Rf * CAP
    A = [dict(f='e', eq=0.0, hwm=0.0) for _ in range(24)]; F = [dict(f=1, eq=0.0, pago=True) for _ in range(ncfd)]
    mes = np.zeros(T // 21 + 2); inv = 24 * PRECIO + ncfd * EXAMEN; gasto = 0.0
    for t in range(T):
        r = R[t]; rf = Rf[t]
        for a in A:
            if a['f'] == 'e':
                a['eq'] += r; a['hwm'] = min(max(a['hwm'], a['eq']), DD)
                if a['eq'] <= a['hwm'] - DD: a['f'] = 'x'
                elif a['eq'] >= OBJ: a.update(f='f', bal=CAP, hwm=CAP, k=0, dias=0, mx=0.0, ini=CAP)
            elif a['f'] == 'f':
                a['bal'] += r; a['hwm'] = max(a['hwm'], a['bal'])
                if a['bal'] <= min(a['hwm'] - DD, CAP + 100): a['f'] = 'x'; continue
                if r >= 350: a['dias'] += 1
                a['mx'] = max(a['mx'], r); ben = a['bal'] - a['ini']
                if a['bal'] >= MINC and a['dias'] >= 5 and ben > 0 and a['mx'] < 0.5 * ben:
                    q = min(ESC[a['k']], a['bal'] - RED)
                    if q >= 500:
                        a['bal'] -= q; a['k'] += 1; a.update(dias=0, mx=0.0, ini=a['bal']); mes[t // 21] += q
                        if a['k'] == 6: a['f'] = 'x'
        A = [a for a in A if a['f'] != 'x']
        while sum(a['f'] == 'f' for a in A) + sum(a['f'] == 'e' for a in A) < 24: A.append(dict(f='e', eq=0.0, hwm=0.0)); gasto += PRECIO
        for c in F:
            c['eq'] += rf
            if c['eq'] <= -0.10 or rf <= -0.05: c.update(f=1, eq=0.0, pago=True, ini=t); gasto += EXAMEN; continue
            if c['f'] == 1 and c['eq'] >= 0.10: c.update(f=2, eq=0.0)
            elif c['f'] == 2 and c['eq'] >= 0.05: c.update(f=3, eq=0.0, ini=t)
            elif c['f'] == 3 and (t - c['ini']) % 10 == 0 and c['eq'] > 0:
                q = c['eq'] * 100000 * 0.8 + (EXAMEN if c['pago'] else 0); c.update(eq=0.0, pago=False); mes[t // 21] += q
    mm = pd.Series(mes[:T // 21]).rolling(3).mean().values
    h1 = np.argmax(mm >= 10000) if np.any(mm >= 10000) else np.nan
    h2 = np.argmax(mm >= 14300) if np.any(mm >= 14300) else np.nan
    return h1, h2, inv, mes
for ncfd in (0, 10, 20):
    for hair, et in ((0.6, 'REAL AL 60 %'), (1.0, 'BACKTEST')):
        x = SER - SER.mean() * (1 - hair); res = [corre(x, ncfd) for _ in range(600)]
        h1 = np.array([r[0] for r in res]); h2 = np.array([r[1] for r in res]); M = np.array([r[3][:36] for r in res])
        print(f'Apex 20 + CFD {ncfd} × 100K | {et:12s} | inversión inicial {res[0][2]:,.0f} $ | 10.000 $ cobrados: mes {np.nanmedian(h1)+1:.0f} '
              f'(rápido {np.nanpercentile(h1,25)+1:.0f}, lento {np.nanpercentile(h1,75)+1:.0f}) | 10.000 $ limpios: mes {np.nanmedian(h2)+1:.0f} '
              f'(llega en 3 años {np.mean(~np.isnan(h2))*100:.0f} %) | cobrado año 1 {M[:, :12].sum(axis=1).mean():,.0f} $, año 2 {M[:, 12:24].sum(axis=1).mean():,.0f} $')
