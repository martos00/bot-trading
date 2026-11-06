"""Plan de reinversión en ETF 1 paso 150K (riesgo 0,65 %, cartera actual con C113). Todas las cuentas siguen el MISMO camino de
rentabilidades (mismas operaciones), cada una desde el día en que se abre. Uso: python3 plan_reinversion_etf.py DIR_SCRATCH"""
import sys, numpy as np, pandas as pd
import c94_ruptura_otros_futuros as c94
from c112_momentum_sesiones import sesiones
SP = sys.argv[1]; c94.SP = SP
C = pd.read_csv(f'{SP}/componentes_B.csv', index_col=0, parse_dates=True).loc['2018-03-26':]
h, ex = c94.carga_h1('GC'); rr = sesiones(h, pd.Timedelta(hours=1), ex).asia.loc['2018-03-26':]
sig = rr.rolling(250, min_periods=60).std().shift(1).fillna(rr.std())
C['c113'] = (0.005 * 0.2 * (rr - 0.74) / sig).reindex(C.index).fillna(0)
cols = ['yen', 'cesta_yen', 'oro_vie_1655', 'oro_D-2', 'plata_visp_1655', 'plata_viernes', 'nikkei_Q+2', 'nikkei_Q-2', 'c113']
P = C[cols].sum(axis=1); pv = P.rolling(60, min_periods=40).std().shift(1); SER = (P * (P.std() / pv).clip(0.5, 2)).dropna().loc['2018-11-05':].values * 0.65 / 0.5
CAP, OBJ, DD, TOPE, ACT, CUOTA, RESET, MAXC, B, T = 150000, 9000 / 150000, 5000 / 150000, 2250, 247, 34.70, 47, 20, 20, 504
rng = np.random.default_rng(11)
def sim(x, plan, solo_max=False):
    st = rng.integers(0, len(x) - B, T // B + 1); R = x[(st[:, None] + np.arange(B)).ravel()[:T]]
    cuentas = [dict(f='eval', eq=0.0, hwm=0.0, ini=0, tc=0)]; perdidas = 0; bolsa = 0.0; bolsillo = -CUOTA; impuestos = 0.0; n12 = None
    for t in range(T):
        frac = plan(t)
        for a in cuentas:
            a['eq'] += R[t]; a['hwm'] = min(max(a['hwm'], a['eq']), DD)
            if t - a['tc'] >= 21:   # cuota mensual de la evaluación
                if a['f'] == 'eval': bolsa -= CUOTA
                a['tc'] = t
            if a['eq'] <= a['hwm'] - DD:   # suspende o pierde la fondeada → nueva evaluación en ese hueco
                perdidas += a['f'] == 'fond'; bolsa -= RESET if a['f'] == 'eval' else CUOTA; a.update(f='eval', eq=0.0, hwm=0.0, tc=t); continue
            if a['f'] == 'eval' and a['eq'] >= OBJ: bolsa -= ACT; a.update(f='fond', eq=0.0, hwm=0.0, ini=t); continue
            if a['f'] == 'fond' and (t - a['ini']) % 10 == 0 and a['eq'] > DD and (not solo_max or (a['eq'] - DD) * CAP >= TOPE):
                q = min((a['eq'] - DD) * CAP, TOPE); a['eq'] -= q / CAP; cobro = 0.9 * q
                impuestos += 0.3 * cobro; bolsa += frac * cobro; bolsillo += (0.7 - frac) * cobro
        while bolsa >= 400 and len(cuentas) < MAXC: cuentas.append(dict(f='eval', eq=0.0, hwm=0.0, ini=t, tc=t)); bolsa -= CUOTA
        if bolsa < 0: bolsillo += bolsa; bolsa = 0.0   # lo que falta sale de tu bolsillo
        if t == 251: n12 = (len(cuentas), sum(a['f'] == 'fond' for a in cuentas), bolsillo)
    return n12, (len(cuentas), sum(a['f'] == 'fond' for a in cuentas), bolsillo + bolsa, perdidas)
PLANES = {'1 cuenta sin reinvertir': lambda t: 0.0, 'Reinvertir (50 % 6 meses, luego 70 %)': lambda t: 0.5 if t < 126 else 0.7}
for hair, et in ((1.0, 'BACKTEST'), (0.6, 'REAL AL 60 %')):
    x = SER - SER.mean() * (1 - hair); print(f'\n######## {et}')
    for nom, pl in PLANES.items():
        for sm in (False, True):
            res = [sim(x, pl, sm) for _ in range(2000)]; a24 = np.array([r[1] for r in res])
            n = a24[:, 0].mean()
            print(f'{nom:38s} | {"solo cobra 2.250 $ completos" if sm else "cobra lo que haya (hasta 2.250 $)":34s} | fondeadas pérdidas en 24 m por cuenta {a24[:,3].mean()/n:.1f} | '
                  f'dinero para ti {a24[:,2].mean():9,.0f} $ (mediana {np.median(a24[:,2]):9,.0f}; 10 % peor {np.percentile(a24[:,2],10):8,.0f}) | P(perder) {(a24[:,2]<0).mean()*100:3.0f} %')
