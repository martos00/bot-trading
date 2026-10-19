"""H72 — evaluación pre-registrada (PREREGISTRO_H72_rebalanceo.md, secciones 6-7).

Uso: python3 h72_evaluacion.py H72_CSV
"""
import sys
import numpy as np
import pandas as pd
import statsmodels.api as sm
from scipy import stats

N_ENSAYOS = 81
VAR_SR_MIN_ANUAL = 0.5 ** 2
C_ES, C_ZN, C_CFD, FIN_CFD = 0.6e-4, 1.0e-4, 0.8e-4, 0.025
REP = ('1997-09-10', '2023-03-17')
OOS = ('2023-03-20', '2030-01-01')
rng = np.random.default_rng(20261019)


def t_nw(x):
    return sm.OLS(np.asarray(x, float), np.ones(len(x))).fit(cov_type='HAC', cov_kwds={'maxlags': 5}).tvalues[0]


def met(r):
    r = r.dropna()
    w = (1 + r).cumprod()
    return dict(n=len(r), anual_pct=r.mean() * 252 * 100, vol_pct=r.std() * np.sqrt(252) * 100,
                sharpe=r.mean() / r.std() * np.sqrt(252), t_nw=t_nw(r), max_dd_pct=(w / w.cummax() - 1).min() * 100,
                asimetria=stats.skew(r))


def dsr(r, var_sr):
    r = r.dropna().to_numpy()
    T, sr = len(r), r.mean() / r.std(ddof=1)
    g3, g4 = stats.skew(r), stats.kurtosis(r, fisher=False)
    v = max(var_sr, VAR_SR_MIN_ANUAL) / 252
    emc = 0.5772156649
    sr0 = np.sqrt(v) * ((1 - emc) * stats.norm.ppf(1 - 1 / N_ENSAYOS) + emc * stats.norm.ppf(1 - 1 / (N_ENSAYOS * np.e)))
    return stats.norm.cdf((sr - sr0) * np.sqrt(T - 1) / np.sqrt(1 - g3 * sr + (g4 - 1) / 4 * sr ** 2)), sr0 * np.sqrt(252)


def main():
    pd.set_option('display.width', 220)
    pd.set_option('display.float_format', lambda v: f'{v:8.3f}')
    d = pd.read_csv(sys.argv[1], index_col=0, parse_dates=True)
    d = d.loc['1997-09-10':]
    rot = d['w'].diff().abs().shift(1).fillna(0)          # rotación al cierre de t-1, pagada en t
    d['neto_fut'] = d['estr'] - rot * (C_ES + C_ZN)
    d['neto_cfd_rv'] = d['estr_rv'] - rot * C_CFD - d['w'].shift(1).abs() * FIN_CFD / 252
    print(f"Rotación media diaria |Δw|: {rot.mean():.3f}  (|w| medio {d['w'].abs().mean():.3f}, días con w=0 por la pata Calendar: n/a)")
    filas = []
    for tramo, (a, b) in {'REP 1997-2023': REP, 'OOS 2023-2026': OOS}.items():
        for col, nom in [('estr', 'H72a bruto'), ('neto_fut', 'H72a neto futuros'), ('estr_rv', 'H72b bruto (solo RV)'),
                         ('neto_cfd_rv', 'H72b neto CFD')]:
            filas.append(dict(tramo=tramo, serie=nom, **met(d[col].loc[a:b])))
    print(pd.DataFrame(filas).set_index(['tramo', 'serie']).to_string())
    x = d['estr'].loc[REP[0]:REP[1]]
    sin_crisis = x[~(((x.index >= '2008-09-01') & (x.index <= '2009-03-31')) | ((x.index >= '2020-03-01') & (x.index <= '2020-03-31')))]
    print(f"REP sin sep08-mar09 ni mar20 (paper: 0,90): Sharpe {met(sin_crisis)['sharpe']:.2f}")
    print('Integridad: el día 2001-09-17 recoge el cierre real del mercado tras el 11-S; REP sin ese día: Sharpe',
          round(met(x.drop(pd.Timestamp('2001-09-17'), errors='ignore'))['sharpe'], 3))
    for col in ['estr', 'neto_fut', 'neto_cfd_rv']:
        print(f'Por año ({col}, %):', (d[col].loc['2015':].groupby(d.loc['2015':].index.year).sum() * 100).round(1).to_dict())
    r = d['estr'].loc[OOS[0]:].to_numpy()
    sims = np.array([(rng.choice([-1, 1], len(r)) * r).mean() for _ in range(10000)])
    print(f'Signo aleatorio OOS (H72a bruto): p = {(sims >= r.mean()).mean():.4f}')
    var_sr = np.var([met(d[c].loc[OOS[0]:])['sharpe'] for c in ['estr', 'estr_rv']], ddof=1)
    for col in ['estr', 'neto_fut', 'neto_cfd_rv']:
        p, sr0 = dsr(d[col].loc[OOS[0]:], var_sr)
        print(f'DSR OOS {col}: {p:.4f} (SR0 exigido {sr0:.2f})')
    # contribución de cada señal en OOS (bruto, dos patas)
    th_only = (-d['threshold'] / 0.015 / 2).shift(1) * (d['r_sp'] - d['r_10y'])
    cal_only = (d['cal_mod'] / 2).shift(1) * (d['r_sp'] - d['r_10y'])
    for nom, s in [('Threshold', th_only), ('Calendar', cal_only)]:
        print(f'{nom}: REP Sharpe {met(s.loc[REP[0]:REP[1]])["sharpe"]:.2f}  OOS Sharpe {met(s.loc[OOS[0]:])["sharpe"]:.2f}')


if __name__ == '__main__':
    main()
