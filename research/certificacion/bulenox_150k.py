"""Bulenox 150K a mano. Reglas de cobro copiadas de su página (16-nov-2026): ≥ 10 días de trading por periodo (el nuevo periodo empieza al
pagarse; solicitud hasta el viernes, pago el miércoles → se pierden ~3 hábiles), mín. 1.000 $, máx. 2.000 $ los 3 primeros y luego < 50 %
del beneficio de la cuenta, reserva 4.600 $ por encima del inicial tras el cobro, consistencia 40 % (mejor día ≤ 40 % del P&L del periodo;
en el 1.º desde el inicio, con la reserva incluida), 90 % para ti. Web: examen 325 $ pago único, objetivo 9.000 $, pérdida 4.500 $ EOD, 30 días.
SUPUESTOS*: examen sin consistencia; activación Master 150 $; pérdida de la Master 4.500 $ EOD que se fija en +100 $; la Master sigue
tras 3 cobros (el soporte dijo que siguen activas). Día de trading = día con alguna operación de la cartera.
Uso: python3 bulenox_150k.py DIR_SCRATCH"""
import sys, numpy as np, pandas as pd
exec(open('plan_reinversion_etf.py').read().split('CAP, OBJ')[0])
CAP = 150000; B = 20; T = 1260; rng = np.random.default_rng(77)
def plaza(Re, Rf, Op):
    t = 0; neto = 0.0; perd = 0; cob = []; primero = None
    while t < T:
        neto -= 325; eq = hwm = 0.0; ok = False; t0 = t
        while t < T and t - t0 < 21:
            r = Re[t]; t += 1; eq += r; hwm = max(hwm, eq)
            if eq <= min(hwm, 4600) - 4500: break
            if eq >= 9000: ok = True; break
        if not ok: continue
        neto -= 150; bal = hwm = 0.0; dias = 0; mx = 0.0; b0 = 0.0; n = 0; espera = 0
        while t < T:
            r = Rf[t]; o = Op[t]; t += 1; bal += r; hwm = max(hwm, bal)
            piso = 100 if hwm >= 4600 else hwm - 4500
            if bal <= piso: perd += 1; break
            if espera > 0: espera -= 1; continue
            if o: dias += 1
            mx = max(mx, r); pnl = bal - b0
            if dias >= 10 and pnl > 0 and mx <= 0.4 * pnl:
                q = bal - 4600
                q = min(q, 2000) if n < 3 else min(q, 0.499 * bal)
                if q >= 1000:
                    bal -= q; neto += 0.9 * q; n += 1; cob.append(t)
                    if primero is None: primero = t
                    dias = 0; mx = 0.0; b0 = bal; espera = 3
    return neto, perd, n, primero
for nom, cols in (('CON Nikkei', ['yen', 'cesta_yen', 'oro_vie_1655', 'oro_D-2', 'plata_visp_1655', 'plata_viernes', 'nikkei_Q+2', 'nikkei_Q-2', 'c113']),
                  ('SIN Nikkei', ['yen', 'cesta_yen', 'oro_vie_1655', 'oro_D-2', 'plata_visp_1655', 'plata_viernes', 'c113']),
                  ('SIN Nikkei ni oro de madrugada', ['yen', 'cesta_yen', 'oro_vie_1655', 'oro_D-2', 'plata_visp_1655', 'plata_viernes'])):
    P = C[cols].sum(axis=1); OPS = (C[cols].abs().sum(axis=1) > 0)
    pv = P.rolling(60, min_periods=40).std().shift(1); S0 = (P * (P.std() / pv).clip(0.5, 2)).dropna().loc['2018-11-05':]
    O0 = OPS.reindex(S0.index).values; S0 = S0.values
    print(f'\n=== {nom}: {S0.mean()*252*100:.1f} %/año a riesgo 0,5 | Sharpe {S0.mean()/S0.std()*np.sqrt(252):.2f} | días con operación {O0.mean()*100:.0f} %')
    for hair, et in ((0.6, 'PRUDENTE'), (1.0, 'BACKTEST')):
        for re, rf in ((1.0, 0.5), (2.0, 0.5), (2.0, 0.65)):
            xe = (S0 - S0.mean() * (1 - hair)) * re / 0.5 * CAP; xf = (S0 - S0.mean() * (1 - hair)) * rf / 0.5 * CAP; res = []
            for _ in range(1500):
                st = rng.integers(0, len(S0) - B, T // B + 1); idx = (st[:, None] + np.arange(B)).ravel()[:T]; res.append(plaza(xe[idx], xf[idx], O0[idx]))
            v = np.array([q[0] for q in res]) / 60; pr = np.array([q[3] if q[3] else np.nan for q in res]) / 21
            print(f'{et:8s} examen {re} / Master {rf} | por cuenta {np.median(v):6,.0f} $/mes (media {v.mean():6,.0f}) → 5 cuentas {5*v.mean():7,.0f} $/mes | '
                  f'cobros en 5 años {np.mean([q[2] for q in res]):4.1f} | 1.er cobro (mediana) {np.nanmedian(pr):4.1f} meses | pierde la Master en 5 años {np.mean([q[1] for q in res]):.1f} veces', flush=True)
