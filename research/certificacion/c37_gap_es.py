"""C37: reversión del hueco de apertura 16:00 → 09:30 en ES. Ver PREREGISTRO_C37. Uso: python3 c37_gap_es.py ES_1m.pkl"""
import sys
import numpy as np, pandas as pd
from c1_certificacion import t_nw
COSTE, TIC = 1.5e-4, 0.25
x = pd.read_pickle(sys.argv[1])
x.index = pd.to_datetime(x.ts_event, utc=True).dt.tz_convert('America/New_York')
x = x.sort_index()
x['dia'] = x.index.tz_localize(None).normalize(); x['hm'] = x.index.hour * 100 + x.index.minute
rth = x[(x.hm >= 930) & (x.hm <= 1559)]
ops, prev = [], None
for d, s in rth.groupby('dia'):
    if d.weekday() >= 5 or len(s) < 300: prev = None; continue
    if prev is not None and s.hm.iloc[0] == 930 and prev[1] == s.instrument_id.iloc[0]:
        C, A = prev[0], s.open.iloc[0]; g = np.log(A / C)
        if 0.001 <= abs(g) <= 0.01:
            lado = -np.sign(g); stop = A - lado * 2 * abs(A - C)
            v = s[s.hm <= 1159]; sal = None
            for o, h, l, c in zip(v.open.values, v.high.values, v.low.values, v.close.values):
                if (lado > 0 and l <= stop) or (lado < 0 and h >= stop):
                    sal = min(stop, o) if lado > 0 else max(stop, o); break
                if (lado > 0 and h >= C + TIC) or (lado < 0 and l <= C - TIC):
                    sal = C; break
            if sal is None: sal = v.close.values[-1]
            b = lado * np.log(sal / A)
            ops.append(dict(dia=d, g=g, bruto=b, neto=b - COSTE, lleno=sal == C))
    q = s[s.hm == 1559]
    prev = (q.close.iloc[0], q.instrument_id.iloc[0]) if len(q) else None
t = pd.DataFrame(ops).set_index('dia')
print(f'operaciones {len(t)} ({len(t)/t.index.year.nunique():.0f}/año), huecos cerrados {t.lleno.mean()*100:.0f}%')
for a, b in (('2010', '2017'), ('2018', '2026')):
    y = t.loc[a:b]; an = y.neto.groupby(y.index.year).sum()
    print(f'{a}-{b}: n {len(y)} bruto {y.bruto.mean()*1e4:.2f} pb neto {y.neto.mean()*1e4:.2f} pb (t {t_nw(y.neto.values):.2f}) años+ {(an>0).sum()}/{len(an)}')
    print('   por año (%):', (an * 100).round(1).to_dict())
c = t.loc['2018':]
for lo, hi in ((0.001, 0.003), (0.003, 0.006), (0.006, 0.0101)):
    z = c[(c.g.abs() >= lo) & (c.g.abs() < hi)]
    print(f'  tramo {lo*100:.1f}-{hi*100:.1f}%: n {len(z)} neto {z.neto.mean()*1e4:.2f} pb (t {t_nw(z.neto.values):.2f})')
for nom, z in (('hueco arriba (corto)', c[c.g > 0]), ('hueco abajo (largo)', c[c.g < 0])):
    print(f'  {nom}: n {len(z)} neto {z.neto.mean()*1e4:.2f} pb (t {t_nw(z.neto.values):.2f})')
an = c.neto.groupby(c.index.year).sum()
crit = {'1 t>=2': c.neto.mean() > 0 and t_nw(c.neto.values) >= 2, '2 años>=60%': (an > 0).mean() >= 0.6, '3 bruto>=3·coste': c.bruto.mean() >= 3 * COSTE}
print('CRITERIOS:', crit, '→ CERTIFICADA' if all(crit.values()) else '→ NO CERTIFICADA')
