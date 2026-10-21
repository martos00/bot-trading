"""C35: base de los futuros del VIX (Simon-Campasano 2014). Ver PREREGISTRO_C35. Uso: python3 c35_base_vix.py DIR_VX VIX_HISTORY_CSV"""
import glob, os, sys
import numpy as np, pandas as pd
from c1_certificacion import t_nw
D, VIXF = sys.argv[1:3]
fut = {}
for f in sorted(glob.glob(os.path.join(D, 'VX_*.csv'))):
    venc = pd.Timestamp(os.path.basename(f)[3:13])
    x = pd.read_csv(f)
    x['Trade Date'] = pd.to_datetime(x['Trade Date'])
    s = x.set_index('Trade Date').Settle.astype(float)
    fut[venc] = s[s > 0]
vix = pd.read_csv(VIXF); vix.columns = [c.strip().upper() for c in vix.columns]
vix = pd.Series(vix.CLOSE.values, index=pd.to_datetime(vix.DATE)).sort_index()
dias = sorted(set().union(*[set(s.index) for s in fut.values()]))
dias = [d for d in dias if d >= pd.Timestamp('2013-01-02') and d <= pd.Timestamp('2026-09-30')]
vencs = sorted(fut)
filas, prev = [], None
for i, d in enumerate(dias[:-1]):
    d1 = dias[i + 1]
    if d not in vix.index: continue
    cand = [v for v in vencs if v > d and d in fut[v].index and d1 in fut[v].index]
    if not cand: continue
    v = cand[0]
    if np.busday_count(d.date(), v.date()) < 10:
        if len(cand) < 2: continue
        v = cand[1]
    bd = np.busday_count(d.date(), v.date())
    roll = (fut[v][d] - vix[d]) / bd
    pos = -1 if roll > 0.10 else (1 if roll < -0.10 else 0)
    pnl = pos * (fut[v][d1] - fut[v][d])
    coste = 0.05 if (pos != 0 and (prev is None or (pos, v) != prev)) else 0.0
    filas.append(dict(dia=d1, pos=pos, bruto=pnl, neto=pnl - coste, roll=roll))
    prev = (pos, v) if pos != 0 else None
t = pd.DataFrame(filas).set_index('dia')
print(f'días con posición: {(t.pos != 0).mean()*100:.0f}% (corto {(t.pos < 0).mean()*100:.0f}%, largo {(t.pos > 0).mean()*100:.0f}%)')
for a, b in (('2013', '2014'), ('2015', '2026')):
    y = t.loc[a:b]; an = y.neto.groupby(y.index.year).sum(); eq = y.neto.cumsum()
    print(f'{a}-{b}: media {y.neto.mean():.4f} puntos/día (t {t_nw(y.neto.values):.2f}), Sharpe anual {y.neto.mean()/y.neto.std()*np.sqrt(252):.2f}, '
          f'años+ {(an>0).sum()}/{len(an)}, peor día {y.neto.min():.2f} pt, caída máx {(eq-eq.cummax()).min():.1f} pt')
    print('   por año (puntos):', an.round(1).to_dict())
c = t.loc['2015':]; an = c.neto.groupby(c.index.year).sum()
crit = {'1 t>=2': c.neto.mean() > 0 and t_nw(c.neto.values) >= 2, '2 años>=60%': (an > 0).mean() >= 0.6}
print('CRITERIOS:', crit, '→ CERTIFICADA' if all(crit.values()) else '→ NO CERTIFICADA')
