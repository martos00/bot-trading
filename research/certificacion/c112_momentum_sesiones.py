"""C112 — largo en la sesión asiática (18:00→03:00 NY) si el día anterior fue positivo; oro y plata (PREREGISTRO_C112).
Uso: python3 c112_momentum_sesiones.py DIR_SCRATCH"""
import sys, numpy as np, pandas as pd
from c1_certificacion import t_nw
from c93_oro_ruptura_dia_anterior import carga
import c94_ruptura_otros_futuros as c94
def sesiones(x, dur, excl=()):
    """x: velas (o,h,l,c) con hora de inicio NY; dur: duración de la vela. Devuelve por día D: Asia (18:00→03:00) y día completo (18:00→17:00)."""
    n = x.index.tz_localize(None); fin = n + dur; o, c = x.o.values, x.c.values
    def abre(t):   # apertura de la primera vela que empieza en t o después (≤ 15 min tarde)
        k = n.searchsorted(t); return o[k] if k < len(n) and n[k] - t <= pd.Timedelta(minutes=15) else np.nan
    def cierra(t):  # cierre de la última vela que termina en t o antes (≤ 15 min antes)
        k = fin.searchsorted(t, 'right') - 1; return c[k] if k >= 0 and t - fin[k] <= pd.Timedelta(minutes=15) else np.nan
    out = {}
    for D in pd.date_range(n[0].normalize() + pd.Timedelta(days=3), n[-1].normalize(), freq='B'):
        if D in excl: continue
        ini = D - pd.Timedelta(days=1 if D.weekday() else 3) + pd.Timedelta(hours=18)
        a = np.log(cierra(D + pd.Timedelta(hours=3)) / abre(ini))
        dia = np.log(cierra(D + pd.Timedelta(hours=17)) / abre(ini))
        out[D] = (a * 1e4, dia * 1e4)
    r = pd.DataFrame(out, index=['asia', 'dia']).T.dropna()
    r['prev'] = r.dia.shift(1); return r.dropna()
def evalua(r, coste):
    s = r.asia[r.prev > 0] - coste; ctl = r.asia - coste; neg = r.asia[r.prev < 0] - coste
    an = s.groupby(s.index.year).sum()
    return s, ctl, neg, an
if __name__ == '__main__':
    SP = sys.argv[1]; c94.SP = SP
    M = [('ORO', 'hd2/XAUUSD', 'GC', 0.74), ('PLATA', 'hd_new/XAGUSD', 'SI', 2.3)]
    for nom, d, fut, co in M:
        x = carga(f'{SP}/{d}').loc['2010-06-01':'2026-09-30']; r = sesiones(x, pd.Timedelta(minutes=1))
        h, ex = c94.carga_h1(fut); rf = sesiones(h, pd.Timedelta(hours=1), ex)
        s, ctl, neg, an = evalua(r, co); sf, ctlf, negf, _ = evalua(rf, co)
        t = t_nw(s.values)
        crit = {'t>=2.24': s.mean() > 0 and t >= 2.24, '2010-17>0': s.loc[:'2017'].mean() > 0, '2018-26>0': s.loc['2018':].mean() > 0,
                'años>=60%': (an > 0).mean() >= 0.6, 'desde 2023>0': s.loc['2023':].mean() > 0, 'futuros': sf.mean() > 0 and t_nw(sf.values) >= 2.0}
        sh = lambda q: q.mean() / q.std() * np.sqrt(len(q) / ((q.index[-1] - q.index[0]).days / 365.25))
        print(f'\n{nom} (coste {co} pb) — señal: Asia larga si el día anterior > 0')
        print(f'  HistData: n {len(s)} media neta {s.mean():+.2f} pb (t {t:.2f}) | 2010-17 {s.loc[:"2017"].mean():+.2f} | 2018-26 {s.loc["2018":].mean():+.2f} | desde 2023 {s.loc["2023":].mean():+.2f} | años+ {(an>0).sum()}/{len(an)} | Sharpe anual {sh(s):.2f}')
        print(f'  Futuros {fut} 1 h: n {len(sf)} media neta {sf.mean():+.2f} pb (t {t_nw(sf.values):.2f}) | 2018-26 {sf.loc["2018":].mean():+.2f} | desde 2023 {sf.loc["2023":].mean():+.2f}')
        print(f'  Control todos los días: HistData {ctl.mean():+.2f} pb (t {t_nw(ctl.values):.2f}), 2018-26 {ctl.loc["2018":].mean():+.2f} | futuros {ctlf.mean():+.2f} (t {t_nw(ctlf.values):.2f})')
        print(f'  Control día anterior < 0: HistData {neg.mean():+.2f} pb (t {t_nw(neg.values):.2f}) | futuros {negf.mean():+.2f}')
        print(f'  Diferencia señal − días negativos (HistData): {s.mean()-neg.mean():+.2f} pb')
        print('  por año (suma pb):', an.round(0).astype(int).to_dict())
        print('  RESULTADO:', 'PASA' if all(crit.values()) else 'NO PASA: falla ' + ', '.join(k for k, v in crit.items() if not v))
        pd.DataFrame({'senal': s}).to_csv(f'{SP}/c112_{nom}.csv')
