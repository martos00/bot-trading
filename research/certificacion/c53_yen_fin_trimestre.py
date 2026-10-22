"""C53: USDJPY D−2 07-08 NY, fin de trimestre frente al resto. Ver PREREGISTRO_C53."""
import io, contextlib
import numpy as np, pandas as pd
from scipy import stats
from c1_certificacion import t_nw
with contextlib.redirect_stdout(io.StringIO()):
    exec(open('c48_yen_d2.py').read().split("x = serie(")[0])
for nom, cfg in (('USDJPY largo', ('USDJPY', 3, 7, 8, 1)), ('USDCHF largo (inf.)', ('USDCHF', 3, 7, 8, 1)), ('EURUSD corto (inf.)', ('EURUSD', 3, 7, 8, -1))):
    x = serie(*cfg).bruto; q = x[x.index.month.isin([3, 6, 9, 12])]; r = x[~x.index.month.isin([3, 6, 9, 12])]; dic = x[x.index.month == 12]
    t = stats.ttest_ind(q, r, equal_var=False)
    print(f'{nom}: fin de trimestre n {len(q)} {q.mean()*1e4:.2f} pb (t {t_nw(q.values):.2f}) | resto n {len(r)} {r.mean()*1e4:.2f} pb (t {t_nw(r.values):.2f}) '
          f'| diferencia {(q.mean()-r.mean())*1e4:.2f} pb (t Welch {t.statistic:.2f}) | diciembre n {len(dic)} {dic.mean()*1e4:.2f} pb')
    if nom == 'USDJPY largo': print('   →', 'PASA' if t.statistic >= 1.65 else 'NO PASA')
