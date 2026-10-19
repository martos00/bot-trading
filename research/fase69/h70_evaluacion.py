"""H70 — evaluación pre-registrada (PREREGISTRO_H70_trend_following.md, secciones 5-7).

Uso: python3 h70_evaluacion.py DIR_DATOS AQR_XLSX
"""
import os, sys
import numpy as np
import pandas as pd
import statsmodels.api as sm
from scipy import stats
import h70_motor as m

N_ENSAYOS = 73
VAR_SR_MIN_ANUAL = 0.5 ** 2
rng = np.random.default_rng(20261019)


def t_nw(x, lags=3):
    x = np.asarray(x, float)
    return sm.OLS(x, np.ones(len(x))).fit(cov_type='HAC', cov_kwds={'maxlags': lags}).tvalues[0]


def met(r):
    r = r.dropna()
    w = (1 + r).cumprod()
    return dict(meses=len(r), ret_anual=r.mean() * 12 * 100, vol=r.std() * np.sqrt(12) * 100,
                sharpe=r.mean() / r.std() * np.sqrt(12), t_nw=t_nw(r), max_dd=(w / w.cummax() - 1).min() * 100,
                pct_meses_pos=(r > 0).mean() * 100)


def dsr(r, var_sr_anual):
    r = r.dropna().to_numpy()
    T, sr = len(r), r.mean() / r.std(ddof=1)
    g3, g4 = stats.skew(r), stats.kurtosis(r, fisher=False)
    v = max(var_sr_anual, VAR_SR_MIN_ANUAL) / 12
    emc = 0.5772156649
    sr0 = np.sqrt(v) * ((1 - emc) * stats.norm.ppf(1 - 1 / N_ENSAYOS) + emc * stats.norm.ppf(1 - 1 / (N_ENSAYOS * np.e)))
    return stats.norm.cdf((sr - sr0) * np.sqrt(T - 1) / np.sqrt(1 - g3 * sr + (g4 - 1) / 4 * sr ** 2)), sr0 * np.sqrt(12)


def main():
    d, aqr_xlsx = sys.argv[1:3]
    pd.set_option('display.width', 220)
    pd.set_option('display.float_format', lambda v: f'{v:8.3f}')
    p = pd.read_csv(os.path.join(d, 'panel_excesos.csv'), index_col=0)
    p.index = pd.PeriodIndex(p.index, freq='M')
    cl = pd.read_csv(os.path.join(d, 'clases.csv'), index_col=0)['clase']
    aqr = pd.read_excel(aqr_xlsx, 'TSMOM Factors', header=17, index_col=0)
    aqr.index = pd.to_datetime(aqr.index).to_period('M')
    aqr = aqr.astype(float)

    r, w = m.hop(p, cl)
    n_mercados = w.shift(1).notna().sum(axis=1)
    inicio = n_mercados[n_mercados >= 15].index.min()
    print(f'Inicio PRE (primer mes con >=15 mercados posicionados): {inicio}')
    print('Mercados posicionados por década:', n_mercados.groupby(n_mercados.index.year // 10 * 10).mean().round(1).to_dict())
    r = r.loc[inicio:]
    netos = {e: (r - m.costes(w, p, cl, e).loc[inicio:]) for e in ['futuros', 'cfd']}
    lev = w.shift(1).abs().sum(axis=1).loc[inicio:]
    print(f'Nocional bruto medio / NAV: {lev.mean():.2f}x (p90 {lev.quantile(.9):.2f}x); por clase:',
          {c: round(w[cl[cl == c].index].shift(1).abs().sum(axis=1).loc[inicio:].mean(), 2) for c in ['EQ', 'BD', 'FX', 'CM']})

    largo, _ = m.hop(p, cl, signo_fijo=1)
    largo = largo.loc[inicio:]
    tramos = {'PRE': (inicio, pd.Period('2011-12', 'M')), 'POST': (pd.Period('2012-01', 'M'), r.index.max())}
    filas = []
    for nom, (a, b) in tramos.items():
        filas.append(dict(serie='H70 bruto', tramo=nom, **met(r.loc[a:b])))
        filas.append(dict(serie='H70 neto futuros', tramo=nom, **met(netos['futuros'].loc[a:b])))
        filas.append(dict(serie='H70 neto CFD', tramo=nom, **met(netos['cfd'].loc[a:b])))
        filas.append(dict(serie='Siempre largo (mismos pesos de riesgo)', tramo=nom, **met(largo.loc[a:b])))
        filas.append(dict(serie='AQR TSMOM (bruto, 58 futuros)', tramo=nom, **met(aqr['TSMOM'].loc[a:b])))
    print(pd.DataFrame(filas).set_index(['tramo', 'serie']).to_string())

    jj = pd.concat([r.rename('h70'), aqr['TSMOM']], axis=1).dropna()
    print(f"\nCorrelación H70 bruto vs AQR TSMOM: total {jj.h70.corr(jj.TSMOM):.3f}; POST {jj.loc['2012':].h70.corr(jj.loc['2012':].TSMOM):.3f}")
    eq = p['EQ_SP500'].loc[inicio:]
    print(f'Correlación con S&P 500 (exceso): {r.corr(eq):.3f}; POST {r.loc["2012":].corr(eq.loc["2012":]):.3f}')

    # Sharpe por clase y por señal (bruto), POST y PRE
    print('\nSharpe bruto por clase (contribución de cada clase a la cartera):')
    for c in ['EQ', 'BD', 'FX', 'CM']:
        cols = cl[cl == c].index
        rc = (w[cols].shift(1) * p[cols]).sum(axis=1, min_count=1).loc[inicio:]
        print(f'  {c}: PRE {met(rc.loc[:"2011-12"])["sharpe"]:.2f}  POST {met(rc.loc["2012-01":])["sharpe"]:.2f}')
    print('Sharpe bruto por señal individual (misma construcción, un solo lookback):')
    guard = m.LOOKBACKS
    for k in guard:
        m.LOOKBACKS = (k,)
        rk, _ = m.hop(p, cl)
        rk = rk.loc[inicio:]
        print(f'  {k:>2}m: PRE {met(rk.loc[:"2011-12"])["sharpe"]:.2f}  POST {met(rk.loc["2012-01":])["sharpe"]:.2f}')
    m.LOOKBACKS = guard

    # Control de signo aleatorio (POST, bruto): 5.000 matrices de signos aleatorios
    post = slice(pd.Period('2012-01', 'M'), None)
    sr_obs = met(r.loc[post])['sharpe']
    s_ref = m.senal_hop(p)
    sims = []
    for _ in range(5000 if os.environ.get('H70_SIMS') is None else int(os.environ['H70_SIMS'])):
        signos = pd.DataFrame(rng.choice([-1.0, 1.0], size=s_ref.shape), index=s_ref.index, columns=s_ref.columns)
        rs, _ = m.hop(p, cl, signo_fijo=signos)
        x = rs.loc[post].dropna()
        sims.append(x.mean() / x.std() * np.sqrt(12))
    sims = np.array(sims)
    print(f'\nSigno aleatorio POST: Sharpe observado {sr_obs:.3f}; p(simulado >= observado) = {(sims >= sr_obs).mean():.4f}; '
          f'media simulada {sims.mean():.3f}, p95 {np.quantile(sims, .95):.3f}')

    var_sr = np.var([met(r.loc[post])['sharpe'], met(r.loc[:'2011-12'])['sharpe']], ddof=1)
    for nom, serie in [('bruto', r), ('neto futuros', netos['futuros']), ('neto CFD', netos['cfd'])]:
        for tr, sl in [('POST', post), ('TOTAL', slice(None))]:
            pdsr, sr0 = dsr(serie.loc[sl], var_sr)
            print(f'DSR {nom} {tr}: {pdsr:.4f} (SR0 exigido {sr0:.2f}, SR {met(serie.loc[sl])["sharpe"]:.2f})')
    print('\nRentabilidad neta futuros por año (POST, %):', (netos['futuros'].loc[post].groupby(lambda x: x.year).sum() * 100).round(1).to_dict())
    print('Rentabilidad neta CFD por año (POST, %):', (netos['cfd'].loc[post].groupby(lambda x: x.year).sum() * 100).round(1).to_dict())
    pd.DataFrame({'bruto': r, 'neto_futuros': netos['futuros'], 'neto_cfd': netos['cfd'], 'siempre_largo': largo}).to_csv(
        os.path.join(d, 'h70_series_mensuales.csv'))


if __name__ == '__main__':
    main()
