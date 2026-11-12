"""Ingresos en Upcomers con la cartera CFD de C116 (costes de Upcomers, con bitcoin y oro 16:55; serie a riesgo 0,5 % con control de vol.).
Reglas (centro de ayuda, 10-nov-2026): Horizon 1 fase 9 %, diaria 3 %; Odyssey 6 % + 6 %, diaria 4 %; ambas pérdida máx. 6 % arrastrada
que se fija en el saldo inicial. Fondeada 80 %, cobro cada 14 días (10 laborables) con ≥ 3 % de beneficio en el ciclo; se deja un colchón
del 3 %; comisión de cobro 19,9 $ + 2,49 %. Topes por cobro solo en cuentas de 800K+ (5k/7,5k/10k/15k/20k/25k/30k, luego sin tope).
Si se suspende o se pierde, se vuelve a comprar el examen. 24 meses, bloques de 20 días. Precios en $ (1 € ≈ 1,16 $; 2M supuesto).
Uso: python3 upcomers_cfd_c116.py SERIE_CSV"""
import sys, numpy as np, pandas as pd
V = pd.read_csv(sys.argv[1], index_col=0, parse_dates=True)['nueva'].dropna().values
rng = np.random.default_rng(116); B = 20; T = 504; COL = 0.03; TOPES = [5000, 7500, 10000, 15000, 20000, 25000, 30000]
def sim(x, fases, diaria, cap, precio):
    st = rng.integers(0, len(x) - B, T // B + 1); R = x[(st[:, None] + np.arange(B)).ravel()[:T]]
    t = 0; pag = 0.0; cob = 0.0; perd = 0; n = 0; mes1 = None; compras = 0
    while t < T:
        pag += precio; compras += 1; ok = True
        for obj in fases:
            eq = hwm = 0.0; ok = False
            while t < T:
                r = R[t]; t += 1; eq += r; hwm = max(hwm, eq)
                if r <= -diaria or eq <= min(hwm, 0.06) - 0.06: break
                if eq >= obj: ok = True; break
            if not ok: break
        if not ok: continue
        bal = hwm = 0.0; k = 0; ben0 = 0.0; ini = t
        while t < T:
            r = R[t]; t += 1; bal += r; hwm = max(hwm, bal)
            if r <= -diaria or bal <= min(hwm - 0.06, 0.0): perd += 1; break
            if (t - ini) % 10 == 0 and bal - ben0 >= 0.03 and bal > COL:
                q = (bal - COL) * cap
                if cap >= 800_000 and k < len(TOPES): q = min(q, TOPES[k])
                bal -= q / cap; ben0 = bal; k += 1; n += 1; cob += 0.8 * q * (1 - 0.0249) - 19.9
                if mes1 is None: mes1 = t / 21
    return cob - pag, perd, n, mes1, compras
CUENTAS = (('50K', 50_000, 103), ('100K', 100_000, 232), ('1,5M', 1_500_000, 2300), ('2M (precio supuesto)', 2_000_000, 2900))
for nom, fases, diaria in (('Horizon', (0.09,), 0.03), ('Odyssey', (0.06, 0.06), 0.04)):
    for hair, et in ((0.6, 'REAL AL 60 %'), (1.0, 'BACKTEST')):
        for r in (0.5, 0.65):
            x = (V - V.mean() * (1 - hair)) * r / 0.5
            for cn, cap, pr in CUENTAS:
                res = [sim(x, fases, diaria, cap, pr) for _ in range(1500)]; v = np.array([q[0] for q in res])
                m1 = [q[3] for q in res if q[3] is not None]
                print(f'{nom:8s} {cn:21s} {et:12s} riesgo {r:.2f} | neto 24 m {v.mean():10,.0f} $ (~{v.mean()/24:7,.0f} $/mes; mediana {np.median(v)/24:7,.0f} $/mes; 10 % peor {np.percentile(v,10):9,.0f} $) '
                      f'| 1.er cobro: {np.median(m1) if m1 else float("nan"):.1f} meses (lo logra {len(m1)/len(res)*100:.0f} %) | pierde alguna fondeada {np.mean([q[1]>0 for q in res])*100:3.0f} % | exámenes {np.mean([q[4] for q in res]):.1f}')
