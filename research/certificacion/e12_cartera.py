"""E12: cesta no metálica en víspera de festivo (PREREGISTRO_E12) y cartera de 6 ventajas. Uso como e11b_cartera.py."""
import sys, io, contextlib
import numpy as np, pandas as pd
argv0 = list(sys.argv)
with contextlib.redirect_stdout(io.StringIO()):
    exec(open('e11b_cartera.py').read().rsplit("def sh(p): return", 1)[0])   # e1, oro, yen, plata, cesta yen (ej)
sys.argv = argv0
ns69 = {}
with contextlib.redirect_stdout(io.StringIO()):
    exec(open('c69_vispera_futuros.py').read().split('# las barras diarias')[0], ns69)
R69, PRE69 = ns69['R'], ns69['PRE']
NM = ['CL', 'HO', 'RB', 'NG', 'ZC', 'ZS', 'ZW', 'ZL', 'ZM', 'KE', 'LE', 'HE']
sdm = R69[NM].rolling(60, min_periods=40).std().shift(1)
w = (0.005 / len(NM)) / sdm                                   # igual riesgo por mercado
ret = (w * (R69[NM] - 5e-4)).reindex(PRE69).dropna(how='all').sum(axis=1)
ret = ret[ret != 0]; an = ret.groupby(ret.index.year).sum()
print(f'E12 sola (2010-26): n {len(ret)}, {ret.mean()*len(ret)/len(an)*100:.2f} %/año, Sharpe anual {ret.mean()/ret.std()*np.sqrt(len(ret)/len(an)):.2f}, años+ {(an>0).sum()}/{len(an)}')
def sh(p): return p.mean() / p.std() * np.sqrt(252)
e1x = pd.read_csv(sys.argv[2], index_col=0, parse_dates=True)
for ne, ce in (('E1 FTMO 0,79', 0.79), ('E1 bajo 0,44', 0.44)):
    e = construir(e1x, 0.005, ce).ret.loc['2018':]
    for co, cp in ((0.74, 2.3), (1.5, 4.0)):
        J = pd.concat([e.rename('e1'), oro(0.005, co).ret.loc['2018':].rename('oro'), yen.loc['2018':].rename('yen'), plata(cp).loc['2018':].rename('plata'),
                       ej.loc['2018':].rename('ej'), ret.loc['2018':].rename('fest')], axis=1).fillna(0)
        def cart(cols):
            q = J[cols].sum(axis=1); q = q * J.e1.std() / q.std(); eq = q.cumsum(); return sh(q), q.mean() * 252 * 100, (eq - eq.cummax()).min() * 100
        s5 = cart(['e1', 'oro', 'yen', 'plata', 'ej']); s6 = cart(['e1', 'oro', 'yen', 'plata', 'ej', 'fest'])
        print(f'  {ne} | oro {co}, plata {cp} → 5 ventajas {s5[0]:.2f} | 6 ventajas {s6[0]:.2f} ({s6[1]:.1f} %/año, DD {s6[2]:.1f} %)')
