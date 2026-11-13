"""Apex 150K EOD: riesgo óptimo en la cuenta fondeada (PA), contando el coste de reponer cada cuenta (examen a riesgo 3: 3,3 exámenes por
aprobado en prudente, 2,2 en backtest, a 219 $; activación 159 $). Reglas de la PA confirmadas por Apex (límite diario por niveles 2.500-4.000
$, aproximado recortando el día; 5 días ≥ 350 $; consistencia 50 % neta; colchón 154.100; escalera 2.500-5.000; 6 cobros). Con y sin la
regla «margen < 2.000 $ → mitad de riesgo». Cartera manual sin rupturas (con C113). Uso: python3 apex_riesgo_fondeada.py DIR_SCRATCH"""
import sys, numpy as np
src = open('apex_150k_eod_real.py').read(); exec(src[:src.index('for nom, cols in')])
P = C[base + ['c113']].sum(axis=1); pv = P.rolling(60, min_periods=40).std().shift(1); SA = (P * (P.std() / pv).clip(0.5, 2)).dropna().loc['2018-11-05':].values
NIVDLL = [(0, 2500), (2000, 2500), (3000, 2500), (5000, 3000), (10000, 4000)]
def pa(R, M):
    bal = hwm = 0.0; d = 0; mx = 0.0; b0 = 0.0; q = []
    for t, r0 in enumerate(R):
        piso = 100 if hwm >= 4100 else hwm - 4000
        dll = max(v for u, v in NIVDLL if bal >= u) if bal >= 0 else 2500
        r = max(r0 * (0.5 if M and bal - piso < M else 1.0), -dll)
        bal += r; hwm = max(hwm, bal); piso = 100 if hwm >= 4100 else hwm - 4000
        if bal <= piso: return q, t + 1
        if r >= 350: d += 1
        mx = max(mx, r); ben = bal - b0
        if bal >= 4600 and d >= 5 and ben > 0 and mx < 0.5 * ben:
            a = min(ESC[len(q)], bal - 4100)
            if a >= 500:
                bal -= a; q.append(a); d = 0; mx = 0.0; b0 = bal
                if len(q) == 6: return q, t + 1
    return q, len(R)
for hair, et, nex in ((0.6, 'PRUDENTE', 3.3), (1.0, 'BACKTEST', 2.2)):
    repo = nex * 219 + 159
    for r in (0.35, 0.5, 0.65, 0.8, 1.0):
        x = (SA - SA.mean() * (1 - hair)) * r / 0.5          # camino() ya multiplica por CAP
        for M in (0, 2000):
            F = [pa(camino(x, 2000), M) for _ in range(3000)]
            tot = np.array([sum(q) for q, _ in F]); vida = np.array([v for _, v in F]) / 21; n6 = np.mean([len(q) == 6 for q, _ in F])
            neto = (tot.mean() - repo) / vida.mean()
            print(f'{et:8s} riesgo fondeada {r:.2f} {"+ mitad cerca del límite" if M else "                        "} | 6 cobros {n6*100:3.0f} % | se pierde {100-n6*100:3.0f} % | cobrado {tot.mean():6,.0f} $ | '
                  f'vida {vida.mean():4.1f} m | NETO por plaza y mes {neto:5,.0f} $ → 20 plazas {20*neto:7,.0f} $/mes | reposiciones al año (20 plazas) {20/vida.mean()*12:4.1f}', flush=True)
