"""LucidFlex 150K a mano. Respuestas del soporte de Lucid (16-nov-2026; parecen de su asistente, citan su centro de ayuda y webs de terceros):
mercados MGC, SI, SIL, 6J, NKD sí; todo cerrado a las 16:45 NY (→ oro viernes 16:45, plata de víspera 16:45, SIN plata del viernes, que gana
entre 16:50 y 16:57); examen 9.000 $, pérdida 4.500 $ EOD (se fija en 150.100 $ al llegar a 154.600 $ o con el 1.er cobro), consistencia
40 % en el examen, sin plazo*, pago único ~300 $*, sin activación. Fondeada: sin consistencia ni colchón; cobro con 5 días de ≥ 250 $ desde
el anterior y beneficio del ciclo > 0; máx. 50 % del beneficio y 3.000 $; mín. 500 $; 90 %; tras el 5.º cobro pasa a revisión para real:
se cuenta como fin de la cuenta + opción de cobrar el 50 % del beneficio restante (90 %). La cuenta real no se cuenta. Máx. 5 fondeadas.
Uso: python3 lucid_flex_150k.py DIR_SCRATCH"""
import sys, numpy as np, pandas as pd
exec(open('plan_reinversion_etf.py').read().split('CAP, OBJ')[0])
CA = pd.read_csv(f'{SP}/componentes_A.csv', index_col=0, parse_dates=True).loc['2018-03-26':]
CAP = 150000; B = 20; T = 1260; rng = np.random.default_rng(91); CUOTA = 300
def plaza(Re, Rf):
    t = 0; neto = 0.0; perd = 0; ncob = 0; fins = 0; primero = None
    while t < T:
        neto -= CUOTA; eq = hwm = mx = 0.0; ok = False
        while t < T:
            r = Re[t]; t += 1; eq += r; hwm = max(hwm, eq); mx = max(mx, r)
            if eq <= min(hwm, 4600) - 4500: break
            if eq >= 9000 and mx <= 0.4 * eq: ok = True; break
        if not ok: continue
        bal = hwm = 0.0; fijo = False; dias = 0; b0 = 0.0; n = 0
        while t < T:
            r = Rf[t]; t += 1; bal += r; hwm = max(hwm, bal)
            if hwm >= 4600: fijo = True
            piso = 100 if fijo else hwm - 4500
            if bal <= piso: perd += 1; break
            if r >= 250: dias += 1
            if dias >= 5 and bal - b0 > 0:
                q = min(0.5 * bal, 3000)
                if q >= 500:
                    bal -= q; neto += 0.9 * q; n += 1; ncob += 1; fijo = True; dias = 0; b0 = bal
                    if primero is None: primero = t
                    if n == 5: neto += 0.9 * 0.5 * max(bal, 0); fins += 1; break
    return neto, perd, ncob, primero, fins
for nom, cols, c113 in (('con Nikkei y oro de madrugada', ['yen', 'cesta_yen', 'oro_vie_1645', 'oro_D-2', 'plata_visp_1645', 'nikkei_Q+2', 'nikkei_Q-2'], True),
                        ('con Nikkei, sin oro de madrugada', ['yen', 'cesta_yen', 'oro_vie_1645', 'oro_D-2', 'plata_visp_1645', 'nikkei_Q+2', 'nikkei_Q-2'], False)):
    P = CA[cols].sum(axis=1)
    if c113: P = P + C['c113'].reindex(CA.index).fillna(0)
    pv = P.rolling(60, min_periods=40).std().shift(1); S0 = (P * (P.std() / pv).clip(0.5, 2)).dropna().loc['2018-11-05':].values
    print(f'\n=== {nom}: {S0.mean()*252*100:.1f} %/año a riesgo 0,5 | Sharpe {S0.mean()/S0.std()*np.sqrt(252):.2f}')
    for hair, et in ((0.6, 'PRUDENTE'), (1.0, 'BACKTEST')):
        for re, rf in ((1.0, 0.5), (2.0, 0.5), (2.0, 0.65)):
            xe = (S0 - S0.mean() * (1 - hair)) * re / 0.5 * CAP; xf = (S0 - S0.mean() * (1 - hair)) * rf / 0.5 * CAP; res = []
            for _ in range(1500):
                st = rng.integers(0, len(S0) - B, T // B + 1); idx = (st[:, None] + np.arange(B)).ravel()[:T]; res.append(plaza(xe[idx], xf[idx]))
            v = np.array([q[0] for q in res]) / 60; pr = np.array([q[3] if q[3] else np.nan for q in res]) / 21
            print(f'{et:8s} examen {re} / fondeada {rf} | por cuenta {np.median(v):6,.0f} $/mes (media {v.mean():6,.0f}) → 5 cuentas {5*v.mean():7,.0f} $/mes | '
                  f'cobros en 5 años {np.mean([q[2] for q in res]):4.1f} | cuentas que llegan al 5.º cobro {np.mean([q[4] for q in res]):.1f} | 1.er cobro (mediana) {np.nanmedian(pr):4.1f} m | '
                  f'pierde la fondeada {np.mean([q[1] for q in res]):.1f} veces', flush=True)
