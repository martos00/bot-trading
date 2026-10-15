"""
Version con coste/riesgo real de CPI Drift (continuacion de
hipotesis_cpi_drift.py tras un hallazgo direccionalmente consistente
en los 3 mercados -- no claramente significativo en todos, pero
tampoco una señal plana como FOMC/NFP). Regla UNICA, pre-registrada
ahora mismo, sin optimizar tras ver el backtest con coste:

 - LARGO incondicional al Open del dia de publicacion del IPC (mismo
   signo en los 3 mercados en la Fase 1).
 - SL protector: 1.5xATR14 (conocido al cierre del dia anterior).
 - Cierre: Close del dia SIGUIENTE a la publicacion (mismo horizonte
   de 2 dias medido en la Fase 1), o SL antes si se toca.
"""
import sys

import numpy as np
import pandas as pd

from orb_backtest import calcular_r_multiplos, metricas_en_r
from estrategia_gap_fade import calcular_atr_diario
from datos_multiactivo import cargar_universo, UNIVERSO
from hipotesis_cpi_drift import FECHAS_CPI, MERCADOS_PERMITIDOS

RIESGO_EN_ATR = 1.5
ESTRES_COSTE = [0.0, 1.0, 3.0]


def ejecutar(diario, fechas_cpi, point):
    d = diario.copy().reset_index(drop=True)
    d['atr14_prev'] = calcular_atr_diario(d).shift(1)
    d['dia_fecha'] = d['dia'].dt.date
    idx_por_fecha = {f: i for i, f in enumerate(d['dia_fecha'])}

    trades = []
    for fecha in fechas_cpi:
        idx_entrada = idx_por_fecha.get(fecha)
        if idx_entrada is None or idx_entrada + 1 >= len(d):
            continue
        if pd.isna(d['atr14_prev'].iloc[idx_entrada]) or d['atr14_prev'].iloc[idx_entrada] <= 0:
            continue
        precio_entrada = d['Open'].iloc[idx_entrada]
        riesgo = RIESGO_EN_ATR * d['atr14_prev'].iloc[idx_entrada]
        sl = precio_entrada - riesgo
        idx_salida_plazo = idx_entrada + 1

        resultado, motivo, idx_salida = None, None, idx_salida_plazo
        for j in range(idx_entrada, idx_salida_plazo + 1):
            if d['Low'].iloc[j] <= sl:
                resultado, motivo, idx_salida = sl, 'SL', j
                break
        if resultado is None:
            resultado, motivo, idx_salida = d['Close'].iloc[idx_salida_plazo], 'CIERRE_PLAZO', idx_salida_plazo

        ret_bruto = resultado - precio_entrada
        spread_entrada = d['Spread'].iloc[idx_entrada] * point if pd.notna(d['Spread'].iloc[idx_entrada]) else 0.0
        trades.append(dict(dia=d['dia'].iloc[idx_entrada], anio=d['dia'].iloc[idx_entrada].year, direccion='largo',
                            ret_bruto_puntos=ret_bruto, riesgo_puntos=riesgo, spread_entrada_precio=spread_entrada,
                            motivo_salida=motivo, peor_flotante_r=np.nan))
    return pd.DataFrame(trades)


def main():
    universo = cargar_universo(MERCADOS_PERMITIDOS)
    for nombre, diario in universo.items():
        point = UNIVERSO[nombre]['point']
        ops = ejecutar(diario, FECHAS_CPI, point)
        print(f"\n######## CPI Drift (largo, con coste) -- {nombre} ########")
        print(f"Operaciones: {len(ops)}")
        if len(ops) == 0:
            print("  SIN OPERACIONES.")
            continue
        print(f"  Motivo salida: {ops['motivo_salida'].value_counts().to_dict()}")
        for extra in ESTRES_COSTE:
            etiqueta = "solo spread real" if extra == 0.0 else f"spread real + {extra:.0f} estres"
            ops_r = calcular_r_multiplos(ops, extra)
            m = metricas_en_r(ops_r)
            print(f"  [{etiqueta}] n={m['n']}  Media R={m['media_R']:+.4f}  PF={m['profit_factor']:.3f}  "
                  f"%Acierto={m['pct_acierto']:.1f}%  Drawdown={m['max_drawdown_balance_R']:.2f}R")
            if extra == 0.0:
                for anio, g in ops_r.groupby('anio'):
                    mg = metricas_en_r(g)
                    print(f"      {anio}: n={mg['n']}  Media R={mg['media_R']:+.4f}  PF={mg['profit_factor']:.3f}")


if __name__ == '__main__':
    main()
