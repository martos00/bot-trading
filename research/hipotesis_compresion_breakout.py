"""
Hipotesis B del nuevo ciclo: Volatility Compression Breakout.

Fundamento economico: tras un periodo de volatilidad comprimida
(terciles de ATR14/precio ya clasificados por regimenes_mercado.py),
la liquidez/posicionamiento se acumula y el primer dia que rompe esa
compresion con rango por encima de lo habitual tiende a marcar el
inicio de un movimiento direccional (patron "Bollinger squeeze"/
contraccion-expansion, DISTINTO de Volatility Expansion Continuation
ya cerrada: aqui la señal exige ADEMAS que el dia ANTERIOR estuviera en
regimen de volatilidad BAJA -- VolExp no exigia ningun contexto previo,
solo el propio dia de expansion).

VIABILIDAD (comprobada antes de programar, con datos.ciclo2 ya cargado):
 - El regimen 'baja' de volatilidad ya esta clasificado y tiene
   cientos de dias por mercado (ver datos_ciclo2.py, ~590-600 dias
   XAUUSD, ~230 USTEC/US500) -- suficiente base para exigir la
   condicion previa.
 - Umbral de ruptura DISTINTO del de VolExp (1.0x ATR14 en vez de 1.5x)
   -- se fija ahora, antes de ver resultados, precisamente porque el
   nivel base (ATR en regimen bajo) ya es mas bajo que el tipico, asi
   que exigir 1.5x seria un umbral demasiado estricto para esta
   hipotesis especifica.

REGLAS (unica version, pre-registrada, sin optimizar):
 - Precondicion: regimen_vol[t-1] == 'baja' (dia ANTERIOR al de ruptura
   ya estaba en el tercil mas bajo de volatilidad expandida, causal).
 - Señal de ruptura: rango[t] = High[t]-Low[t] > 1.0*ATR14[t-1].
 - Direccion = la del propio dia de ruptura (igual convencion que
   VolExp): Close[t]>Open[t] => largo; si no => corto.
 - Entrada: Open[t+1]. SL: extremo opuesto del dia de ruptura. TP: 2R.
 - Cierre forzoso: 5 dias. SL gana empates mismo dia.
"""
import sys

import numpy as np
import pandas as pd

from orb_backtest import calcular_r_multiplos, metricas_en_r
from validacion_independiente_volexp import calcular_equity_simultanea, control_direccion_aleatoria
from regimenes_mercado import resumen_por_regimen
from datos_ciclo2 import MERCADOS

UMBRAL_RUPTURA_ATR = 1.0
TP_EN_R = 2.0
DIAS_MAX_EN_MERCADO = 5
ESTRES_COSTE = [0.0, 1.0, 3.0]
SEED = 20261015


def ejecutar(d, point):
    d = d.copy().reset_index(drop=True)
    d['rango'] = d['High'] - d['Low']
    d['regimen_vol_prev'] = d['regimen_vol'].shift(1)

    trades = []
    for i in range(1, len(d) - 1):
        row = d.iloc[i]
        if pd.isna(row['atr14_prev']) or row['atr14_prev'] <= 0:
            continue
        if row['regimen_vol_prev'] != 'baja':
            continue
        if row['rango'] <= UMBRAL_RUPTURA_ATR * row['atr14_prev']:
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
    print(f"\n\n######## Hipotesis B (Compresion -> Ruptura) -- {nombre} ########")
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
