"""H71 — evaluación pre-registrada (PREREGISTRO_H71_fixings_fx.md, secciones 5-7).

Uso: python3 h71_evaluacion.py DIR_SALIDAS [SPREADS_CSV]
  DIR_SALIDAS contiene h71_<PAR>.csv del motor; SPREADS_CSV es la salida de h71_spreads_dukascopy.py.
"""
import os, sys
import numpy as np
import pandas as pd
import statsmodels.api as sm
from scipy import stats

PARES = ['EURUSD', 'GBPUSD', 'USDJPY']
N_ENSAYOS = 79
VAR_SR_MIN_ANUAL = 0.5 ** 2
COMISION_PB, DESLIZ_PB = 0.35, 0.10            # por lado
PIP_PB_ESTANDAR = {'EURUSD': 1.0, 'GBPUSD': 1.5, 'USDJPY': 1.0}   # pips de spread fijo en cuenta estándar
rng = np.random.default_rng(20261019)


def t_nw(x, lags=5):
    return sm.OLS(np.asarray(x, float), np.ones(len(x))).fit(cov_type='HAC', cov_kwds={'maxlags': lags}).tvalues[0]


def met(r):
    r = r.dropna()
    w = r.cumsum()
    return dict(n=len(r), media_pb=r.mean() * 1e4, t_nw=t_nw(r), pct_pos=(r > 0).mean() * 100,
                anual_pct=r.mean() * 252 * 100, sharpe=r.mean() / r.std() * np.sqrt(252), max_dd_pct=(w - w.cummax()).min() * 100)


def dsr(r, var_sr_anual):
    r = r.dropna().to_numpy()
    T, sr = len(r), r.mean() / r.std(ddof=1)
    g3, g4 = stats.skew(r), stats.kurtosis(r, fisher=False)
    v = max(var_sr_anual, VAR_SR_MIN_ANUAL) / 252
    emc = 0.5772156649
    sr0 = np.sqrt(v) * ((1 - emc) * stats.norm.ppf(1 - 1 / N_ENSAYOS) + emc * stats.norm.ppf(1 - 1 / (N_ENSAYOS * np.e)))
    return stats.norm.cdf((sr - sr0) * np.sqrt(T - 1) / np.sqrt(1 - g3 * sr + (g4 - 1) / 4 * sr ** 2)), sr0 * np.sqrt(252)


def coste_dia(par, est, spreads, precio, escenario):
    """Coste diario en fracción (2 tramos de ida y vuelta)."""
    lado = (COMISION_PB + DESLIZ_PB) * 1e-4
    if escenario == 'estandar':
        pip = 0.01 if par.endswith('JPY') else 0.0001
        sp = PIP_PB_ESTANDAR[par] * pip / precio      # spread fijo por ida y vuelta
        return 2 * sp
    if spreads is None:
        return None
    s = spreads.loc[(par if par in spreads.index.get_level_values(0) else 'EURUSD', est)]['mediana_pb']
    mult = 2.0 if escenario == 'estres' else 1.0
    if est == 'EUROPA':
        sp_pb = (s['t1a'] + s['t1b']) / 2 + (s['t2a'] + s['t2b']) / 2
    else:  # TOKIO: el instante 09:55 Tokio es común a los dos tramos; los extremos se toman como el de Europa 08:00
        sp_pb = (spreads.loc[(par if par in spreads.index.get_level_values(0) else 'EURUSD', 'EUROPA')]['mediana_pb']['t2b'] + s['t1b']) / 2 \
            + (s['t1b'] + spreads.loc[(par if par in spreads.index.get_level_values(0) else 'EURUSD', 'EUROPA')]['mediana_pb']['t1a']) / 2
    if par == 'USDJPY' and 'USDJPY' not in spreads.index.get_level_values(0):
        sp_pb *= 1.5   # aproximación declarada en el pre-registro
    return mult * sp_pb * 1e-4 + 4 * lado


def main():
    out = sys.argv[1]
    spreads = None
    if len(sys.argv) > 2 and os.path.exists(sys.argv[2]):
        spreads = pd.read_csv(sys.argv[2], index_col=[0, 1, 2])
    pd.set_option('display.width', 250)
    pd.set_option('display.float_format', lambda v: f'{v:8.3f}')
    series = {}
    for par in PARES:
        f = os.path.join(out, f'h71_{par}.csv')
        if not os.path.exists(f):
            continue
        df = pd.read_csv(f, parse_dates=['dia'])
        df = df[df.completo]
        for est in ['EUROPA', 'TOKIO']:
            d = df[df.estrategia == est].set_index('dia').sort_index()
            netas = {}
            for esc in ['ecn', 'estres', 'estandar']:
                c = coste_dia(par, est, spreads, d['p1a'], esc)
                if c is not None:
                    netas[esc] = d['r'] - c
            filas = []
            for tramo, (a, b) in {'REP 2003-2019': ('2003', '2019'), 'OOS 2020-2026': ('2020', '2026'),
                                  '  de ello 2024-2026': ('2024', '2026')}.items():
                filas.append(dict(tramo=tramo, serie='bruto', **met(d['r'].loc[a:b])))
                for esc, s in netas.items():
                    filas.append(dict(tramo=tramo, serie=f'neto {esc}', **met(s.loc[a:b])))
            print(f'\n===== {par} | {est} =====')
            print(pd.DataFrame(filas).set_index(['tramo', 'serie']).to_string())
            print('  tramo 1 / tramo 2 bruto OOS (pb/día):', round(d['r1'].loc['2020':].mean() * 1e4, 3), '/', round(d['r2'].loc['2020':].mean() * 1e4, 3))
            print('  bruto por año (pb/día):', (d['r'].groupby(d.index.year).mean() * 1e4).round(2).to_dict())
            for esc, s in netas.items():
                print(f'  neto {esc} por año (pb/día):', (s.loc['2020':].groupby(s.loc['2020':].index.year).mean() * 1e4).round(2).to_dict())
            r = d['r'].loc['2020':].to_numpy()
            sims = np.array([(rng.choice([-1, 1], len(r)) * r).mean() for _ in range(10000)])
            print(f'  signo aleatorio OOS: p = {(sims >= r.mean()).mean():.4f}')
            series[(par, est)] = (d['r'], netas)
    sr = [met(v[0].loc['2020':])['sharpe'] for v in series.values()]
    var_sr = np.var(sr, ddof=1) if len(sr) > 1 else 0
    print('\nSharpe bruto OOS de los ensayos:', dict(zip([f'{k[0]}-{k[1]}' for k in series], np.round(sr, 2))))
    for k, (bruto, netas) in series.items():
        texto = [f'bruto {dsr(bruto.loc["2020":], var_sr)[0]:.4f}']
        for esc, s in netas.items():
            texto.append(f'{esc} {dsr(s.loc["2020":], var_sr)[0]:.4f}')
        print(f'DSR OOS {k}:', ', '.join(texto), f'(SR0 exigido {dsr(bruto.loc["2020":], var_sr)[1]:.2f})')


if __name__ == '__main__':
    main()
