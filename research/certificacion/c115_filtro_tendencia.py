"""C115 — filtro de tendencia (precio 16:00 > media de 20 días de las 16:00) en oro y plata del viernes (PREREGISTRO_C115).
Uso: python3 c115_filtro_tendencia.py DIR_SCRATCH"""
import sys, numpy as np, pandas as pd
from c1_certificacion import t_nw
from c93_oro_ruptura_dia_anterior import carga
import c94_ruptura_otros_futuros as c94
SP = sys.argv[1]; c94.SP = SP
def precios(x, dur):
    n = x.index.tz_localize(None); fin = n + dur; c = x.c.values
    def p(t):
        k = fin.searchsorted(t, 'right') - 1
        return c[k] if k >= 0 and t - fin[k] <= pd.Timedelta(minutes=15) else np.nan
    return p
def tendencia(p, dias):
    p16 = pd.Series({d: p(d + pd.Timedelta(hours=16)) for d in dias}).dropna()
    ma = p16.rolling(20).mean().shift(1)
    return (p16 > ma).where(ma.notna())
sh = lambda r, n_año: r.mean() / r.std() * np.sqrt(n_año) if r.std() > 0 else np.nan
C = pd.read_csv(f'{SP}/componentes_B.csv', index_col=0, parse_dates=True).loc['2018-03-26':]
res = {}
for nom, d, h0, h1, fut, col in (('ORO', 'hd2/XAUUSD', (16, 0), (16, 55), 'GC', 'oro_vie_1655'), ('PLATA', 'hd_new/XAGUSD', (16, 30), (17, 0), 'SI', 'plata_viernes')):
    x = carga(f'{SP}/{d}').loc['2010-06-01':'2026-09-30']; p = precios(x, pd.Timedelta(minutes=1))
    dias = pd.date_range('2010-06-01', '2026-09-30', freq='B'); tr = tendencia(p, dias)
    vie = [v for v in dias if v.weekday() == 4]
    r = pd.Series({v: np.log(p(v + pd.Timedelta(hours=h1[0], minutes=h1[1])) / p(v + pd.Timedelta(hours=h0[0], minutes=h0[1]))) * 1e4 for v in vie}).dropna()
    t = tr.reindex(r.index); r = r[t.notna()]; t = t[t.notna()].astype(bool)
    up, dn = r[t], r[~t]; dif_t = (up.mean() - dn.mean()) / np.sqrt(up.var() / len(up) + dn.var() / len(dn))
    filt = r.where(t, 0.0)
    print(f'\n{nom} — contado HistData 2010-2026 (bruto, pb por viernes)')
    print(f'  viernes alcistas n {len(up)} media {up.mean():+.2f} | bajistas n {len(dn)} media {dn.mean():+.2f} | diferencia t {dif_t:+.2f}')
    for a, b in (('2010', '2017'), ('2018', '2026')):
        print(f'  {a}-{b[2:]}: Sharpe sin filtro {sh(r.loc[a:b], 52):.2f} | con filtro {sh(filt.loc[a:b], 52):.2f} | media alcistas {up.loc[a:b].mean():+.2f} / bajistas {dn.loc[a:b].mean():+.2f}')
    h, ex = c94.carga_h1(fut); pf = precios(h, pd.Timedelta(hours=1)); trf = tendencia(pf, pd.date_range('2018-01-01', '2026-09-30', freq='B'))
    rf = C[col][C[col] != 0]; tf = trf.reindex(rf.index); rf = rf[tf.notna()]; tf = tf[tf.notna()].astype(bool)
    ff = rf.where(tf, 0.0)
    print(f'  Futuros 2018-26 (neto): Sharpe sin filtro {sh(rf, 52):.2f} | con filtro {sh(ff, 52):.2f} | media alcistas {rf[tf].mean()*1e4:+.2f} / bajistas {rf[~tf].mean()*1e4:+.2f} (en unidades de la cartera ×1e4)')
    res[nom] = dict(dif_t=dif_t, s1=(sh(filt.loc['2010':'2017'], 52) > sh(r.loc['2010':'2017'], 52)), s2=(sh(filt.loc['2018':], 52) > sh(r.loc['2018':], 52)), sf=sh(ff, 52) > sh(rf, 52), tfut=tf)
# cartera 150K
base = ['yen', 'cesta_yen', 'oro_vie_1655', 'oro_D-2', 'plata_visp_1655', 'plata_viernes', 'nikkei_Q+2', 'nikkei_Q-2']
def volctl(P): pv = P.rolling(60, min_periods=40).std().shift(1); return (P * (P.std() / pv).clip(0.5, 2)).dropna()
D = C[base].copy()
for nom, col in (('ORO', 'oro_vie_1655'), ('PLATA', 'plata_viernes')):
    m = res[nom]['tfut'].reindex(D.index); D.loc[(D[col] != 0) & (m == False), col] = 0.0
A, Bf = volctl(C[base].sum(axis=1)), volctl(D.sum(axis=1)); s = lambda q: q.mean() / q.std() * np.sqrt(252)
print(f'\nCartera 150K: Sharpe actual {s(A):.2f} (2018-21 {s(A.loc[:"2021"]):.2f}, 2022-26 {s(A.loc["2022":]):.2f}) | con filtro {s(Bf):.2f} (2018-21 {s(Bf.loc[:"2021"]):.2f}, 2022-26 {s(Bf.loc["2022":]):.2f})')
ok = all(res[k]['dif_t'] >= 2.0 and res[k]['s1'] and res[k]['s2'] and res[k]['sf'] for k in res) and s(Bf.loc[:'2021']) > s(A.loc[:'2021']) and s(Bf.loc['2022':]) > s(A.loc['2022':])
print('RESULTADO:', 'SE ADOPTA' if ok else 'NO SE ADOPTA (el bot sigue comprando todos los viernes)')
