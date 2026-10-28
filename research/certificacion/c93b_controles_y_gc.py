"""C93 — controles (largos/cortos, deriva sin condicionar) y segunda fuente: futuro GC 1 min (Databento, contrato frontal).
Uso: python3 c93b_controles_y_gc.py DIR_HISTDATA_XAUUSD DIR_GC_1M"""
import sys, glob, os
import numpy as np, pandas as pd
from c1_certificacion import t_nw
from c93_oro_ruptura_dia_anterior import carga, simula, informe

def carga_gc(d):
    x = pd.concat([pd.read_csv(f) for f in sorted(glob.glob(os.path.join(d, 'GC_*.csv')))])
    x.index = pd.to_datetime(x.ts_event).dt.tz_convert('America/New_York'); x = x.sort_index(); x = x[~x.index.duplicated()]
    ses = (x.index.tz_localize(None) + pd.Timedelta(hours=7)).normalize()
    g = pd.Series(x.instrument_id.values, index=ses).groupby(level=0)
    moda = g.agg(lambda v: v.mode().iloc[0]); mezcla = g.nunique() > 1
    excl = set(moda.index[(moda != moda.shift()) | mezcla | mezcla.shift(fill_value=False)])   # sesiones con cambio de contrato
    return x[['open', 'high', 'low', 'close']].set_axis(['o', 'h', 'l', 'c'], axis=1), excl

def lados(nom, z):
    for sg, n in ((1, 'largos'), (-1, 'cortos')):
        r = z.r[z.sg == sg] * 1e4; print(f'   {nom} {n}: n {len(r)} media {r.mean():.2f} pb (t {t_nw(r.values):.2f}) | 2010-19 {r.loc[:"2019"].mean():.2f} | 2020-26 {r.loc["2020":].mean():.2f}')

def deriva(x, v0, cierre):
    n = x.index.tz_localize(None); mm = n.hour * 60 + n.minute; dia = n.normalize()
    c = pd.Series(x.c.values, index=dia)
    a = c[(mm >= v0 - 10) & (mm < v0)].groupby(level=0).last(); b = c[(mm >= cierre - 10) & (mm < cierre)].groupby(level=0).last()
    r = np.log(b / a).dropna() * 1e4; r = r[r.index.weekday < 5]
    print(f'   control: largo siempre {v0//60:02d}:{v0%60:02d}→{cierre//60}:00 NY: {r.mean():.2f} pb (t {t_nw(r.values):.2f}) | 2010-19 {r.loc[:"2019"].mean():.2f} | 2020-26 {r.loc["2020":].mean():.2f}')

if __name__ == '__main__':
    V = (('A', 420, 840, 960), ('B', 480, 900, 1020))
    x = carga(sys.argv[1]).loc['2010-06-01':'2026-09-30']
    print('HistData XAUUSD:')
    for nom, v0, v1, ci in V:
        lados(nom, simula(x, v0, v1, ci, 1.0)); deriva(x, v0, ci)
    g, excl = carga_gc(sys.argv[2]); g = g.loc['2010-06-01':'2026-09-30']
    print(f'Futuro GC (segunda fuente; {len(excl)} sesiones de cambio de contrato excluidas), coste 0,74 pb:')
    for nom, v0, v1, ci in V:
        z = simula(g, v0, v1, ci, 1.0, excluir=excl); c = informe(f' GC {nom}', z, coste=0.74); print('   CRITERIOS:', c, '→ PASA' if all(c.values()) else '→ NO PASA'); lados(nom, z)
        print('   por año (pb):', (z.r.groupby(z.index.year).sum() * 1e4).round(0).to_dict())
