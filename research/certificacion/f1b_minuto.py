"""F1b, comprobación de consistencia (descriptiva; misma fuente Databento, a minuto): corto NG jueves 09:00→10:00 NY y tramos vecinos."""
import glob, os, sys
import numpy as np, pandas as pd
from c1_certificacion import t_nw
F = {}
for f in sorted(glob.glob(os.path.join(sys.argv[1], '*.csv'))):
    x = pd.read_csv(f)
    if len(x) < 50 or x.instrument_id.nunique() > 1: continue
    x.index = pd.to_datetime(x.ts_event, utc=True).dt.tz_convert('America/New_York'); x = x.sort_index()
    hm = x.index.hour * 60 + x.index.minute
    def px(m):
        y = x.close[(hm < m) & (hm >= m - 10)]; return y.iloc[-1] if len(y) else np.nan
    F[pd.Timestamp(os.path.basename(f)[:10])] = {k: px(m) for k, m in (('0830', 510), ('0900', 540), ('0930', 570), ('1000', 600), ('1029', 629))}
P = pd.DataFrame(F).T
for a, b in (('0900', '1000'), ('0830', '0900'), ('0900', '0930'), ('0930', '1000'), ('1000', '1029')):
    r = -np.log(P[b] / P[a]).dropna()
    an = r.groupby(r.index.year).sum()
    print(f'corto {a}→{b}: n {len(r)} {r.mean()*1e4:6.1f} pb (t {t_nw(r.values):5.2f}) | 2010-17 {r.loc[:"2017"].mean()*1e4:6.1f} | 2018-26 {r.loc["2018":].mean()*1e4:6.1f} | años+ {(an>0).sum()}/{len(an)}')
