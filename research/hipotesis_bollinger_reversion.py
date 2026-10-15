"""
Hipotesis C del nuevo ciclo: Bollinger Band Mean Reversion (diaria).

Fundamento economico: un cierre fuera de +-2 desviaciones tipicas de su
media de 20 dias refleja una extension de precio estadisticamente
inusual que tiende a revertir parcialmente hacia la media (mean
reversion clasica de bandas de Bollinger) -- mecanismo DISTINTO de
RSI(2) (oscilador de momentum) aunque ambas sean "mean reversion":
aqui la señal es distancia de PRECIO a su media en desviaciones
tipicas, no un oscilador acotado 0-100, y el objetivo es la propia
media (no 2R fijo) -- igual filosofia que Gap Fade (TP = nivel natural,
no multiplo fijo de riesgo).

VIABILIDAD (comprobada antes de programar):
 - Bandas de Bollinger(20,2) son estandar, no calibradas con estos
   datos. Un precio en cierre fuera de banda no es raro ni universal
   (tipicamente ~5% de los dias en una serie con distribucion
   razonablemente normal) -- variacion real esperada.
 - Objetivo (SMA20) y riesgo (ATR14) ya estan disponibles sin
   dependencia horaria intradia.

REGLAS (unica version, pre-registrada, sin optimizar):
 - SMA20 y desviacion tipica de 20 dias sobre el Close diario (barra
   cerrada, causal). Banda inferior = SMA20-2*std20, superior =
   SMA20+2*std20.
 - Señal: Close[t] <= banda_inferior[t] => LARGO (sobreventa). Close[t]
   >= banda_superior[t] => CORTO (sobrecompra).
 - Entrada: Open[t+1] (sin lookahead).
 - SL: 1.5*ATR14[t-1] en contra de la entrada (mismo tipo de unidad de
   riesgo que el resto del proyecto, NO ligado al ancho de la propia
   banda para no mezclar la señal con el riesgo).
 - TP: SMA20[t] (el nivel de reversion natural -- la propia media que
   genero la señal, igual filosofia que el TP de Gap Fade).
 - Si se tocan SL y TP el mismo dia: gana el SL (convencion
   conservadora de siempre). Cierre forzoso: 5 dias de sesion.
"""
import sys

import numpy as np
import pandas as pd

from orb_backtest import calcular_r_multiplos, metricas_en_r
from validacion_independiente_volexp import calcular_equity_simultanea, control_direccion_aleatoria
from regimenes_mercado import resumen_por_regimen
from datos_ciclo2 import MERCADOS

PERIODO_BB = 20
DESV_BB = 2.0
RIESGO_EN_ATR = 1.5
DIAS_MAX_EN_MERCADO = 5
ESTRES_COSTE = [0.0, 1.0, 3.0]
SEED = 20261015


def ejecutar(d, point):
    d = d.copy().reset_index(drop=True)
    d['sma20'] = d['Close'].rolling(PERIODO_BB).mean()
    d['std20'] = d['Close'].rolling(PERIODO_BB).std()
    d['banda_inf'] = d['sma20'] - DESV_BB * d['std20']
    d['banda_sup'] = d['sma20'] + DESV_BB * d['std20']

    trades = []
    for i in range(1, len(d) - 1):
        row = d.iloc[i]
        if pd.isna(row['atr14_prev']) or row['atr14_prev'] <= 0 or pd.isna(row['sma20']):
            continue
        if row['Close'] <= row['banda_inf']:
            direccion = 'largo'
        elif row['Close'] >= row['banda_sup']:
            direccion = 'corto'
        else:
            continue

        idx_entrada = i + 1
        precio_entrada = d['Open'].iloc[idx_entrada]
        riesgo = RIESGO_EN_ATR * row['atr14_prev']
        objetivo = row['sma20']
        if direccion == 'largo':
            sl = precio_entrada - riesgo
            tp = objetivo
            if tp <= precio_entrada:
                continue
        else:
            sl = precio_entrada + riesgo
            tp = objetivo
            if tp >= precio_entrada:
                continue

        idx_fin = min(idx_entrada + DIAS_MAX_EN_MERCADO, len(d) - 1)
        resultado_precio, motivo, idx_salida = None, None, idx_fin
        for j in range(idx_entrada, idx_fin + 1):
            hi, lo = d['High'].iloc[j], d['Low'].iloc[j]
            if direccion == 'largo':
                toca_sl, toca_tp = lo <= sl, hi >= tp
            else:
                toca_sl, toca_tp = hi >= sl, lo <= tp
            if toca_sl:
                resultado_precio, motivo, idx_salida = sl, 'SL', j
                break
            if toca_tp:
                resultado_precio, motivo, idx_salida = tp, 'TP', j
                break
        if resultado_precio is None:
            resultado_precio, motivo, idx_salida = d['Close'].iloc[idx_fin], 'CIERRE_PLAZO', idx_fin

        ret_bruto = (resultado_precio - precio_entrada) if direccion == 'largo' else (precio_entrada - resultado_precio)
        spread_entrada = d['Spread'].iloc[idx_entrada] * point if pd.notna(d['Spread'].iloc[idx_entrada]) else 0.0
        trades.append(dict(
            dia=d['dia'].iloc[idx_entrada], anio=d['dia'].iloc[idx_entrada].year, direccion=direccion,
            idx_entrada=idx_entrada, idx_salida=idx_salida, precio_entrada=precio_entrada, riesgo_puntos=riesgo,
            ret_bruto_puntos=ret_bruto, spread_entrada_precio=spread_entrada, motivo_salida=motivo,
            regimen=row['regimen'], peor_flotante_r=np.nan,
        ))
    return pd.DataFrame(trades), d


def analizar(nombre, d, point):
    print(f"\n\n######## Hipotesis C (Bollinger Mean Reversion) -- {nombre} ########")
    ops, d_full = ejecutar(d, point)
    print(f"Operaciones: {len(ops)}")
    if len(ops) == 0:
        print("  SIN OPERACIONES.")
        return
    print(f"  Direccion: {ops['direccion'].value_counts().to_dict()}")
    print("  Motivo salida:", ops['motivo_salida'].value_counts().to_dict())

    for extra in ESTRES_COSTE:
        etiqueta = "solo spread real" if extra == 0.0 else f"spread real + {extra:.0f}$ estres"
        ops_r = calcular_r_multiplos(ops, extra)
        m = metricas_en_r(ops_r)
        print(f"\n--- {etiqueta} ---")
        print(f"  n={m['n']}  Media R={m['media_R']:+.4f}  PF={m['profit_factor']:.3f}  "
              f"%Acierto={m['pct_acierto']:.1f}%  Drawdown balance={m['max_drawdown_balance_R']:.2f}R")
        for anio, g in ops_r.groupby('anio'):
            mg = metricas_en_r(g)
            print(f"    {anio}: n={mg['n']}  Media R={mg['media_R']:+.4f}  PF={mg['profit_factor']:.3f}")
        if extra == 0.0:
            resumen_por_regimen(ops_r)

    eq = calcular_equity_simultanea(ops, d_full)
    print(f"\n  Max posiciones simultaneas: {eq['max_posiciones_simultaneas']}  "
          f"Drawdown equity: {eq['max_drawdown_equity_R']:.2f}R ({eq['dia_max_drawdown'].date()})")

    rng = np.random.default_rng(SEED)
    media_real, media_ctrl, std_ctrl, z = control_direccion_aleatoria(ops, rng)
    print(f"  Control direccion aleatoria: media real={media_real:+.4f}  media aleatoria={media_ctrl:+.4f}  z={z:+.2f}")


def main():
    for nombre, cfg in MERCADOS.items():
        d = cfg['cargar']()
        analizar(f"{nombre} [{cfg['tramo']}]", d, cfg['point'])


if __name__ == '__main__':
    main()
