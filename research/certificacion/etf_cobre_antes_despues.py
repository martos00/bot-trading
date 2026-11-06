"""ETF 1 paso 150K: cartera actual, + oro en Asia (C113), + cobre (C102). Riesgo 0,65 %. Uso: python3 etf_cobre_antes_despues.py DIR_SCRATCH"""
import sys, numpy as np, pandas as pd
import c94_ruptura_otros_futuros as c94
from c112_momentum_sesiones import sesiones
SP = sys.argv[1]; c94.SP = SP
C = pd.read_csv(f'{SP}/componentes_B.csv', index_col=0, parse_dates=True).loc['2018-03-26':]
h, ex = c94.carga_h1('GC'); rr = sesiones(h, pd.Timedelta(hours=1), ex).asia.loc['2018-03-26':]
sig = rr.rolling(250, min_periods=60).std().shift(1).fillna(rr.std())
C['oro_asia_C113'] = (0.005 * 0.2 * (rr - 0.74) / sig).reindex(C.index).fillna(0)
base = ['yen', 'cesta_yen', 'oro_vie_1655', 'oro_D-2', 'plata_visp_1655', 'plata_viernes', 'nikkei_Q+2', 'nikkei_Q-2']
def volctl(P): pv = P.rolling(60, min_periods=40).std().shift(1); return (P * (P.std() / pv).clip(0.5, 2)).dropna()
CART = {'Antes (8 estrategias)': base, 'Ahora (+ oro en Asia)': base + ['oro_asia_C113'], 'Con cobre (+ cobre)': base + ['oro_asia_C113', 'cobre_asia_C102']}
CAP, OBJ, DD, TOPE, ACT, CUOTA, RESET, B, T = 150000, 9000, 5000, 2250, 247, 34.70, 47, 20, 504
rng = np.random.default_rng(5)
def simula(p):
    st = rng.integers(0, len(p) - B, T // B + 1); R = p[(st[:, None] + np.arange(B)).ravel()[:T]]
    t = 0; pag = CUOTA; ret = 0.0; perd = 0; intentos = 0; tf = None; tu = 0; primero = None; o, d = OBJ / CAP, DD / CAP
    while t < T:
        intentos += 1
        if intentos > 1: pag += RESET
        eq = hwm = 0.0; ok = False
        while t < T:
            eq += R[t]; t += 1; hwm = min(max(hwm, eq), d)
            if t - tu >= 21: pag += CUOTA; tu = t
            if eq <= hwm - d: break
            if eq >= o: ok = True; break
        if primero is None: primero = ok
        if not ok: continue
        if tf is None: tf = t
        pag += ACT; eq = hwm = 0.0; ini = t; vivo = True
        while t < T:
            eq += R[t]; t += 1; hwm = min(max(hwm, eq), d)
            if eq <= hwm - d: vivo = False; perd += 1; break
            if (t - ini) % 10 == 0 and eq > d: q = min((eq - d) * CAP, TOPE); ret += 0.9 * q; eq -= q / CAP   # 2 cobros al mes
        if vivo: break
        tu = t; pag += CUOTA
    return pag, ret, perd, intentos, tf, bool(primero)
sh = lambda s: s.mean() / s.std() * np.sqrt(252)
for nom, cols in CART.items():
    S = volctl(C[cols].sum(axis=1)).loc['2018-11-05':]
    p0 = S.values * 0.65 / 0.5; e = pd.Series(p0).cumsum(); me = pd.Series(p0, index=S.index).resample('ME').sum()
    print(f'\n##### {nom} — 1 paso 150K, riesgo 0,65 %')
    print(f'Backtest: Sharpe {sh(S):.2f} | rentabilidad {p0.mean()*252*100:.1f} %/año ({p0.mean()*252*CAP:,.0f} $) | caída máx. {(e-e.cummax()).min()*100:.1f} % ({(e-e.cummax()).min()*CAP:,.0f} $) | peor día {p0.min()*CAP:,.0f} $ | peor mes {me.min()*CAP:,.0f} $ | meses negativos {(me<0).mean()*100:.0f} % | operaciones/año {int((C[cols]!=0).sum().sum()/((C.index[-1]-C.index[0]).days/365.25))}')
    for hair, et, rk in ((1.0, 'backtest', 0.65), (0.6, 'real al 60 %', 0.65), (1.0, 'backtest, riesgo 0,45 %', 0.45), (0.6, 'real al 60 %, riesgo 0,45 %', 0.45)):
        x = (S.values - S.values.mean() * (1 - hair)) * rk / 0.5; R_ = [simula(x) for _ in range(4000)]
        pg = np.array([q[0] for q in R_]); rt = np.array([q[1] for q in R_]); tf = np.array([q[4] if q[4] else np.nan for q in R_])
        print(f'  [{et}] aprueba al 1.º {np.mean([q[5] for q in R_])*100:.0f} % | meses hasta fondeada {np.nanmedian(tf)/21:.1f} | exámenes en 24 m {np.mean([q[3] for q in R_]):.1f} | '
              f'pierde la fondeada en 24 m {np.mean([q[2]>0 for q in R_])*100:.0f} % | 24 m: pagado {pg.mean():,.0f} $, cobrado {rt.mean():,.0f} $ (mediana {np.median(rt):,.0f}), neto {(rt-pg).mean():,.0f} $ | P(perder dinero) {((rt-pg)<0).mean()*100:.0f} %')
