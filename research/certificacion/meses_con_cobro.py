"""% de meses con algún cobro (≥ 500 $) combinando firmas, ya en marcha (todas fondeadas desde el día 0 y repuestas al momento; Tradeify
repite examen si suspende). Apex 20×150K EOD (cuentas escalonadas: una nueva cada 3 días al principio), TPT 5×150K PRO (sin examen: ya PRO),
Tradeify 5×50K Flex (bot), Upcomers 2M (EA). 24 meses tras 6 de arranque. Uso: python3 meses_con_cobro.py DIR_SCRATCH"""
import sys, numpy as np, pandas as pd
src = open('camino_millon_todo.py').read()
exec(src[src.index("src = open('planes_10k.py')"):src.index("CAP = 150000")].replace("src = open('planes_10k.py').read(); ", "SPD = sys.argv[1]; src = open('planes_10k.py').read(); "))
CAP = 150000; T0 = 6 * 21; T = 30 * 21; rng = np.random.default_rng(4)
class TptPro:
    def __init__(s): s.bal = s.hb = 0.0
    def dia(s, r, t):
        s.bal += r; s.hb = max(s.hb, s.bal); piso = 100 if s.hb >= 4600 else s.hb - 4500
        if s.bal <= piso: s.__init__(); return 0.0
        if t % 5 == 0 and s.bal > 6500: q = s.bal - 6500; s.bal -= q; return 0.8 * q
        return 0.0
for hair, et in ((0.6, 'PRUDENTE'), (1.0, 'BACKTEST')):
    X = {k: (J[k] - J[k].mean() * (1 - hair)).values for k in ('U', 'T', 'AP', 'TP')}
    R = {k: [] for k in ('Apex ×20', 'TPT ×5', 'Tradeify ×5', 'Upcomers 2M', 'Apex + TPT', 'Apex + TPT + Tradeify', 'TODAS')}
    for _ in range(300):
        st = rng.integers(0, len(J) - 20, T // 20 + 1); idx = (st[:, None] + np.arange(20)).ravel()[:T]
        ap = []; tp = [TptPro() for _ in range(5)]; tf = [Fut(50_000, 109, 3000, 2000, 150, 2500, 1.0, 0.8) for _ in range(5)]; up = Upc(2_000_000, 2900, 1.0, 0.8)
        m = {k: np.zeros(T) for k in ('a', 'p', 'f', 'u')}
        for t in range(T):
            i = idx[t]
            if len(ap) < 20 and t % 3 == 0: ap.append(Apx())
            for j, c in enumerate(ap):
                r = c.dia(X['AP'][i] * CAP)
                if r is None: ap[j] = Apx(); continue
                m['a'][t] += r[1]
                if r[0] == 'fin': ap[j] = Apx()
            for c in tp: m['p'][t] += c.dia(X['TP'][i] * CAP, t)
            for c in tf: q, g = c.dia(X['T'][i], t); m['f'][t] += q
            q, g = up.dia(X['U'][i], t); m['u'][t] += q
        M = {k: np.add.reduceat(v[T0:], np.arange(0, T - T0, 21)) for k, v in m.items()}
        for nom, keys in (('Apex ×20', 'a'), ('TPT ×5', 'p'), ('Tradeify ×5', 'f'), ('Upcomers 2M', 'u'), ('Apex + TPT', 'ap'), ('Apex + TPT + Tradeify', 'apf'), ('TODAS', 'apfu')):
            R[nom].append(sum(M[k] for k in keys) >= 500)
    print(f'\n{et}: % de meses con algún cobro (≥ 500 $)')
    for nom, v in R.items():
        v = np.array(v); racha = np.mean([max((len(s) for s in ''.join('1' if x else '0' for x in fila).split('1')), default=0) for fila in v])
        print(f'   {nom:24s}: {v.mean()*100:3.0f} % de los meses | racha media más larga sin cobrar: {racha:.1f} meses')
