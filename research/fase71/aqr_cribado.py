"""Cribado de estilos con datos de AQR (Century of Factor Premia, mensual): Sharpe antes/después de 2012.
Uso: python3 aqr_cribado.py Century-of-Factor-Premia-Monthly.xlsx
Fuente: https://www.aqr.com/-/media/AQR/Documents/Insights/Data-Sets/Century-of-Factor-Premia-Monthly.xlsx"""
import sys
import numpy as np
import pandas as pd

d = pd.read_excel(sys.argv[1], 0, header=None)
hr = [i for i in range(40) if str(d.iat[i, 0]).strip().lower().startswith('date')][0]
d.columns = d.iloc[hr]
d = d.iloc[hr + 1:]
d = d[pd.to_datetime(d.iloc[:, 0], errors='coerce').notna()]
d.index = pd.to_datetime(d.iloc[:, 0])
d = d.iloc[:, 1:].apply(pd.to_numeric, errors='coerce')


def sr(x):
    x = x.dropna()
    return x.mean() / x.std() * np.sqrt(12) if len(x) > 24 else np.nan


print('último mes:', d.index.max().date())
print(pd.DataFrame({'SR<2012': d.loc[:'2011'].apply(sr), 'SR2012+': d.loc['2012':].apply(sr),
                    't2012+': d.loc['2012':].apply(lambda x: x.mean() / x.std() * np.sqrt(x.count())),
                    'SR2020+': d.loc['2020':].apply(sr)}).round(2).to_string())
