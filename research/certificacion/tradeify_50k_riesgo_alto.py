"""Variante de tradeify_50k_actual.py con riesgos altos (examen 1,0-1,5; fondeada 0,65-0,8). Tradeify 50K con las reglas de su web (12-nov-2026) y la configuración del bot para Tradeify, de la compra al cobro, 24 meses.
Examen: 116 $ (código NOV; reset 109 $), objetivo 3.000 $, pérdida máx. 2.000 $ al cierre del día (arrastrada; supuesto: se fija en
+100 $ como en la fondeada), sin límite diario, consistencia 40 % (el mejor día ≤ 40 % del beneficio al aprobar; si no, se sigue operando).
Fondeada Flex: 2.000 $ EOD arrastrada que se fija en +100 $ (supuesto), sin límite diario ni consistencia; cobro tras 5 días ganadores
de ≥ 150 $, importe = mín(50 % del beneficio, 2.500 $), 90 % para ti. Si se suspende o se pierde, se vuelve a comprar (109 $).
Cartera del bot en Tradeify (futuros, costes de futuros): yen E9 y E11, oro viernes 16:55, oro D-2, plata víspera y plata viernes,
C93 y C99 (peso 0,2), C113 (peso 0,2); sin Nikkei, cobre, bitcoin ni E12. Control de volatilidad. Sin límite de contratos ni
redondeo a micros (con 50K y riesgo 0,5-1 el bot usa pocos micros). Uso: python3 tradeify_50k_actual.py DIR_SCRATCH"""
import sys, numpy as np, pandas as pd
SP = sys.argv[1]; sys.path.insert(0, '.')
C = pd.read_csv(f'{SP}/componentes_B.csv', index_col=0, parse_dates=True).loc['2018-03-26':]
cols = ['yen', 'cesta_yen', 'oro_vie_1655', 'oro_D-2', 'plata_visp_1655', 'plata_viernes', 'oro_video_C93', 'oro_asia_C99']
import c94_ruptura_otros_futuros as c94
from c112_momentum_sesiones import sesiones
c94.SP = SP; h, ex = c94.carga_h1('GC'); rr = sesiones(h, pd.Timedelta(hours=1), ex).asia.loc['2018-03-26':]
rr.index = pd.DatetimeIndex(rr.index); sig = rr.rolling(250, min_periods=60).std().shift(1).fillna(rr.std())
c113 = (0.005 * 0.2 * (rr - 0.74) / sig).reindex(C.index).fillna(0)
P = C[cols].sum(axis=1) + c113; pv = P.rolling(60, min_periods=40).std().shift(1); SER = (P * (P.std() / pv).clip(0.5, 2)).dropna().values
pass  # print(f'Cartera Tradeify: {SER.mean()*252*100:.1f} %/año a riesgo 0,5 | Sharpe {SER.mean()/SER.std()*np.sqrt(252):.2f}')
CAP = 50000; DD = 2000; B = 20; T = 504; rng = np.random.default_rng(116)
def sim(xe, xf):
    st = rng.integers(0, len(xe) - B, T // B + 1); idx = (st[:, None] + np.arange(B)).ravel()[:T]; Re, Rf = xe[idx] * CAP, xf[idx] * CAP
    t = 0; pag = 0.0; cob = 0.0; m1 = None; compras = 0
    while t < T:
        pag += 116 if compras == 0 else 109; compras += 1
        bal = hwm = mx = 0.0; ok = False
        while t < T:
            r = Re[t]; t += 1; bal += r; hwm = min(max(hwm, bal), DD + 100); mx = max(mx, r)
            if bal <= hwm - DD: break
            if bal >= 3000 and mx <= 0.4 * bal: ok = True; break
        if not ok: continue
        bal = hwm = 0.0; dias = 0
        while t < T:
            r = Rf[t]; t += 1; bal += r; hwm = min(max(hwm, bal), DD + 100)
            if bal <= hwm - DD: break
            if r >= 150: dias += 1
            if dias >= 5 and bal > 0:
                q = min(0.5 * bal, 2500); bal -= q; cob += 0.9 * q; dias = 0
                if m1 is None: m1 = t / 21
    return cob - pag, m1, pag
for hair, et in ((0.6, 'PRUDENTE'), (1.0, 'BACKTEST')):
    for rf in (0.65, 0.8):
        xf = (SER - SER.mean() * (1 - hair)) * rf / 0.5
        for re in (1.0, 1.25, 1.5):
            if re < rf: continue
            xe = (SER - SER.mean() * (1 - hair)) * re / 0.5; res = [sim(xe, xf) for _ in range(3000)]
            v = np.array([q[0] for q in res]); m1 = np.array([q[1] if q[1] is not None else np.nan for q in res]); pg = np.array([q[2] for q in res])
            print(f'{et:8s} examen {re:.2f} / fondeada {rf:.2f} | 1.er cobro desde la compra: mediana {np.nanmedian(m1):.1f} m; <2 m {np.mean(m1<2)*100:3.0f} %, <3 m {np.mean(m1<3)*100:3.0f} %, <4 m {np.mean(m1<4)*100:3.0f} %, <6 m {np.mean(m1<6)*100:3.0f} % '
                  f'| neto 24 m: media {v.mean()/24:5,.0f} $/mes, mediana {np.median(v)/24:5,.0f} $/mes, 10 % peor {np.percentile(v,10)/24:5,.0f} $/mes | exámenes {pg.mean():,.0f} $')
