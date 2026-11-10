"""Apex 150K con reinversión: empiezas con 3 evaluaciones; de cada cobro apartas 30 % para impuestos y el resto compra evaluaciones nuevas
(200 $ cada una, supuesto) hasta 20 cuentas (fondeadas + en examen ≤ 24). Mismas operaciones en todas. ¿Cuándo llega a 10.000 $/mes?
(media móvil de 3 meses de los cobros). Uso: python3 apex_reinversion_10k.py DIR_SCRATCH"""
import sys, numpy as np, pandas as pd
exec(open('apex_rotacion.py').read().split('rng = np.random')[0])
rng = np.random.default_rng(41); PRECIO = 200; T = 252 * 4
def flota(x):
    st = rng.integers(0, len(x) - B, T // B + 1); R = x[(st[:, None] + np.arange(B)).ravel()[:T]] * CAP
    A = [dict(f='e', eq=0.0, hwm=0.0) for _ in range(3)]; bolsa = 0.0; mes = np.zeros(T // 21 + 2)
    for t in range(T):
        r = R[t]
        for a in A:
            if a['f'] == 'e':
                a['eq'] += r; a['hwm'] = min(max(a['hwm'], a['eq']), DD)
                if a['eq'] <= a['hwm'] - DD: a['f'] = 'x'
                elif a['eq'] >= OBJ: a.update(f='f', bal=CAP, hwm=CAP, k=0, dias=0, mx=0.0, ini=CAP)
            elif a['f'] == 'f':
                a['bal'] += r; a['hwm'] = max(a['hwm'], a['bal']); piso = min(a['hwm'] - DD, CAP + 100)
                if a['bal'] <= piso: a['f'] = 'x'; continue
                if r >= 350: a['dias'] += 1
                a['mx'] = max(a['mx'], r); ben = a['bal'] - a['ini']
                if a['bal'] >= MINC and a['dias'] >= 5 and ben > 0 and a['mx'] < 0.5 * ben:
                    q = min(ESC[a['k']], a['bal'] - RED)
                    if q >= 500:
                        a['bal'] -= q; a['k'] += 1; a.update(dias=0, mx=0.0, ini=a['bal']); mes[t // 21] += q; bolsa += 0.7 * q
                        if a['k'] == 6: a['f'] = 'x'
        A = [a for a in A if a['f'] != 'x']
        nf = sum(a['f'] == 'f' for a in A)
        while bolsa >= PRECIO and nf + sum(a['f'] == 'e' for a in A) < 24 and nf < 20:
            A.append(dict(f='e', eq=0.0, hwm=0.0)); bolsa -= PRECIO
        if not A and bolsa < PRECIO: A.append(dict(f='e', eq=0.0, hwm=0.0))   # si te quedas sin nada, compras otra de tu bolsillo
    mm = pd.Series(mes[:T // 21]).rolling(3).mean().values
    hit = np.argmax(mm >= 10000) if np.any(mm >= 10000) else None
    return hit, mes
for hair, et in ((1.0, 'BACKTEST'), (0.6, 'REAL AL 60 %')):
    x = SER - SER.mean() * (1 - hair); res = [flota(x) for _ in range(1000)]
    h = np.array([r[0] if r[0] is not None else np.nan for r in res]); M = np.array([r[1][:48] for r in res])
    print(f'{et}: llega a 10.000 $/mes cobrados (media de 3 meses) en 4 años {np.mean(~np.isnan(h))*100:.0f} % | mes mediano {np.nanmedian(h)+1:.0f} (25 % más rápido: {np.nanpercentile(h,25)+1:.0f}; 25 % más lento: {np.nanpercentile(h,75)+1:.0f})')
    print('   cobro medio por año (antes de impuestos):', [f'{M[:, i*12:(i+1)*12].sum(axis=1).mean():,.0f} $' for i in range(4)])
