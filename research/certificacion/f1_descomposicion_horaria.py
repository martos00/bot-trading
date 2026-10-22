"""F1 (descriptivo, no certifica): ¿en qué horas del jueves cae el gas? NG.v.0 1h (Databento), hora de NY.
Tramos (cierre de barra = inicio + 1 h): mié 14:30-ish → jue 09:00 | 09:00-10:00 | 10:00-11:00 (EIA 10:30) | 11:00-14:00 | 14:00-17:00."""
import sys
import numpy as np, pandas as pd
from c1_certificacion import t_nw
x = pd.read_csv(sys.argv[1]); x.index = pd.to_datetime(x.ts_event, utc=True).dt.tz_convert('America/New_York'); x = x.sort_index()
x['fin'] = x.index + pd.Timedelta(hours=1)                    # el cierre de la barra corresponde al final de su hora
c = x.set_index('fin')[['close', 'instrument_id']]
def px(t):
    j = c.index.searchsorted(t, side='right') - 1
    return (c.close.iloc[j], c.instrument_id.iloc[j]) if j >= 0 and (t - c.index[j]) <= pd.Timedelta(hours=2) else (np.nan, None)
H = [('mié 15:00', -1, 15), ('jue 09:00', 0, 9), ('jue 10:00', 0, 10), ('jue 11:00', 0, 11), ('jue 14:00', 0, 14), ('jue 17:00', 0, 17)]
filas = []
for d in pd.date_range('2010-06-10', '2026-09-30', freq='W-THU'):
    pts = [px(pd.Timestamp(d.year, d.month, d.day, h, tz='America/New_York') + pd.Timedelta(days=o)) for _, o, h in H]
    if any(np.isnan(p) for p, _ in pts) or len({i for _, i in pts}) > 1: continue
    filas.append([np.log(pts[k + 1][0] / pts[k][0]) for k in range(len(pts) - 1)] + [np.log(pts[-1][0] / pts[0][0])])
nom = [f'{H[k][0]}→{H[k+1][0]}' for k in range(len(H) - 1)] + ['total mié 15:00→jue 17:00']
X = pd.DataFrame(filas, columns=nom)
print(f'jueves válidos: {len(X)}')
for col in X: print(f'  {col:28s} media {X[col].mean()*1e4:7.1f} pb (t {t_nw(X[col].values):5.2f})  % del total {X[col].mean()/X[nom[-1]].mean()*100:5.0f}%')
