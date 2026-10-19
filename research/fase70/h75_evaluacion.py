"""H75 — evaluación pre-registrada (PREREGISTRO_H75_connors.md, secciones 4-5).

Uso: python3 h75_evaluacion.py DIR_H75
"""
import glob, os, sys
import numpy as np
import pandas as pd
import statsmodels.api as sm
from scipy import stats

N_ENSAYOS = 88
TRAMOS = {'IS 1995-2007': ('1995', '2007'), 'OOS 2008-2026': ('2008', '2026')}
rng = np.random.default_rng(20261019)


def met_ops(o):
    if len(o) == 0:
        return dict(n=0)
    g, p = o.ret[o.ret > 0].sum(), -o.ret[o.ret < 0].sum()
    t = sm.OLS(o.ret.to_numpy(), np.ones(len(o))).fit().tvalues[0] if len(o) > 2 else np.nan
    return dict(n=len(o), pct_gan=(o.ret > 0).mean() * 100, media_op_pct=o.ret.mean() * 100, t_op=t,
                pf=g / p if p > 0 else np.inf, dias_med=o.dias.mean())


def met_cap(r):
    w = (1 + r).cumprod()
    return dict(cagr=(w.iloc[-1] ** (252 / len(r)) - 1) * 100, sharpe=r.mean() / r.std() * np.sqrt(252),
                mdd=(w / w.cummax() - 1).min() * 100, exposicion=None)


def aleatorio(d, ops, n_sim=1000):
    """Misma cantidad de operaciones y misma duración, con entradas al azar en días SPY>SMA200 (o <, si es corto)."""
    if len(ops) == 0:
        return np.nan
    r = d['r_spy'].fillna(0).to_numpy()
    lado = np.sign(d['pos'].replace(0, np.nan).dropna().iloc[0]) if (d['pos'] != 0).any() else 1
    filtro = d['tendencia_ok'].to_numpy()[:-1]
    idx_ok = np.arange(len(d) - 1)[filtro]
    medias = []
    dur = ops.dias.to_numpy()
    for _ in range(n_sim):
        ini = rng.choice(idx_ok, len(dur))
        rets = [lado * (np.prod(1 + r[i + 1:min(i + 1 + k, len(r))]) - 1) for i, k in zip(ini, dur)]
        medias.append(np.mean(rets))
    return (np.array(medias) >= ops.ret.mean()).mean()


def dsr(r, var_sr):
    r = r.to_numpy()
    T, sr = len(r), r.mean() / r.std(ddof=1)
    g3, g4 = stats.skew(r), stats.kurtosis(r, fisher=False)
    v = max(var_sr, 0.25) / 252
    emc = 0.5772156649
    sr0 = np.sqrt(v) * ((1 - emc) * stats.norm.ppf(1 - 1 / N_ENSAYOS) + emc * stats.norm.ppf(1 - 1 / (N_ENSAYOS * np.e)))
    return stats.norm.cdf((sr - sr0) * np.sqrt(T - 1) / np.sqrt(1 - g3 * sr + (g4 - 1) / 4 * sr ** 2))


def main():
    base = sys.argv[1]
    pd.set_option('display.width', 250)
    pd.set_option('display.float_format', lambda v: f'{v:8.3f}')
    filas, srs = [], {}
    for f in sorted(glob.glob(os.path.join(base, '*_diario.csv'))):
        nom = os.path.basename(f).replace('_diario.csv', '')
        d = pd.read_csv(f, index_col=0, parse_dates=True)
        # filtro del benchmark (pre-registro): días con SPY por encima (largos) o por debajo (corto) de su SMA200,
        # reconstruido con el precio total (la diferencia con el precio sin ajustar no cambia el filtro en la práctica)
        nivel = (1 + d['r_spy'].fillna(0)).cumprod()
        sobre = (nivel > nivel.rolling(200).mean()).to_numpy()
        d['tendencia_ok'] = ~sobre if nom.startswith('H75d') else sobre
        for col in ('bruto', 'neto_etf', 'neto_cfd'):
            ops = pd.read_csv(os.path.join(base, f'{nom}_ops_{col}.csv'), parse_dates=['entrada', 'salida'])
            for tramo, (a, b) in TRAMOS.items():
                o = ops[(ops.entrada >= a) & (ops.entrada <= f'{b}-12-31')]
                r = d[col].loc[a:b].fillna(0)
                fila = dict(estrategia=nom, coste=col, tramo=tramo, **met_ops(o), **met_cap(r),
                            expos=(d['pos'].loc[a:b] != 0).mean() * 100)
                if col == 'neto_cfd' and tramo.startswith('OOS'):
                    fila['p_aleatorio'] = aleatorio(d.loc[a:b], o)
                    srs[nom] = r
                filas.append(fila)
    t = pd.DataFrame(filas).drop(columns=['exposicion'])
    print(t.set_index(['estrategia', 'coste', 'tramo']).to_string())
    spy = pd.read_csv(f, index_col=0, parse_dates=True)['r_spy']
    for tramo, (a, b) in TRAMOS.items():
        print(f'SPY comprar y mantener {tramo}:', {k: round(v, 2) for k, v in met_cap(spy.loc[a:b].fillna(0)).items() if v is not None})
    var = np.var([met_cap(r)['sharpe'] for r in srs.values()], ddof=1)
    for k, r in srs.items():
        print(f'DSR OOS neto CFD {k}: {dsr(r, var):.4f}')


if __name__ == '__main__':
    main()
