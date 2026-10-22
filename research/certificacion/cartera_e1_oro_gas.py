"""Cartera E1 + oro viernes (E8) + gas jueves 09-10 (F1b), informativo. Uso: python3 cartera_e1_oro_gas.py DIR_GC_VIE e1_franjas.csv NG_1h.csv"""
import sys, io, contextlib
import numpy as np, pandas as pd
from e1_estrategia import construir
with contextlib.redirect_stdout(io.StringIO()):
    sys.argv = [sys.argv[0], sys.argv[1], sys.argv[2], sys.argv[3]]
    src = open('e8_oro_viernes.py').read().split("e1x = pd.read_csv")[0]; exec(src)
# gas: corto jueves 09:00 → 10:00 NY con barras de 1 h (fin de barra)
x = pd.read_csv(sys.argv[3]); x.index = pd.to_datetime(x.ts_event, utc=True).dt.tz_convert('America/New_York') + pd.Timedelta(hours=1)
x = x.sort_index(); x['dia'] = x.index.tz_localize(None).normalize(); x['h'] = x.index.hour
a = x[x.h == 9].set_index('dia')[['close', 'instrument_id', 'high']]; b = x[x.h == 10].set_index('dia')[['close', 'instrument_id', 'high']]
j = a.join(b, lsuffix='0', rsuffix='1', how='inner'); j = j[(j.instrument_id0 == j.instrument_id1) & (j.index.weekday == 3)]
rg = -np.log(j.close1 / j.close0); sdg = rg.rolling(52).std().shift(1); advg = j.high1 / j.close0 - 1
def gas(obj, c):
    w = (obj / sdg).clip(upper=20); stop = advg >= 4 * sdg
    br = np.where(stop, -(4 * sdg + 1e-4), rg)
    return pd.Series(w * (br - c / 1e4), index=rg.index).dropna()
def sh(p): return p.mean() / p.std() * np.sqrt(252)
e1x = pd.read_csv(sys.argv[2], index_col=0, parse_dates=True)
print('Sharpe anual 2018-2026 (cada pata al 0,5 % de riesgo; cartera reescalada a la volatilidad de E1 solo)')
for ne, ce in (('E1 coste FTMO 0,79', 0.79), ('E1 coste bajo 0,44', 0.44)):
    e = construir(e1x, 0.005, ce).ret.loc['2018':]
    for co in (0.74, 1.5):
        for cg in (4.7, 10.0):
            g = oro(0.005, co).ret.loc['2018':]; n = gas(0.005, cg).loc['2018':]
            J = pd.concat([e.rename('e1'), g.rename('oro'), n.rename('gas')], axis=1).fillna(0)
            p = J.sum(axis=1); p = p * J.e1.std() / p.std(); eq = p.cumsum(); an = p.groupby(p.index.year).sum()
            print(f'{ne} | oro {co} pb | gas {cg} pb → E1 {sh(J.e1):.2f}, oro {sh(J.oro):.2f}, gas {sh(J.gas):.2f} | E1+oro {sh(J.e1+J.oro):.2f} | '
                  f'E1+oro+gas {sh(p):.2f} ({p.mean()*252*100:.1f} %/año, DD {(eq-eq.cummax()).min()*100:.1f} %, años+ {(an>0).sum()}/{len(an)}) | corr máx {J.corr().where(~np.eye(3, dtype=bool)).abs().max().max():.2f}')
