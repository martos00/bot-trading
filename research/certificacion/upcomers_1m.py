"""Upcomers Thunderbolt 1M (centro de ayuda, 10-nov-2026): examen 1 fase +5 %, diaria 3 %, pérdida máx. 6 % ARRASTRADA desde el máximo
(se queda fija al llegar al saldo inicial). Fondeada: 100 % para ti; cobro si hay ≥ 1 % desde el último cobro y el mejor día ≤ 20 % del
beneficio desde el último cobro; topes por cobro 5k/7,5k/10k/15k/20k/25k/30k y sin tope desde el 8.º; comisión 19,9 $ + 2,49 %.
Examen 799 $ (con el 90 % de descuento), devuelto con el 3.er cobro. Se deja un colchón sobre el saldo inicial al cobrar.
Cartera actual (con C113). 24 meses. Uso: python3 upcomers_1m.py DIR_SCRATCH"""
import sys, numpy as np, pandas as pd
exec(open('plan_reinversion_etf.py').read().split('CAP, OBJ')[0])
BASE = SER / 1.3; rng = np.random.default_rng(53); B = 20; T = 504; CAP = 1_000_000; PRECIO = 799
TOPES = [5000, 7500, 10000, 15000, 20000, 25000, 30000]
def sim(x, colchon):
    st = rng.integers(0, len(x) - B, T // B + 1); R = x[(st[:, None] + np.arange(B)).ravel()[:T]]
    t = 0; pag = 0.0; cob = 0.0; perd = 0; ex = 0; ncob_tot = 0; espera = []
    while t < T:
        ex += 1; pag += PRECIO; eq = 0.0; hwm = 0.0; ok = False
        while t < T:                                   # examen
            r = R[t]; t += 1; eq += r; hwm = max(hwm, eq)
            if r <= -0.03 or eq <= min(hwm, 0.06) - 0.06: break
            if eq >= 0.05: ok = True; break
        if not ok: continue
        bal = 0.0; hwm = 0.0; k = 0; ben0 = 0.0; mx = 0.0; tc = t; reembolsado = False
        while t < T:                                   # fondeada
            r = R[t]; t += 1; bal += r; hwm = max(hwm, bal); piso = min(hwm - 0.06, 0.0)
            if r <= -0.03 or bal <= piso: perd += 1; break
            mx = max(mx, r); ben = bal - ben0
            if ben >= 0.01 and mx <= 0.20 * ben and bal - colchon > 0:
                q = min(bal - colchon, ben) * CAP
                if k < len(TOPES): q = min(q, TOPES[k])
                if q >= 1000:
                    neto = q - 19.9 - 0.0249 * q; cob += neto; bal -= q / CAP; k += 1; ncob_tot += 1; espera.append(t - tc); tc = t
                    ben0 = bal; mx = 0.0
                    if k == 3 and not reembolsado: cob += PRECIO; reembolsado = True
    return cob - pag, perd, ex, ncob_tot, (np.mean(espera) / 21 if espera else np.nan)
for hair, et in ((0.6, 'REAL AL 60 %'), (1.0, 'BACKTEST')):
    print(f'\n### {et} — cuenta de 1 M$, 24 meses (dinero ya neto de comisiones de cobro y exámenes; antes de impuestos)')
    for r in (0.30, 0.40, 0.50, 0.65):
        for col in (0.02, 0.04):
            x = (BASE - BASE.mean() * (1 - hair)) * r / 0.5; res = [sim(x, col) for _ in range(2000)]
            n = np.array([q[0] for q in res])
            print(f'  riesgo {r:.2f} %, colchón {col*100:.0f} %: neto {n.mean():9,.0f} $ (mediana {np.median(n):9,.0f}; 10 % peor {np.percentile(n,10):8,.0f}) = ~{n.mean()/24:6,.0f} $/mes | '
                  f'pierde la cuenta {np.mean([q[1]>0 for q in res])*100:3.0f} % | exámenes {np.mean([q[2] for q in res]):.1f} | cobros {np.mean([q[3] for q in res]):.1f} | meses entre cobros {np.nanmean([q[4] for q in res]):.1f}')
