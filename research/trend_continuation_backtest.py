"""
Backtest de Trend Continuation Pullback (EMA) en USTEC y US500. Reglas
FIJAS, pre-registradas antes de ver resultados -- no se optimiza nada.
Ver README.md, seccion "Trend Continuation Pullback (EMA)", para el
registro completo de la version base y las dos variantes estructurales
(no se eligen parametros mirando los resultados).

Estrategia (version discrecional conocida): tras el impulso inicial de
apertura, el precio se mantiene en tendencia y hace retrocesos poco
profundos a una media movil antes de continuar -- complemento directo
de VWAP mean reversion (aqui se opera A FAVOR de la tendencia).

DEFINICION version base (fija):
 - EMA20 de Close, calculada de forma CONTINUA sobre toda la serie M15
   (no se reinicia por sesion), causal (ewm adjust=False).
 - Sesgo de tendencia del dia: fijado UNA vez en la vela de apertura
   (9:30-9:45 ET) de la sesion RTH confirmada -- Close>=EMA20 en esa
   vela => ALCISTA; si no, BAJISTA. No se reevalua durante el dia.
 - Señal: primera vela posterior (dentro de la sesion) cuyo Low toca o
   perfora la EMA20 Y cuyo Close cierra de vuelta por encima de ella
   (sesgo alcista) -- o simetricamente High toca/supera y Close cierra
   de vuelta por debajo (sesgo bajista).
 - Direccion operada: LA MISMA que el sesgo del dia (continuacion).
 - Entrada: Open de la vela siguiente a la señal (sin lookahead).
 - SL: extremo de la propia vela de la señal.
 - TP: 2R (misma convencion que ORB/Liquidity Sweep).
 - Cierre forzoso: Close de la vela de las 16:00 ET. Empate SL/TP en la
   misma vela -> gana SL. Maximo una operacion por dia.

Variante A (EMA9): identica a la base sustituyendo EMA20 por EMA9 como
unica media de sesgo y de retroceso.

Variante B (doble media EMA9/EMA20): el sesgo del dia se define por la
alineacion de las dos medias en la vela de apertura (EMA9>=EMA20 =>
alcista); el nivel de retroceso vigilado pasa a ser la media RAPIDA
(EMA9).
"""
import sys
from datetime import timedelta

import numpy as np
import pandas as pd

from orb_backtest import (
    MINUTOS_SESION_REGULAR, TP_EN_R, EXTRA_PUNTOS_ESTRES,
    cargar_y_verificar, clasificar_huecos, detectar_apertura_caja_por_semana,
    construir_regimenes, filtrar_regimenes_confiables,
    calcular_r_multiplos, metricas_en_r,
)


def ejecutar_tendencia_pullback(df, categoria_hueco, regimenes_confiables, point,
                                 nivel_pullback, modo, nivel_bias_lenta=None):
    """
    modo='precio_vs_nivel': sesgo = Close vs nivel_pullback en la vela de apertura
        (version base con EMA20, variante A con EMA9).
    modo='doble_ma': sesgo = nivel_pullback (EMA rapida) vs nivel_bias_lenta (EMA lenta)
        en la vela de apertura; el retroceso se vigila contra nivel_pullback (variante B).
    """
    tiempos = df['TimestampServidor']
    idx_por_tiempo = {t: i for i, t in enumerate(tiempos)}
    n = len(df)
    dias = sorted(set(tiempos.dt.normalize()))

    operaciones = []
    descartes = dict(
        offset_no_confirmado=0, vela_sesion_ausente=0, hueco_en_sesion=0,
        sin_pullback_en_sesion=0, entrada_ausente=0,
    )

    for dia in dias:
        if dia.dayofweek >= 5:
            continue

        reg = regimenes_confiables[(regimenes_confiables['inicio'] <= dia) & (regimenes_confiables['fin'] > dia)]
        if len(reg) == 0:
            descartes['offset_no_confirmado'] += 1
            continue

        slot_apertura = int(reg.iloc[0]['slot_apertura'])
        hora_a, minuto_a = slot_apertura // 4, (slot_apertura % 4) * 15
        t_apertura = dia + timedelta(hours=hora_a, minutes=minuto_a)
        t_cierre = t_apertura + timedelta(minutes=MINUTOS_SESION_REGULAR) - timedelta(minutes=15)

        idx_apertura = idx_por_tiempo.get(t_apertura)
        idx_cierre = idx_por_tiempo.get(t_cierre)
        if idx_apertura is None or idx_cierre is None or idx_cierre >= n or idx_cierre <= idx_apertura:
            descartes['vela_sesion_ausente'] += 1
            continue
        if (categoria_hueco.iloc[idx_apertura:idx_cierre + 1] != 'intrasesion').any():
            descartes['hueco_en_sesion'] += 1
            continue

        if modo == 'precio_vs_nivel':
            sesgo_alcista = df['Close'].iloc[idx_apertura] >= nivel_pullback.iloc[idx_apertura]
        else:  # doble_ma
            sesgo_alcista = nivel_pullback.iloc[idx_apertura] >= nivel_bias_lenta.iloc[idx_apertura]

        idx_senal = None
        for j in range(idx_apertura + 1, idx_cierre + 1):
            if categoria_hueco.iloc[j] != 'intrasesion':
                break
            hi, lo, c = df['High'].iloc[j], df['Low'].iloc[j], df['Close'].iloc[j]
            nivel_j = nivel_pullback.iloc[j]
            if sesgo_alcista:
                if lo <= nivel_j and c > nivel_j:
                    idx_senal = j
                    break
            else:
                if hi >= nivel_j and c < nivel_j:
                    idx_senal = j
                    break

        if idx_senal is None:
            descartes['sin_pullback_en_sesion'] += 1
            continue

        idx_entrada = idx_senal + 1
        if idx_entrada > idx_cierre or idx_entrada >= n or categoria_hueco.iloc[idx_entrada] != 'intrasesion':
            descartes['entrada_ausente'] += 1
            continue

        precio_entrada = df['Open'].iloc[idx_entrada]
        direccion = 'largo' if sesgo_alcista else 'corto'
        if direccion == 'largo':
            sl = df['Low'].iloc[idx_senal]
            riesgo = precio_entrada - sl
            tp = precio_entrada + TP_EN_R * riesgo
        else:
            sl = df['High'].iloc[idx_senal]
            riesgo = sl - precio_entrada
            tp = precio_entrada - TP_EN_R * riesgo
        if riesgo <= 0:
            descartes['entrada_ausente'] += 1
            continue

        spread_entrada = df['Spread'].iloc[idx_entrada] * point

        resultado_precio, motivo_salida, idx_salida = None, None, None
        peor_flotante_r = 0.0
        for k in range(idx_entrada, idx_cierre + 1):
            if categoria_hueco.iloc[k] != 'intrasesion' and k != idx_entrada:
                break
            hi, lo = df['High'].iloc[k], df['Low'].iloc[k]
            if direccion == 'largo':
                flotante_r_vela = (lo - precio_entrada) / riesgo
                toca_sl = lo <= sl
                toca_tp = hi >= tp
            else:
                flotante_r_vela = (precio_entrada - hi) / riesgo
                toca_sl = hi >= sl
                toca_tp = lo <= tp
            if toca_sl:
                flotante_r_vela = max(flotante_r_vela, -1.0)
            peor_flotante_r = min(peor_flotante_r, flotante_r_vela)
            if toca_sl:
                resultado_precio, motivo_salida, idx_salida = sl, 'SL', k
                break
            if toca_tp:
                resultado_precio, motivo_salida, idx_salida = tp, 'TP', k
                break
        if resultado_precio is None:
            resultado_precio = df['Close'].iloc[idx_cierre]
            motivo_salida, idx_salida = 'CIERRE_SESION', idx_cierre

        ret_bruto_puntos = (resultado_precio - precio_entrada) if direccion == 'largo' else (precio_entrada - resultado_precio)

        operaciones.append(dict(
            dia=dia, anio=dia.year, direccion=direccion, sesgo_alcista=sesgo_alcista,
            precio_entrada=precio_entrada, sl=sl, tp=tp,
            resultado_precio=resultado_precio, motivo_salida=motivo_salida,
            ret_bruto_puntos=ret_bruto_puntos, riesgo_puntos=riesgo,
            spread_entrada_precio=spread_entrada, peor_flotante_r=peor_flotante_r,
        ))

    return pd.DataFrame(operaciones), descartes


def resumen_instrumento(nombre, ops):
    print(f"\n\n######## {nombre} ########")
    print(f"Operaciones totales (todos los años): {len(ops)}")
    if len(ops) == 0:
        print("  SIN OPERACIONES -- no se puede evaluar.")
        return

    for extra in EXTRA_PUNTOS_ESTRES:
        etiqueta = f"spread real + {extra:.0f} puntos extra de estres (comision/slippage NO confirmados)" \
            if extra > 0 else "SOLO spread real (verificado), sin comision ni slippage adicional"
        print(f"\n--- Escenario: {etiqueta} ---")
        ops_r = calcular_r_multiplos(ops, extra)
        m = metricas_en_r(ops_r)
        print(f"  n={m['n']}  Suma R={m['suma_R']:+.2f}  Media R/operacion={m['media_R']:+.4f}  "
              f"Mediana R={m['mediana_R']:+.4f}  Profit Factor={m['profit_factor']:.3f}  "
              f"%Acierto={m['pct_acierto']:.1f}%")
        print(f"  Drawdown balance (cierres, maximo pico-valle en R): {m['max_drawdown_balance_R']:.2f}R")
        print(f"  Excursion flotante (equity intra-operacion): peor caso individual="
              f"{m['peor_excursion_flotante_individual_R']:.2f}R  media={m['media_excursion_flotante_R']:.3f}R")

        print("  Por año:")
        for anio, g in ops_r.groupby('anio'):
            mg = metricas_en_r(g)
            aviso = "  [2025 incompleto]" if anio == 2025 else ""
            print(f"    {anio}: n={mg['n']}  Suma R={mg['suma_R']:+.2f}  Media R={mg['media_R']:+.4f}  "
                  f"PF={mg['profit_factor']:.3f}  %Acierto={mg['pct_acierto']:.1f}%{aviso}")

    print("\n  Distribucion por direccion:")
    print(ops['direccion'].value_counts().to_dict())
    print("  Distribucion por motivo de salida:")
    print(ops['motivo_salida'].value_counts().to_dict())
    print(f"  Riesgo medio por operacion (puntos de indice): {ops['riesgo_puntos'].mean():.2f}")
    print(f"  Spread medio en el momento de entrada (puntos de indice): {ops['spread_entrada_precio'].mean():.3f}")
    print(f"  Spread medio como fraccion del riesgo (cuanto 'come' el spread de cada 1R): "
          f"{(ops['spread_entrada_precio'] / ops['riesgo_puntos']).mean() * 100:.1f}%")


def main(rutas):
    resultados = {}
    for nombre, path in rutas.items():
        df = cargar_y_verificar(path, nombre)
        categoria_hueco = clasificar_huecos(df)
        tabla = detectar_apertura_caja_por_semana(df)
        reg = construir_regimenes(tabla)
        reg_conf = filtrar_regimenes_confiables(reg)

        point = 0.01  # US500 y USTEC: Digitos=2

        ema9 = df['Close'].ewm(span=9, adjust=False).mean()
        ema20 = df['Close'].ewm(span=20, adjust=False).mean()

        versiones = {
            'BASE (EMA20)': dict(nivel_pullback=ema20, modo='precio_vs_nivel', nivel_bias_lenta=None),
            'Variante A (EMA9)': dict(nivel_pullback=ema9, modo='precio_vs_nivel', nivel_bias_lenta=None),
            'Variante B (doble EMA9/EMA20)': dict(nivel_pullback=ema9, modo='doble_ma', nivel_bias_lenta=ema20),
        }

        resultados[nombre] = {}
        for etiqueta, params in versiones.items():
            print(f"\n\n========== {nombre} -- {etiqueta} ==========")
            ops, descartes = ejecutar_tendencia_pullback(df, categoria_hueco, reg_conf, point, **params)
            print(f"[{nombre} -- {etiqueta}] Descartes: {descartes}")
            resumen_instrumento(f"{nombre} -- {etiqueta}", ops)
            resultados[nombre][etiqueta] = ops

    return resultados


if __name__ == '__main__':
    main({'USTEC': sys.argv[1], 'US500': sys.argv[2]})
