"""C117 — ETH 21-23 UTC en la cartera CFD (preregistro PREREGISTRO_C117_cripto_cfd.md). Uso: python3 c117_cripto_cfd.py DIR_SCRATCH"""
import sys, io, glob, zipfile, contextlib, runpy, numpy as np, pandas as pd
SP = sys.argv[1]; sys.argv = ['x', SP]
with contextlib.redirect_stdout(io.StringIO()): g = runpy.run_path('c116_mejoras_cartera_cfd.py')
P0, X, comp, volctl, sh, tstat, btc = g['P0'], g['X'], g['comp'], g['volctl'], g['sh'], g['tstat'], g['btc']
pas = g['pasan']; P1 = P0.copy()
for nom, (a, quita) in pas.items(): P1 = P1 + a - (X[quita] if quita else 0)     # base C116 (bitcoin 0,2 + oro 16:55)
rows = []
for f in sorted(glob.glob(f'{SP}/bn/eth1h/ETHUSDT-1h-*.zip')):
    with zipfile.ZipFile(f) as z: rows.append(pd.read_csv(io.BytesIO(z.read(z.namelist()[0])), header=None, usecols=[0, 1]))
b = pd.concat(rows); t = b[0].astype('int64'); t = np.where(t > 1e14, t // 1000, t)
o = pd.Series(b[1].astype(float).values, index=pd.to_datetime(t, unit='ms')); o = o[~o.index.duplicated()]
o21 = o[o.index.hour == 21]; o23 = o[o.index.hour == 23]; o21.index = o21.index.normalize(); o23.index = o23.index.normalize()
eth = np.log(o23 / o21).dropna(); eth = eth[eth.index.dayofweek < 5]
V1 = volctl(P1)
print(f'BASE C116: Sharpe {sh(V1):.2f} | 2018-21 {sh(V1.loc[:"2021"]):.2f} | 2022-26 {sh(V1.loc["2022":]):.2f}')
btc02 = comp(btc, 1.2e-4, 0.2)
cases = {'N1 + ETH peso 0,2 (1,5 pb)': P1 + comp(eth, 1.5e-4, 0.2),
         'N2 cesta BTC 0,1 + ETH 0,1': P1 - btc02 + comp(btc, 1.2e-4, 0.1) + comp(eth, 1.5e-4, 0.1),
         '(informativo) N1 con ETH a 3 pb': P1 + comp(eth, 3e-4, 0.2)}
rr = eth.loc['2018-03-26':] - 1.5e-4; tt, n = tstat(rr); print(f'ETH neto 1,5 pb: {rr.mean()*1e4:+.2f} pb/op (t {tt:.2f}, n {n}); 2022-26 {rr.loc["2022":].mean()*1e4:+.2f} pb; corr. BTC {eth.corr(btc):.2f}')
for nom, P in cases.items():
    V = volctl(P); d = (sh(V) - sh(V1), sh(V.loc[:'2021']) - sh(V1.loc[:'2021']), sh(V.loc['2022':]) - sh(V1.loc['2022':]))
    ok = d[0] >= 0.05 and d[1] > 0 and d[2] > 0 and tt >= 1.96
    print(f'{nom:34s} ΔSharpe {d[0]:+.2f} (18-21 {d[1]:+.2f}, 22-26 {d[2]:+.2f}) | Sharpe {sh(V):.2f} | {"PASA" if ok and not nom.startswith("(") else ("" if nom.startswith("(") else "NO PASA")}')
