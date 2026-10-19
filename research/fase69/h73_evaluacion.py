"""H73 — evaluación (PREREGISTRO_H73_usdjpy_tokio.md, sección 4) con los spreads medidos en Dukascopy.

Uso: python3 h73_evaluacion.py H71_USDJPY_CSV VALIDACION_CSV
  VALIDACION_CSV = salida de `h73_validacion_dukascopy.py medir`.
"""
import sys
import numpy as np
import pandas as pd
import statsmodels.api as sm

COMISION_PB, DESLIZ_PB = 0.35, 0.10


def t_nw(x):
    return sm.OLS(np.asarray(x, float), np.ones(len(x))).fit(cov_type='HAC', cov_kwds={'maxlags': 5}).tvalues[0]


def main():
    d = pd.read_csv(sys.argv[1], parse_dates=['dia'])
    d = d[(d.estrategia == 'TOKIO') & d.completo].set_index('dia').sort_index()
    v = pd.read_csv(sys.argv[2], parse_dates=['dia'])
    pd.set_option('display.float_format', lambda x: f'{x:8.3f}')
    for nombre, q in [('mediana', 0.5), ('p90', 0.9)]:
        s = {k: v[f'spread_{k}_pb'].quantile(q) for k in ['t1a', 't1b', 't2b']}
        # tramo 1: entra en t1a, sale en t1b; tramo 2: entra en t1b, sale en t2b; medio spread en cada extremo
        coste_pb = (s['t1a'] + s['t1b']) / 2 + (s['t1b'] + s['t2b']) / 2 + 4 * (COMISION_PB + DESLIZ_PB)
        neta = d['r'] - coste_pb * 1e-4
        x = neta.loc['2020':]
        print(f'\n== Coste con spread {nombre}: {coste_pb:.2f} pb/día '
              f"(spreads pb: 17:05NY {s['t1a']:.2f}, 09:55TOK {s['t1b']:.2f}, 08:00FRA {s['t2b']:.2f})")
        print(f'OOS 2020-2026 neto: {x.mean() * 1e4:.3f} pb/día, t_NW={t_nw(x):.2f}, Sharpe {x.mean() / x.std() * np.sqrt(252):.2f}, '
              f'{x.mean() * 252 * 100:.2f}%/año sobre nocional')
        anual = x.groupby(x.index.year).mean() * 1e4
        print('  por año (pb/día):', anual.round(2).to_dict(), f'-> años positivos {(anual > 0).sum()} de {len(anual)}')
        y = neta.loc['2003':'2019']
        print(f'REP 2003-2019 neto (con spreads actuales, solo referencia): {y.mean() * 1e4:.3f} pb/día, t={t_nw(y):.2f}')
    vol_d = d['r'].loc['2020':].std()
    print(f'\nVol diaria del bruto OOS: {vol_d * 1e4:.1f} pb -> nocional para 10% de vol anual = {0.10 / (vol_d * np.sqrt(252)):.2f}x el capital')


if __name__ == '__main__':
    main()
