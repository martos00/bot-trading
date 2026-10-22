"""Cartera de 6 ventajas SIN costes (techo teórico, informativo). Uso como e12_cartera.py."""
import sys, io, contextlib, glob
from datetime import datetime
import numpy as np, pandas as pd
argv0 = list(sys.argv)
with contextlib.redirect_stdout(io.StringIO()):
    exec(open("e12_cartera.py").read().rsplit("def sh(p): return", 1)[0])
sys.argv = argv0
# yen fin de mes (E9) bruto, con mid
b, a = D['USDJPY']; f = {}
for d in fin.index[fin.values == 3]:
    t0 = datetime(d.year, d.month, d.day, 7, tzinfo=NY); t1 = datetime(d.year, d.month, d.day, 8, tzinfo=NY)
    v = [en(b, t0), en(a, t0), en(b, t1), en(a, t1)]
    if not np.isnan(v).any(): f[d] = np.log((v[2] + v[3]) / (v[0] + v[1]))
Yb = pd.Series(f); sdb = Yb.rolling(24).std().shift(1); yenb = ((0.005 / sdb).clip(upper=20) * Yb).dropna()
# yen fin de trimestre (E11b, 00:30-02:00) bruto
def pata_b(par):
    bj, aj = {}, {}
    for fl in sorted(glob.glob(S + par + '/' + par + '_*.csv.gz')):
        bb, aa = fxcm(fl); bj.update(bb); aj.update(aa)
    v = {}
    for d in pd.bdate_range('2012-01-02', '2026-09-30'):
        t0 = datetime(d.year, d.month, d.day, 0, 30, tzinfo=NY); t1 = datetime(d.year, d.month, d.day, 2, tzinfo=NY)
        w = [en(bj, t0), en(aj, t0), en(bj, t1), en(aj, t1)]
        if not np.isnan(w).any(): v[d] = -np.log((w[2] + w[3]) / (w[0] + w[1]))
    r = pd.Series(v); sdj = r.rolling(60).std().shift(1)
    s_ = pd.Series(range(len(r)), index=r.index); fj = s_.groupby(s_.index.to_period('M')).cumcount(ascending=False) + 1
    q0 = r.index[(fj.values == 1) & np.isin(r.index.month, [3, 6, 9, 12])]
    return ((0.005 / 3 / sdj) * r).reindex(q0)
ejb = pd.concat([pata_b(p) for p in ('EURJPY', 'USDJPY', 'GBPJPY')], axis=1).sum(axis=1, min_count=1).dropna()
festb = (w * R69[NM]).reindex(PRE69).dropna(how='all').sum(axis=1); festb = festb[festb != 0]
e1x = pd.read_csv(sys.argv[2], index_col=0, parse_dates=True)
for desde in ('2018', '2012'):
    J = pd.concat([construir(e1x, 0.005, 0.0).ret.loc[desde:].rename('euro'), oro(0.005, 0.0).ret.loc[desde:].rename('oro'), plata(0.0).loc[desde:].rename('plata'),
                   yenb.loc[desde:].rename('yen_mes'), ejb.loc[desde:].rename('yen_trim'), festb.loc[desde:].rename('materias')], axis=1).fillna(0)
    J = J.loc[J.index >= max(J.euro.ne(0).idxmax(), pd.Timestamp(desde))]
    def est(q, nom):
        eq = q.cumsum(); m = q.groupby(q.index.to_period('M')).sum()
        return f'{nom:22s} {q.mean()*252*100:5.1f} %/año | Sharpe {q.mean()/q.std()*np.sqrt(252):.2f} | DD {(eq-eq.cummax()).min()*100:6.1f} % | meses + {(m>0).mean()*100:.0f} % | peor mes {m.min()*100:5.1f} %'
    print(f'=== Sin costes, desde {J.index.min().date()} (cada pata al 0,5 % de riesgo) ===')
    for c in J: print('  ' + est(J[c], c))
    p = J.sum(axis=1); k = J.euro.std() / p.std(); print('  ' + est(p * k, 'CARTERA (vol = euro)'))
    for vol in (0.08, 0.10, 0.125):
        kk = vol / (p.std() * np.sqrt(252)); q = p * kk; eq = q.cumsum(); m = q.groupby(q.index.to_period('M')).sum(); an = q.groupby(q.index.year).sum()
        print(f'  cartera a vol {vol*100:.1f} %: {q.mean()*252*100:.1f} %/año, DD {(eq-eq.cummax()).min()*100:.1f} %, peor año {an.min()*100:.1f} %, años + {(an>0).sum()}/{len(an)}, meses + {(m>0).mean()*100:.0f} %')
    print('  correlación máxima entre patas:', round(J.corr().where(~np.eye(6, dtype=bool)).abs().max().max(), 3))
