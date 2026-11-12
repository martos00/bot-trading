"""INFORMATIVO: cartera CFD C116 si los 5 $/lote de Upcomers (divisas y metales) fueran por operación completa y no por ejecución.
Ahorro por operación (ida y vuelta): USDJPY 0,50 pb; cesta yen 0,44 pb (media de USD/EUR/GBP); oro 0,125 pb (100 oz × ~4.000 $).
Nikkei sin comisión; bitcoin (0,04 % por ejecución) sin cambios. Uso: python3 c116_informativo_comision_unica.py DIR_SCRATCH"""
import sys, io, contextlib, runpy, numpy as np
SP = sys.argv[1]; sys.argv = ['x', SP]
with contextlib.redirect_stdout(io.StringIO()): g = runpy.run_path('c116_mejoras_cartera_cfd.py')
P0, X, volctl, sh, comp, o55 = g['P0'], g['X'], g['volctl'], g['sh'], g['comp'], g['o55']
P1 = P0.copy()
for nom, (a, quita) in g['pasan'].items(): P1 = P1 + a - (X[quita] if quita else 0)
AH = {'yen': (0.50, 10, 1), 'cesta_yen': (0.44, 10, 1 / 3), 'oro_D-2': (0.125, 33, 1), 'oro_video_C93': (0.125, 80, 0.2), 'oro_asia_C99': (0.125, 90, 0.2)}
P2 = P1.copy()
for c, (ah, sg, w) in AH.items():
    m = X[c] != 0; P2[m] += 0.005 * w * ah / sg
k4 = comp(o55, (0.74 + 0.58 + 0.10) * 1e-4, 1.0); P2[k4 != 0] += 0.005 * 0.125e-4 / o55.loc['2018-03-26':].std()   # oro viernes 16:55
for nom, P in (('Comisión por ejecución (actual)', P1), ('Comisión por operación completa', P2)):
    V = volctl(P); out = []
    for r in (0.5, 0.65, 0.8):
        p = V * r / 0.5; e = p.cumsum(); out.append(f'r{r}: {p.mean()*252*100:.1f} %/año (60 %: {0.6*p.mean()*252*100:.1f}), caída {(e-e.cummax()).min()*100:.1f} %')
    print(f'{nom:34s} Sharpe {sh(V):.2f} | ' + ' | '.join(out))
