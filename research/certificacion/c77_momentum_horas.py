"""C77: momentum de horas tras EIA (WTI) y tras NFP/FOMC (EURUSD). PREREGISTRO_C77 (commit 0f77600).
Uso: python3 c77_momentum_horas.py FOMC_CSV ES_1m.pkl DIR_HISTDATA_EURUSD DIR_HISTDATA_WTI"""
import sys
import holidays
import numpy as np
import pandas as pd
from c1_certificacion import t_nw
from c74_modelo_tjr_ny import cargar_histdata
from c76_continuacion_noticias import precio, fechas_nfp

def ops(serie, eventos, h0, h1):
    out = {}
    for T in eventos:
        fin = T.normalize() + pd.Timedelta(hours=h1[0], minutes=h1[1])
        p0, p5, p1 = precio(serie, T), precio(serie, T + pd.Timedelta(minutes=5)), precio(serie, fin)
        if np.isnan(p0) or np.isnan(p5) or np.isnan(p1) or np.log(p5 / p0) == 0: continue
        out[T.normalize()] = np.sign(np.log(p5 / p0)) * np.log(p1 / p5) * 1e4
    return pd.Series(out)

def main():
    fomc_csv, es_pkl, dir_eu, dir_wti = sys.argv[1:5]
    fest = holidays.financial_holidays('NYSE', years=range(2010, 2027))
    eia = []
    for w in pd.date_range('2010-06-02', '2026-09-30', freq='W-WED'):
        lun = w - pd.Timedelta(days=2)
        if lun.date() in fest or w.date() in fest: eia.append(w + pd.Timedelta(days=1, hours=11))
        else: eia.append(w + pd.Timedelta(hours=10, minutes=30))
    es = pd.read_pickle(es_pkl); es.index = pd.to_datetime(es['ts_event'], utc=True).dt.tz_convert('America/New_York').dt.tz_localize(None)
    es = es[~es.index.duplicated()].sort_index()
    nfp = fechas_nfp(es)
    fomc = pd.DatetimeIndex(pd.read_csv(fomc_csv).iloc[:, 0]); fomc = fomc[(fomc >= '2013-03-01') & (fomc <= '2026-09-30')]
    eu = cargar_histdata(dir_eu)['close']; wti = cargar_histdata(dir_wti)['close']
    pruebas = [('WTI tras EIA (T+5 -> 14:30)', wti, pd.DatetimeIndex(eia), (14, 30), 8.0),
               ('EURUSD tras NFP (08:35 -> 12:00)', eu, nfp + pd.Timedelta(hours=8, minutes=30), (12, 0), 1.1),
               ('EURUSD tras FOMC (14:05 -> 16:00)', eu, fomc + pd.Timedelta(hours=14), (16, 0), 1.1)]
    lin = []
    for nom, s, ev, h1, coste in pruebas:
        r = ops(s, ev, None, h1); a, b = r[r.index < '2020-01-01'], r[r.index >= '2020-01-01']; t = t_nw(r.values)
        pasa = r.mean() > 0 and t >= 2.39 and a.mean() > 0 and b.mean() > coste
        an = r.groupby(r.index.year).mean()
        lin.append(f'{nom}: n {len(r)}  {r.mean():+.2f} pb (t {t:+.2f}) aciertos {(r>0).mean()*100:.0f} % | antes de 2020 {a.mean():+.2f} (t {t_nw(a.values):+.2f}) '
                   f'| desde 2020 {b.mean():+.2f} (t {t_nw(b.values):+.2f}) | coste {coste} pb | años+ {(an>0).sum()}/{len(an)} -> {"PASA" if pasa else "no pasa"}')
    txt = '\n'.join(lin); print(txt); open('c77_resultados.txt', 'w').write(txt + '\n')

if __name__ == '__main__':
    main()
