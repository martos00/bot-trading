"""Con solo ~200 € (sin reserva): ¿en qué orden reinvertir? Inicio Tradeify 50K + Upcomers 50K o 2× Upcomers 50K.
Órdenes: R1 futuros 150K primero (como planes_200eur.py); R2 cuentas baratas primero (más Upcomers 50K hasta 4, Lucid 50K hasta 5,
luego Tradeify 150K, FTMO, 2M); R3 ahorrar para la Upcomers 2M primero (no se compra nada hasta tenerla), luego FTMO y futuros.
Uso: python3 planes_200eur_orden.py SERIES_CSV"""
import sys, numpy as np
src = open('planes_200eur.py').read()
exec(src[src.index('import sys'):src.index('PL = {')])
ORD = {'R1 futuros 150K primero': [('t150', 5), ('l50', 5), ('ftmo', 2), ('ugr', 1)],
       'R2 cuentas baratas primero': [('u50', 4), ('l50', 5), ('t150', 5), ('ftmo', 2), ('ugr', 1)],
       'R3 la 2M primero': [('ugr', 1), ('ftmo', 2), ('t150', 5), ('l50', 5)]}
PL = {'Tradeify 50K + Upcomers 50K': ['t50', 'u50'], 'Upcomers 50K ×2': ['u50', 'u50']}
for hair, et in ((0.6, 'PRUDENTE'), (1.0, 'BACKTEST')):
    X = {k: (D[k] - D[k].mean() * (1 - hair)).values for k in D}
    for nom, ini in PL.items():
        for on, orden in ORD.items():
            rng = np.random.default_rng(7); L = []; RU = []
            for _ in range(NS):
                st = rng.integers(0, len(X['U']) - B, T // B + 1); idx = (st[:, None] + np.arange(B)).ravel()[:T]; R = {k: X[k][idx] for k in X}
                cs = [FAB[k]() for k in ini]; tipos = list(ini); deuda = [0.0] * len(cs); caja = 0.0; neto = np.zeros(T)
                for t in range(T):
                    for i, c in enumerate(cs):
                        if deuda[i] > 0:
                            if caja >= deuda[i]: caja -= deuda[i]; neto[t] -= deuda[i]; deuda[i] = 0.0
                            else: continue
                        q, g = c.dia(R[c.ser][t], t); caja += q; neto[t] += q
                        if g > 0:
                            if caja >= g: caja -= g; neto[t] -= g
                            else: deuda[i] = g
                    for k, mx in orden:
                        n = tipos.count(k) - (ini.count(k) if k == 'u50' else 0)
                        if n < mx and caja >= PRECIO[k] + 200:
                            cs.append(FAB[k]()); tipos.append(k); deuda.append(0.0); caja -= PRECIO[k]; neto[t] -= PRECIO[k]
                        if on.startswith('R3') and k == 'ugr' and 'ugr' not in tipos: break   # ahorrar para la 2M antes que nada
                m = np.add.reduceat(neto, np.arange(0, T, 21)); doce = np.convolve(m, np.ones(12), 'full')[:len(m)]
                L.append(np.argmax(doce >= 120_000) + 1 if (doce >= 120_000).any() else np.nan); RU.append(len(cs) == len(ini) and all(d > 0 for d in deuda))
            L = np.array(L, float)
            print(f'{et:8s} | {nom:28s} | {on:27s} | 120k/año: 2 años {np.mean(L<=24)*100:3.0f} %, 3 años {np.mean(L<=36)*100:3.0f} %, 5 años {np.mean(L<=60)*100:3.0f} % | mes mediano (si llega) {np.nanmedian(L) if np.isfinite(L).any() else float("nan"):4.0f} | sin nada {np.mean(RU)*100:3.0f} %', flush=True)
