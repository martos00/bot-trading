"""Apex con las reglas CONFIRMADAS por soporte (13-nov-2026). Sin rupturas (M2: horas fijas + C113).
150K EOD: examen 219 $ (90 % dto.; lista 2.190), objetivo 9.000, EOD 4.000, límite diario 2.000 (pausa el día: se aproxima recortando la
pérdida), 30 días, sin reset; activación 159 $. PA: niveles 4/5/7/10/10 contratos (micros 10:1, límite conjunto), límite diario 2.500-4.000
(pausa), 5 días ≥ 350 $, consistencia 50 % sobre el beneficio NETO desde el último cobro, saldo ≥ 154.600, colchón 154.100, escalera
2.500/3.000/3.000/3.000/4.000/5.000, cierre tras el 6.º. Yen solo con 6J (MJY no): a riesgo r el yen necesita ~9·r/0.5 contratos 6J → se
recorta al límite (examen 12; PA según nivel); oro y plata caben. 20 PA por hogar. Copiador permitido.
HEREDADAS (legacy) 250K/300K: objetivo 15.000/20.000, pérdida 6.500/7.500; PA vitalicia, cobros ilimitados, máx. 3.000/3.500 $ por cobro,
mín. 500; consistencia 30 % (solo en la PA). SUPUESTOS*: examen sin plazo y pérdida EOD; en la PA pérdida arrastrada EOD que se fija en
+100; para cobrar 8 días de operación desde el último cobro; se deja un colchón de 2.500 $ sobre el inicial + 100; precio examen* 200 $.
Uso: python3 apex_confirmado.py DIR_SCRATCH"""
import sys, numpy as np, pandas as pd
exec(open('plan_reinversion_etf.py').read().split('CAP, OBJ')[0])
base = ['yen', 'cesta_yen', 'oro_vie_1655', 'oro_D-2', 'plata_visp_1655', 'plata_viernes', 'nikkei_Q+2', 'nikkei_Q-2', 'c113']
B = 20; rng = np.random.default_rng(7)
D = C.loc['2018-11-05':]
def serie(yfac):
    X = D[base].copy(); X['yen'] *= yfac; X['cesta_yen'] *= min(1.0, yfac * 3)   # E11 usa 1/3 del tamaño
    P = X.sum(axis=1); pv = P.rolling(60, min_periods=40).std().shift(1); return (P * (P.std() / pv).clip(0.5, 2)).dropna().values
def camino(x, T): st = rng.integers(0, len(x) - B, T // B + 1); return (st[:, None] + np.arange(B)).ravel()[:T]
NIV = [(0, 4, 2500), (2000, 5, 2500), (3000, 7, 2500), (5000, 10, 3000), (10000, 10, 4000)]
def pa150(Rs, idx):     # Rs: dict nivel->serie (dólares) con el yen recortado según contratos del nivel
    bal = hwm = 0.0; d = 0; mx = 0.0; b0 = 0.0; q = []; t = 0
    for k, i in enumerate(idx):
        lv = max([0] + [j for j, (u, _, _) in enumerate(NIV) if bal >= u]); r = max(Rs[lv][i], -NIV[lv][2])
        bal += r; hwm = max(hwm, bal); piso = 100 if hwm >= 4100 else hwm - 4000
        if bal <= piso: return q, k + 1
        if r >= 350: d += 1
        mx = max(mx, r); ben = bal - b0
        if bal >= 4600 and d >= 5 and ben > 0 and mx < 0.5 * ben:
            a = min([2500, 3000, 3000, 3000, 4000, 5000][len(q)], bal - 4100)
            if a >= 500:
                bal -= a; q.append(a); d = 0; mx = 0.0; b0 = bal
                if len(q) == 6: return q, k + 1
    return q, len(idx)
def ex150(x, idx):
    eq = hwm = 0.0
    for k, i in enumerate(idx[:21]):
        r = max(x[i], -2000); eq += r; hwm = max(hwm, eq); piso = 9000 if hwm >= 13000 else hwm - 4000
        if eq <= piso: return False
        if eq >= 9000: return True
    return False
def exleg(x, idx, obj, dd):
    eq = hwm = 0.0
    for k, i in enumerate(idx):
        eq += x[i]; hwm = min(max(hwm, eq), dd + 100)
        if eq <= hwm - dd: return False, k + 1
        if eq >= obj: return True, k + 1
    return False, len(idx)
def paleg(x, idx, dd, tope):
    bal = hwm = 0.0; dias = 0; mx = 0.0; b0 = 0.0; q = []
    for k, i in enumerate(idx):
        r = x[i]; bal += r; hwm = max(hwm, bal); piso = 100 if hwm >= dd + 100 else hwm - dd
        if bal <= piso: return q, k + 1
        dias += 1; mx = max(mx, r); ben = bal - b0
        if dias >= 8 and ben > 0 and mx < 0.3 * ben and bal > 2600 + 500:
            a = min(tope, bal - 2600)
            if a >= 500: bal -= a; q.append(a); dias = 0; mx = 0.0; b0 = bal
    return q, len(idx)
for hair, et in ((0.6, 'PRUDENTE'), (1.0, 'BACKTEST')):
    # 150K EOD: examen riesgo 1,5 (yen limitado a 12 contratos: 12/(9·3) ≈ 0,44); PA riesgo 0,5 (yen 4/9, 5/9, 7/9, 1, 1)
    def esc(s, r): return (s - s.mean() * (1 - hair)) * r / 0.5 * 150000
    xe = esc(serie(12 / 27), 1.5); Rs = [esc(serie(min(1, n / 9)), 0.5) for _, n, _ in NIV]
    ok = 0; F = []
    for _ in range(4000):
        if ex150(xe, camino(xe, 30)): ok += 1; F.append(pa150(Rs, camino(xe, 2000)))
    pa = ok / 4000; tot = np.array([sum(q) for q, _ in F]); vida = np.array([v for _, v in F]) / 21
    m = 20 * tot.mean() / vida.mean(); exm = 20 / vida.mean() / pa; neto = m - exm * 219 - 20 / vida.mean() * 159
    print(f'{et:8s} 150K EOD (yen recortado) | aprueba en 30 días {pa*100:3.0f} % | cobrado por cuenta {tot.mean():6,.0f} $ | vida {vida.mean():4.1f} m | 20 plazas {m:7,.0f} $/mes brutos, {exm:.1f} exámenes/mes → NETO ~{neto:7,.0f} $/mes ({12*neto:9,.0f} $/año)', flush=True)
    for nom, cap, obj, dd, tope in (('250K heredada', 250000, 15000, 6500, 3000), ('300K heredada', 300000, 20000, 7500, 3500)):
        for re, rf in ((0.5, 0.5), (0.65, 0.5), (0.65, 0.65)):
            s0 = serie(1.0); xe = (s0 - s0.mean() * (1 - hair)) * re / 0.5 * cap; xf = (s0 - s0.mean() * (1 - hair)) * rf / 0.5 * cap
            ok = 0; tex = []; F = []
            for _ in range(3000):
                a, t = exleg(xe, camino(xe, 1500), obj, dd); tex.append(t)
                if a: ok += 1; F.append(paleg(xf, camino(xf, 2520), dd, tope))
            pa = ok / 3000; tot = np.array([sum(q) for q, _ in F]); vida = np.array([v for _, v in F]) / 21; nc = np.array([len(q) for q, _ in F])
            m = 20 * tot.mean() / vida.mean(); exm = 20 / vida.mean() / pa; neto = m - exm * 200 - 20 / vida.mean() * 159
            print(f'{et:8s} {nom} examen {re}/PA {rf} | aprueba {pa*100:3.0f} % (examen {np.mean(tex)/21:.1f} m) | cobros por cuenta {nc.mean():4.1f} cada {vida.sum()/max(nc.sum(),1):.1f} m | '
                  f'vida {vida.mean():4.1f} m | cobrado {tot.mean():7,.0f} $ | 20 plazas {m:7,.0f} $/mes → NETO ~{neto:7,.0f} $/mes ({12*neto:9,.0f} $/año)', flush=True)
