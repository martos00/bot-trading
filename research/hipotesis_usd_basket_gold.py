"""
USD-basket -> Gold lead-lag, familia nueva (intermarket), no probada
antes en este proyecto. Fundamento: el oro cotiza en USD; un
fortalecimiento/debilitamiento amplio del dolar tiene una relacion
inversa con el oro ampliamente documentada (relacion moneda-materia
prima estandar, no es una anomalia discutible). La pregunta
ACCIONABLE no es la correlacion contemporanea (ya esta descontada el
mismo dia, no es operable) sino si el movimiento del DOLAR de HOY
predice el movimiento del ORO de MAÑANA -- una reaccion con retraso,
que si seria explotable.

VIABILIDAD: usa los 6 pares Forex, solo disponibles 2023-2026 -- esta
hipotesis se evalua en esa ventana (Forex como secundario, segun lo
pedido), no en el historico largo de XAUUSD.

FASE 1 (antes de construir señal/SL/TP): se mide (a) correlacion
contemporanea USD-oro (control de sanity, se espera negativa) y (b)
correlacion entre el movimiento del USD HOY y el retorno del oro
MAÑANA, y se compara contra si el propio retorno del oro de AYER
predice igual o mejor el de mañana (para no confundir "el USD predice"
con "el oro tiene autocorrelacion y el USD solo la refleja").

REGLAS (unica version, pre-registrada, sin optimizar):
 - cesta_usd_ret[t] = media de las contribuciones orientadas de los 6
   pares (signo tal que + = USD se fortalece): -ret(EURUSD), -ret(GBPUSD),
   +ret(USDJPY), +ret(USDCAD), +ret(USDCHF), +ret(USDSEK).
 - z_usd[t] = cesta_usd_ret[t] / std_60d(cesta_usd_ret).
 - Señal: z_usd[t] > 1.0 => CORTO oro; z_usd[t] < -1.0 => LARGO oro.
 - Entrada: Open[t+1] del oro (sin lookahead). SL: 1.5xATR14[t_señal]
   (vela de señal, conocido al cierre). TP: 2R. Cierre forzoso: 5 dias.
"""
import sys

import numpy as np
import pandas as pd

from orb_backtest import calcular_r_multiplos, metricas_en_r
from validacion_independiente_volexp import calcular_equity_simultanea, control_direccion_aleatoria
from datos_multiactivo import cargar_universo, UNIVERSO
from estrategia_gap_fade import calcular_atr_diario

PARES_USD = {'EURUSD': -1, 'GBPUSD': -1, 'USDJPY': 1, 'USDCAD': 1, 'USDCHF': 1, 'USDSEK': 1}
UMBRAL_Z = 1.0
RIESGO_EN_ATR = 1.5
TP_EN_R = 2.0
DIAS_MAX = 5
ESTRES_COSTE = [0.0, 1.0, 3.0]
SEED = 20261015


def construir_cesta_usd(universo):
    piezas = []
    for par, signo in PARES_USD.items():
        d = universo[par][['dia', 'Close']].copy()
        d['ret'] = signo * (d['Close'] / d['Close'].shift(1) - 1.0)
        piezas.append(d[['dia', 'ret']].rename(columns={'ret': par}))
    m = piezas[0]
    for p in piezas[1:]:
        m = pd.merge(m, p, on='dia', how='inner')
    m['cesta_usd_ret'] = m[list(PARES_USD.keys())].mean(axis=1)
    m['z_usd'] = m['cesta_usd_ret'] / m['cesta_usd_ret'].rolling(60).std()
    return m[['dia', 'cesta_usd_ret', 'z_usd']]


def fase1_correlaciones(oro, cesta):
    m = pd.merge(oro[['dia', 'Close']], cesta, on='dia').sort_values('dia').reset_index(drop=True)
    m['ret_oro'] = m['Close'] / m['Close'].shift(1) - 1.0
    m['ret_oro_mañana'] = m['ret_oro'].shift(-1)
    m['ret_oro_ayer'] = m['ret_oro'].shift(1)

    corr_contemporanea = m['cesta_usd_ret'].corr(m['ret_oro'])
    corr_usd_hoy_oro_mañana = m['cesta_usd_ret'].corr(m['ret_oro_mañana'])
    corr_oro_ayer_oro_mañana = m['ret_oro_ayer'].corr(m['ret_oro'])  # autocorrelacion propia del oro (control)
    print(f"  Correlacion contemporanea (USD hoy, oro hoy): {corr_contemporanea:+.3f} (control de sanity, se espera negativa)")
    print(f"  Correlacion USD HOY -> oro MAÑANA: {corr_usd_hoy_oro_mañana:+.3f}")
    print(f"  Control -- autocorrelacion del propio oro (ayer -> hoy, mismo tipo de relacion): {corr_oro_ayer_oro_mañana:+.3f}")
    return m


def ejecutar(oro_prep, cesta, point):
    d = pd.merge(oro_prep, cesta, on='dia').sort_values('dia').reset_index(drop=True)
    trades = []
    for i in range(1, len(d) - 1):
        z = d['z_usd'].iloc[i]
        if pd.isna(z) or pd.isna(d['atr14_prev'].iloc[i]) or d['atr14_prev'].iloc[i] <= 0:
            continue
        if z > UMBRAL_Z:
            direccion = 'corto'
        elif z < -UMBRAL_Z:
            direccion = 'largo'
        else:
            continue

        idx_entrada = i + 1
        precio_entrada = d['Open'].iloc[idx_entrada]
        riesgo = RIESGO_EN_ATR * d['atr14_prev'].iloc[i]
        if direccion == 'largo':
            sl = precio_entrada - riesgo
            tp = precio_entrada + TP_EN_R * riesgo
        else:
            sl = precio_entrada + riesgo
            tp = precio_entrada - TP_EN_R * riesgo

        idx_fin = min(idx_entrada + DIAS_MAX, len(d) - 1)
        resultado, motivo, idx_salida = None, None, idx_fin
        for j in range(idx_entrada, idx_fin + 1):
            hi, lo = d['High'].iloc[j], d['Low'].iloc[j]
            if direccion == 'largo':
                toca_sl, toca_tp = lo <= sl, hi >= tp
            else:
                toca_sl, toca_tp = hi >= sl, lo <= tp
            if toca_sl:
                resultado, motivo, idx_salida = sl, 'SL', j
                break
            if toca_tp:
                resultado, motivo, idx_salida = tp, 'TP', j
                break
        if resultado is None:
            resultado, motivo, idx_salida = d['Close'].iloc[idx_fin], 'CIERRE_PLAZO', idx_fin

        ret_bruto = (resultado - precio_entrada) if direccion == 'largo' else (precio_entrada - resultado)
        spread_entrada = d['Spread'].iloc[idx_entrada] * point if pd.notna(d['Spread'].iloc[idx_entrada]) else 0.0
        trades.append(dict(dia=d['dia'].iloc[idx_entrada], anio=d['dia'].iloc[idx_entrada].year, direccion=direccion,
                            idx_entrada=idx_entrada, idx_salida=idx_salida, precio_entrada=precio_entrada,
                            riesgo_puntos=riesgo, ret_bruto_puntos=ret_bruto, spread_entrada_precio=spread_entrada,
                            motivo_salida=motivo, peor_flotante_r=np.nan))
    return pd.DataFrame(trades), d


def main():
    universo = cargar_universo(['XAUUSD', 'EURUSD', 'GBPUSD', 'USDJPY', 'USDCAD', 'USDCHF', 'USDSEK'])
    oro = universo['XAUUSD']
    oro_2023 = oro[oro['dia'] >= '2023-01-01'].reset_index(drop=True)
    cesta = construir_cesta_usd(universo)

    print("################ Fase 1: USD-basket vs Oro (2023-2026) ################")
    fase1_correlaciones(oro_2023, cesta)

    oro_prep = oro_2023.copy().reset_index(drop=True)
    oro_prep['atr14_prev'] = calcular_atr_diario(oro_prep).shift(1)
    ops, d = ejecutar(oro_prep, cesta, UNIVERSO['XAUUSD']['point'])
    print(f"\nOperaciones: {len(ops)}")
    if len(ops) == 0:
        print("  SIN OPERACIONES.")
        return
    print(f"  Direccion: {ops['direccion'].value_counts().to_dict()}")
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

    eq = calcular_equity_simultanea(ops, d)
    print(f"\n  Drawdown equity: {eq['max_drawdown_equity_R']:.2f}R")
    rng = np.random.default_rng(SEED)
    media_real, media_ctrl, std_ctrl, z = control_direccion_aleatoria(ops, rng)
    print(f"  Control direccion aleatoria: media real={media_real:+.4f}  media aleatoria={media_ctrl:+.4f}  z={z:+.2f}")


if __name__ == '__main__':
    main()
