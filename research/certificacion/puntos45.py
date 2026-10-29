import numpy as np, pandas as pd
def sh(s): return s.mean() / s.std() * np.sqrt(252)
def dd25(s):
    s = s * 0.25 / (s.mean() * 252); eq = s.cumsum(); return (eq - eq.cummax()).min() * 100
for nom in ('A', 'B'):
    C = pd.read_csv(f'componentes_{nom}.csv', index_col=0, parse_dates=True).loc['2018-03-26':]
    P = C.sum(axis=1); print(f'\n===== Cartera {nom}: Sharpe {sh(P):.2f}, caída máx. al 25 % {dd25(P):.1f} % =====')
    print('PUNTO 5 — cada estrategia: Sharpe propio (en sus días) | correlación con el resto | Sharpe de la cartera SIN ella | aporte')
    for k in C:
        x = C[k]; act = x[x != 0]; resto = P - x
        print(f'  {k:18s} ops/año {len(act)/8.5:5.0f} | Sharpe propio {act.mean()/act.std()*np.sqrt(len(act)/8.5):5.2f} | corr {np.corrcoef(x, resto)[0,1]:+.2f} | sin ella {sh(resto):.2f} | aporte {sh(P)-sh(resto):+.2f}')
    print('PUNTO 4 — formas de repartir el riesgo (comparadas en 2019-2026 para que las que usan el pasado tengan historia):')
    per = slice('2019-01-01', None)
    res = {'actual (0,5 % por op.; diarias al 20 %)': P}
    vol_full = C.std(); res['igual riesgo por estrategia (vol. de todo el periodo: mira el futuro)'] = (C / vol_full * vol_full.mean()).sum(axis=1)
    v_roll = C.rolling(252, min_periods=126).std().shift(1)
    w = (1 / v_roll).replace([np.inf], np.nan); w = w.div(w.sum(axis=1), axis=0) * len(C.columns)
    res['igual riesgo con vol. pasada (sin mirar el futuro)'] = (C * w * v_roll.mean(axis=1).values[:, None]).sum(axis=1)
    pv = P.rolling(60, min_periods=40).std().shift(1); tgt = P.std()
    res['actual + control de volatilidad de la cartera (60 días)'] = P * (tgt / pv).clip(0.5, 2)
    q = res['igual riesgo con vol. pasada (sin mirar el futuro)']; qv = q.rolling(60, min_periods=40).std().shift(1)
    res['igual riesgo pasado + control de volatilidad'] = q * (q.std() / qv).clip(0.5, 2)
    for k, v in res.items():
        v = v.loc[per].dropna(); print(f'  {k:62s} Sharpe {sh(v):.2f} | caída máx. al 25 % {dd25(v):5.1f} %')
