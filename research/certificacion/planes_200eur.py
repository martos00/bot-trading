"""Planes con solo ~200 € (~230 $) de dinero propio: el resto (resets, cuentas nuevas, grandes) se paga SOLO con lo cobrado.
Si una cuenta se pierde y no hay caja para el reset, queda parada hasta que la haya. Reinversión, en este orden cuando hay caja
(+200 $ de margen): Tradeify 150K (hasta 5), Lucid 50K (hasta 5), 2 tipo FTMO 200K, Upcomers 2M (1). Mismas reglas y series que
planes_10k.py. 5 años. Variante: RESERVA = dinero propio adicional disponible solo para resets (la caja puede bajar hasta −RESERVA).
Uso: python3 planes_200eur.py SERIES_CSV [RESERVA]"""
import sys, numpy as np, pandas as pd
src = open('planes_10k.py').read(); exec(src[src.index('import sys'):src.index('PLANES = {')].replace("D = pd.read_csv(sys.argv[1]", "D = pd.read_csv(sys.argv[1]"))
PRECIO['t50'] = 116    # código NOV (hasta el 13-nov)
RES = float(sys.argv[2]) if len(sys.argv) > 2 else 0.0
REINV = [('t150', 5), ('l50', 5), ('ftmo', 2), ('ugr', 1)]
PL = {
    'K1 Tradeify 50K + Upcomers 50K (219 $)':  ['t50', 'u50'],
    'K2 Lucid 50K + Upcomers 50K (218 $)*':    ['l50', 'u50'],
    'K3 Tradeify 50K + Lucid 50K (231 $)*':    ['t50', 'l50'],
    'K4 Solo Upcomers 50K ×2 (206 $)':         ['u50', 'u50'],
    'K5 Solo Tradeify 50K (116 $)':            ['t50'],
}
def corre(hair, et, reinv, etq):
    X = {k: (D[k] - D[k].mean() * (1 - hair)).values for k in D}
    for nom, ini in PL.items():
        rng = np.random.default_rng(7); L = []; Y = []; RU = []; MG = []
        for _ in range(NS):
            st = rng.integers(0, len(X['U']) - B, T // B + 1); idx = (st[:, None] + np.arange(B)).ravel()[:T]; R = {k: X[k][idx] for k in X}
            cs = [FAB[k]() for k in ini]; tipos = list(ini); deuda = [0.0] * len(cs); caja = 0.0; neto = np.zeros(T); parada_total = 0
            for t in range(T):
                for i, c in enumerate(cs):
                    if deuda[i] > 0:
                        if caja + RES >= deuda[i]: caja -= deuda[i]; neto[t] -= deuda[i]; deuda[i] = 0.0
                        else: continue
                    q, g = c.dia(R[c.ser][t], t)
                    caja += q; neto[t] += q
                    if g > 0:
                        if caja + RES >= g: caja -= g; neto[t] -= g
                        else: deuda[i] = g
                if reinv:
                    for k, mx in REINV:
                        if tipos.count(k) < mx and caja >= PRECIO[k] + 200:
                            cs.append(FAB[k]()); tipos.append(k); deuda.append(0.0); caja -= PRECIO[k]; neto[t] -= PRECIO[k]
                if all(d > 0 for d in deuda): parada_total += 1
            m = np.add.reduceat(neto, np.arange(0, T, 21)); doce = np.convolve(m, np.ones(12), 'full')[:len(m)]
            L.append(np.argmax(doce >= 120_000) + 1 if (doce >= 120_000).any() else np.nan); Y.append((m[:12].sum(), m[12:24].sum(), m[24:36].sum(), m[36:60].sum() / 2))
            RU.append(parada_total >= T - 1 - 0 or (parada_total > 0 and all(d > 0 for d in deuda) and len(cs) == len(ini)))
            MG.append(len(cs))
        L = np.array(L, float); Y = np.array(Y)
        print(f'{et:8s} {etq} | {nom:40s} | 10k/mes: 2 años {np.mean(L<=24)*100:3.0f} %, 3 años {np.mean(L<=36)*100:3.0f} %, 5 años {np.mean(L<=60)*100:3.0f} %, mes mediano {np.nanmedian(L) if np.isfinite(L).any() else float("nan"):4.0f} '
              f'| cobrado neto (mediana) año1 {np.median(Y[:,0]):8,.0f} año2 {np.median(Y[:,1]):8,.0f} año3 {np.median(Y[:,2]):8,.0f} años4-5/año {np.median(Y[:,3]):8,.0f} '
              f'| se queda sin nada (todas paradas sin caja, sin haber crecido) {np.mean(RU)*100:3.0f} % | cuentas compradas (mediana) {np.median(MG):.0f}', flush=True)
for hair, et in ((0.6, 'PRUDENTE'), (1.0, 'BACKTEST')): corre(hair, et, True, f'reserva {RES:.0f} $')
