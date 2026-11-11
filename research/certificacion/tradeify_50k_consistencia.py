"""Tradeify 50K fondeada: ¿cada cuánto se cobra con regla del mejor día del 35 % (desde el último cobro) frente a sin regla?
Supuestos (sin confirmar): pérdida 2.000 $ al cierre del día (arrastrada, se fija en +100 $), 5 días ganadores ≥ 150 $ por cobro,
cobro = mín(50 % del beneficio, 2.000 $), 90 % para ti. Cartera de 50K (sin C113 ni Nikkei: oro y plata viernes, plata víspera,
oro D-2, yen). 24 meses desde que estás fondeado. Uso: python3 tradeify_50k_consistencia.py DIR_SCRATCH"""
import sys, numpy as np, pandas as pd
C = pd.read_csv(f'{sys.argv[1]}/componentes_B.csv', index_col=0, parse_dates=True).loc['2018-03-26':]
cols = ['yen', 'cesta_yen', 'oro_vie_1655', 'oro_D-2', 'plata_visp_1655', 'plata_viernes']
P = C[cols].sum(axis=1); pv = P.rolling(60, min_periods=40).std().shift(1); SER = (P * (P.std() / pv).clip(0.5, 2)).dropna().values
CAP = 50000; DD = 2000; B = 20; T = 504; rng = np.random.default_rng(79)
def sim(x, regla):
    st = rng.integers(0, len(x) - B, T // B + 1); R = x[(st[:, None] + np.arange(B)).ravel()[:T]] * CAP
    bal = hwm = 0.0; dias = 0; ben0 = 0.0; mx = 0.0; cob = []; t_ult = 0
    for t, r in enumerate(R):
        bal += r; hwm = min(max(hwm, bal), DD + 100)
        if bal <= hwm - DD: return cob, t, True
        if r >= 150: dias += 1
        mx = max(mx, r); ben = bal - ben0
        if dias >= 5 and bal > 0 and ben > 0 and mx <= regla * ben:
            q = min(0.5 * bal, 2000); bal -= q; cob.append((t - t_ult, 0.9 * q)); t_ult = t; dias = 0; ben0 = bal; mx = 0.0
    return cob, T, False
for hair, et in ((0.6, 'REAL AL 60 %'), (1.0, 'BACKTEST')):
    for r in (0.50, 0.65):
        for regla, nom in ((0.35, 'regla 35 %'), (10.0, 'sin regla ')):
            x = (SER - SER.mean() * (1 - hair)) * r / 0.5; res = [sim(x, regla) for _ in range(3000)]
            esp = [e for c, _, _ in res for e, _ in c]; dinero = [sum(q for _, q in c) for c, _, _ in res]; vida = np.array([t for _, t, _ in res]) / 21
            print(f'{et:12s} riesgo {r:.2f} % {nom}: tiempo entre cobros mediana {np.median(esp)/21:.1f} meses (media {np.mean(esp)/21:.1f}) | 1.er cobro mediana {np.median([c[0][0] for c, _, _ in res if c])/21:.1f} meses | '
                  f'cobros por cuenta {np.mean([len(c) for c, _, _ in res]):.1f} | cobrado medio {np.mean(dinero):,.0f} $ | dura la cuenta {np.median(vida):.1f} meses (mediana) | la pierde {np.mean([p for *_, p in res])*100:.0f} %')
