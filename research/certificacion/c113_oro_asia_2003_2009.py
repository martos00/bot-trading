"""C113 — oro largo 18:00→03:00 NY en 2003-2009 (Dukascopy). Uso: python3 c113_oro_asia_2003_2009.py xau_bid xau_ask xag_bid xag_ask"""
import sys, numpy as np, pandas as pd
from c1_certificacion import t_nw
from c106_metales_viernes_2003_2009 import medio
def asia(m):
    n = m.index.tz_localize(None); s = pd.Series(m.values, index=n); out = {}
    for D in pd.date_range('2003-05-06', '2009-12-31', freq='B'):
        ini = D - pd.Timedelta(days=1 if D.weekday() else 3) + pd.Timedelta(hours=18)
        def p(t):
            k = s.index.searchsorted(t, 'right') - 1
            return s.iloc[k] if k >= 0 and t - s.index[k] <= pd.Timedelta(minutes=15) else np.nan
        a, b, c = p(ini), p(D + pd.Timedelta(hours=3)), p(D + pd.Timedelta(hours=17))
        out[D] = (np.log(b / a) * 1e4, np.log(c / b) * 1e4)
    return pd.DataFrame(out, index=['asia', 'resto']).T.dropna()
for nom, fb, fa in (('ORO', sys.argv[1], sys.argv[2]), ('PLATA (informativo)', sys.argv[3], sys.argv[4])):
    m, _ = medio(fb, fa); r = asia(m.loc['2003-05-01':'2009-12-31']); a = r.asia - 0.74; an = a.groupby(a.index.year).mean(); t = t_nw(a.values)
    hora_a, hora_r = r.asia.mean() / 9, r.resto.mean() / 14
    print(f'{nom}: Asia n {len(a)} media neta {a.mean():+.2f} pb (t {t:.2f}) | años+ {(an>0).sum()}/{len(an)} {an.round(1).to_dict()}')
    print(f'   por hora: Asia {hora_a:+.3f} pb/h | resto del día {hora_r:+.3f} pb/h (resto total {r.resto.mean():+.2f} pb, t {t_nw(r.resto.values):.2f})')
    if nom == 'ORO':
        c = {'t>=2.0': a.mean() > 0 and t >= 2.0, 'años>=60%': (an > 0).mean() >= 0.6, 'Asia>resto por hora': hora_a > hora_r}
        print('   RESULTADO:', 'PASA' if all(c.values()) else 'NO PASA: falla ' + ', '.join(k for k, v in c.items() if not v))
