"""C32: London Fix 15 min, Frankfurt breakout, cointegración EUR/SEK–EUR/NOK (PREREGISTRO_C32)."""
import glob, os, sys
from datetime import datetime
from zoneinfo import ZoneInfo
import numpy as np, pandas as pd
from scipy import stats
from c1_certificacion import fxcm, en, t_nw
import c3_breedon_ranaldo as C3
LON, UTC, NY = ZoneInfo('Europe/London'), ZoneInfo('UTC'), ZoneInfo('America/New_York')
S = '/tmp/claude-0/-home-user-bot-trading/682335b1-28ae-5d18-9355-ce7f0f968722/scratchpad/'
COM, DESL = 0.45e-4, 0.1e-4
def carga(par):
    b, a = {}, {}
    for f in sorted(glob.glob(S + f'fxcm/{par}/{par}_*.csv.gz')):
        bb, aa = fxcm(f); b.update(bb); a.update(aa)
    return b, a
def ejec(b, a, t0, t1, lado):
    """rentabilidad ejecutable (ASK/BID reales) de una posición lado (+1 compra) de t0 a t1, menos comisión y deslizamiento."""
    b0, a0, b1, a1 = en(b, t0), en(a, t0), en(b, t1), en(a, t1)
    if np.isnan([b0, a0, b1, a1]).any(): return np.nan, np.nan
    bruto = lado * np.log(((b1 + a1) / 2) / ((b0 + a0) / 2))
    neto = (np.log(b1 / a0) if lado > 0 else np.log(b0 / a1)) - COM - 2 * DESL
    return bruto, neto
res = {}
# L
filas = {}
for par in ('EURUSD', 'GBPUSD'):
    b, a = carga(par)
    for d in pd.bdate_range('2012-01-03', '2026-09-30'):
        t0 = datetime(d.year, d.month, d.day, 15, 45, tzinfo=LON); t1 = t0.replace(hour=16, minute=0); t2 = t0.replace(hour=16, minute=15)
        g1, n1 = ejec(b, a, t0, t1, -1); g2, n2 = ejec(b, a, t1, t2, +1)
        if not np.isnan([g1, g2]).any(): filas.setdefault(d, []).append((g1 + g2, n1 + n2))
L = pd.DataFrame({d: np.mean(v, axis=0) for d, v in filas.items() if len(v) == 2}, index=['bruto', 'neto']).T
res['L London Fix'] = (L, '2012', '2018', '2019')
# F
ops = {}
for par in ('EURUSD', 'EURJPY'):
    b, a = carga(par)
    for d in pd.bdate_range('2012-01-03', '2026-09-30'):
        base = int(datetime(d.year, d.month, d.day, 6, tzinfo=UTC).timestamp()) // 60
        mids = [((b.get(base + k), a.get(base + k))) for k in range(0, 180)]
        if sum(x[0] is not None for x in mids[:60]) < 40: continue
        rango = [(x[0] + x[1]) / 2 for x in mids[:60] if x[0] is not None]
        hi, lo = max(rango), min(rango)
        if hi <= lo: continue
        lado = 0
        for k in range(60, 180):
            bb, aa = mids[k]
            if bb is None: continue
            m = (bb + aa) / 2
            if lado == 0:
                if m > hi: lado, ent, sp_e = +1, hi, aa - bb
                elif m < lo: lado, ent, sp_e = -1, lo, aa - bb
                if lado: stop = lo if lado > 0 else hi
            elif (lado > 0 and m <= stop) or (lado < 0 and m >= stop):
                sal, sp_s = stop, aa - bb; break
        else:
            if lado:
                last = [x for x in mids[150:180] if x[0] is not None]
                if not last: continue
                sal, sp_s = (last[-1][0] + last[-1][1]) / 2, last[-1][1] - last[-1][0]
        if lado == 0: continue
        bruto = lado * np.log(sal / ent); coste = (sp_e + sp_s) / 2 / ent + COM + 2 * DESL
        ops.setdefault(d, []).append((bruto, bruto - coste))
F = pd.DataFrame({d: np.mean(v, axis=0) for d, v in ops.items()}, index=['bruto', 'neto']).T
res['F Frankfurt breakout'] = (F, '2012', '2018', '2019')
# P
dias = pd.bdate_range('2010-01-04', '2026-09-30'); T = C3.instantes(dias, 'NY', 16)
px = {}
for p in ('EURSEK', 'EURNOK'):
    m, v = C3.cargar_histdata(S + 'hd_c20', p); px[p] = pd.Series(np.log(C3.precio(m, v, T)), index=dias)
X = pd.DataFrame(px).dropna()
beta = X.EURSEK.rolling(250).cov(X.EURNOK) / X.EURNOK.rolling(250).var()
s = X.EURSEK - beta.shift(1) * X.EURNOK
z = (s - s.rolling(60).mean().shift(1)) / s.rolling(60).std().shift(1)
tr, pos, dias_pos, ent_s = [], 0, 0, None
for i in range(len(X)):
    if np.isnan(z.iloc[i]): continue
    if pos == 0 and abs(z.iloc[i]) > 2:
        pos, dias_pos, ent = -np.sign(z.iloc[i]), 0, (X.EURSEK.iloc[i], X.EURNOK.iloc[i], beta.iloc[i - 1])
    elif pos != 0:
        dias_pos += 1
        if np.sign(z.iloc[i]) != -pos or dias_pos >= 20 or (pos * z.iloc[i] >= 0):
            ds = (X.EURSEK.iloc[i] - ent[0]) - ent[2] * (X.EURNOK.iloc[i] - ent[1])
            tr.append((X.index[i], pos * ds, pos * ds - 10e-4)); pos = 0
P = pd.DataFrame(tr, columns=['dia', 'bruto', 'neto']).set_index('dia')
res['P Cointegración SEK/NOK'] = (P, '2010', '2017', '2018')
ps, filas = [], []
for nom, (x, a0, a1, c0) in res.items():
    d, c = x.loc[a0:a1], x.loc[c0:'2026']; an = c.neto.groupby(c.index.year).sum()
    t = t_nw(c.neto.values); ps.append(1 - stats.norm.cdf(t)); filas.append((nom, d, c, an, t))
orden = np.argsort(ps); ok = [False] * 3; seguir = True
for k, i in enumerate(orden):
    seguir = seguir and ps[i] <= 0.05 / (3 - k); ok[i] = seguir
for (nom, d, c, an, t), o in zip(filas, ok):
    coste = (c.bruto - c.neto).mean()
    cert = o and (an > 0).mean() >= 0.6 and c.bruto.mean() >= 3 * coste
    print(f'{nom}: descubrimiento n {len(d)} neto {d.neto.mean()*1e4:6.2f} pb (t {t_nw(d.neto.values):.2f}) | confirmación n {len(c)} '
          f'bruto {c.bruto.mean()*1e4:6.2f} pb neto {c.neto.mean()*1e4:6.2f} pb (t {t:.2f}) coste {coste*1e4:.2f} pb años+ {(an>0).sum()}/{len(an)} '
          f'| Holm {o} → {"CERTIFICADA" if cert else "no"}')
