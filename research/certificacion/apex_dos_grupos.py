"""Plan del usuario: grupo A = 10 cuentas Apex 150K EOD fondeadas desde el día 0; grupo B = 10 más fondeadas 1,5 meses después (31 hábiles).
Riesgo 0,5 con «mitad cerca del límite»; reglas confirmadas. Si una cuenta se pierde o completa 6 cobros, se repone al momento (misma posición
en su grupo). ¿En qué meses cobra cada grupo? Comparación: 20 cuentas empezadas el mismo día. 24 meses, mismos días para todas.
Uso: python3 apex_dos_grupos.py DIR_SCRATCH"""
import sys, numpy as np, pandas as pd
src = open('camino_millon_todo.py').read()
exec(src[src.index("src = open('planes_10k.py')"):src.index("class Tpt:")].replace("src = open('planes_10k.py').read(); ", "SPD = sys.argv[1]; src = open('planes_10k.py').read(); "))
CAP = 150000; T = 24 * 21; rng = np.random.default_rng(15)
for hair, et in ((0.6, 'PRUDENTE'), (1.0, 'BACKTEST')):
    x = ((J.AP - J.AP.mean() * (1 - hair)) * CAP).values
    res = {'A': [], 'B': [], 'A+B': [], '20 a la vez': []}; ejemplo = None
    for k in range(500):
        st = rng.integers(0, len(J) - 20, T // 20 + 1); idx = (st[:, None] + np.arange(20)).ravel()[:T]
        mA = np.zeros(T); mB = np.zeros(T); mC = np.zeros(T)
        gA = [Apx() for _ in range(10)]; gB = [None] * 10; gC = [Apx() for _ in range(20)]
        for t in range(T):
            if t == 31: gB = [Apx() for _ in range(10)]
            for grp, m in ((gA, mA), (gB, mB), (gC, mC)):
                for j, c in enumerate(grp):
                    if c is None: continue
                    r = c.dia(x[idx[t]])
                    if r is None: grp[j] = Apx(); continue
                    m[t] += r[1]
                    if r[0] == 'fin': grp[j] = Apx()
        mes = lambda m: np.add.reduceat(m, np.arange(0, T, 21))
        a, b, c = mes(mA), mes(mB), mes(mC)
        res['A'].append(a > 0); res['B'].append(b > 0); res['A+B'].append((a + b) > 0); res['20 a la vez'].append(c > 0)
        if k == 0: ejemplo = (a, b)
    print(f'\n{et}: % de meses con algún cobro (24 meses) → ' + ' | '.join(f'{n}: {np.mean(v)*100:.0f} %' for n, v in res.items()))
    ab = np.array(res['A+B']); sync = np.mean([np.mean(np.array(res['A'][i]) & np.array(res['B'][i])) / max(np.mean(np.array(res['A'][i]) | np.array(res['B'][i])), 1e-9) for i in range(500)])
    print(f'   de los meses en que cobra algún grupo, cobran LOS DOS a la vez: {sync*100:.0f} %')
    a, b = ejemplo
    print('   Ejemplo de una trayectoria (miles de $ cobrados por mes):')
    print('   mes:     ' + ' '.join(f'{i+1:3d}' for i in range(24)))
    print('   grupo A: ' + ' '.join(f'{v/1000:3.0f}' for v in a))
    print('   grupo B: ' + ' '.join(f'{v/1000:3.0f}' for v in b))
