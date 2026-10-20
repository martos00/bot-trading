"""H80 — evaluación según el pre-registro: descubrimiento 2010-2017 (|t| ≥ 3) y confirmación 2018-2026.
Uso: python3 h80_evaluacion.py DIR_CSV"""
import os, sys
import numpy as np
import pandas as pd
from scipy import stats

COSTE = {'SPXUSD': 1.5, 'NSXUSD': 1.0, 'XAUUSD': 1.5, 'EURUSD': 1.0, 'GBPUSD': 1.2, 'USDJPY': 1.0}   # pb ida y vuelta
DESC, CONF = slice('2010-01-01', '2017-12-31'), slice('2018-01-01', '2026-09-30')


def t_nw(x, L=5):
    x = np.asarray(x, float); x = x[~np.isnan(x)]; n = len(x); e = x - x.mean()
    g = [e[k:] @ e[:n - k] / n for k in range(L + 1)]
    return x.mean() / np.sqrt((g[0] + 2 * sum((1 - k / (L + 1)) * g[k] for k in range(1, L + 1))) / n)


if __name__ == '__main__':
    filas = []
    datos = {s: pd.read_csv(os.path.join(sys.argv[1], f'{s}.csv'), index_col=0, parse_dates=True) for s in COSTE}
    for s, d in datos.items():
        for c in d.columns:
            x = d.loc[DESC, c].dropna()
            filas.append({'sim': s, 'franja': c, 'n_desc': len(x), 'media_desc_pb': x.mean() * 1e4, 't_desc': t_nw(x)})
    f = pd.DataFrame(filas)
    print(f'Franjas evaluadas: {len(f)}')
    print('Distribución de t en descubrimiento (si no hubiera nada, ~N(0,1)):',
          f't medio {f.t_desc.mean():.2f}, desv. {f.t_desc.std():.2f}, |t|>=2: {(f.t_desc.abs() >= 2).sum()} (esperadas por azar ≈ {0.0455 * len(f):.0f}), '
          f'|t|>=3: {(f.t_desc.abs() >= 3).sum()} (≈ {0.0027 * len(f):.1f})')
    sel = f[f.t_desc.abs() >= 3.0].copy()
    k = len(sel)
    print(f'\nPasan el descubrimiento (|t| ≥ 3): k = {k}')
    if k:
        t_bonf = stats.norm.ppf(1 - 0.05 / k)
        print(f't de Bonferroni unilateral en confirmación: {t_bonf:.2f}\n')
        res = []
        for _, r in sel.iterrows():
            lado = np.sign(r.media_desc_pb)
            y = datos[r.sim].loc[CONF, r.franja].dropna() * lado
            neto = y - COSTE[r.sim] / 1e4
            anual = y.groupby(y.index.year).mean()
            res.append({'sim': r.sim, 'franja': r.franja, 'lado': 'largo' if lado > 0 else 'corto',
                        'media_desc_pb': round(r.media_desc_pb * lado, 2), 't_desc': round(abs(r.t_desc), 2),
                        'n_conf': len(y), 'media_conf_pb': round(y.mean() * 1e4, 2), 't_conf': round(t_nw(y), 2),
                        'neto_pb': round(neto.mean() * 1e4, 2), 't_neto': round(t_nw(neto), 2),
                        'coste_pb': COSTE[r.sim], 'años_pos': f'{(anual > 0).sum()}/{len(anual)}',
                        'c1_bonf': t_nw(y) >= t_bonf, 'c2_neto': t_nw(neto) >= 2, 'c3_coste': y.mean() * 1e4 >= 3 * COSTE[r.sim],
                        'c4_años': (anual > 0).sum() >= 6})
        res = pd.DataFrame(res)
        res['confirmada'] = res[['c1_bonf', 'c2_neto', 'c3_coste', 'c4_años']].all(axis=1)
        pd.set_option('display.width', 250); pd.set_option('display.max_columns', 30)
        print(res.sort_values('t_conf', ascending=False).to_string(index=False))
        res.to_csv(os.path.join(sys.argv[1], 'h80_confirmacion.csv'), index=False)
    f.to_csv(os.path.join(sys.argv[1], 'h80_descubrimiento.csv'), index=False)
