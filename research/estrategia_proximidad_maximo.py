"""
Candidata (ciclo autonomo): Proximidad al maximo de 252 dias (familia
52-week-high, George & Hwang 2004) -- distinta del Time Series Momentum
ya probado: aqui la señal es CONTINUA (distancia al maximo reciente),
no el signo binario del retorno de 12 meses, por lo que si mostro
variacion real en el cribado de viabilidad (29.8%-50.5% de los dias a
menos del 1% del maximo, resto mas lejos).

Fundamento: los activos cerca de su maximo de 52 semanas tienden a
continuar su tendencia (infrarreaccion a buenas noticias que llevan a
nuevos maximos); lejos del maximo, el comportamiento es mas incierto/
de reversion.

REGLAS: cada dia, dist = Close/Max252 - 1. Señal LARGA si dist>-1%
(a menos del 1% del maximo de 252d) Y no se tenia posicion abierta ese
dia. Entrada: Open[t+1]. SL: 2xATR14. Salida: cuando dist cae por
debajo de -3% (se aleja claramente del maximo) o cierre forzoso a 20
dias de sesion, lo que ocurra primero (ademas del SL).
"""
import sys

import numpy as np
import pandas as pd

from orb_backtest import EXTRA_PUNTOS_ESTRES, calcular_r_multiplos, metricas_en_r
from hipotesis_rsi2_sma200 import cargar_m15
from estrategia_gap_fade import agregar_diario_con_spread, calcular_atr_diario

UMBRAL_ENTRADA = -0.01
UMBRAL_SALIDA = -0.03
DIAS_MAX_EN_MERCADO = 20


def ejecutar(diario, point):
    d = diario.copy().reset_index(drop=True)
    d['atr14'] = calcular_atr_diario(d, periodo=14)
    d['max252'] = d['Close'].rolling(252).max()
    d['dist'] = d['Close'] / d['max252'] - 1.0

    operaciones = []
    i = 252
    while i < len(d) - 1:
        if pd.isna(d['dist'].iloc[i]) or d['dist'].iloc[i] < UMBRAL_ENTRADA:
            i += 1
            continue
        atr_prev = d['atr14'].iloc[i]
        if pd.isna(atr_prev) or atr_prev <= 0:
            i += 1
            continue
        idx_entrada = i + 1
        precio_entrada = d['Open'].iloc[idx_entrada]
        riesgo = 2.0 * atr_prev
        sl = precio_entrada - riesgo

        idx_fin = min(idx_entrada + DIAS_MAX_EN_MERCADO, len(d) - 1)
        resultado, motivo, idx_salida = None, None, idx_fin
        for j in range(idx_entrada, idx_fin + 1):
            if d['Low'].iloc[j] <= sl:
                resultado, motivo, idx_salida = sl, 'SL', j
                break
            if not pd.isna(d['dist'].iloc[j]) and d['dist'].iloc[j] < UMBRAL_SALIDA:
                resultado, motivo, idx_salida = d['Close'].iloc[j], 'ALEJAMIENTO_MAXIMO', j
                break
        if resultado is None:
            resultado, motivo, idx_salida = d['Close'].iloc[idx_fin], 'CIERRE_PLAZO', idx_fin

        ret_bruto = resultado - precio_entrada
        spread_entrada = d['Spread'].iloc[idx_entrada] * point if pd.notna(d['Spread'].iloc[idx_entrada]) else 0.0
        operaciones.append(dict(
            dia=d['dia'].iloc[idx_entrada], anio=d['dia'].iloc[idx_entrada].year, direccion='largo',
            ret_bruto_puntos=ret_bruto, riesgo_puntos=riesgo, spread_entrada_precio=spread_entrada,
            motivo_salida=motivo, peor_flotante_r=np.nan,
        ))
        i = idx_salida + 1  # no solapar operaciones del mismo activo

    return pd.DataFrame(operaciones)


def resumen(nombre, ops):
    print(f"\n\n######## {nombre} ########")
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


def main(rutas):
    for nombre, path in rutas.items():
        df = cargar_m15(path)
        diario = agregar_diario_con_spread(df)
        ops = ejecutar(diario, point=0.01)
        resumen(nombre, ops)


if __name__ == '__main__':
    main({'USTEC': sys.argv[1], 'US500': sys.argv[2], 'XAUUSD': sys.argv[3]})
