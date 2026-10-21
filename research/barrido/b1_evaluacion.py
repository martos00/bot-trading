"""B1 — evaluación según el pre-registro: descubrimiento 2010-2017 (|t| ≥ 3), confirmación 2018-2026-09 con Bonferroni,
neto del coste base t ≥ 2, ventaja ≥ 2 × coste, ≥ 6/9 años. Lee F1_<SIM>.csv y F2_<SIM>.csv de DIR.
Uso: python3 b1_evaluacion.py DIR"""
import os, sys
import numpy as np
import pandas as pd
from scipy import stats

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'fase72'))
from h80_evaluacion import t_nw  # noqa: E402

COSTE = {'GRXEUR': 0.8, 'UKXGBP': 1.2, 'JPXJPY': 2.5, 'ETXEUR': 3.5, 'FRXEUR': 1.5, 'AUXAUD': 1.2, 'HKXHKD': 3.5,
         'XAGUSD': 1.0, 'WTIUSD': 0.6, 'BCOUSD': 0.7, 'EURGBP': 1.0, 'EURCHF': 1.2, 'GBPJPY': 1.8, 'AUDJPY': 1.5,
         'NZDUSD': 1.4, 'USDCAD': 1.1, 'EURAUD': 2.0}
DESC, CONF = slice('2010-01-01', '2017-12-31'), slice('2018-01-01', '2026-09-30')

if __name__ == '__main__':
    d = sys.argv[1]
    datos, filas = {}, []
    for s in COSTE:
        for fam in ('F1', 'F2'):
            f = os.path.join(d, f'{fam}_{s}.csv')
            if not os.path.exists(f):
                continue
            x = pd.read_csv(f, index_col=0, parse_dates=True)
            for c in x.columns:
                datos[(s, c)] = x[c]
                y = x.loc[DESC, c].dropna()
                if len(y) < 250:
                    continue
                filas.append({'sim': s, 'regla': c, 'fam': fam, 'n_desc': len(y), 'desde': y.index.min().year,
                              'media_desc_pb': y.mean() * 1e4, 't_desc': t_nw(y.values)})
    f = pd.DataFrame(filas)
    print(f'Reglas evaluadas: {len(f)} ({(f.fam == "F1").sum()} F1, {(f.fam == "F2").sum()} F2)')
    print(f'Descubrimiento: |t| ≥ 2: {(f.t_desc.abs() >= 2).sum()} (por azar ≈ {0.0455 * len(f):.0f}); |t| ≥ 3: {(f.t_desc.abs() >= 3).sum()} (por azar ≈ {0.0027 * len(f):.1f})')
    sel = f[f.t_desc.abs() >= 3].copy()
    k = len(sel)
    tb = stats.norm.ppf(1 - 0.05 / max(k, 1))
    print(f'Pasan al tramo de confirmación: k = {k}; t de Bonferroni = {tb:.2f}\n')
    res = []
    for _, r in sel.iterrows():
        lado = np.sign(r.media_desc_pb)
        y = datos[(r.sim, r.regla)].loc[CONF].dropna() * lado
        c = COSTE[r.sim] / 1e4
        neto = y - c
        an = y.groupby(y.index.year).mean()
        tc, tn = t_nw(y.values), t_nw(neto.values)
        res.append({'sim': r.sim, 'regla': r.regla, 'lado': 'largo' if lado > 0 else 'corto',
                    'desc_pb': round(r.media_desc_pb * lado, 2), 't_desc': round(abs(r.t_desc), 2),
                    'conf_pb': round(y.mean() * 1e4, 2), 't_conf': round(tc, 2), 'neto_pb': round(neto.mean() * 1e4, 2),
                    't_neto': round(tn, 2), 'coste': COSTE[r.sim], 'años': f'{(an > 0).sum()}/{len(an)}',
                    'sharpe_neto': round(neto.mean() / neto.std() * np.sqrt(252), 2),
                    'c1': tc >= tb, 'c2': tn >= 2, 'c3': y.mean() * 1e4 >= 2 * COSTE[r.sim], 'c4': (an > 0).sum() >= 6})
    r = pd.DataFrame(res)
    if len(r):
        r['confirmada'] = r[['c1', 'c2', 'c3', 'c4']].all(axis=1)
        pd.set_option('display.width', 250); pd.set_option('display.max_columns', 30); pd.set_option('display.max_rows', 300)
        print(r.sort_values('t_conf', ascending=False).to_string(index=False))
        r.to_csv(os.path.join(d, 'b1_confirmacion.csv'), index=False)
        print(f'\nCONFIRMADAS: {int(r.confirmada.sum())}')
    f.to_csv(os.path.join(d, 'b1_descubrimiento.csv'), index=False)
