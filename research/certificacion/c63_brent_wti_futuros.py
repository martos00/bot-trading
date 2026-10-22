"""C63: reversión Brent/WTI con futuros BZ.c.0 y CL.c.0 sin saltos de contrato. Ver PREREGISTRO_C63."""
import glob, os
import numpy as np, pandas as pd
from c1_certificacion import t_nw
S = '/tmp/claude-0/-home-user-bot-trading/682335b1-28ae-5d18-9355-ce7f0f968722/scratchpad/databento/'
def rets(df, sym):
    x = df[df.symbol == sym].copy(); x['dia'] = pd.to_datetime(x.ts_event).dt.tz_localize(None).dt.normalize()
    y = x.drop_duplicates('dia').set_index('dia').sort_index(); y = y[(y.index.weekday < 5) & (y.close > 0)]
    r = np.log(y.close).diff(); r[y.instrument_id != y.instrument_id.shift()] = np.nan; return r
bz = rets(pd.read_csv(S + 'BZ_c0_1d.csv'), 'BZ.c.0')
cl = rets(pd.concat([pd.read_csv(f) for f in glob.glob(S + 'curva/CL_*.csv') if os.path.getsize(f) > 100]), 'CL.c.0')
R = pd.concat([bz.rename('a'), cl.rename('b')], axis=1).loc['2010-06-01':'2026-09-30']
R = R[R.notna().any(axis=1)]
s = (R.a.fillna(0) - R.b.fillna(0)).cumsum()                  # diferencial acumulando solo rentabilidades válidas
z = (s - s.rolling(60).mean().shift(1)) / s.rolling(60).std().shift(1)
ops, pos, acum, dias = [], 0, 0.0, 0
for i in range(61, len(R)):
    if pos != 0:
        acum += pos * ((0 if np.isnan(R.a.iloc[i]) else R.a.iloc[i]) - (0 if np.isnan(R.b.iloc[i]) else R.b.iloc[i])) / 2; dias += 1
        if np.sign(z.iloc[i]) == pos or dias >= 20: ops.append((R.index[i], acum - 8e-4 - 0.5e-4 * dias, dias)); pos = 0
    elif abs(z.iloc[i]) > 2: pos, acum, dias = -np.sign(z.iloc[i]), 0.0, 0
X = pd.DataFrame(ops, columns=['dia', 'neto', 'dias']).set_index('dia')
for nom, c in (('2018-26', X.loc['2018':]), ('2018-26 sin 2020', X.loc['2018':][X.loc['2018':].index.year != 2020]), ('2010-17 (inf.)', X.loc[:'2017'])):
    an = c.neto.groupby(c.index.year).sum(); t = t_nw(c.neto.values, 2)
    ok = c.neto.mean() > 0 and t >= 2 and (an > 0).mean() >= 0.6
    print(f'{nom}: n {len(c)} neto {c.neto.mean()*1e4:.1f} pb/op (t {t:.2f}) años+ {(an>0).sum()}/{len(an)} peor {c.neto.min()*1e4:.0f} pb → {"PASA" if ok else "NO PASA"}')
print('por año 2018-26 (pb):', (X.loc['2018':].neto.groupby(X.loc['2018':].index.year).sum() * 1e4).round(0).to_dict())
