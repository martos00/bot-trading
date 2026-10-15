"""
H6 (ciclo intradia): Narrow-Range prior-session Breakout Continuation.

Fundamento economico/conductual: una sesion regular con rango
inusualmente ESTRECHO suele reflejar indecision/acumulacion de
posiciones; la ruptura de ese rango comprimido al dia siguiente (patron
"NR7 breakout" de la practica de trading, analogo intradia de la
Hipotesis B del ciclo diario) tiende a marcar el inicio de un
movimiento con continuacion, por el desbloqueo de liquidez acumulada.
Mecanismo DISTINTO de H1 (que haec FADE de una extension que FALLA en
30 min, condicionada por un GAP de apertura) y de ORB (que rompe el
rango de la PROPIA apertura de hoy): aqui la precondicion es la
COMPRESION del dia anterior completo, y se opera la ruptura de ESE
rango (no el de la apertura de hoy) en CONTINUACION, en cualquier
momento de la sesion de hoy.

VIABILIDAD: rango de sesion completa por dia ya disponible; percentil
de compresion sobre ventana de 60 dias confirmados anteriores (no
expandida, para no depender de la primera parte de la muestra como en
el ciclo diario) -- requiere al menos 60 dias de historial antes de
empezar a operar.

REGLAS (unica version, pre-registrada, sin optimizar):
 - Rango de sesion = High-Low de la sesion regular completa (apertura a
   cierre) de cada dia confirmado.
 - Precondicion: rango de AYER <= percentil 33 de los rangos de los 60
   dias confirmados anteriores a ayer (causal).
 - Señal: la PRIMERA vela de la sesion de HOY (de cualquier hora,
   aperura a cierre) cuyo Close rompe por encima del High de ayer
   (largo) o por debajo del Low de ayer (corto).
 - Entrada: Open de la vela siguiente. SL: extremo opuesto del rango de
   ayer. TP: 2R. Cierre forzoso: Close de fin de sesion regular (16:00
   ET), nunca overnight. SL gana empates en la misma vela.
"""
import sys

import numpy as np
import pandas as pd

from orb_backtest import cargar_y_verificar
from sesion_ny import construir_tabla_sesiones, sin_huecos_en_tramo
from datos_ciclo2 import cargar_ustec_2023_2026, cargar_us500_2023_2026
from motor_intradia import analizar, etiquetar_regimen

TP_EN_R = 2.0
VENTANA_PERCENTIL_DIAS = 60
PERCENTIL_COMPRESION = 33
MAX_DIAS_CONTEXTO_PREVIO = 4


def ejecutar(df, tabla_sesiones, categoria_hueco, point):
    confirmados = tabla_sesiones[tabla_sesiones['confirmado']].reset_index(drop=True)
    rango_sesion = np.array([df['High'].iloc[int(r['idx_apertura']):int(r['idx_cierre_sesion']) + 1].max() -
                              df['Low'].iloc[int(r['idx_apertura']):int(r['idx_cierre_sesion']) + 1].min()
                              for _, r in confirmados.iterrows()])

    trades = []
    for i in range(VENTANA_PERCENTIL_DIAS + 1, len(confirmados)):
        hoy, ayer = confirmados.iloc[i], confirmados.iloc[i - 1]
        if (hoy['dia'] - ayer['dia']).days > MAX_DIAS_CONTEXTO_PREVIO:
            continue
        umbral = np.percentile(rango_sesion[i - 1 - VENTANA_PERCENTIL_DIAS:i - 1], PERCENTIL_COMPRESION)
        if rango_sesion[i - 1] > umbral:
            continue  # ayer no fue un dia comprimido -- no aplica esta hipotesis

        idx_ap_ayer, idx_ci_ayer = int(ayer['idx_apertura']), int(ayer['idx_cierre_sesion'])
        idx_ap_hoy, idx_ci_hoy = int(hoy['idx_apertura']), int(hoy['idx_cierre_sesion'])
        if idx_ap_hoy >= idx_ci_hoy:
            continue
        if not sin_huecos_en_tramo(categoria_hueco, idx_ap_hoy, idx_ci_hoy):
            continue

        high_ayer = df['High'].iloc[idx_ap_ayer:idx_ci_ayer + 1].max()
        low_ayer = df['Low'].iloc[idx_ap_ayer:idx_ci_ayer + 1].min()

        idx_ruptura, direccion = None, None
        for j in range(idx_ap_hoy, idx_ci_hoy + 1):
            c = df['Close'].iloc[j]
            if c > high_ayer:
                idx_ruptura, direccion = j, 'largo'
                break
            if c < low_ayer:
                idx_ruptura, direccion = j, 'corto'
                break
        if idx_ruptura is None or idx_ruptura + 1 > idx_ci_hoy:
            continue

        idx_entrada = idx_ruptura + 1
        precio_entrada = df['Open'].iloc[idx_entrada]
        if direccion == 'largo':
            sl = low_ayer
            riesgo = precio_entrada - sl
            tp = precio_entrada + TP_EN_R * riesgo
        else:
            sl = high_ayer
            riesgo = sl - precio_entrada
            tp = precio_entrada - TP_EN_R * riesgo
        if riesgo <= 0:
            continue

        resultado_precio, motivo, idx_salida = None, None, idx_ci_hoy
        for k in range(idx_entrada, idx_ci_hoy + 1):
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
        analizar('H6 Narrow-Range Breakout Continuation', nombre, ops, df)


if __name__ == '__main__':
    main({'USTEC': sys.argv[1], 'US500': sys.argv[2]})
