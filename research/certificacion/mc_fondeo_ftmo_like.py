"""Cuenta de futuros con reglas tipo FTMO (100.000 $): fase 1 +10 %, fase 2 +5 %, pérdida máx. 10 % FIJA sobre el saldo inicial, pérdida
diaria 5 %; 500 $ por intento (fase 1 + fase 2); fondeada: misma pérdida fija 10 % y diaria 5 %, retiro mensual de todo el beneficio
(80 %), el saldo vuelve al inicial. Horizonte 24 meses. Comparación: reglas típicas de futuros (−4 % arrastrado, objetivo 6 %, 50.000 $, 150 $)."""
import numpy as np, pandas as pd
X = pd.read_csv('carteras_v3.csv', index_col=0, parse_dates=True)
rng = np.random.default_rng(5); B = 20; T = 504; CAP = 100000; CUOTA = 500
def camino(p):
    st = rng.integers(0, len(p) - B, T // B + 1); return p[(st[:, None] + np.arange(B)).ravel()[:T]]
def simula(p):
    R = camino(p); t = 0; pagado = 0; ret = 0.0; perdio = False; t_f = None; primero = None
    while t < T:
        pagado += CUOTA; ok = True
        for obj in (0.10, 0.05):
            eq = 0.0
            while t < T:
                eq += R[t]; t += 1
                if eq <= -0.10 or R[t - 1] <= -0.05: ok = False; break
                if eq >= obj: break
            if not ok or eq < obj: ok = False; break
        if primero is None: primero = ok
        if not ok: continue
        t_f = t if t_f is None else t_f; eq = 0.0; ini = t; vivo = True
        while t < T:
            eq += R[t]; t += 1
            if eq <= -0.10 or R[t - 1] <= -0.05: vivo = False; perdio = True; break
            if (t - ini) % 21 == 0 and eq > 0: ret += 0.8 * eq * CAP; eq = 0.0
        if vivo: break
    return pagado, ret, perdio, t_f, primero
for c in ('A_conf', 'B_conf'):
    x = X[c].values; m = x.mean() * 252
    print(f'\n=== {c} (Sharpe {x.mean()/x.std()*np.sqrt(252):.2f}) — reglas tipo FTMO, cuenta 100.000 $ ===')
    print('rent. objetivo | riesgo/op | aprueba las 2 fases al 1.er intento | intentos pagados | meses hasta fondeada | pierde la fondeada (24 m) | retirado 24 m (media) | neto | P(perder dinero)')
    for obj in (0.15, 0.25, 0.35, 0.50):
        S = [simula(x * obj / m) for _ in range(4000)]
        pg = np.array([s[0] for s in S]); rt = np.array([s[1] for s in S]); tf = np.array([s[3] if s[3] else np.nan for s in S])
        print(f'{obj*100:4.0f} % | {0.5*obj/m:.2f} % | {np.mean([bool(s[4]) for s in S])*100:3.0f} % | {pg.mean()/CUOTA:.1f} | {np.nanmedian(tf)/21:4.1f} | '
              f'{np.mean([s[2] for s in S])*100:3.0f} % | {rt.mean():,.0f} $ | {(rt-pg).mean():,.0f} $ | {((rt-pg)<0).mean()*100:.0f} %')
