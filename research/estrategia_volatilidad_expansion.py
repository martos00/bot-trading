"""
Candidata (ciclo autonomo, ver README): Volatility Expansion Continuation.
Fundamento: tras un dia de expansion de rango claramente por encima de lo
habitual, con cierre direccional, el movimiento tiende a continuar al dia
siguiente (ruptura de volatilidad confirmada por el propio rango, patron
documentado en trading de "volatility breakout"). Familia distinta de
momentum direccional puro (B se activa por EXPANSION DE RANGO, no por
signo de retorno acumulado).

Viabilidad: datos de precio diario ya verificados que permiten medir
rango/ATR; sin dependencia horaria intradia; variacion real esperada
(los dias de expansion de rango no son raros ni universales); numero de
oportunidades a verificar en ejecucion.

REGLAS (unica version, sin optimizar):
 - rango[t] = High[t]-Low[t]; "dia de expansion" si rango[t] > 1.5*ATR14[t-1].
 - Direccion = la del propio dia de expansion (Close[t]>Open[t] => largo;
   si no, corto) -- continuacion, no reversion.
 - Entrada: Open[t+1] (sin lookahead).
 - SL: el extremo opuesto del propio dia de expansion (Low si largo, High
   si corto).
 - TP: 2R (misma convencion que el resto del proyecto).
 - Cierre forzoso: 5 dias de sesion si no se toca SL/TP antes.
"""
import sys

import numpy as np
import pandas as pd

from orb_backtest import EXTRA_PUNTOS_ESTRES, calcular_r_multiplos, metricas_en_r
from hipotesis_rsi2_sma200 import cargar_m15, agregar_diario
from estrategia_gap_fade import agregar_diario_con_spread, calcular_atr_diario

UMBRAL_EXPANSION_ATR = 1.5
TP_EN_R = 2.0
DIAS_MAX_EN_MERCADO = 5


def ejecutar(diario, point):
    d = diario.copy().reset_index(drop=True)
    d['atr14'] = calcular_atr_diario(d, periodo=14)
    d['atr14_prev'] = d['atr14'].shift(1)
    d['rango'] = d['High'] - d['Low']

    operaciones = []
    for i in range(1, len(d) - 1):
        row = d.iloc[i]
        if pd.isna(row['atr14_prev']) or row['atr14_prev'] <= 0:
            continue
        if row['rango'] <= UMBRAL_EXPANSION_ATR * row['atr14_prev']:
            continue

        direccion = 'largo' if row['Close'] > row['Open'] else 'corto'
        idx_entrada = i + 1
        precio_entrada = d['Open'].iloc[idx_entrada]
        if direccion == 'largo':
            sl = row['Low']
            riesgo = precio_entrada - sl
            tp = precio_entrada + TP_EN_R * riesgo
        else:
            sl = row['High']
            riesgo = sl - precio_entrada
            tp = precio_entrada - TP_EN_R * riesgo
        if riesgo <= 0:
            continue

        idx_fin = min(idx_entrada + DIAS_MAX_EN_MERCADO, len(d) - 1)
        resultado_precio, motivo = None, None
        for j in range(idx_entrada, idx_fin + 1):
            hi, lo = d['High'].iloc[j], d['Low'].iloc[j]
            if direccion == 'largo':
                toca_sl, toca_tp = lo <= sl, hi >= tp
            else:
                toca_sl, toca_tp = hi >= sl, lo <= tp
            if toca_sl:
                resultado_precio, motivo = sl, 'SL'
                break
            if toca_tp:
                resultado_precio, motivo = tp, 'TP'
                break
        if resultado_precio is None:
            resultado_precio, motivo = d['Close'].iloc[idx_fin], 'CIERRE_PLAZO'

        ret_bruto = (resultado_precio - precio_entrada) if direccion == 'largo' else (precio_entrada - resultado_precio)
        spread_entrada = d['Spread'].iloc[idx_entrada] * point if pd.notna(d['Spread'].iloc[idx_entrada]) else 0.0
        operaciones.append(dict(
            dia=d['dia'].iloc[idx_entrada], anio=d['dia'].iloc[idx_entrada].year, direccion=direccion,
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
    print(f"  Direccion: {ops['direccion'].value_counts().to_dict()}")
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
