"""H69 — evaluación pre-registrada (PREREGISTRO_H69_momentum_intradia.md, secciones 5-7).

Uso: python3 h69_evaluacion.py DIR_SALIDAS   (lee h69_SPXUSD.csv y h69_NSXUSD.csv del motor)
"""
import os, sys
import numpy as np
import pandas as pd
import statsmodels.api as sm
from scipy import stats

N_ENSAYOS = 72                 # 68 previos del proyecto + 4 de esta familia
VAR_SR_MIN_ANUAL = 0.5 ** 2    # mínimo conservador de la varianza de Sharpe entre ensayos
COSTES = {'SPXUSD': [0.40, 0.65], 'NSXUSD': [0.90, 1.40]}   # puntos por ida y vuelta
PERIODOS = {'P1 2010-2013': ('2010', '2013'), 'P2 2014-may2020': ('2014', '2020-05-31'),
            'P3 jun2020-2026': ('2020-06-01', '2026')}
rng = np.random.default_rng(20261019)


def hac_t(y, x=None, lags=5):
    X = np.ones((len(y), 1)) if x is None else sm.add_constant(x)
    r = sm.OLS(y, X).fit(cov_type='HAC', cov_kwds={'maxlags': lags})
    return r.params, r.tvalues, r.rsquared


def sharpe_anual(r):
    return r.mean() / r.std(ddof=1) * np.sqrt(252) if r.std() > 0 else np.nan


def dsr(r, sr_ensayos_anual):
    """Deflated Sharpe Ratio (Bailey & López de Prado 2014), con Sharpe por observación."""
    T = len(r)
    sr = r.mean() / r.std(ddof=1)
    g3, g4 = stats.skew(r), stats.kurtosis(r, fisher=False)
    var_sr = max(np.var(sr_ensayos_anual, ddof=1), VAR_SR_MIN_ANUAL) / 252
    emc = 0.5772156649
    sr0 = np.sqrt(var_sr) * ((1 - emc) * stats.norm.ppf(1 - 1 / N_ENSAYOS) + emc * stats.norm.ppf(1 - 1 / (N_ENSAYOS * np.e)))
    z = (sr - sr0) * np.sqrt(T - 1) / np.sqrt(1 - g3 * sr + (g4 - 1) / 4 * sr ** 2)
    return stats.norm.cdf(z), sr0 * np.sqrt(252)


def resumen(r):
    p, t, _ = hac_t(r.to_numpy())
    return dict(n=len(r), media_pb=r.mean() * 1e4, t_hac=t[0], sr_anual=sharpe_anual(r),
                pct_pos=(r > 0).mean() * 100, anual_pct=r.mean() * 252 * 100)


def evaluar(df, sim, senal):
    d = df[df.completo & (df[senal] != 0)].copy()
    pos = np.sign(d[senal])
    d['estr'] = pos * d['r_LH']
    filas = []
    b, tb, r2 = hac_t(d['r_LH'].to_numpy(), d[senal].to_numpy())
    print(f'\n=== {sim} | señal {senal} | regresión r_LH ~ señal: b={b[1]:.4f} t_HAC={tb[1]:.2f} R2={r2*100:.2f}%')
    tramos = {'TOTAL': d.index}
    tramos.update({k: d.loc[a:z].index for k, (a, z) in PERIODOS.items()})
    for nombre, idx in tramos.items():
        x = d.loc[idx]
        fila = dict(tramo=nombre, **resumen(x['estr']))
        fila['always_long_pb'] = x['r_LH'].mean() * 1e4
        # coste de equilibrio y netos (coste en puntos -> log-rentabilidad aprox. coste/precio)
        fila['equilibrio_pb'] = x['estr'].mean() * 1e4
        for c in COSTES[sim]:
            neta = x['estr'] - c / x['p1530']
            fila[f'neta_{c}pt_pb'] = neta.mean() * 1e4
            fila[f'neta_{c}pt_t'] = hac_t(neta.to_numpy())[1][0]
        fila['coste_pb_0.40pt' if sim == 'SPXUSD' else 'coste_pb_0.90pt'] = (COSTES[sim][0] / x['p1530']).mean() * 1e4
        filas.append(fila)
    tabla = pd.DataFrame(filas).set_index('tramo')
    # benchmark de signo aleatorio (10.000 permutaciones) sobre el total
    r_lh = d['r_LH'].to_numpy()
    medias = np.array([(rng.choice([-1, 1], len(r_lh)) * r_lh).mean() for _ in range(10000)])
    p_aleat = (medias >= d['estr'].mean()).mean()
    # beta frente a always-long
    bb, tbb, _ = hac_t(d['estr'].to_numpy(), r_lh)
    # por año
    anual = d.groupby(d.index.year)['estr'].agg(lambda s: s.mean() * 1e4)
    return tabla, p_aleat, (bb[0] * 1e4, tbb[0], bb[1]), anual, d


def main():
    out = sys.argv[1]
    pd.set_option('display.width', 250)
    pd.set_option('display.float_format', lambda v: f'{v:8.3f}')
    resultados, series = {}, {}
    for sim in ['SPXUSD', 'NSXUSD']:
        df = pd.read_csv(os.path.join(out, f'h69_{sim}.csv'), index_col=0, parse_dates=True)
        for senal in ['r_ROD', 'r_ONFH']:
            tabla, p_aleat, (alfa_pb, t_alfa, beta), anual, d = evaluar(df, sim, senal)
            print(tabla.to_string())
            print(f'  signo aleatorio: p(media >= observada) = {p_aleat:.4f}')
            print(f'  alfa frente a always-long: {alfa_pb:.3f} pb/día (t_HAC={t_alfa:.2f}), beta={beta:.3f}')
            print('  media bruta por año (pb):', anual.round(2).to_dict())
            resultados[(sim, senal)] = tabla
            series[(sim, senal)] = d['estr']
    sr_ensayos = [sharpe_anual(s) for s in series.values()]
    print('\nSharpe anual bruto de los 4 ensayos:', np.round(sr_ensayos, 3))
    for k, s in series.items():
        p, sr0 = dsr(s, sr_ensayos)
        cost = COSTES[k[0]][1]
        dfk = pd.read_csv(os.path.join(out, f'h69_{k[0]}.csv'), index_col=0, parse_dates=True).loc[s.index]
        neta = s - cost / dfk['p1530']
        pn, _ = dsr(neta, sr_ensayos)
        print(f'DSR {k}: bruto={p:.4f}  neto({cost}pt)={pn:.4f}  (SR0 anual exigido={sr0:.2f}, SR bruto={sharpe_anual(s):.2f}, SR neto={sharpe_anual(neta):.2f})')


if __name__ == '__main__':
    main()
