"""Cuenta propia hasta 1 millón con TODAS las fuentes: Apex 150K EOD a mano (N exámenes/mes a riesgo 3, aprueba 31 %/45 %, fondeada 0,5 con
«mitad cerca del límite», hasta 20), Upcomers 2M con el EA (examen 1,0 / fondeada 0,8, reglas confirmadas, 2.900 $* y recompra), Tradeify 5×50K
con el bot (planes_10k.Fut, examen 1,0 / fondeada 0,8, reset 109 $), Take Profit Trader 5×150K PRO a mano (examen supuesto: objetivo 9.000 $,
4.500 $ EOD, consistencia 50 %, cuota 360 $ cada 21 días; PRO: retira cada semana lo que pasa de 154.500 + 2.000 $, 80 %). 50 % del neto
mensual positivo a la cuenta propia (60.000 $ iniciales, bot de futuros completo, sin retiradas). Mismos días para todo. 8 años.
Uso: python3 camino_millon_todo.py DIR_SCRATCH NEXAMENES"""
import sys, numpy as np, pandas as pd
SPD = sys.argv[1]; NEX = int(sys.argv[2])
src = open('planes_10k.py').read(); exec(src[src.index('import sys'):src.index('PLANES = {')].replace('D = pd.read_csv(sys.argv[1]', 'D = pd.read_csv(SPD + "/series_planes_10k.csv"'))
sys.argv = ['x', SPD]
exec(open('plan_reinversion_etf.py').read().split('CAP, OBJ')[0])
CA = pd.read_csv(f'{SPD}/componentes_A.csv', index_col=0, parse_dates=True).loc['2018-03-26':]
def ser(P): pv = P.rolling(60, min_periods=40).std().shift(1); return (P * (P.std() / pv).clip(0.5, 2)).dropna()
AP = ser(C[['yen', 'cesta_yen', 'oro_vie_1655', 'oro_D-2', 'plata_visp_1655', 'plata_viernes', 'nikkei_Q+2', 'nikkei_Q-2', 'c113']].sum(axis=1))
TP = ser(CA[['yen', 'cesta_yen', 'oro_vie_1645', 'oro_D-2', 'plata_visp_1645', 'nikkei_Q+2', 'nikkei_Q-2']].sum(axis=1) + C['c113'].reindex(CA.index).fillna(0))
J = pd.concat([D, AP.rename('AP'), TP.rename('TP')], axis=1).dropna().loc['2018-11-05':]
ESC = [2500, 3000, 3000, 3000, 4000, 5000]; NIV = [(0, 2500), (2000, 2500), (3000, 2500), (5000, 3000), (10000, 4000)]
class Apx:
    def __init__(s): s.bal = s.hwm = 0.0; s.d = 0; s.mx = 0.0; s.b0 = 0.0; s.k = 0
    def dia(s, r0):
        piso = 100 if s.hwm >= 4100 else s.hwm - 4000; dll = max([2500] + [v for u, v in NIV if s.bal >= u])
        r = max(r0 * (0.5 if s.bal - piso < 2000 else 1.0), -dll); s.bal += r; s.hwm = max(s.hwm, s.bal); piso = 100 if s.hwm >= 4100 else s.hwm - 4000
        if s.bal <= piso: return None
        if r >= 350: s.d += 1
        s.mx = max(s.mx, r); ben = s.bal - s.b0
        if s.bal >= 4600 and s.d >= 5 and ben > 0 and s.mx < 0.5 * ben:
            a = min(ESC[s.k], s.bal - 4100)
            if a >= 500:
                s.bal -= a; s.k += 1; s.d = 0; s.mx = 0.0; s.b0 = s.bal; return ('fin' if s.k == 6 else 'ok', a)
        return ('', 0)
class Tpt:
    def __init__(s): s.f = 0; s.eq = s.hwm = s.mx = 0.0; s.dt = 0
    def dia(s, r, t):
        g = 0.0; c = 0.0
        if s.f == 0:
            s.dt += 1
            if s.dt % 21 == 1: g += 360
            r1 = r * 2; s.eq += r1; s.hwm = min(max(s.hwm, s.eq), 4600); s.mx = max(s.mx, r1)
            if s.eq <= s.hwm - 4500: s.eq = s.hwm = s.mx = 0.0
            elif s.eq >= 9000 and s.mx <= 0.5 * s.eq: s.f = 1; s.bal = s.hb = 0.0; g += 130
            return c, g
        s.bal += r; s.hb = max(s.hb, s.bal); piso = 100 if s.hb >= 4600 else s.hb - 4500
        if s.bal <= piso: s.__init__(); return c, g
        if t % 5 == 0 and s.bal > 6500: q = s.bal - 6500; s.bal -= q; c = 0.8 * q
        return c, g
CAP = 150000
T = 8 * 252; rng = np.random.default_rng(77)
for hair, et, pex in ((0.6, 'PRUDENTE', 0.31), (1.0, 'BACKTEST', 0.45)):
    X = {k: (J[k] - J[k].mean() * (1 - hair)).values for k in ('U', 'T', 'O', 'AP', 'TP')}
    for rp in (0.8, 1.0):
        L = []; F3 = []; F5 = []; NM = []; MINC = []
        for _ in range(200):
            st = rng.integers(0, len(J) - 20, T // 20 + 1); idx = (st[:, None] + np.arange(20)).ravel()[:T]
            apx = []; exs = []; up = Upc(2_000_000, 2900, 1.0, 0.8); tf = [Fut(50_000, 109, 3000, 2000, 150, 2500, 1.0, 0.8) for _ in range(5)]; tp = [Tpt() for _ in range(5)]
            prop = 60000.0; mes = -2900 - 5 * 116; acum = mes; minc = acum; llega = None; nm = []
            for t in range(T):
                i = idx[t]; md = t % 21
                if md in [int(21 * j / NEX) for j in range(NEX)] and len(apx) + len(exs) < 20: exs.append(t + 21); mes -= 219
                for _e in [e for e in exs if e == t]:
                    if rng.random() < pex: apx.append(Apx()); mes -= 159
                exs = [e for e in exs if e != t]; viv = []
                for c in apx:
                    r = c.dia(X['AP'][i] * CAP)
                    if r is None: continue
                    mes += r[1]
                    if r[0] != 'fin': viv.append(c)
                apx = viv
                q, g = up.dia(X['U'][i], t); mes += q - g
                for c in tf: q, g = c.dia(X['T'][i], t); mes += q - g
                for c in tp: q, g = c.dia(X['TP'][i] * CAP, t); mes += q - g
                prop *= 1 + X['O'][i] * rp / 0.5
                if md == 20:
                    acum += mes; minc = min(minc, acum)
                    if mes > 0: prop += 0.5 * mes
                    nm.append(mes); mes = 0.0
                if llega is None and prop >= 1_000_000: llega = t / 252
                if t == 3 * 252: F3.append(prop)
                if t == 5 * 252: F5.append(prop)
            L.append(llega if llega is not None else np.nan); NM.append(np.mean(nm[12:36])); MINC.append(minc)
        L = np.array(L)
        print(f'{et:8s} Apex {NEX} exámenes/mes | propia riesgo {rp} | 1 M en 3 años {np.mean(L<=3)*100:3.0f} %, 4 {np.mean(L<=4)*100:3.0f} %, 5 {np.mean(L<=5)*100:3.0f} %, 6 {np.mean(L<=6)*100:3.0f} % | '
              f'mediana {np.nanmedian(L):.1f} años | propia a 3 años {np.median(F3):10,.0f} $, a 5 {np.median(F5):10,.0f} $ | prop firms neto medio años 2-3 {np.mean(NM):7,.0f} $/mes | '
              f'dinero a adelantar (mediana) {-np.median(MINC):7,.0f} $', flush=True)
