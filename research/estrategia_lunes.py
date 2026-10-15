"""
Candidata (ciclo autonomo): Efecto Lunes (day-of-week).
Fundamento: anomalia clasica documentada (French, 1980, y decadas de
literatura posterior) -- el retorno medio del lunes historicamente
distinto (mas bajo/negativo) que el resto de dias, atribuido a flujo de
noticias/ventas acumuladas durante el fin de semana. Nota: ampliamente
reconocido en la literatura reciente como DEBILITADO/inconsistente tras
su publicacion -- se prueba de todos modos por ser rapido y con muestra
grande garantizada.

Viabilidad: ~190+ lunes en la muestra por mercado, sin dependencia
horaria intradia, variacion real (retorno de cada lunes).

REGLAS: CORTO al Open del lunes, cubrir al Close del mismo lunes
(apuesta a la anomalia historica de retorno negativo). SL=1.5xATR14.
Sin TP explicito -- cierre al Close si no toca el SL.
"""
import sys

import numpy as np
import pandas as pd

from orb_backtest import EXTRA_PUNTOS_ESTRES, calcular_r_multiplos, metricas_en_r
from hipotesis_rsi2_sma200 import cargar_m15
from estrategia_gap_fade import agregar_diario_con_spread, calcular_atr_diario

SL_EN_ATR = 1.5


def ejecutar(diario, point):
    d = diario.copy().reset_index(drop=True)
    d['atr14'] = calcular_atr_diario(d, periodo=14)
    d['atr14_prev'] = d['atr14'].shift(1)
    d['dow'] = d['dia'].dt.dayofweek

    operaciones = []
    for i in range(1, len(d)):
        if d['dow'].iloc[i] != 0:  # 0 = lunes
            continue
        atr_prev = d['atr14_prev'].iloc[i]
        if pd.isna(atr_prev) or atr_prev <= 0:
            continue
        precio_entrada = d['Open'].iloc[i]
        riesgo = SL_EN_ATR * atr_prev
        sl = precio_entrada + riesgo  # corto
        hi, lo = d['High'].iloc[i], d['Low'].iloc[i]
        if hi >= sl:
            resultado, motivo = sl, 'SL'
        else:
            resultado, motivo = d['Close'].iloc[i], 'CIERRE_DIA'
        ret_bruto = precio_entrada - resultado
        spread_entrada = d['Spread'].iloc[i] * point if pd.notna(d['Spread'].iloc[i]) else 0.0
        operaciones.append(dict(
            dia=d['dia'].iloc[i], anio=d['dia'].iloc[i].year, direccion='corto',
            ret_bruto_puntos=ret_bruto, riesgo_puntos=riesgo, spread_entrada_precio=spread_entrada,
            motivo_salida=motivo, peor_flotante_r=np.nan,
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
