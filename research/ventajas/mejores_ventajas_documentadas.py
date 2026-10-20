"""¿Qué ventajas documentadas siguen funcionando tras 2012? Factores mensuales de Kenneth French (EE. UU. y desarrollados)
y AQR (BAB, QMJ). Sharpe y t antes y después de 2012 (rentabilidad bruta del factor, long-short).
Uso: python3 mejores_ventajas_documentadas.py DIR_DATOS"""
import io, os, sys
import numpy as np
import pandas as pd

d = sys.argv[1]


def french(f):
    txt = open(os.path.join(d, f), encoding='latin1').read().split('\n')
    i = next(k for k, l in enumerate(txt) if l.strip().startswith(',') or l.lower().startswith(',mkt'))
    filas = []
    for l in txt[i + 1:]:
        p = l.strip().split(',')
        if len(p) < 2 or not p[0].strip().isdigit() or len(p[0].strip()) != 6:
            if filas:
                break
            continue
        filas.append(p)
    cab = [c.strip() for c in txt[i].split(',')]
    x = pd.DataFrame(filas, columns=cab[:len(filas[0])])
    x.index = pd.to_datetime(x.iloc[:, 0].str.strip(), format='%Y%m')
    return x.iloc[:, 1:].apply(pd.to_numeric, errors='coerce') / 100


def aqr(f, hoja):
    x = pd.read_excel(os.path.join(d, f), sheet_name=hoja, header=None)
    h = next(k for k in range(40) if str(x.iat[k, 0]).strip().upper() == 'DATE')
    x.columns = x.iloc[h]; x = x.iloc[h + 1:]
    x = x[pd.to_datetime(x.iloc[:, 0], errors='coerce').notna()]
    x.index = pd.to_datetime(x.iloc[:, 0]); return x.iloc[:, 1:].apply(pd.to_numeric, errors='coerce')


def met(r):
    r = r.dropna()
    if len(r) < 36:
        return np.nan, np.nan
    return r.mean() / r.std() * np.sqrt(12), r.mean() / r.std() * np.sqrt(len(r))


us = french('F-F_Research_Data_5_Factors_2x3.csv'); um = french('F-F_Momentum_Factor.csv')
dv = french('Developed_5_Factors.csv'); dm = french('Developed_MOM_Factor.csv')
bab = aqr('Betting-Against-Beta-Equity-Factors-Monthly.xlsx', 'BAB Factors')
qmj = aqr('Quality-Minus-Junk-Factors-Monthly.xlsx', 'QMJ Factors')
series = {
    'EE.UU. mercado (Mkt-RF)': us['Mkt-RF'], 'EE.UU. value (HML)': us['HML'], 'EE.UU. tamaño (SMB)': us['SMB'],
    'EE.UU. rentabilidad (RMW)': us['RMW'], 'EE.UU. inversión (CMA)': us['CMA'], 'EE.UU. momentum (UMD)': um.iloc[:, 0],
    'Desarrollados mercado': dv['Mkt-RF'], 'Desarrollados value': dv['HML'], 'Desarrollados rentabilidad': dv['RMW'],
    'Desarrollados inversión': dv['CMA'], 'Desarrollados momentum': dm.iloc[:, 0],
    'EE.UU. baja beta (BAB, AQR)': bab['USA'], 'Global baja beta (BAB)': bab['Global'],
    'EE.UU. calidad (QMJ, AQR)': qmj['USA'], 'Global calidad (QMJ)': qmj['Global'],
}
filas = []
for nom, s in series.items():
    a = met(s.loc[:'2011']); b = met(s.loc['2012':])
    filas.append({'factor': nom, 'SR<2012': round(a[0], 2), 'SR 2012+': round(b[0], 2), 't 2012+': round(b[1], 2),
                  'datos hasta': s.dropna().index.max().strftime('%Y-%m')})
print(pd.DataFrame(filas).sort_values('t 2012+', ascending=False).to_string(index=False))
