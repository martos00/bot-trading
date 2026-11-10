"""Apex 150K (reglas 2026 según proea.app/propdatalab, sin verificar en Apex): evaluación (objetivo 9.000 $, pérdida máx. 5.000 $ arrastrada
al cierre) → cuenta fondeada: cobro si saldo ≥ 154.600 $, ≥ 5 días con ≥ 350 $ desde el último cobro y ningún día ≥ 50 % del beneficio
desde el último cobro; escalera 2.500/3.000/3.000/3.000/4.000/5.000 $; se cierra tras 6 cobros. Cartera actual (con C113), riesgo 0,65 %.
Uso: python3 apex_rotacion.py DIR_SCRATCH"""
import sys, numpy as np, pandas as pd
exec(open('plan_reinversion_etf.py').read().split('CAP, OBJ')[0])   # SER = serie diaria de la cartera a 0,65 %
CAP = 150000; OBJ = 9000; DD = 5000; RED = 154100; MINC = 154600; ESC = [2500, 3000, 3000, 3000, 4000, 5000]; B = 20
rng = np.random.default_rng(23)
def camino(x, T): st = rng.integers(0, len(x) - B, T // B + 1); return x[(st[:, None] + np.arange(B)).ravel()[:T]] * CAP
def evaluacion(R, t):
    eq = hwm = 0.0
    while t < len(R):
        eq += R[t]; t += 1; hwm = min(max(hwm, eq), DD)
        if eq <= hwm - DD: return False, t
        if eq >= OBJ: return True, t
    return None, t
def fondeada(R, t):
    bal = CAP; hwm = CAP; k = 0; dias = 0; mx = 0.0; ini_ben = bal; cobros = []
    while t < len(R):
        r = R[t]; bal += r; t += 1
        hwm = min(max(hwm, bal), RED + DD)          # arrastre que se fija en 154.100 + ... (aprox.: deja de subir al colchón)
        if bal <= min(hwm, RED) - DD + (0 if hwm < RED else DD) - DD * 0: pass
        piso = min(hwm - DD, RED - DD + 100) if hwm - DD < CAP + 100 else CAP + 100
        if bal <= piso: return cobros, t, 'perdida'
        if r >= 350: dias += 1
        mx = max(mx, r); ben = bal - ini_ben
        if bal >= MINC and dias >= 5 and ben > 0 and mx < 0.5 * ben:
            q = min(ESC[k], bal - RED)
            if q >= 500:
                bal -= q; cobros.append(q); k += 1; dias = 0; mx = 0.0; ini_ben = bal
                if k == 6: return cobros, t, 'cerrada_6_cobros'
    return cobros, t, 'sigue'
for hair, et in ((1.0, 'BACKTEST'), (0.6, 'REAL AL 60 %')):
    x = SER - SER.mean() * (1 - hair); E, F = [], []
    for _ in range(4000):
        R = camino(x, 1500); ok, t = evaluacion(R, 0); E.append((ok, t))
        if ok: F.append(fondeada(R, t))
    pa = np.mean([e[0] is True for e in E]); te = np.mean([e[1] for e in E]) / 21
    dur = np.array([(f[1]) for f in F]); fin = [f[2] for f in F]; ncob = np.array([len(f[0]) for f in F]); tot = np.array([sum(f[0]) for f in F])
    t_ini = np.array([e[1] for e in E if e[0] is True]); vida = (dur - t_ini) / 21
    print(f'\n######## {et}')
    print(f'Evaluación: aprueba {pa*100:.0f} % | dura de media {te:.1f} meses (aprobada o suspendida)')
    print(f'Fondeada: llega a los 6 cobros {np.mean([f=="cerrada_6_cobros" for f in fin])*100:.0f} % | se pierde antes {np.mean([f=="perdida" for f in fin])*100:.0f} % | '
          f'vida media {vida.mean():.1f} meses (mediana {np.median(vida):.1f}) | cobros medios {ncob.mean():.1f} | cobrado medio {tot.mean():,.0f} $ (100 % tuyo)')
    meses_por_cobro = vida.sum() / max(ncob.sum(), 1); print(f'  meses entre cobros (media) {meses_por_cobro:.1f}')
    ritmo = 18 / vida.mean(); compras = ritmo / pa
    print(f'Para mantener ~18 fondeadas: se cierran/pierden ~{ritmo:.1f} al mes → comprar ~{compras:.1f} evaluaciones al mes (≈ una cada {30/compras:.0f} días), '
          f'con ~{compras*te:.0f} evaluaciones en curso a la vez | cobro medio de la flota ~{18*tot.mean()/vida.mean():,.0f} $/mes')
