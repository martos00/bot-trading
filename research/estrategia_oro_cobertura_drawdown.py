"""
Candidata (ciclo autonomo): Oro como cobertura durante drawdowns de
renta variable. Fundamento: demanda de activo refugio documentada
durante caidas fuertes de bolsa (flight-to-safety). Familia cross-asset
distinta de la rotacion mensual ya probada: aqui la señal es un
DRAWDOWN RECIENTE de USTEC (no un retorno relativo mensual), y la
entrada es inmediata (intradia siguiente), no mensual.

REGLAS: drawdown_ustec[t] = Close_USTEC[t]/Max20d_USTEC[t] - 1. Si
drawdown_ustec[t] < -5% (caida de al menos 5% desde el maximo de 20
dias), LARGO XAUUSD al Open[t+1]. SL=2xATR14(oro). Salida: cuando el
drawdown de USTEC se recupera por encima de -2%, o cierre forzoso a 15
dias de sesion, lo que ocurra primero (ademas del SL).
"""
import sys

import numpy as np
import pandas as pd

from orb_backtest import EXTRA_PUNTOS_ESTRES, calcular_r_multiplos, metricas_en_r
from hipotesis_rsi2_sma200 import cargar_m15, agregar_diario
from estrategia_gap_fade import agregar_diario_con_spread, calcular_atr_diario

UMBRAL_DD_ENTRADA = -0.05
UMBRAL_DD_SALIDA = -0.02
DIAS_MAX_EN_MERCADO = 15


def main(path_ustec, path_oro):
    d_ustec = agregar_diario(cargar_m15(path_ustec)).set_index('dia')
    d_ustec['max20'] = d_ustec['Close'].rolling(20).max()
    d_ustec['dd'] = d_ustec['Close'] / d_ustec['max20'] - 1.0

    d_oro = agregar_diario_con_spread(cargar_m15(path_oro)).reset_index(drop=True)
    d_oro['atr14'] = calcular_atr_diario(d_oro, periodo=14)

    dd_por_dia = d_ustec['dd']
    operaciones = []
    i = 20
    en_posicion_hasta = -1
    while i < len(d_oro) - 1:
        dia = d_oro['dia'].iloc[i]
        dd_hoy = dd_por_dia.asof(dia) if dia in dd_por_dia.index or True else np.nan
        try:
            dd_hoy = dd_por_dia.loc[dd_por_dia.index <= dia].iloc[-1]
        except IndexError:
            i += 1
            continue
        if pd.isna(dd_hoy) or dd_hoy > UMBRAL_DD_ENTRADA or i <= en_posicion_hasta:
            i += 1
            continue

        atr_prev = d_oro['atr14'].iloc[i]
        if pd.isna(atr_prev) or atr_prev <= 0:
            i += 1
            continue
        idx_entrada = i + 1
        precio_entrada = d_oro['Open'].iloc[idx_entrada]
        riesgo = 2.0 * atr_prev
        sl = precio_entrada - riesgo

        idx_fin = min(idx_entrada + DIAS_MAX_EN_MERCADO, len(d_oro) - 1)
        resultado, motivo, idx_salida = None, None, idx_fin
        for j in range(idx_entrada, idx_fin + 1):
            if d_oro['Low'].iloc[j] <= sl:
                resultado, motivo, idx_salida = sl, 'SL', j
                break
            dia_j = d_oro['dia'].iloc[j]
            try:
                dd_j = dd_por_dia.loc[dd_por_dia.index <= dia_j].iloc[-1]
            except IndexError:
                dd_j = np.nan
            if not pd.isna(dd_j) and dd_j > UMBRAL_DD_SALIDA:
                resultado, motivo, idx_salida = d_oro['Close'].iloc[j], 'RECUPERACION_USTEC', j
                break
        if resultado is None:
            resultado, motivo, idx_salida = d_oro['Close'].iloc[idx_fin], 'CIERRE_PLAZO', idx_fin

        ret_bruto = resultado - precio_entrada
        spread_entrada = d_oro['Spread'].iloc[idx_entrada] * 0.01 if pd.notna(d_oro['Spread'].iloc[idx_entrada]) else 0.0
        operaciones.append(dict(
            dia=d_oro['dia'].iloc[idx_entrada], anio=d_oro['dia'].iloc[idx_entrada].year, direccion='largo',
            ret_bruto_puntos=ret_bruto, riesgo_puntos=riesgo, spread_entrada_precio=spread_entrada,
            motivo_salida=motivo, peor_flotante_r=np.nan,
        ))
        en_posicion_hasta = idx_salida
        i = idx_salida + 1

    ops = pd.DataFrame(operaciones)
    print(f"\n\n######## XAUUSD (señal: drawdown de USTEC) ########")
    print(f"Operaciones totales: {len(ops)}")
    if len(ops) == 0:
        print("  SIN OPERACIONES.")
        return
    for extra in EXTRA_PUNTOS_ESTRES:
        etiqueta = f"spread real + {extra:.0f} pts estres" if extra > 0 else "SOLO spread real"
        ops_r = calcular_r_multiplos(ops, extra)
        m = metricas_en_r(ops_r)
        print(f"\n--- {etiqueta} ---")
        print(f"  n={m['n']}  Suma R={m['suma_R']:+.2f}  Media R={m['media_R']:+.4f}  "
              f"PF={m['profit_factor']:.3f}  %Acierto={m['pct_acierto']:.1f}%  Drawdown={m['max_drawdown_balance_R']:.2f}R")
        for anio, g in ops_r.groupby('anio'):
            mg = metricas_en_r(g)
            print(f"    {anio}: n={mg['n']}  Suma R={mg['suma_R']:+.2f}  Media R={mg['media_R']:+.4f}  PF={mg['profit_factor']:.3f}")
    print("  Motivo salida:", ops['motivo_salida'].value_counts().to_dict())


if __name__ == '__main__':
    main(sys.argv[1], sys.argv[2])
