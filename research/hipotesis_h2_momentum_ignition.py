"""
H2 (ciclo intradia): Intraday Momentum Ignition.

Fundamento economico/conductual: una vela M15 con un movimiento
anormalmente grande respecto al tamaño de vela habitual de esa sesion
suele reflejar un desequilibrio de flujo de ordenes (orden institucional
grande, dato macro, noticia) -- la literatura de microestructura
("order flow imbalance", "momentum ignition", Easley/O'Hara y
practica de trading de futuros) documenta que ese tipo de movimiento
suele tener continuacion de corto plazo antes de que la liquidez se
reequilibre. Mecanismo DISTINTO de ORB/VWAP/EMA: la señal es el TAMAÑO
RELATIVO de UNA sola vela cualquiera durante la sesion (no un rango de
apertura ni una media), comparado con el tamaño de vela habitual
reciente de esa sesion.

VIABILIDAD: con ~680-800 dias confirmados y ~22 velas intradia por dia
(excluyendo apertura/cierre reservados a H1/H5/H4), hay decenas de
miles de velas candidatas -- variacion real a comprobar (velas de ese
tamaño no deberian ser diarias).

REGLAS (unica version, pre-registrada, sin optimizar):
 - Linea base de tamaño de vela: mediana de |Close-Open| de TODAS las
   velas de sesion regular de los 20 dias confirmados ANTERIORES (sin
   incluir hoy, causal).
 - Señal: la PRIMERA vela de la sesion de HOY (excluyendo las 2
   primeras, reservadas a H1, y las ultimas 4, reservadas a H4) cuyo
   |Close-Open| > 3x esa linea base. Solo la primera cuenta (evita
   señales correlacionadas el mismo dia).
 - Direccion: CONTINUACION del signo de esa vela (Close>Open => largo).
 - Entrada: Open de la vela siguiente. SL: extremo opuesto de la vela
   de ignicion. TP: 2R. Cierre forzoso: Close de fin de sesion regular
   (16:00 ET), nunca overnight. SL gana empates en la misma vela.
"""
import sys

import numpy as np
import pandas as pd

from orb_backtest import cargar_y_verificar
from sesion_ny import construir_tabla_sesiones, sin_huecos_en_tramo
from datos_ciclo2 import cargar_ustec_2023_2026, cargar_us500_2023_2026
from motor_intradia import analizar, etiquetar_regimen

TP_EN_R = 2.0
MULTIPLO_IGNICION = 3.0
VENTANA_BASELINE_DIAS = 20
BARRAS_RESERVADAS_APERTURA = 2
BARRAS_RESERVADAS_CIERRE = 4


def ejecutar(df, tabla_sesiones, categoria_hueco, point):
    confirmados = tabla_sesiones[tabla_sesiones['confirmado']].reset_index(drop=True)
    rangos_por_dia = []
    for _, row in confirmados.iterrows():
        ia, ic = int(row['idx_apertura']), int(row['idx_cierre_sesion'])
        rangos_por_dia.append(np.abs(df['Close'].iloc[ia:ic + 1].to_numpy() - df['Open'].iloc[ia:ic + 1].to_numpy()))

    trades = []
    for i in range(VENTANA_BASELINE_DIAS, len(confirmados)):
        hoy = confirmados.iloc[i]
        idx_ap, idx_ci = int(hoy['idx_apertura']), int(hoy['idx_cierre_sesion'])
        baseline = np.median(np.concatenate(rangos_por_dia[i - VENTANA_BASELINE_DIAS:i]))
        if baseline <= 0:
            continue

        idx_inicio_scan = idx_ap + BARRAS_RESERVADAS_APERTURA
        idx_fin_scan = idx_ci - BARRAS_RESERVADAS_CIERRE
        if idx_inicio_scan >= idx_fin_scan:
            continue
        if not sin_huecos_en_tramo(categoria_hueco, idx_ap, idx_ci):
            continue

        idx_ignicion, direccion = None, None
        for j in range(idx_inicio_scan, idx_fin_scan + 1):
            cuerpo = df['Close'].iloc[j] - df['Open'].iloc[j]
            if abs(cuerpo) > MULTIPLO_IGNICION * baseline:
                idx_ignicion, direccion = j, ('largo' if cuerpo > 0 else 'corto')
                break
        if idx_ignicion is None or idx_ignicion + 1 > idx_ci:
            continue

        idx_entrada = idx_ignicion + 1
        precio_entrada = df['Open'].iloc[idx_entrada]
        if direccion == 'largo':
            sl = df['Low'].iloc[idx_ignicion]
            riesgo = precio_entrada - sl
            tp = precio_entrada + TP_EN_R * riesgo
        else:
            sl = df['High'].iloc[idx_ignicion]
            riesgo = sl - precio_entrada
            tp = precio_entrada - TP_EN_R * riesgo
        if riesgo <= 0:
            continue

        resultado_precio, motivo, idx_salida = None, None, idx_ci
        for k in range(idx_entrada, idx_ci + 1):
            hi, lo = df['High'].iloc[k], df['Low'].iloc[k]
            if direccion == 'largo':
                toca_sl, toca_tp = lo <= sl, hi >= tp
            else:
                toca_sl, toca_tp = hi >= sl, lo <= tp
            if toca_sl:
                resultado_precio, motivo, idx_salida = sl, 'SL', k
                break
            if toca_tp:
                resultado_precio, motivo, idx_salida = tp, 'TP', k
                break
        if resultado_precio is None:
            resultado_precio, motivo, idx_salida = df['Close'].iloc[idx_ci], 'CIERRE_SESION', idx_ci

        ret_bruto = (resultado_precio - precio_entrada) if direccion == 'largo' else (precio_entrada - resultado_precio)
        spread_entrada = df['Spread'].iloc[idx_entrada] * point if pd.notna(df['Spread'].iloc[idx_entrada]) else 0.0
        trades.append(dict(
            dia=hoy['dia'], anio=hoy['dia'].year, direccion=direccion,
            idx_entrada=idx_entrada, idx_salida=idx_salida, precio_entrada=precio_entrada, riesgo_puntos=riesgo,
            ret_bruto_puntos=ret_bruto, spread_entrada_precio=spread_entrada, motivo_salida=motivo,
            peor_flotante_r=np.nan,
        ))
    return pd.DataFrame(trades)


def main(rutas):
    cargadores_diarios = {'USTEC': cargar_ustec_2023_2026, 'US500': cargar_us500_2023_2026}
    for nombre, path in rutas.items():
        df = cargar_y_verificar(path, nombre)
        tabla_sesiones, categoria_hueco = construir_tabla_sesiones(df)
        ops = ejecutar(df, tabla_sesiones, categoria_hueco, point=0.01)
        ops = etiquetar_regimen(ops, cargadores_diarios[nombre]())
        analizar('H2 Momentum Ignition', nombre, ops, df)


if __name__ == '__main__':
    main({'USTEC': sys.argv[1], 'US500': sys.argv[2]})
