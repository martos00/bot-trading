"""Paso 2 — ¿Cuánto queda de la ventaja certificada C1 (EURUSD corto 06→08 ET) con los costes de cada sitio?
Coste ida y vuelta = comisión por lote (100.000 EUR) + spread pagado una vez (corto al BID a las 06:00, recompra al ASK a las
08:00: con el punto medio como referencia se pagan dos medios spreads) + deslizamiento 0,1 pb.
Uso: python3 paso2_costes_eurusd.py c1_precios.csv"""
import sys
import numpy as np
import pandas as pd
from c1_certificacion import t_nw

x = pd.read_csv(sys.argv[1], index_col=0, parse_dates=True)
r = -np.log(x.mid8 / x.mid6)
spread = ((x.spr6 + x.spr8) / 2).median()            # pb, medido en FXCM/Dukascopy a esas horas
nocional = 100_000 * x.mid6.loc['2025':].mean()       # $ por lote estándar
print(f'Ventaja bruta {r.mean() * 1e4:.2f} pb/día; spread mediano medido {spread:.2f} pb; 1 lote ≈ {nocional:,.0f} $ (1 pb = {nocional / 1e4:.1f} $)')
SITIOS = [  # nombre, comisión ida y vuelta por lote en $ (rango de fuentes), multiplicador de spread frente al medido
    ('FundingPips (2 $ i/v, Benzinga)', 2.0, 1.0), ('FundingPips (2,50 $ por lado)', 5.0, 1.0),
    ('FTMO (3 $ i/v, Investing/Propvator)', 3.0, 1.0), ('FTMO (3 $ por lado, foro)', 6.0, 1.0),
    ('FundedNext (5 $ i/v)', 5.0, 1.0), ('FundedNext (5 $ por lado)', 10.0, 1.0),
    ('ECN minorista, IC Markets (7 $ i/v + 0,1 pip)', 7.0, 1.0),
    ('Futuros 6E en Topstep (1 tick + 3,20 $ tasas + 1 $; nocional 125k EUR)', None, None),
]
filas = []
for nom, com, ms in SITIOS:
    if com is None:
        coste = (6.25 + 3.20 + 1.0) / (125_000 * x.mid6.loc['2025':].mean()) * 1e4 + 0.1
    else:
        coste = com / nocional * 1e4 + spread * ms + 0.1
    n = r.dropna() - coste / 1e4
    filas.append({'sitio': nom, 'coste_pb': round(coste, 2), 'ventaja/coste': round(r.mean() * 1e4 / coste, 2),
                  'neto_pb': round(n.mean() * 1e4, 2), 't_neto': round(t_nw(n), 2),
                  'Sharpe_anual_neto': round(n.mean() / n.std() * np.sqrt(252), 2),
                  'años_netos_positivos': f"{(n.groupby(n.index.year).mean() > 0).sum()}/9"})
pd.set_option('display.width', 250)
print(pd.DataFrame(filas).to_string(index=False))
