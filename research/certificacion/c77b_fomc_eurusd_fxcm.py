"""C77b: segunda fuente (FXCM, punto medio BID/ASK) de EURUSD tras el comunicado del FOMC 14:05 -> 16:00 NY (regla de C77).
Criterio fijado antes de ejecutar: media > 0 con t >= 2,0, > 0 antes y desde 2020, y desde 2020 > coste 1,1 pb.
Informativo: GBPUSD (FXCM), oro (GC Databento). Uso: python3 c77b_fomc_eurusd_fxcm.py FOMC_CSV DIR_FXCM DIR_GC_M1"""
import glob, os, sys
import numpy as np, pandas as pd
from c1_certificacion import fxcm, t_nw
from c76_continuacion_noticias import precio, cargar_gc
from c77_momentum_horas import ops

def serie_fxcm(carpeta, par):
    b, a = {}, {}
    for f in sorted(glob.glob(os.path.join(carpeta, par, f'{par}_*.csv.gz'))):
        x, y = fxcm(f); b.update(x); a.update(y)
    m = sorted(set(b) & set(a))
    idx = pd.to_datetime(np.array(m) * 60, unit='s', utc=True).tz_convert('America/New_York').tz_localize(None)
    return pd.Series([(b[k] + a[k]) / 2 for k in m], index=idx).sort_index()

if __name__ == "__main__":
  fomc = pd.DatetimeIndex(pd.read_csv(sys.argv[1]).iloc[:, 0]); fomc = fomc[(fomc >= '2013-03-01') & (fomc <= '2026-09-30')]
  ev = fomc + pd.Timedelta(hours=14)
  gc = cargar_gc(sys.argv[3], list(fomc))
  for nom, s in (('EURUSD FXCM (confirmacion)', serie_fxcm(sys.argv[2], 'EURUSD')), ('GBPUSD FXCM (informativo)', serie_fxcm(sys.argv[2], 'GBPUSD')),
                 ('Oro GC (informativo)', gc['close'])):
      r = ops(s, ev, None, (16, 0)); a, b = r[r.index < '2020-01-01'], r[r.index >= '2020-01-01']; an = r.groupby(r.index.year).mean()
      print(f'{nom}: n {len(r)} {r.mean():+.2f} pb (t {t_nw(r.values):+.2f}) aciertos {(r>0).mean()*100:.0f} % | antes 2020 {a.mean():+.2f} | desde 2020 {b.mean():+.2f} (t {t_nw(b.values):+.2f}) | años+ {(an>0).sum()}/{len(an)}')
