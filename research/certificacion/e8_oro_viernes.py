"""E8: backtest de la estrategia oro del viernes (PREREGISTRO_E8) y cartera con E1. Uso: python3 e8_oro_viernes.py DIR_GC_VIE e1_franjas.csv"""
import glob, os, sys
import numpy as np, pandas as pd
from c1_certificacion import t_nw
from e1_estrategia import construir, resumen
F = {}
for f in sorted(glob.glob(os.path.join(sys.argv[1], '*.csv'))):
    x = pd.read_csv(f)
    if len(x) < 30 or x.instrument_id.nunique() > 1: continue
    x.index = pd.to_datetime(x.ts_event, utc=True).dt.tz_convert('America/New_York'); mm = x.index.hour * 60 + x.index.minute
    a = x.close[(mm < 960) & (mm >= 950)]; b = x.close[(mm < 1015) & (mm >= 1005)]; v = x[(mm >= 960) & (mm < 1015)]
    if len(a) and len(b) and len(v): F[pd.Timestamp(os.path.basename(f)[:10])] = (a.iloc[-1], b.iloc[-1], v.low.min())
X = pd.DataFrame(F, index=['p0', 'p1', 'low']).T
r = np.log(X.p1 / X.p0); sd = r.rolling(52).std().shift(1); adverso = 1 - X.low / X.p0
def oro(obj, coste_pb):
    w = (obj / sd).clip(upper=20); stop = adverso >= 4 * sd
    bruto = np.where(stop, -(4 * sd + 0.5e-4), r)
    return pd.DataFrame({'ret': w * (bruto - coste_pb / 1e4), 'stop': stop, 'w': w}).dropna()
def res(d, per_year):
    eq = d.ret.cumsum(); an = d.ret.groupby(d.index.year).sum()
    return (f'{d.ret.mean()*per_year*100:.1f}%/año Sharpe {d.ret.mean()/d.ret.std()*np.sqrt(per_year):.2f} DD {(eq-eq.cummax()).min()*100:.1f}% '
            f'años+ {(an>0).sum()}/{len(an)} stops {int(d.stop.sum())} expo media {d.w.mean():.1f}x')
e1x = pd.read_csv(sys.argv[2], index_col=0, parse_dates=True)
for c_oro in (0.74, 1.5, 2.5):
    g = oro(0.005, c_oro); g18 = g.loc['2018':]
    print(f'ORO vie 16:00-16:55, riesgo 0,5%, coste {c_oro} pb: 2011-26 {res(g.loc["2011":], 52)} | 2018-26 {res(g18, 52)}')
for nc, c in (('FTMO 0,79', 0.79), ('bajo 0,44', 0.44)):
    e = construir(e1x, 0.005, c); e = e[['ret']].loc['2018':]
    for c_oro in (0.74, 1.5, 2.5):
        g = oro(0.005, c_oro)[['ret']].loc['2018':]
        J = pd.concat([e.ret.rename('e1'), g.ret.rename('oro')], axis=1).fillna(0)
        corr = J.e1.corr(J.oro); p = J.e1 + J.oro
        k = J.e1.std() / p.std(); p = p * k                     # misma volatilidad diaria que E1 solo
        eq = p.cumsum(); an = p.groupby(p.index.year).sum()
        print(f'  E1 ({nc}) {e.ret.mean()*252*100:.1f}%/año Sharpe {e.ret.mean()/e.ret.std()*np.sqrt(252):.2f} + ORO ({c_oro} pb) → CARTERA (misma vol que E1 al 0,5%): '
              f'{p.mean()*252*100:.1f}%/año Sharpe {p.mean()/p.std()*np.sqrt(252):.2f} DD {(eq-eq.cummax()).min()*100:.1f}% años+ {(an>0).sum()}/{len(an)} | corr {corr:.3f}')
w = r.loc['2011':]
print(f'robustez 2011-26: mediana {w.median()*1e4:.2f} pb, % viernes positivos {(w>0).mean()*100:.0f}%, media recortada 5% {w[(w>w.quantile(.05))&(w<w.quantile(.95))].mean()*1e4:.2f} pb, sd {w.std()*1e4:.1f} pb')
