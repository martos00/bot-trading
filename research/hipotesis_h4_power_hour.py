"""
H4 (ciclo intradia): Power Hour -- continuacion de la tendencia del dia
hacia el cierre.

Fundamento economico/conductual: la ultima hora de la sesion regular de
EEUU (15:00-16:00 ET) concentra flujo institucional de rebalanceo y
ordenes ligadas a la subasta de cierre (MOC/"closing auction
imbalance", efecto bien documentado en futuros/indices de EEUU) --
la tendencia intradia ACUMULADA hasta las 15:00 tiende a tener
continuacion en esa ultima hora, mas que revertirse. Mecanismo DISTINTO
de los demas: no hay TP fijo -- es una apuesta direccional "a favor del
dia" protegida solo por un SL, manteniendose hasta el cierre de sesion
(16:00 ET) por diseño, igual estructura que Efecto Lunes (ya cerrada)
pero aplicada a la ultima hora de CUALQUIER dia en vez de solo lunes.

VIABILIDAD: la vela de las 14:45-15:00 ET (cierre=senal) y la hora
15:00-16:00 ET (4 velas) existen en todo dia confirmado con sesion
completa -- sin dependencia de ningun otro dato.

REGLAS (unica version, pre-registrada, sin optimizar):
 - Señal (cierre de la vela 14:45-15:00 ET): ret_dia = Close[15:00] /
   Open[9:30 ET] - 1. Direccion = largo si ret_dia>0, corto si <0 (se
   descarta el caso exactamente 0, no observado en la practica).
 - Riesgo = rango realizado del dia hasta las 15:00 (High-Low acumulado
   desde la apertura) -- SL a esa distancia en contra de la entrada.
 - Entrada: Open de la vela de las 15:00-15:15 ET (mismo instante que
   el cierre de la señal, sin lookahead).
 - SIN TP fijo: se mantiene hasta Close de fin de sesion (16:00 ET) o
   hasta que el SL se toque antes, lo que ocurra primero. Nunca
   overnight.
"""
import sys

import numpy as np
import pandas as pd

from orb_backtest import cargar_y_verificar
from sesion_ny import construir_tabla_sesiones, sin_huecos_en_tramo
from datos_ciclo2 import cargar_ustec_2023_2026, cargar_us500_2023_2026
from motor_intradia import analizar, etiquetar_regimen

OFFSET_SEÑAL = 21  # vela 14:45-15:00 ET (cierre = lectura de las 15:00)


def ejecutar(df, tabla_sesiones, categoria_hueco, point):
    confirmados = tabla_sesiones[tabla_sesiones['confirmado']].reset_index(drop=True)
    trades = []
    for _, hoy in confirmados.iterrows():
        idx_ap, idx_ci = int(hoy['idx_apertura']), int(hoy['idx_cierre_sesion'])
        idx_señal = idx_ap + OFFSET_SEÑAL
        idx_entrada = idx_señal + 1
        if idx_entrada > idx_ci:
            continue
        if not sin_huecos_en_tramo(categoria_hueco, idx_ap, idx_ci):
            continue

        open_dia = df['Open'].iloc[idx_ap]
        close_senal = df['Close'].iloc[idx_señal]
        ret_dia = close_senal / open_dia - 1.0
        if ret_dia == 0:
            continue
        direccion = 'largo' if ret_dia > 0 else 'corto'

        rango_hasta_ahora = df['High'].iloc[idx_ap:idx_señal + 1].max() - df['Low'].iloc[idx_ap:idx_señal + 1].min()
        if rango_hasta_ahora <= 0:
            continue
        precio_entrada = df['Open'].iloc[idx_entrada]
        riesgo = rango_hasta_ahora
        sl = precio_entrada - riesgo if direccion == 'largo' else precio_entrada + riesgo

        resultado_precio, motivo, idx_salida = None, None, idx_ci
        for k in range(idx_entrada, idx_ci + 1):
            hi, lo = df['High'].iloc[k], df['Low'].iloc[k]
            toca_sl = (lo <= sl) if direccion == 'largo' else (hi >= sl)
            if toca_sl:
                resultado_precio, motivo, idx_salida = sl, 'SL', k
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
        analizar('H4 Power Hour', nombre, ops, df)


if __name__ == '__main__':
    main({'USTEC': sys.argv[1], 'US500': sys.argv[2]})
