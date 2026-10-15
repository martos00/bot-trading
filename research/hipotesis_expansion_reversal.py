"""
Hipotesis A del nuevo ciclo: Volatility Expansion REVERSAL (fade).

Fundamento economico: un dia de rango muy por encima de lo habitual
(>1.5x ATR14) puede reflejar informacion genuina que continua (hipotesis
ya cerrada, NO validada) O una sobrerreaccion/clímax de liquidez que se
revierte parcialmente cuando pasa el impulso (patron de "exhaustion"/
"blow-off" documentado en la practica de trading de volatilidad) --
familia DISTINTA, mecanismo de entrada/direccion exactamente opuesto al
ya cerrado, mismo marco de riesgo para que la comparacion sea limpia.

VIABILIDAD (comprobada antes de programar):
 - Señal identica a la ya cerrada (rango[t]>1.5*ATR14[t-1]) -- ya
   sabemos que genera ~46 señales/año en XAUUSD, suficiente.
 - Direccion no es constante (depende del signo del dia, ya verificado
   58% largo/corto en el ciclo anterior).

REGLAS (unica version, pre-registrada, sin optimizar):
 - Señal: rango[t] = High[t]-Low[t] > 1.5*ATR14[t-1] (igual que la
   candidata cerrada).
 - Direccion FADE (opuesta al cierre del propio dia de expansion):
   Close[t]>Open[t] (dia alcista) => CORTO; si no => LARGO.
 - SL: el extremo ALCANZADO durante el dia de expansion EN LA DIRECCION
   DEL MOVIMIENTO ORIGINAL (si el dia subio y fadeamos en corto, SL en
   el High del dia -- una nueva maxima invalida la tesis de
   agotamiento; simetrico para el caso bajista) -- NO es el mismo nivel
   de SL que la version de continuacion (que usa el extremo OPUESTO).
 - Entrada: Open[t+1] (sin lookahead, igual que siempre).
 - TP: 2R (misma convencion que el resto del proyecto, para que la
   comparacion con la version de continuacion sea directa).
 - Cierre forzoso: 5 dias de sesion. SL gana empates mismo dia.
"""
import sys

import numpy as np
import pandas as pd

from orb_backtest import calcular_r_multiplos, metricas_en_r
from validacion_independiente_volexp import calcular_equity_simultanea, control_direccion_aleatoria
from regimenes_mercado import resumen_por_regimen
from datos_ciclo2 import MERCADOS

UMBRAL_EXPANSION_ATR = 1.5
TP_EN_R = 2.0
DIAS_MAX_EN_MERCADO = 5
ESTRES_COSTE = [0.0, 1.0, 3.0]
SEED = 20261015


def ejecutar(d, point):
    d = d.copy().reset_index(drop=True)
    d['rango'] = d['High'] - d['Low']

    trades = []
    for i in range(1, len(d) - 1):
        row = d.iloc[i]
        if pd.isna(row['atr14_prev']) or row['atr14_prev'] <= 0:
            continue
        if row['rango'] <= UMBRAL_EXPANSION_ATR * row['atr14_prev']:
            continue

        dia_subio = row['Close'] > row['Open']
        direccion = 'corto' if dia_subio else 'largo'
        idx_entrada = i + 1
        precio_entrada = d['Open'].iloc[idx_entrada]
        if direccion == 'corto':
            sl = row['High']
            riesgo = sl - precio_entrada
            tp = precio_entrada - TP_EN_R * riesgo
        else:
            sl = row['Low']
            riesgo = precio_entrada - sl
            tp = precio_entrada + TP_EN_R * riesgo
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
    print(f"\n\n######## Hipotesis A (Expansion Reversal / Fade) -- {nombre} ########")
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
