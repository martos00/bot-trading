"""Solo Apex 150K EOD ×20 (a mano, sin rupturas): ¿cómo cobrar el máximo de meses? Variantes: (a) todas a riesgo 0,5; (b) riesgos mezclados
(0,35/0,5/0,65/0,8 por cuartos); (c) cola de cobros: como mucho K cobros al mes (las cuentas que cumplen esperan al mes siguiente; si
mientras tanto dejan de cumplir, esperan otra vez). Cuentas que se pierden o completan 6 cobros: repuestas al momento. Cuentas nuevas
escalonadas (una cada 3 días al empezar). 24 meses tras 6 de arranque. Uso: python3 apex_cobros_cada_mes.py DIR_SCRATCH"""
import sys, numpy as np, pandas as pd
src = open('camino_millon_todo.py').read()
exec(src[src.index("src = open('planes_10k.py')"):src.index("class Tpt:")].replace("src = open('planes_10k.py').read(); ", "SPD = sys.argv[1]; src = open('planes_10k.py').read(); "))
CAP = 150000; T0 = 6 * 21; T = 30 * 21; rng = np.random.default_rng(9)
class ApxQ(Apx):
    def __init__(s, rk): super().__init__(); s.rk = rk
    def listo(s):
        return s.bal >= 4600 and s.d >= 5 and (s.bal - s.b0) > 0 and s.mx < 0.5 * (s.bal - s.b0) and min(ESC[s.k], s.bal - 4100) >= 500
    def paso(s, r0):           # día sin pedir cobro
        piso = 100 if s.hwm >= 4100 else s.hwm - 4000; dll = max([2500] + [v for u, v in NIV if s.bal >= u])
        r = max(r0 * s.rk / 0.5 * (0.5 if s.bal - piso < 2000 else 1.0), -dll); s.bal += r; s.hwm = max(s.hwm, s.bal)
        piso = 100 if s.hwm >= 4100 else s.hwm - 4000
        if s.bal <= piso: return False
        if r >= 350: s.d += 1
        s.mx = max(s.mx, r); return True
    def cobra(s):
        a = min(ESC[s.k], s.bal - 4100); s.bal -= a; s.k += 1; s.d = 0; s.mx = 0.0; s.b0 = s.bal; return a
for hair, et in ((0.6, 'PRUDENTE'), (1.0, 'BACKTEST')):
    x = ((J.AP - J.AP.mean() * (1 - hair)) * CAP).values
    for nom, riesgos, K in (('todas a 0,5, cobrar siempre', [0.5], 99), ('riesgos mezclados 0,35-0,8', [0.35, 0.5, 0.65, 0.8], 99),
                            ('0,5 + cola: máx. 5 cobros/mes', [0.5], 5), ('0,5 + cola: máx. 3 cobros/mes', [0.5], 3), ('0,5 + cola: máx. 2 cobros/mes', [0.5], 2),
                            ('mezclados + cola máx. 3/mes', [0.35, 0.5, 0.65, 0.8], 3)):
        meses_con = []; total = []; rachas = []
        for _ in range(300):
            st = rng.integers(0, len(J) - 20, T // 20 + 1); idx = (st[:, None] + np.arange(20)).ravel()[:T]
            cs = []; m = np.zeros(T); n_mes = 0
            for t in range(T):
                if t % 21 == 0: n_mes = 0
                if len(cs) < 20 and t % 3 == 0: cs.append(ApxQ(riesgos[len(cs) % len(riesgos)]))
                for j, c in enumerate(cs):
                    if not c.paso(x[idx[t]]): cs[j] = ApxQ(c.rk); continue
                    if c.listo() and n_mes < K:
                        m[t] += c.cobra(); n_mes += 1
                        if c.k == 6: cs[j] = ApxQ(c.rk)
            M = np.add.reduceat(m[T0:], np.arange(0, T - T0, 21)); con = M >= 500
            meses_con.append(con.mean()); total.append(M.mean())
            rachas.append(max((len(s) for s in ''.join('1' if v else '0' for v in con).split('1')), default=0))
        print(f'{et:8s} {nom:34s} | meses con cobro {np.mean(meses_con)*100:3.0f} % | racha más larga sin cobrar (media) {np.mean(rachas):4.1f} meses | cobrado medio {np.mean(total):7,.0f} $/mes', flush=True)
