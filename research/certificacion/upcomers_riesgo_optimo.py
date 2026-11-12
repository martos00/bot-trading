"""Riesgo que más rinde en Upcomers 1,5M/2M (Horizon y Odyssey) con la cartera CFD de C116. Mismas reglas que upcomers_cfd_c116.py.
No cambia la estrategia: solo el riesgo por operación. Se decide con el escenario REAL AL 60 % y mirando la mediana y la pérdida de cuentas.
Uso: python3 upcomers_riesgo_optimo.py SERIE_CSV"""
import sys, numpy as np
exec(open('upcomers_cfd_c116.py').read().split('CUENTAS =')[0])
for nom, fases, diaria in (('Horizon', (0.09,), 0.03), ('Odyssey', (0.06, 0.06), 0.04)):
    for cn, cap, pr in (('1,5M', 1_500_000, 2300), ('2M', 2_000_000, 2900)):
        for hair, et in ((0.6, 'REAL AL 60 %'), (1.0, 'BACKTEST')):
            for r in (0.5, 0.65, 0.8, 0.95, 1.1):
                x = (V - V.mean() * (1 - hair)) * r / 0.5; e = np.cumsum(x)
                res = [sim(x, fases, diaria, cap, pr) for _ in range(1500)]; v = np.array([q[0] for q in res]); m1 = [q[3] for q in res if q[3] is not None]
                print(f'{nom:8s} {cn:5s} {et:12s} riesgo {r:.2f} ({x.mean()*252*100:4.1f} %/año, caída hist. {(e-np.maximum.accumulate(e)).min()*100:5.1f} %) | media {v.mean()/24:7,.0f} $/mes | mediana {np.median(v)/24:7,.0f} $/mes | '
                      f'25 % peor {np.percentile(v,25)/24:7,.0f} $/mes | 1.er cobro {np.median(m1) if m1 else float("nan"):.1f} m ({len(m1)/len(res)*100:.0f} %) | pierde fondeada {np.mean([q[1]>0 for q in res])*100:3.0f} % | exámenes {np.mean([q[4] for q in res]):.1f}', flush=True)
