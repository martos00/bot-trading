"""C54: confirmación independiente (HistData) de los hallazgos de fin de trimestre de B13. Ver PREREGISTRO_C54."""
import numpy as np, pandas as pd
from c1_certificacion import t_nw
from c45_oro_viernes import carga
S = '/tmp/claude-0/-home-user-bot-trading/682335b1-28ae-5d18-9355-ce7f0f968722/scratchpad/'
def tipo_dias(s):
    dias = pd.DatetimeIndex(sorted(set(s.index.tz_localize(None).normalize()))); dias = dias[dias.weekday < 5]
    mes = dias.to_period('M'); idx = pd.Series(np.arange(len(dias)), index=dias)
    pos = idx.groupby(mes).cumcount().values + 1; fin = idx.groupby(mes).cumcount(ascending=False).values + 1
    t = pd.Series('', index=dias); qm = np.isin(dias.month, [3, 6, 9, 12]); qn = np.isin(dias.month, [1, 4, 7, 10])
    t[(fin == 2) & qm] = 'Q-1'; t[(fin == 1) & qm] = 'Q0'; t[(pos == 1) & qn] = 'Q+1'
    return t
def tramo(s, h0, m0, h1, m1):
    df = pd.DataFrame({'c': s.values, 'dia': s.index.tz_localize(None).normalize(), 'mm': s.index.hour * 60 + s.index.minute})
    a = df[(df.mm < h0 * 60 + m0) & (df.mm >= h0 * 60 + m0 - 10)].groupby('dia').c.last()
    b = df[(df.mm <= h1 * 60 + m1) & (df.mm >= h1 * 60 + m1 - 10)].groupby('dia').c.last()
    return np.log(b / a).dropna()
def prueba(nom, s, tipo, h0, m0, h1, m1, signo, a0, a1, umbral):
    td = tipo_dias(s); r = signo * tramo(s, h0, m0, h1, m1); r = r[td.reindex(r.index).values == tipo].loc[a0:a1]
    an = r.groupby(r.index.year).sum(); t = t_nw(r.values)
    ok = r.mean() > 0 and t >= umbral and (an > 0).mean() >= 0.6
    print(f'{nom} {a0}-{a1}: n {len(r)} {r.mean()*1e4:.2f} pb (t {t:.2f}) años con signo {(an>0).sum()}/{len(an)} → {"PASA" if ok else "NO PASA"}')
eu = carga(S + 'hd_all/EURUSD')
prueba('1a EURUSD Q+1 15-16 largo', eu, 'Q+1', 15, 0, 15, 59, 1, '2012', '2026-09', 2.0)
prueba('1b EURUSD Q+1 15-16 largo', eu, 'Q+1', 15, 0, 15, 59, 1, '2003', '2011', 1.65)
prueba('2  EURJPY Q0 01-02 corto', carga(S + 'hd_eurjpy'), 'Q0', 1, 0, 1, 59, -1, '2012', '2026-09', 2.0)
prueba('3  WTIUSD Q-1 16-17 largo (inf. para HO)', carga(S + 'hd_new/WTIUSD'), 'Q-1', 16, 0, 16, 58, 1, '2010', '2026-09', 2.0)
