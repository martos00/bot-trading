"""Take Profit Trader 150K a mano (sin rupturas, cierre 16:55 NY → oro viernes 16:45, plata víspera 16:45, sin plata viernes).
PRO (crosstrade.io/proea.app, sin verificar): cobros diarios, sin tope ni consistencia, 80 %, saldo > 154.500 $ para retirar; máx. 5 cuentas.
SUPUESTOS*: examen objetivo 9.000 $, pérdida 4.500 $ EOD arrastrada (se fija en +100 $), mejor día ≤ 50 % del beneficio al aprobar,
sin plazo, cuota 360 $ cada 21 hábiles mientras se examina (y se renueva al suspender); activación PRO 130 $; en la PRO la pérdida
máx. también 4.500 $ arrastrada que se fija en 150.100 $; se retira cada semana lo que pasa de 154.500 $ + colchón extra.
Cada plaza en serie (examen → PRO → si se pierde, examen otra vez), 5 años, 5 plazas. Uso: python3 tpt_pro_manual.py DIR_SCRATCH"""
import sys, numpy as np, pandas as pd
exec(open('plan_reinversion_etf.py').read().split('CAP, OBJ')[0])
CA = pd.read_csv(f'{SP}/componentes_A.csv', index_col=0, parse_dates=True).loc['2018-03-26':]
base = ['yen', 'cesta_yen', 'oro_vie_1645', 'oro_D-2', 'plata_visp_1645', 'nikkei_Q+2', 'nikkei_Q-2']
CAP = 150000; B = 20; T = 1260; rng = np.random.default_rng(55)
def plaza(Re, Rf, extra):
    t = 0; neto = 0.0; perd = 0; ncob = 0
    while t < T:
        eq = hwm = mx = 0.0; t0 = t; ok = False; neto -= 360
        while t < T:
            r = Re[t]; t += 1; eq += r; hwm = min(max(hwm, eq), 4600); mx = max(mx, r)
            if (t - t0) % 21 == 0: neto -= 360
            if eq <= hwm - 4500: break
            if eq >= 9000 and mx <= 0.5 * eq: ok = True; break
        if not ok: continue
        neto -= 130; bal = hwm = 0.0
        while t < T:
            r = Rf[t]; t += 1; bal += r; hwm = max(hwm, bal)
            piso = 100 if hwm >= 4600 else hwm - 4500
            if bal <= piso: perd += 1; break
            if t % 5 == 0 and bal > 4500 + extra: q = bal - 4500 - extra; bal -= q; neto += 0.8 * q; ncob += 1
    return neto, perd, ncob
for nom, extra_cols in (('sin oro de madrugada', []), ('con oro de madrugada (C113)', ['c113'])):
    cols = base; P = CA[cols].sum(axis=1)
    if extra_cols: P = P + C['c113'].reindex(CA.index).fillna(0)
    pv = P.rolling(60, min_periods=40).std().shift(1); S0 = (P * (P.std() / pv).clip(0.5, 2)).dropna().loc['2018-11-05':].values
    print(f'\n=== {nom}: {S0.mean()*252*100:.1f} %/año a riesgo 0,5 | Sharpe {S0.mean()/S0.std()*np.sqrt(252):.2f}')
    for hair, et in ((0.6, 'PRUDENTE'), (1.0, 'BACKTEST')):
        for re, rf, extra in ((0.65, 0.5, 0), (1.0, 0.5, 0), (1.0, 0.5, 2000), (1.0, 0.65, 2000)):
            xe = (S0 - S0.mean() * (1 - hair)) * re / 0.5 * CAP; xf = (S0 - S0.mean() * (1 - hair)) * rf / 0.5 * CAP; res = []
            for _ in range(1500):
                st = rng.integers(0, len(S0) - B, T // B + 1); idx = (st[:, None] + np.arange(B)).ravel()[:T]; res.append(plaza(xe[idx], xf[idx], extra))
            v = np.array([q[0] for q in res]) / 60
            print(f'{et:8s} examen {re} / PRO {rf} / colchón extra {extra:5d} $ | por cuenta {np.median(v):6,.0f} $/mes (media {v.mean():6,.0f}) → 5 cuentas {5*np.median(v):7,.0f} $/mes ({5*v.mean():7,.0f}) | '
                  f'pierde la PRO en 5 años {np.mean([q[1] for q in res]):.1f} veces de media', flush=True)
