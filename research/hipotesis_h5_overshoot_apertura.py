"""
H5 (ciclo intradia): First-bar Opening Liquidity Overshoot Reversion.

Fundamento economico/conductual: en los primeros 15 minutos de la
sesion de NY, el libro de ordenes esta mas fino (liquidez limitada,
grandes ordenes de apertura, ajuste de precios tras el cierre/overnight)
-- un primer rango anormalmente grande que cierra cerca de un extremo
suele reflejar un "overshoot" de corto plazo que se corrige en los
minutos siguientes conforme la liquidez normal regresa (efecto de
microestructura, distinto del fallo de ruptura de H1 -- aqui NO se
compara con el rango de AYER, solo con el tamaño HABITUAL de esa misma
primera vela, y la operacion dura como mucho 1 vela mas, no 30 min).

VIABILIDAD: la vela de apertura (9:30-9:45 ET) existe todos los dias
confirmados; un rango anormal que cierre cerca de un extremo no deberia
ser diario (variacion real a comprobar).

REGLAS (unica version, pre-registrada, sin optimizar):
 - Linea base: mediana del rango (High-Low) de la PROPIA vela de
   apertura de los 20 dias confirmados anteriores (especifica de esa
   franja horaria, no mezclada con el resto de la sesion).
 - Señal: rango de la vela de apertura de HOY > 2x esa linea base, Y el
   Close de esa vela esta en el tercio superior de su propio rango
   (=> CORTO, se fade la subida) o en el tercio inferior (=> LARGO);
   si cierra en el tercio medio, no hay señal (ambiguo).
 - Entrada: Open de la vela siguiente (9:45-10:00 ET).
 - SL: el extremo de la vela de apertura (High si corto, Low si largo).
 - Salida: Close de esa MISMA vela de entrada (10:00 ET) si no se toca
   el SL antes -- operacion de una sola vela, sin TP fijo. Nunca
   overnight (ya garantizado por construccion).
"""
import sys

import numpy as np
import pandas as pd

from orb_backtest import cargar_y_verificar
from sesion_ny import construir_tabla_sesiones, sin_huecos_en_tramo
from datos_ciclo2 import cargar_ustec_2023_2026, cargar_us500_2023_2026
from motor_intradia import analizar, etiquetar_regimen

MULTIPLO_OVERSHOOT = 2.0
VENTANA_BASELINE_DIAS = 20


def ejecutar(df, tabla_sesiones, categoria_hueco, point):
    confirmados = tabla_sesiones[tabla_sesiones['confirmado']].reset_index(drop=True)
    rango_primera_vela = np.array([df['High'].iloc[int(r['idx_apertura'])] - df['Low'].iloc[int(r['idx_apertura'])]
                                    for _, r in confirmados.iterrows()])

    trades = []
    for i in range(VENTANA_BASELINE_DIAS, len(confirmados)):
        hoy = confirmados.iloc[i]
        idx_ap, idx_ci = int(hoy['idx_apertura']), int(hoy['idx_cierre_sesion'])
        if idx_ap + 1 > idx_ci:
            continue
        if not sin_huecos_en_tramo(categoria_hueco, idx_ap, idx_ap + 1):
            continue

        baseline = np.median(rango_primera_vela[i - VENTANA_BASELINE_DIAS:i])
        hi_ap, lo_ap, close_ap = df['High'].iloc[idx_ap], df['Low'].iloc[idx_ap], df['Close'].iloc[idx_ap]
        rango_ap = hi_ap - lo_ap
        if baseline <= 0 or rango_ap <= 0 or rango_ap <= MULTIPLO_OVERSHOOT * baseline:
            continue

        posicion = (close_ap - lo_ap) / rango_ap
        if posicion >= 2 / 3:
            direccion = 'corto'
        elif posicion <= 1 / 3:
            direccion = 'largo'
        else:
            continue

        idx_entrada = idx_ap + 1
        precio_entrada = df['Open'].iloc[idx_entrada]
        sl = hi_ap if direccion == 'corto' else lo_ap
        riesgo = (sl - precio_entrada) if direccion == 'corto' else (precio_entrada - sl)
        if riesgo <= 0:
            continue

        hi_e, lo_e = df['High'].iloc[idx_entrada], df['Low'].iloc[idx_entrada]
        toca_sl = (hi_e >= sl) if direccion == 'corto' else (lo_e <= sl)
        if toca_sl:
            resultado_precio, motivo, idx_salida = sl, 'SL', idx_entrada
        else:
            resultado_precio, motivo, idx_salida = df['Close'].iloc[idx_entrada], 'CIERRE_VELA', idx_entrada

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
        analizar('H5 Opening Overshoot Reversion', nombre, ops, df)


if __name__ == '__main__':
    main({'USTEC': sys.argv[1], 'US500': sys.argv[2]})
