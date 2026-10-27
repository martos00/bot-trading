"""C80: bolsa local de cierre D-3 a cierre D-1 antes de BoJ, BoE y RBA (PREREGISTRO_C80, commit 37dd366).
Uso: python3 c80_deriva_previa_bc.py DIR_HD_NEW DIR_FECHAS"""
import os, sys
import numpy as np, pandas as pd
from c1_certificacion import t_nw
from c45_oro_viernes import carga
def cierres(carpeta, tz, hh, mm):
    s = carga(carpeta).tz_convert(tz)
    df = pd.DataFrame({'c': s.values, 'dia': s.index.tz_localize(None).normalize(), 'm': s.index.hour * 60 + s.index.minute})
    obj = hh * 60 + mm
    return df[(df.m < obj) & (df.m >= obj - 10)].groupby('dia').c.last()
def prueba(nom, cie, fechas, signo, corte_desc):
    dias = cie.index; pos = {d: i for i, d in enumerate(dias)}
    r, r0 = {}, {}
    for d in fechas:
        if d not in pos or pos[d] < 3: continue
        i = pos[d]; r[d] = np.log(cie.iloc[i - 1] / cie.iloc[i - 3]) * 1e4; r0[d] = np.log(cie.iloc[i] / cie.iloc[i - 1]) * 1e4
    r, r0 = pd.Series(r).sort_index(), pd.Series(r0).sort_index()
    if signo == 0:
        a = r.loc[:'2017']; ta = t_nw(a.values); signo = int(np.sign(a.mean())) if abs(ta) >= 2 else 0
        print(f'  {nom}: descubrimiento 2010-17 {a.mean():+.1f} pb (t {ta:+.2f}) -> signo {signo}')
        if signo == 0: print(f'  {nom}: NO PASA (sin signo en el descubrimiento)'); return
        ev = r.loc['2018':]
    else:
        ev = r
    t = t_nw(ev.values) * signo; an = ev.groupby(ev.index.year).mean(); b = r.loc['2018':]
    pasa = t >= 2.13 and (np.sign(an) == signo).mean() >= 0.6 and b.mean() * signo > 6
    print(f'{nom}: n {len(r)} D-2..D-1 {r.mean():+.1f} pb (t {t_nw(r.values):+.2f}) | 2010-17 {r.loc[:"2017"].mean():+.1f} | 2018-26 {b.mean():+.1f} (t {t_nw(b.values):+.2f}) '
          f'| años con el signo {(np.sign(an)==signo).sum()}/{len(an)} | inf. D0 {r0.mean():+.1f} pb (t {t_nw(r0.values):+.2f}) -> {"PASA" if pasa else "NO PASA"}')
hd, fe = sys.argv[1:3]
F = {k: pd.DatetimeIndex(pd.to_datetime(pd.read_csv(os.path.join(fe, k + '.csv')).iloc[:, 0])) for k in ('boj', 'boe', 'rba')}
rba = F['rba'][F['rba'].dayofweek == 1]
boe = pd.DatetimeIndex([d + pd.Timedelta(days=(3 - d.dayofweek) % 7) for d in F['boe']])
prueba('BoJ -> Nikkei', cierres(os.path.join(hd, 'JPXJPY'), 'Asia/Tokyo', 15, 0), F['boj'], 1, None)
prueba('BoE -> FTSE (2015-26)', cierres(os.path.join(hd, 'UKXGBP'), 'Europe/London', 16, 30), boe, 1, None)
prueba('RBA -> ASX', cierres(os.path.join(hd, 'AUXAUD'), 'Australia/Sydney', 16, 0), rba, 0, '2017')
