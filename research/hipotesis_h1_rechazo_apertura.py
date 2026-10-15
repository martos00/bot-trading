"""
H1 (ciclo intradia): Failed Breakout / Opening Drive Rejection.

Fundamento economico/conductual: cuando el precio ABRE la sesion de NY
mas alla del extremo de la sesion regular ANTERIOR (gap de apertura que
ya extiende el rango de ayer), ese movimiento suele reflejar
sobrerreaccion emocional/orden de mercado concentrada en la apertura.
Si en los primeros 30 minutos (2 velas M15) el precio NO logra
mantenerse fuera de ese rango y cierra de nuevo DENTRO del rango de
ayer, el impulso inicial "fallo" -- patron de "failed breakout"/
"opening drive rejection" ampliamente citado en trading intradia de
futuros de indices. MECANISMO DISTINTO de ORB (que opera la ruptura del
rango de la PROPIA apertura de hoy, en continuacion) y de VWAP Mean
Reversion (que usa distancia a una media intradia, no el rango de la
sesion anterior): aqui la referencia es el rango de AYER, y se opera el
FALLO de la extension, no la ruptura de hoy.

VIABILIDAD (comprobada antes de programar, con sesion_ny.py ya
construido): dias con offset confirmado = 679 (USTEC, 72%) / 801
(US500, 85%) sobre 939-940 dias -- muestra base suficiente. Un gap mas
alla del rango de ayer que fracase en 30 min no es cada dia (variacion
real esperada, a comprobar en ejecucion).

REGLAS (unica version, pre-registrada, sin optimizar):
 - Contexto previo: High/Low de la sesion regular COMPLETA del dia de
   negociacion confirmado inmediatamente anterior (maximo 4 dias de
   calendario de distancia -- si no, no se asume "ayer", se omite).
 - Gap: Open de la vela de apertura de HOY > High de ayer (gap arriba)
   o < Low de ayer (gap abajo). Si no hay gap mas alla de ningun lado,
   no hay señal (igual que si ambos lados a la vez -- no deberia poder
   pasar con un solo precio de apertura, pero se comprueba).
 - Fallo: el CIERRE de la 2a vela de la sesion (9:45-10:00 ET) vuelve a
   estar DENTRO del rango de ayer (Close < High_ayer tras gap arriba, o
   Close > Low_ayer tras gap abajo).
 - Direccion: FADE del gap (gap arriba y fallo => CORTO; gap abajo y
   fallo => LARGO).
 - Entrada: Open de la 3a vela de la sesion (10:00-10:15 ET, sin
   lookahead).
 - SL: el extremo alcanzado en las 2 primeras velas de la sesion (High
   maximo si corto, Low minimo si largo).
 - TP: 2R. Cierre forzoso: Close de la vela de fin de sesion regular
   (16:00 ET) -- NUNCA overnight. SL gana empates en la misma vela.
"""
import sys

import numpy as np
import pandas as pd

from orb_backtest import cargar_y_verificar
from sesion_ny import construir_tabla_sesiones, sin_huecos_en_tramo
from datos_ciclo2 import cargar_ustec_2023_2026, cargar_us500_2023_2026
from motor_intradia import analizar, etiquetar_regimen

TP_EN_R = 2.0
MAX_DIAS_CONTEXTO_PREVIO = 4


def ejecutar(df, tabla_sesiones, categoria_hueco, point):
    confirmados = tabla_sesiones[tabla_sesiones['confirmado']].reset_index(drop=True)
    trades = []
    for i in range(1, len(confirmados)):
        hoy, ayer = confirmados.iloc[i], confirmados.iloc[i - 1]
        if (hoy['dia'] - ayer['dia']).days > MAX_DIAS_CONTEXTO_PREVIO:
            continue
        idx_ap_ayer, idx_ci_ayer = int(ayer['idx_apertura']), int(ayer['idx_cierre_sesion'])
        idx_ap_hoy, idx_ci_hoy = int(hoy['idx_apertura']), int(hoy['idx_cierre_sesion'])
        if idx_ap_hoy + 2 > idx_ci_hoy:
            continue
        if not sin_huecos_en_tramo(categoria_hueco, idx_ap_hoy, idx_ap_hoy + 2):
            continue

        high_ayer = df['High'].iloc[idx_ap_ayer:idx_ci_ayer + 1].max()
        low_ayer = df['Low'].iloc[idx_ap_ayer:idx_ci_ayer + 1].min()
        open_hoy = df['Open'].iloc[idx_ap_hoy]
        gap_arriba, gap_abajo = open_hoy > high_ayer, open_hoy < low_ayer
        if gap_arriba == gap_abajo:  # ninguno o (imposible) ambos
            continue

        cierre_vela2 = df['Close'].iloc[idx_ap_hoy + 1]
        if gap_arriba and cierre_vela2 < high_ayer:
            direccion = 'corto'
            sl = df['High'].iloc[idx_ap_hoy:idx_ap_hoy + 2].max()
        elif gap_abajo and cierre_vela2 > low_ayer:
            direccion = 'largo'
            sl = df['Low'].iloc[idx_ap_hoy:idx_ap_hoy + 2].min()
        else:
            continue  # la extension se mantuvo -- no es nuestra señal (ver H6)

        idx_entrada = idx_ap_hoy + 2
        precio_entrada = df['Open'].iloc[idx_entrada]
        if direccion == 'largo':
            riesgo = precio_entrada - sl
            tp = precio_entrada + TP_EN_R * riesgo
        else:
            riesgo = sl - precio_entrada
            tp = precio_entrada - TP_EN_R * riesgo
        if riesgo <= 0:
            continue

        resultado_precio, motivo, idx_salida = None, None, idx_ci_hoy
        for j in range(idx_entrada, idx_ci_hoy + 1):
            hi, lo = df['High'].iloc[j], df['Low'].iloc[j]
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
            resultado_precio, motivo, idx_salida = df['Close'].iloc[idx_ci_hoy], 'CIERRE_SESION', idx_ci_hoy

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
        analizar('H1 Failed Breakout / Opening Rejection', nombre, ops, df)


if __name__ == '__main__':
    main({'USTEC': sys.argv[1], 'US500': sys.argv[2]})
