"""
Segunda candidata bajo el proceso rapido de 3 etapas (ver README).

Hipotesis: Time Series Momentum (Moskowitz, Ooi & Pedersen, "Time
Series Momentum", Journal of Financial Economics, 2012) -- uno de los
hallazgos mas robustos y replicados de la literatura cuantitativa: el
signo del retorno de los ultimos 12 meses de un activo predice el
signo de su retorno del mes siguiente, documentado de forma consistente
en decadas de datos y en practicamente todas las clases de activo
(incluidos indices de acciones y materias primas como el oro -- a
diferencia de las 4 hipotesis anteriores, que eran todas especificas de
acciones/anuncios de EEUU). Fundamento: subreaccion inicial a la
informacion (difusion lenta) + demanda de cobertura institucional que
genera persistencia de tendencia, no reversion inmediata.

REGLAS (unica version, sencilla, pre-registrada, sin optimizar):
 - Barra diaria agregada desde M15 (misma funcion ya usada en el resto
   del proyecto) -- funciona igual en los 3 mercados sin depender de
   reconstruccion horaria intradia.
 - Al CIERRE del ultimo dia de sesion de cada mes M: retorno de los
   ultimos 252 dias de sesion (~12 meses), ret_12m = Close[hoy]/Close[hace
   252 dias]-1. Si no hay suficiente historial (menos de 252 dias
   previos), no hay señal ese mes.
 - Direccion: LARGO si ret_12m>0; CORTO si ret_12m<0 (sin zona neutra,
   igual que el paper original).
 - Entrada: Open del primer dia de sesion del mes M+1 (señal generada
   al cierre de M, sin lookahead).
 - Salida objetivo: Close del ULTIMO dia de sesion del mes M+1 (se
   reevalua la señal cada mes -- una "operacion" por mes y mercado).
 - Stop-loss de proteccion (ADAPTACION NUESTRA, no parte del paper
   original -- el momentum de series temporales clasico no usa un SL
   fijo, pero el framework de este proyecto necesita un riesgo inicial
   para la contabilidad en R): 2x ATR(20) diario, conocido al cierre
   del mes anterior, sin lookahead.
 - Si se toca el SL antes de fin de mes: se cierra ahi (motivo SL). Si
   no: se cierra al Close del ultimo dia del mes (motivo CIERRE_MES).
 - Costes: mismo motor en R-multiplos, spread real (primera vela M15
   del dia de entrada) + escenarios de estres ya establecidos.
"""
import sys

import numpy as np
import pandas as pd

from orb_backtest import EXTRA_PUNTOS_ESTRES, calcular_r_multiplos, metricas_en_r
from hipotesis_rsi2_sma200 import cargar_m15, agregar_diario
from estrategia_gap_fade import agregar_diario_con_spread, calcular_atr_diario

MESES_LOOKBACK_DIAS = 252
ATR_PERIODO_SL = 20
SL_EN_ATR = 2.0


def construir_tabla_momentum(diario):
    d = diario.copy().reset_index(drop=True)
    d['atr20'] = calcular_atr_diario(d, periodo=ATR_PERIODO_SL)
    d['mes'] = d['dia'].dt.month
    d['anio_mes'] = d['dia'].dt.year
    cambia_mes = d['mes'].shift(-1) != d['mes']
    idx_fin_mes = d.index[cambia_mes & d['mes'].shift(-1).notna()].to_numpy()
    return d, idx_fin_mes


def ejecutar_momentum(diario, point):
    d, idx_fin_mes = construir_tabla_momentum(diario)
    operaciones = []

    for k in range(len(idx_fin_mes) - 1):
        idx_fin_actual = idx_fin_mes[k]
        idx_fin_siguiente = idx_fin_mes[k + 1]
        idx_entrada = idx_fin_actual + 1
        if idx_entrada > idx_fin_siguiente or idx_entrada >= len(d):
            continue
        if idx_fin_actual < MESES_LOOKBACK_DIAS:
            continue  # historial insuficiente para el retorno de 12 meses

        ret_12m = d['Close'].iloc[idx_fin_actual] / d['Close'].iloc[idx_fin_actual - MESES_LOOKBACK_DIAS] - 1.0
        if ret_12m == 0 or pd.isna(ret_12m):
            continue
        direccion = 'largo' if ret_12m > 0 else 'corto'

        atr_entrada = d['atr20'].iloc[idx_fin_actual]
        if pd.isna(atr_entrada) or atr_entrada <= 0:
            continue

        precio_entrada = d['Open'].iloc[idx_entrada]
        riesgo = SL_EN_ATR * atr_entrada
        if direccion == 'largo':
            sl = precio_entrada - riesgo
        else:
            sl = precio_entrada + riesgo

        resultado_precio, motivo = None, None
        for j in range(idx_entrada, idx_fin_siguiente + 1):
            hi, lo = d['High'].iloc[j], d['Low'].iloc[j]
            if direccion == 'largo':
                toca_sl = lo <= sl
            else:
                toca_sl = hi >= sl
            if toca_sl:
                resultado_precio, motivo = sl, 'SL'
                break
        if resultado_precio is None:
            resultado_precio, motivo = d['Close'].iloc[idx_fin_siguiente], 'CIERRE_MES'

        ret_bruto = (resultado_precio - precio_entrada) if direccion == 'largo' else (precio_entrada - resultado_precio)
        spread_entrada = d['Spread'].iloc[idx_entrada] * point if pd.notna(d['Spread'].iloc[idx_entrada]) else 0.0

        operaciones.append(dict(
            dia=d['dia'].iloc[idx_entrada], anio=d['dia'].iloc[idx_entrada].year, direccion=direccion,
            ret_12m=ret_12m, precio_entrada=precio_entrada, sl=sl,
            resultado_precio=resultado_precio, motivo_salida=motivo,
            ret_bruto_puntos=ret_bruto, riesgo_puntos=riesgo,
            spread_entrada_precio=spread_entrada, peor_flotante_r=np.nan,
        ))

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
              f"PF={m['profit_factor']:.3f}  %Acierto={m['pct_acierto']:.1f}%  "
              f"Drawdown balance={m['max_drawdown_balance_R']:.2f}R")
        for anio, g in ops_r.groupby('anio'):
            mg = metricas_en_r(g)
            print(f"    {anio}: n={mg['n']}  Suma R={mg['suma_R']:+.2f}  Media R={mg['media_R']:+.4f}  PF={mg['profit_factor']:.3f}")
    print("\n  Direccion:", ops['direccion'].value_counts().to_dict())
    print("  Motivo de salida:", ops['motivo_salida'].value_counts().to_dict())


def main(rutas):
    for nombre, path in rutas.items():
        df = cargar_m15(path)
        diario = agregar_diario_con_spread(df)
        ops = ejecutar_momentum(diario, point=0.01)
        resumen(nombre, ops)


if __name__ == '__main__':
    main({'USTEC': sys.argv[1], 'US500': sys.argv[2], 'XAUUSD': sys.argv[3]})
