"""¿Cuándo llega la cuenta propia a 1 millón? Cuenta propia: 60.000 $ iniciales, bot de futuros completo (serie O), sin retiradas.
Aportaciones: 50 % de lo cobrado NETO en Apex (cobros − exámenes − activaciones). Apex 150K EOD a mano (sin rupturas, con C113): 2 exámenes
al mes (días 0 y 10) a 219 $ hasta tener 20 entre fondeadas y exámenes; examen 21 hábiles con probabilidad de aprobar 31 % (prudente) / 45 %
(backtest) (apex_riesgo3_escalonados.txt); activación 159 $; fondeada a riesgo 0,5 con «margen < 2.000 $ → mitad», reglas confirmadas
(límite diario aproximado al cierre). Las dos cuentas viven los mismos días (bloques de 20 días). 8 años. Uso: python3 camino_millon_propia.py DIR"""
import sys, numpy as np, pandas as pd
src = open('apex_150k_eod_real.py').read(); exec(src[:src.index('for nom, cols in')])
P = C[base + ['c113']].sum(axis=1); pv = P.rolling(60, min_periods=40).std().shift(1); A = (P * (P.std() / pv).clip(0.5, 2)).dropna()
O = pd.read_csv(f'{SP}/series_planes_10k.csv', index_col=0, parse_dates=True)['O']
J = pd.concat([A.rename('A'), O.rename('O')], axis=1).dropna().loc['2018-11-05':]
NIV = [(0, 2500), (2000, 2500), (3000, 2500), (5000, 3000), (10000, 4000)]
class PA:
    def __init__(s): s.bal = s.hwm = 0.0; s.d = 0; s.mx = 0.0; s.b0 = 0.0; s.k = 0
    def dia(s, r0):
        piso = 100 if s.hwm >= 4100 else s.hwm - 4000
        dll = max([2500] + [v for u, v in NIV if s.bal >= u])
        r = max(r0 * (0.5 if s.bal - piso < 2000 else 1.0), -dll)
        s.bal += r; s.hwm = max(s.hwm, s.bal); piso = 100 if s.hwm >= 4100 else s.hwm - 4000
        if s.bal <= piso: return None
        if r >= 350: s.d += 1
        s.mx = max(s.mx, r); ben = s.bal - s.b0
        if s.bal >= 4600 and s.d >= 5 and ben > 0 and s.mx < 0.5 * ben:
            a = min(ESC[s.k], s.bal - 4100)
            if a >= 500:
                s.bal -= a; s.k += 1; s.d = 0; s.mx = 0.0; s.b0 = s.bal
                return ('fin' if s.k == 6 else 'ok', a)
        return ('', 0)
T = 8 * 252; rng = np.random.default_rng(2026)
for hair, et, pex in ((0.6, 'PRUDENTE', 0.31), (1.0, 'BACKTEST', 0.45)):
    xa = ((J.A - J.A.mean() * (1 - hair)) * CAP).values; xo = (J.O - J.O.mean() * (1 - hair)).values
    for rp in (0.65, 0.8, 1.0):
        L = []; F3 = []; F5 = []; AP = []
        for _ in range(1000):
            st = rng.integers(0, len(J) - 20, T // 20 + 1); idx = (st[:, None] + np.arange(20)).ravel()[:T]
            pas = []; exs = []; prop = 60000.0; llega = None; apex_neto_m = 0.0; ap = []
            for t in range(T):
                mes_dia = t % 21
                if mes_dia in (0, 10) and len(pas) + len(exs) < 20: exs.append(t + 21); apex_neto_m -= 219
                nuevos = [e for e in exs if e == t]; exs = [e for e in exs if e != t]
                for _e in nuevos:
                    if rng.random() < pex: pas.append(PA()); apex_neto_m -= 159
                vivos = []
                for c in pas:
                    r = c.dia(xa[idx[t]] * 1.0)
                    if r is None: continue
                    apex_neto_m += r[1]
                    if r[0] != 'fin': vivos.append(c)
                pas = vivos
                prop *= 1 + xo[idx[t]] * rp / 0.5
                if mes_dia == 20:
                    if apex_neto_m > 0: prop += 0.5 * apex_neto_m
                    ap.append(apex_neto_m); apex_neto_m = 0.0
                if llega is None and prop >= 1_000_000: llega = t / 252
                if t == 3 * 252: F3.append(prop)
                if t == 5 * 252: F5.append(prop)
            L.append(llega if llega is not None else np.nan); AP.append(np.mean(ap[12:36]))
        L = np.array(L)
        print(f'{et:8s} cuenta propia a riesgo {rp} | llega a 1 M: en 3 años {np.mean(L<=3)*100:3.0f} %, 4 años {np.mean(L<=4)*100:3.0f} %, 5 años {np.mean(L<=5)*100:3.0f} %, 8 años {np.mean(L<=8)*100:3.0f} % | '
              f'tiempo mediano {np.nanmedian(L):.1f} años | cuenta propia a 3 años {np.median(F3):10,.0f} $, a 5 años {np.median(F5):10,.0f} $ | Apex neto medio (años 2-3) {np.mean(AP):7,.0f} $/mes', flush=True)
