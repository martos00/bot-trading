import numpy as np, pandas as pd
X = pd.read_csv('cartera_fut_diaria.csv', index_col=0, parse_dates=True)
rng = np.random.default_rng(7)
def boot(x, n, N, B=20):
    L = len(x); st = rng.integers(0, L - B, (N, n // B + 1)); idx = (st[:, :, None] + np.arange(B)).reshape(N, -1)[:, :n]; return x[idx]
def mdd(p): eq = p.cumsum(1); return (np.maximum.accumulate(np.maximum(eq, 0), 1) - eq).max(1)
def prop(x, k, N=20000, lim=0.04, obj=0.06, dias=252):
    p = boot(x * k, dias, N); eq = p.cumsum(1); hwm = np.minimum(np.maximum.accumulate(np.maximum(eq, 0), 1), lim)  # trailing que se bloquea en el saldo inicial
    quema = (eq <= hwm - lim); pasa = eq >= obj
    tq = np.where(quema.any(1), quema.argmax(1), 10**6); tp = np.where(pasa.any(1), pasa.argmax(1), 10**6)
    return (tp < tq).mean(), np.median(tp[tp < tq]) if (tp < tq).any() else np.nan, (tq < 10**6).mean()
for c in X:
    x = X[c].values; m = x.mean() * 252; v = x.std() * np.sqrt(252); k = 0.25 / m
    q = X[c] * k; eq = q.cumsum(); dd = (eq - eq.cummax()).min()
    an = q.groupby(q.index.year).sum(); me = q.resample('ME').sum()
    print(f'=== Cartera {c}: Sharpe {m/v:.2f}; para 25 %/año hay que multiplicar el riesgo estándar (0,5 % por operación) por {k:.2f} → {0.5*k:.2f} % por operación')
    print(f'  histórico 2018-26 a ese tamaño: volatilidad {v*k*100:.1f} %, caída máx {dd*100:.1f} %, peor año {an.min()*100:.1f} %, meses negativos {(me<0).mean()*100:.0f} %, peor mes {me.min()*100:.1f} %')
    print('  por año:', (an * 100).round(1).to_dict())
    p1 = boot(x * k, 252, 20000); r1 = p1.sum(1); d1 = mdd(p1)
    print(f'  simulación 1 año: rentabilidad mediana {np.median(r1)*100:.0f} %, 10 % peor {np.percentile(r1,10)*100:.0f} %, P(año negativo) {(r1<0).mean()*100:.1f} %, '
          f'P(caída >5/10/15/20 %) {(d1>.05).mean()*100:.0f}/{(d1>.10).mean()*100:.0f}/{(d1>.15).mean()*100:.0f}/{(d1>.20).mean()*100:.0f} %')
    p8 = boot(x * k, 252 * 8, 5000); d8 = mdd(p8); print(f'  simulación 8 años: caída máxima mediana {np.median(d8)*100:.0f} %, P(>10 %) {(d8>.10).mean()*100:.0f} %, P(>20 %) {(d8>.20).mean()*100:.0f} %')
    for objetivo in (0.25, 0.15, 0.10, 0.06):
        kk = objetivo / m; pa, td, qm = prop(x, kk)
        print(f'  cuenta de fondeo (pérdida máx. 4 % arrastrada, objetivo 6 %) operando para {objetivo*100:.0f} %/año ({0.5*kk:.2f} % por op.): '
              f'aprueba {pa*100:.0f} %, tarda {td/21:.1f} meses (mediana), quema la cuenta en 1 año {qm*100:.0f} %')
