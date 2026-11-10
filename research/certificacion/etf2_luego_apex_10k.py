"""2 cuentas de ETF para probar; desde el primer cobro, todo a Apex. Fase 1: ETF 150K (34,70 $/mes, activación 247 $, objetivo 9.000 $, pérdida 5.000 $ arrastrada, 2 cobros/mes de hasta 2.250 $ al 90 %)
empezando con 3 evaluaciones y reinvirtiendo hasta 10 cuentas, hasta cobrar 25.000 $ (tope por persona). Fase 2 (EN PARALELO, en cuanto ETF tiene 10 cuentas): Apex 150K con el 70 % de
lo cobrado (30 % impuestos) y reinvirtiendo (200 $ por evaluación, hasta 20 fondeadas). Mismo camino de rentabilidades.
¿Cuándo llegan los cobros a 10.000 $/mes (media de 3 meses)? Uso: python3 etf_luego_apex_10k.py DIR_SCRATCH"""
import sys, numpy as np, pandas as pd
exec(open('apex_rotacion.py').read().split('rng = np.random')[0])
rng = np.random.default_rng(43); T = 252 * 4; PRECIO = 200
FR = 0.7
def corre(x):
    st = rng.integers(0, len(x) - B, T // B + 1); R = x[(st[:, None] + np.arange(B)).ravel()[:T]] * CAP
    mes = np.zeros(T // 21 + 2); etf_tot = 0.0; bolsa = -2 * 34.70; fase = 1; t_tope = None
    E = [dict(f='e', eq=0.0, hwm=0.0, tc=0) for _ in range(2)]; A = []
    for t in range(T):
        r = R[t]
        if fase == 1:
            for a in E:
                a['eq'] += r; a['hwm'] = min(max(a['hwm'], a['eq']), DD)
                if a['f'] == 'e':
                    if t - a['tc'] >= 21: bolsa -= 34.70; a['tc'] = t
                    if a['eq'] <= a['hwm'] - DD: a.update(eq=0.0, hwm=0.0); bolsa -= 47
                    elif a['eq'] >= OBJ: a.update(f='f', eq=0.0, hwm=0.0, ini=t); bolsa -= 247
                else:
                    if a['eq'] <= a['hwm'] - DD: a.update(f='e', eq=0.0, hwm=0.0, tc=t); bolsa -= 34.70; continue
                    if (t - a['ini']) % 10 == 0 and a['eq'] > DD:
                        q = min(a['eq'] - DD, 2250, 25000 - etf_tot); a['eq'] -= q; q *= 0.9
                        etf_tot += q / 0.9; mes[t // 21] += q; bolsa += FR * q
            if etf_tot >= 25000 - 1 and t_tope is None: t_tope = t
            if etf_tot >= 25000 - 1: fase = 2
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
                        a['bal'] -= q; a['k'] += 1; a.update(dias=0, mx=0.0, ini=a['bal']); mes[t // 21] += q; bolsa += FR * q
                        if a['k'] == 6: a['f'] = 'x'
        A = [a for a in A if a['f'] != 'x']; nf = sum(a['f'] == 'f' for a in A)
        while bolsa >= PRECIO and nf + sum(a['f'] == 'e' for a in A) < 24 and nf < 20: A.append(dict(f='e', eq=0.0, hwm=0.0)); bolsa -= PRECIO
        if not A and bolsa < PRECIO: A.append(dict(f='e', eq=0.0, hwm=0.0)); bolsa -= PRECIO
    mm = pd.Series(mes[:T // 21]).rolling(3).mean().values
    hit = np.argmax(mm >= 10000) if np.any(mm >= 10000) else None
    hit14 = np.argmax(mm >= 14300) if np.any(mm >= 14300) else None
    return hit, hit14, t_tope, mes
for FR in (1.0, 0.7):
  print(f'\n=== reinvirtiendo el {FR*100:.0f} % de cada cobro ===')
  for hair, et in ((1.0, 'BACKTEST'), (0.6, 'REAL AL 60 %')):
      x = SER - SER.mean() * (1 - hair); res = [corre(x) for _ in range(1000)]
      f = lambda i: np.array([r[i] if r[i] is not None else np.nan for r in res])
      h, h14, tt = f(0), f(1), f(2) / 21
      M = np.array([r[3][:48] for r in res])
      print(f'{et}: tope de ETF (25.000 $) en el mes {np.nanmedian(tt):.0f} (mediana; lo alcanza {np.mean(~np.isnan(tt))*100:.0f} %)')
      print(f'   10.000 $/mes COBRADOS: mes mediano {np.nanmedian(h)+1:.0f} (25 % rápido {np.nanpercentile(h,25)+1:.0f}, 25 % lento {np.nanpercentile(h,75)+1:.0f}; llega en 4 años {np.mean(~np.isnan(h))*100:.0f} %)')
      print(f'   ~10.000 $/mes LIMPIOS (14.300 cobrados): mes mediano {np.nanmedian(h14)+1 if np.any(~np.isnan(h14)) else float("nan"):.0f} (llega en 4 años {np.mean(~np.isnan(h14))*100:.0f} %)')
      print('   cobro medio por año:', [f'{M[:, i*12:(i+1)*12].sum(axis=1).mean():,.0f} $' for i in range(4)])
