"""Verificación de C9 (regla del 80% de Dalton) con ES de Databento (futuro real, M1), reglas idénticas a c9_regla_80_dalton.py.
Se excluyen los días en que el contrato de hoy no es el de ayer (cambio de contrato). Uso: python3 v_databento_c9.py ES_1m.pkl"""
import sys
import numpy as np, pandas as pd
import c9_regla_80_dalton as C9
x = pd.read_pickle(sys.argv[1])
t = pd.to_datetime(x.ts_event).dt.tz_convert('America/New_York').dt.tz_localize(None)
x = x.assign(t=t).set_index('t').sort_index()
m = x.index.hour * 60 + x.index.minute
x = x[(m >= 570) & (m < 960) & (x.index.weekday < 5)].copy()
x['dia'] = x.index.normalize(); x['per'] = (x.index.hour * 60 + x.index.minute - 570) // 30
contrato = x.groupby('dia').instrument_id.agg(lambda s: s.mode().iloc[0])
ops = C9.operar(x[['o' if 'o' in x else 'open', 'high', 'low', 'close', 'dia', 'per']].rename(columns={'open': 'o', 'high': 'h', 'low': 'l', 'close': 'c'}))
dias = contrato.index
cambio = pd.Series(contrato.values != np.r_[np.nan, contrato.values[:-1]], index=dias)
ops = ops[~cambio.reindex(ops.index).fillna(True).values]
ops.to_csv('v_databento_c9_ops.csv')
C9.informe(ops, 'ES (Databento), sin días de cambio de contrato')
