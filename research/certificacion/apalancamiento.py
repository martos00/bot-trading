import numpy as np, pandas as pd
X = pd.read_csv('carteras_v4.csv', index_col=0, parse_dates=True)
rng = np.random.default_rng(3); B = 20; N = 4000
def caminos(x, n):
    st = rng.integers(0, len(x) - B, (N, n // B + 1)); return x[(st[:, :, None] + np.arange(B)).reshape(N, -1)[:, :n]]
for c, nom in (('B_volctl', 'B + control de volatilidad'), ('A_volctl', 'A + control de volatilidad')):
    x0 = X[c].dropna().values; x0 = x0 * 0.25 / (x0.mean() * 252)          # base: 25 %/año
    for haircut, et in ((1.0, 'Sharpe del backtest'), (0.6, 'Sharpe real = 60 % del backtest')):
        x = x0 - x0.mean() * (1 - haircut); mu, sd = x.mean() * 252, x.std() * np.sqrt(252); S = mu / sd
        kelly = mu / sd**2                                                   # multiplicador óptimo sobre el tamaño base
        print(f'\n=== {nom} | {et}: Sharpe {S:.2f}; Kelly = {kelly:.1f} veces el tamaño del 25 % ===')
        print('  apalancamiento (× tamaño 25 %) | rent. teórica simple | crecimiento anual mediano (compuesto) | 1 de cada 10 años peor que | P(perder >50 % en algún momento del año) | P(ruina, >90 %) en 3 años | caída máx. mediana 3 años')
        R1 = caminos(x, 252); R3 = caminos(x, 756)
        for L in (1, 2, 4, 0.5 * kelly, kelly, 1.5 * kelly, 2 * kelly):
            r1 = np.clip(L * R1, -0.999, None); e1 = np.cumprod(1 + r1, 1); g = e1[:, -1] - 1
            p50 = (e1.min(1) < 0.5).mean()
            r3 = np.clip(L * R3, -0.999, None); e3 = np.cumprod(1 + r3, 1); ruina = (e3.min(1) < 0.1).mean()
            dd3 = np.median((1 - e3 / np.maximum.accumulate(e3, 1)).max(1))
            print(f'  {L:5.1f}× | {L*25:6.0f} % | {np.median(g)*100:9.0f} % | {np.percentile(g,10)*100:7.0f} % | {p50*100:4.0f} % | {ruina*100:4.0f} % | {dd3*100:4.0f} %')
