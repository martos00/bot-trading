"""
H3 (ciclo intradia): Midday Compression -> PM Box Breakout.

Fundamento economico/conductual: la volatilidad intradia de indices
tiene forma de "U" bien documentada (alta en la apertura, minima hacia
el mediodia -- "lunch doldrums"/almuerzo institucional en EEUU,
~12:00-13:30 ET -- y vuelve a expandirse por la tarde hacia el cierre).
El rango comprimido del mediodia actua como una caja de referencia; su
primera ruptura por la tarde suele coincidir con el regreso de
participacion institucional y conviccion direccional. Mecanismo
DISTINTO de ORB (que usa el rango de LA PROPIA apertura, 9:30-9:45, no
un rango de mitad de sesion) y de la Hipotesis B del ciclo diario (que
usaba el regimen de ATR DIARIO, no un rango horario especifico dentro
de la sesion).

VIABILIDAD: la caja de mediodia (12:00-13:30 ET, 6 velas M15) existe
todos los dias confirmados; la tarde (13:30-16:00 ET) deja 10 velas
para que ocurra la ruptura -- suficiente margen temporal.

REGLAS (unica version, pre-registrada, sin optimizar):
 - Caja de mediodia = High/Low de las velas 12:00-13:30 ET (6 velas,
   offsets +10 a +15 desde la apertura de 9:30 ET).
 - Señal: la PRIMERA vela desde las 13:30 ET cuyo Close rompe por
   encima de la caja (largo) o por debajo (corto).
 - Entrada: Open de la vela siguiente. SL: lado opuesto de la caja de
   mediodia. TP: 2R. Cierre forzoso: Close de fin de sesion regular
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
OFFSET_INICIO_MEDIODIA = 10  # 9:30 + 2h30 = 12:00 ET
OFFSET_FIN_MEDIODIA = 15     # hasta 13:15-13:30 ET inclusive (6 velas: +10..+15)
OFFSET_INICIO_TARDE = 16     # 13:30 ET


def ejecutar(df, tabla_sesiones, categoria_hueco, point):
    confirmados = tabla_sesiones[tabla_sesiones['confirmado']].reset_index(drop=True)
    trades = []
    for _, hoy in confirmados.iterrows():
        idx_ap, idx_ci = int(hoy['idx_apertura']), int(hoy['idx_cierre_sesion'])
        idx_mediodia_ini = idx_ap + OFFSET_INICIO_MEDIODIA
        idx_mediodia_fin = idx_ap + OFFSET_FIN_MEDIODIA
        idx_tarde_ini = idx_ap + OFFSET_INICIO_TARDE
        if idx_tarde_ini > idx_ci:
            continue
        if not sin_huecos_en_tramo(categoria_hueco, idx_ap, idx_ci):
            continue

        caja_high = df['High'].iloc[idx_mediodia_ini:idx_mediodia_fin + 1].max()
        caja_low = df['Low'].iloc[idx_mediodia_ini:idx_mediodia_fin + 1].min()

        idx_ruptura, direccion = None, None
        for j in range(idx_tarde_ini, idx_ci + 1):
            c = df['Close'].iloc[j]
            if c > caja_high:
                idx_ruptura, direccion = j, 'largo'
                break
            if c < caja_low:
                idx_ruptura, direccion = j, 'corto'
                break
        if idx_ruptura is None or idx_ruptura + 1 > idx_ci:
            continue

        idx_entrada = idx_ruptura + 1
        precio_entrada = df['Open'].iloc[idx_entrada]
        if direccion == 'largo':
            sl = caja_low
            riesgo = precio_entrada - sl
            tp = precio_entrada + TP_EN_R * riesgo
        else:
            sl = caja_high
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
        analizar('H3 Midday Compression -> PM Breakout', nombre, ops, df)


if __name__ == '__main__':
    main({'USTEC': sys.argv[1], 'US500': sys.argv[2]})
