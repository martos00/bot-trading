"""Certificación C2 — franja 21-23 UTC en ETHUSDT (PREREGISTRO_C2_cripto_21_23utc.md).
Uso: python3 c2_certificacion.py C2_ETH_1H.csv H78_BTC_1H.csv"""
import sys
import numpy as np
import pandas as pd


def t_nw(x, L=5):
    x = np.asarray(x, float); x = x[~np.isnan(x)]; n = len(x); e = x - x.mean()
    g = [e[k:] @ e[:n - k] / n for k in range(L + 1)]
    return x.mean() / np.sqrt((g[0] + 2 * sum((1 - k / (L + 1)) * g[k] for k in range(1, L + 1))) / n)


def leer(f):
    d = pd.read_csv(f, index_col=0, parse_dates=True)
    d.index = d.index.tz_localize(None) if d.index.tz is not None else d.index
    return d


if __name__ == '__main__':
    e, b = leer(sys.argv[1]), leer(sys.argv[2])
    horas = [c for c in e.columns if c.startswith('h')]
    post = e.loc['2022-02-04':'2026-09-30']
    r = post.regla.dropna()
    t = t_nw(r)
    print(f'E1 ETH post-publicación: n {len(r)}, media {r.mean() * 1e4:.2f} pb, t_NW {t:.2f} →', 'CUMPLE' if r.mean() > 0 and t >= 2 else 'NO CUMPLE')
    M = post[horas].to_numpy()
    rng = np.random.default_rng(2)
    sims = np.array([np.nanmean(M[np.arange(len(M)), rng.integers(0, 24, len(M))]) for _ in range(10_000)])
    p = (sims >= r.mean()).mean()
    print(f'E2 control hora aleatoria: p = {p:.4f} (media simulada {sims.mean() * 1e4:.2f} pb) →', 'CUMPLE' if p < 0.05 else 'NO CUMPLE')
    a = r.groupby(r.index.year).mean() * 1e4
    print('E3 por año (pb):', a.round(2).to_dict(), f'positivos {(a > 0).sum()}/{len(a)} →', 'CUMPLE' if (a > 0).sum() >= 3 else 'NO CUMPLE')
    j = pd.concat([r.rename('eth'), b.loc['2022-02-04':'2026-09-30', 'regla'].rename('btc')], axis=1, join='inner').dropna()
    pre = e.loc[:'2022-02-03', 'regla'].dropna()
    print(f'E4 informativo: correlación diaria ETH-BTC en la franja {j.corr().iat[0, 1]:.2f}; '
          f'ETH antes de la publicación (2017-08 → 2022-02): media {pre.mean() * 1e4:.2f} pb, t {t_nw(pre):.2f}')
    print('Media por hora de inicio en ETH post-publicación (pb):', (post[horas].mean() * 1e4).round(1).to_dict())
