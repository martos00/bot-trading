"""2 cuentas de ETF → lo primero que se compra con lo cobrado es Upcomers Odyssey 1,5M (≈2.150 $, 2 fases 6 % + 6 %, diaria 4 %,
pérdida 6 % arrastrada que se fija en el saldo inicial, 1 reset gratis, fondeada: cobro cada 14 días si hay ≥ 3 % en el ciclo, 80 %,
topes 5k/7,5k/10k/15k/20k/25k/30k y luego sin tope, colchón 3 %). Variante «extras»: con el 1.er y 2.º cobro de Upcomers se
desbloquean 2 desafíos más de 1,5M (si la firma lo permite). Después, todo a Apex 150K (200 $/evaluación, hasta 20).
Se reinvierte el 70 % (30 % impuestos). Misma cartera y operaciones en todo, riesgo 0,65 %. Uso: python3 etf_upcomers_apex_10k.py DIR"""
import sys, numpy as np, pandas as pd
exec(open('apex_rotacion.py').read().split('rng = np.random')[0])
rng = np.random.default_rng(61); T = 252 * 4; PRECIO_APEX = 200; PRECIO_UP = 2150; UPCAP = 1_500_000
TOP_UP = [5000, 7500, 10000, 15000, 20000, 25000, 30000]
class Up:
    def __init__(s, reset=True): s.fase = 1; s.eq = 0.0; s.hwm = 0.0; s.reset = reset; s.k = 0; s.ben0 = 0.0; s.ini = 0; s.viva = True; s.ncob = 0
    def dia(s, rf, t):
        if not s.viva: return 0.0
        s.eq += rf; s.hwm = max(s.hwm, s.eq)
        lim = 0.04
        if s.fase < 3:
            if rf <= -lim or s.eq <= min(s.hwm, 0.06) - 0.06:
                if s.reset: s.reset = False; s.fase = 1; s.eq = 0.0; s.hwm = 0.0
                else: s.viva = False
                return 0.0
            if s.eq >= 0.06:
                s.fase += 1; s.eq = 0.0; s.hwm = 0.0
                if s.fase == 3: s.ini = t; s.ben0 = 0.0
            return 0.0
        if rf <= -lim or s.eq <= min(s.hwm - 0.06, 0.0): s.viva = False; return 0.0
        if (t - s.ini) % 10 == 0 and s.eq - s.ben0 >= 0.03 and s.eq > 0.03:
            q = (s.eq - 0.03) * UPCAP
            if s.k < len(TOP_UP): q = min(q, TOP_UP[s.k])
            s.eq -= q / UPCAP; s.ben0 = s.eq; s.k += 1; s.ncob += 1
            return 0.8 * q - 19.9 - 0.0249 * 0.8 * q
        return 0.0
def corre(x, extras):
    st = rng.integers(0, len(x) - B, T // B + 1); Rf = x[(st[:, None] + np.arange(B)).ravel()[:T]]; R = Rf * CAP
    mes = np.zeros(T // 21 + 2); bolsa = -2 * 34.70; etf_tot = 0.0
    E = [dict(f='e', eq=0.0, hwm=0.0, tc=0) for _ in range(2)]; U = []; A = []; extras_dadas = 0; up_comprada = False
    for t in range(T):
        r = R[t]; rf = Rf[t]; m = t // 21
        if etf_tot < 25000:
            for a in E:
                a['eq'] += r; a['hwm'] = min(max(a['hwm'], a['eq']), DD)
                if a['f'] == 'e':
                    if t - a['tc'] >= 21: bolsa -= 34.70; a['tc'] = t
                    if a['eq'] <= a['hwm'] - DD: a.update(eq=0.0, hwm=0.0); bolsa -= 47
                    elif a['eq'] >= OBJ: a.update(f='f', eq=0.0, hwm=0.0, ini=t); bolsa -= 247
                else:
                    if a['eq'] <= a['hwm'] - DD: a.update(f='e', eq=0.0, hwm=0.0, tc=t); bolsa -= 34.70; continue
                    if (t - a['ini']) % 10 == 0 and a['eq'] > DD:
                        q = min(a['eq'] - DD, 2250, 25000 - etf_tot); a['eq'] -= q; etf_tot += q; mes[m] += 0.9 * q; bolsa += 0.7 * 0.9 * q
        for u in U:
            c = u.dia(rf, t)
            if c: mes[m] += c; bolsa += 0.7 * c
        if extras and U:
            while extras_dadas < 2 and U[0].ncob > extras_dadas: U.append(Up(reset=False)); extras_dadas += 1
        if U and not any(u.viva for u in U) and bolsa >= PRECIO_UP: U = [Up()]; bolsa -= PRECIO_UP; extras_dadas = 2
        if not up_comprada and bolsa >= PRECIO_UP: U.append(Up()); bolsa -= PRECIO_UP; up_comprada = True
        if up_comprada:
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
                            a['bal'] -= q; a['k'] += 1; a.update(dias=0, mx=0.0, ini=a['bal']); mes[m] += q; bolsa += 0.7 * q
                            if a['k'] == 6: a['f'] = 'x'
            A = [a for a in A if a['f'] != 'x']; nf = sum(a['f'] == 'f' for a in A)
            while bolsa >= PRECIO_APEX and len(A) < 24 and nf < 20: A.append(dict(f='e', eq=0.0, hwm=0.0)); bolsa -= PRECIO_APEX
    mm = pd.Series(mes[:T // 21]).rolling(3).mean().values
    h1 = np.argmax(mm >= 10000) if np.any(mm >= 10000) else np.nan
    h2 = np.argmax(mm >= 14300) if np.any(mm >= 14300) else np.nan
    return h1, h2, mes
for extras in (False, True):
    for hair, et in ((0.6, 'REAL AL 60 %'), (1.0, 'BACKTEST')):
        x = SER - SER.mean() * (1 - hair); res = [corre(x, extras) for _ in range(800)]
        h1 = np.array([q[0] for q in res]); h2 = np.array([q[1] for q in res]); M = np.array([q[2][:48] for q in res])
        print(f'{"con las 2 extra" if extras else "sin las extra  "} | {et:12s} | 10.000 $ cobrados: mes {np.nanmedian(h1)+1:.0f} (rápido {np.nanpercentile(h1,25)+1:.0f}, lento {np.nanpercentile(h1,75)+1:.0f}; llega en 4 años {np.mean(~np.isnan(h1))*100:.0f} %) '
              f'| 10.000 $ limpios: mes {np.nanmedian(h2)+1:.0f} ({np.mean(~np.isnan(h2))*100:.0f} %) | cobrado por año: ' + ', '.join(f'{M[:, i*12:(i+1)*12].sum(axis=1).mean():,.0f}' for i in range(4)))
