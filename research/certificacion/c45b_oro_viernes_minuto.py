"""C45b (descriptivo): GC futuro a minuto el viernes. ¿Cuánto del 16:00→17:00 está en los últimos minutos? Uso: python3 c45b... DIR"""
import glob, os, sys
import numpy as np, pandas as pd
from c1_certificacion import t_nw
P = {}
for f in sorted(glob.glob(os.path.join(sys.argv[1], '*.csv'))):
    x = pd.read_csv(f)
    if len(x) < 30 or x.instrument_id.nunique() > 1: continue
    x.index = pd.to_datetime(x.ts_event, utc=True).dt.tz_convert('America/New_York'); mm = x.index.hour * 60 + x.index.minute
    def px(m):
        y = x.close[(mm < m) & (mm >= m - 10)]; return y.iloc[-1] if len(y) else np.nan
    P[pd.Timestamp(os.path.basename(f)[:10])] = {k: px(m) for k, m in (('1600', 960), ('1630', 990), ('1655', 1015), ('1658', 1018), ('1700', 1020))}
P = pd.DataFrame(P).T
for a, b in (('1600', '1700'), ('1600', '1658'), ('1600', '1655'), ('1630', '1655'), ('1655', '1658'), ('1658', '1700')):
    r = np.log(P[b] / P[a]).dropna(); an = r.groupby(r.index.year).sum()
    print(f'largo {a}→{b}: n {len(r)} {r.mean()*1e4:5.2f} pb (t {t_nw(r.values):5.2f}) | 2010-17 {r.loc[:"2017"].mean()*1e4:5.2f} | 2018-26 {r.loc["2018":].mean()*1e4:5.2f} (t {t_nw(r.loc["2018":].values):.2f}) | años+ {(an>0).sum()}/{len(an)}')
