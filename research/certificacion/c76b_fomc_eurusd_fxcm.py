"""C76b: segunda fuente (FXCM, punto medio) de C76 'FOMC comunicado 14:00 | EURUSD' (señal 14:00->14:05, posicion 14:05->14:30).
Criterio fijado antes de ejecutar (27-oct-2026): media > 0 con t (NW) >= 2,0; > 0 antes y desde 2020; desde 2020 > 1,1 pb.
Informativo: GBPUSD, USDJPY (FXCM). Uso: python3 c76b_fomc_eurusd_fxcm.py FOMC_CSV DIR_FXCM"""
import sys
import numpy as np, pandas as pd
from c1_certificacion import t_nw
from c76_continuacion_noticias import operaciones
from c77b_fomc_eurusd_fxcm import serie_fxcm
fomc = pd.DatetimeIndex(pd.read_csv(sys.argv[1]).iloc[:, 0]); fomc = fomc[(fomc >= '2013-03-01') & (fomc <= '2026-09-30')]
for par in ('EURUSD', 'GBPUSD', 'USDJPY'):
    r = operaciones(serie_fxcm(sys.argv[2], par), None, fomc, (14, 0)); a, b = r[r.index < '2020-01-01'], r[r.index >= '2020-01-01']
    an = r.groupby(r.index.year).mean(); t = t_nw(r.values)
    pasa = r.mean() > 0 and t >= 2.0 and a.mean() > 0 and b.mean() > 1.1
    print(f'{par} FXCM: n {len(r)} {r.mean():+.2f} pb (t {t:+.2f}) aciertos {(r>0).mean()*100:.0f} % | antes 2020 {a.mean():+.2f} (t {t_nw(a.values):+.2f}) | '
          f'desde 2020 {b.mean():+.2f} (t {t_nw(b.values):+.2f}) | años+ {(an>0).sum()}/{len(an)}' + (f' -> {"CONFIRMA" if pasa else "NO CONFIRMA"}' if par == 'EURUSD' else ' (informativo)'))
