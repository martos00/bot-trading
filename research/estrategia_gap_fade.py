"""
Primera candidata bajo el nuevo proceso rapido (ver README): hipotesis
con fundamento -> version unica completa -> backtest con costes ->
descartar si es negativa sin optimizar.

Hipotesis: Gap Fade de apertura. Fundamento: los gaps entre el cierre
de una sesion y la apertura de la siguiente reflejan a menudo
desequilibrios de liquidez de las horas de baja negociacion (overnight),
que se corrigen parcialmente cuando vuelve la liquidez normal de sesion
-- patron ampliamente documentado en la practica de trading de indices
("fade the gap"). Aqui se construye en barra DIARIA (no M15/sesion RTH)
precisamente para poder probar los 3 mercados sin depender de la
reconstruccion horaria intradia -- que ya sabemos que no es fiable en
XAUUSD.

REGLAS (unica version, pre-registrada, sin optimizar):
 - Barra diaria agregada desde M15 por fecha de calendario del servidor
   (misma funcion ya usada en RSI(2)/turno de mes).
 - ATR(14) diario (Wilder), causal.
 - Gap relativo: gap_rel[t] = (Open[t]-Close[t-1]) / ATR14[t-1] (ATR
   conocido el cierre del dia anterior -- sin lookahead).
 - Señal: |gap_rel[t]| > 0.5 (umbral clasico de la practica de gap
   trading -- medio ATR -- NO calibrado con nuestros datos).
 - Direccion: FADE (contraria al gap) -- gap alcista => corto; gap
   bajista => largo.
 - Entrada: Open[t] (el gap ya es observable en el momento de esa
   apertura, no hay informacion futura implicada).
 - Stop-loss: 1.0 ATR14[t-1] en contra de la entrada (riesgo = 1 ATR,
   conocido en el momento de entrar).
 - Take-profit: Close[t-1] (el cierre previo -- el nivel natural de
   "gap cerrado del todo").
 - Si se tocan SL y TP el mismo dia (ambiguedad OHLC diario): gana el
   SL (misma convencion conservadora del resto del proyecto).
 - Si no se toca ninguno: se cierra al Close[t] (mismo dia, sin
   mantener posiciones varios dias).
 - Costes: mismo motor en R-multiplos que el resto del proyecto --
   spread real (el de la primera vela M15 del dia) + escenarios de
   estres (0/1/3 puntos).
"""
import sys

import numpy as np
import pandas as pd

from orb_backtest import EXTRA_PUNTOS_ESTRES, calcular_r_multiplos, metricas_en_r
from hipotesis_rsi2_sma200 import cargar_m15, agregar_diario

UMBRAL_GAP_ATR = 0.5
ATR_PERIODO = 14


def calcular_atr_diario(diario, periodo=ATR_PERIODO):
    hi, lo, cl_prev = diario['High'], diario['Low'], diario['Close'].shift(1)
    tr = pd.concat([hi - lo, (hi - cl_prev).abs(), (lo - cl_prev).abs()], axis=1).max(axis=1)
    return tr.ewm(alpha=1.0 / periodo, adjust=False).mean()


def agregar_diario_con_spread(df):
    diario = agregar_diario(df)
    d2 = df.copy()
    d2['dia'] = d2['TimestampServidor'].dt.normalize()
    spread_apertura = d2.groupby('dia')['Spread'].first().reset_index()
    return diario.merge(spread_apertura, on='dia', how='left')


def ejecutar_gap_fade(diario, point):
    d = diario.copy().reset_index(drop=True)
    d['atr14'] = calcular_atr_diario(d)
    d['atr14_prev'] = d['atr14'].shift(1)
    d['close_prev'] = d['Close'].shift(1)
    d['gap_rel'] = (d['Open'] - d['close_prev']) / d['atr14_prev']

    operaciones = []
    for i in range(1, len(d)):
        row = d.iloc[i]
        if pd.isna(row['gap_rel']) or pd.isna(row['atr14_prev']) or row['atr14_prev'] <= 0:
            continue
        if abs(row['gap_rel']) <= UMBRAL_GAP_ATR:
            continue

        direccion = 'corto' if row['gap_rel'] > 0 else 'largo'
        precio_entrada = row['Open']
        riesgo = row['atr14_prev'] * 1.0
        if direccion == 'largo':
            sl = precio_entrada - riesgo
            tp = row['close_prev']
        else:
            sl = precio_entrada + riesgo
            tp = row['close_prev']
        if tp == precio_entrada:
            continue
        # si el TP (cierre previo) queda del lado equivocado (gap tan grande
        # que el cierre previo esta mas alla del SL), no hay operacion valida
        if direccion == 'largo' and tp <= sl:
            continue
        if direccion == 'corto' and tp >= sl:
            continue

        riesgo_real = abs(precio_entrada - sl)
        hi, lo = row['High'], row['Low']
        if direccion == 'largo':
            toca_sl, toca_tp = lo <= sl, hi >= tp
        else:
            toca_sl, toca_tp = hi >= sl, lo <= tp

        if toca_sl:
            resultado_precio, motivo = sl, 'SL'
        elif toca_tp:
            resultado_precio, motivo = tp, 'TP'
        else:
            resultado_precio, motivo = row['Close'], 'CIERRE_DIA'

        ret_bruto = (resultado_precio - precio_entrada) if direccion == 'largo' else (precio_entrada - resultado_precio)
        spread_entrada = row['Spread'] * point if pd.notna(row['Spread']) else 0.0

        operaciones.append(dict(
            dia=row['dia'], anio=row['dia'].year, direccion=direccion,
            gap_rel=row['gap_rel'], precio_entrada=precio_entrada, sl=sl, tp=tp,
            resultado_precio=resultado_precio, motivo_salida=motivo,
            ret_bruto_puntos=ret_bruto, riesgo_puntos=riesgo_real,
            spread_entrada_precio=spread_entrada,
            peor_flotante_r=np.nan,
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
    print("\n  Motivo de salida:", ops['motivo_salida'].value_counts().to_dict())


def main(rutas):
    for nombre, path in rutas.items():
        df = cargar_m15(path)
        diario = agregar_diario_con_spread(df)
        ops = ejecutar_gap_fade(diario, point=0.01)
        resumen(nombre, ops)


if __name__ == '__main__':
    main({'USTEC': sys.argv[1], 'US500': sys.argv[2], 'XAUUSD': sys.argv[3]})
