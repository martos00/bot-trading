"""
VWAP Mean Reversion -- variante de salida con TP fijo en +1R. UNICA
modificacion respecto a research/vwap_reversion_backtest.py: el take-profit
deja de ser "reversion completa al VWAP" y pasa a ser un objetivo fijo de
+1R. La señal de entrada, la confirmacion, el SL inicial, el horario
operativo y el modelo de costes NO cambian.

HIPOTESIS REGISTRADA (antes de ejecutar este backtest, basada en el MFE
ya medido sobre este MISMO historico -- por tanto NO es una validacion
fuera de muestra, ver README): la señal de barrido de banda VWAP +
confirmacion podria capturar suficiente movimiento favorable para
alcanzar +1R aunque no complete la reversion total hasta el VWAP. El
MFE medio de las operaciones que acabaron en SL (ya corregido para no
incluir movimiento posterior a la ejecucion del stop) es +0,927R en
USTEC y +0,714R en US500 -- por debajo de 1R en am ambos casos, pero no
muy lejos, lo que motiva probar directamente un TP de +1R en vez de
seguir fiando el objetivo a la reversion completa al VWAP.

DEFINICION (fija, sin cambios frente a la version original salvo el TP):
 - Señal, confirmacion, direccion, entrada, SL: IDENTICOS a
   vwap_reversion_backtest.py (ver su docstring).
 - Take-profit: +1R fijo desde la entrada (en vez de reversion al VWAP).
 - Cierre forzoso: Close de la vela de las 16:00 ET si ni SL ni TP se
   alcanzan antes.
 - Empate SL/TP en la misma vela -> gana SL (igual criterio conservador).
 - Correccion Bid/Ask en cortos: IDENTICA a la version corregida de
   vwap_reversion_backtest.py (SL/TP de cortos comparados contra el
   nivel equivalente en Bid, sl-spread_vela / tp-spread_vela).
 - Costes: mismo motor en R-multiplos, mismos escenarios de estres.

Esta hipotesis se compara contra la version original (reversion al
VWAP) y se reporta la decision sin buscar mas variantes de TP.
"""
import sys
from datetime import timedelta

import numpy as np
import pandas as pd

from orb_backtest import (
    MINUTOS_SESION_REGULAR, EXTRA_PUNTOS_ESTRES,
    cargar_y_verificar, clasificar_huecos, detectar_apertura_caja_por_semana,
    construir_regimenes, filtrar_regimenes_confiables,
    calcular_r_multiplos, metricas_en_r,
)
from vwap_reversion_backtest import N_DESVIACIONES

TP_EN_R_FIJO = 1.0


def ejecutar_vwap_reversion_tp1r(df, categoria_hueco, regimenes_confiables, point):
    tiempos = df['TimestampServidor']
    idx_por_tiempo = {t: i for i, t in enumerate(tiempos)}
    n = len(df)
    dias = sorted(set(tiempos.dt.normalize()))

    operaciones = []
    descartes = dict(
        offset_no_confirmado=0, vela_sesion_ausente=0, hueco_en_sesion=0,
        toque_ambas_bandas=0, sin_senal_en_sesion=0, senal_sin_confirmacion=0,
        entrada_ausente=0,
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

        sub = df.iloc[idx_apertura:idx_cierre + 1]
        tp_precio = (sub['High'] + sub['Low'] + sub['Close']) / 3.0
        vol = sub['TickVolume'].astype(float)
        cum_vol = vol.cumsum()
        cum_pv = (tp_precio * vol).cumsum()
        cum_pv2 = (tp_precio.pow(2) * vol).cumsum()
        vwap = (cum_pv / cum_vol).to_numpy()
        varianza = (cum_pv2 / cum_vol).to_numpy() - vwap ** 2
        sigma = np.sqrt(np.clip(varianza, 0.0, None))
        banda_sup = vwap + N_DESVIACIONES * sigma
        banda_inf = vwap - N_DESVIACIONES * sigma

        idx_senal, lado_banda = None, None
        for off in range(1, len(sub)):
            j = idx_apertura + off
            hi, lo = df['High'].iloc[j], df['Low'].iloc[j]
            toca_arriba = hi >= banda_sup[off]
            toca_abajo = lo <= banda_inf[off]
            if toca_arriba and toca_abajo:
                idx_senal, lado_banda = j, 'ambiguo'
                break
            if toca_arriba:
                idx_senal, lado_banda = j, 'arriba'
                break
            if toca_abajo:
                idx_senal, lado_banda = j, 'abajo'
                break

        if idx_senal is None:
            descartes['sin_senal_en_sesion'] += 1
            continue
        if lado_banda == 'ambiguo':
            descartes['toque_ambas_bandas'] += 1
            continue

        off_senal = idx_senal - idx_apertura
        close_senal = df['Close'].iloc[idx_senal]
        if lado_banda == 'arriba':
            confirmado = close_senal < banda_sup[off_senal]
            direccion = 'corto'
            sl = df['High'].iloc[idx_senal]
        else:
            confirmado = close_senal > banda_inf[off_senal]
            direccion = 'largo'
            sl = df['Low'].iloc[idx_senal]

        if not confirmado:
            descartes['senal_sin_confirmacion'] += 1
            continue

        idx_entrada = idx_senal + 1
        if idx_entrada > idx_cierre or idx_entrada >= n or categoria_hueco.iloc[idx_entrada] != 'intrasesion':
            descartes['entrada_ausente'] += 1
            continue

        precio_entrada = df['Open'].iloc[idx_entrada]
        if direccion == 'largo':
            riesgo = precio_entrada - sl
        else:
            riesgo = sl - precio_entrada
        if riesgo <= 0:
            descartes['entrada_ausente'] += 1
            continue

        # UNICO CAMBIO frente a la version original: TP fijo en +1R desde la
        # entrada (en vez de "reversion al VWAP vigente vela a vela").
        if direccion == 'largo':
            tp_fijo = precio_entrada + TP_EN_R_FIJO * riesgo
        else:
            tp_fijo = precio_entrada - TP_EN_R_FIJO * riesgo

        spread_entrada = df['Spread'].iloc[idx_entrada] * point

        resultado_precio, motivo_salida, idx_salida = None, None, None
        peor_flotante_r = 0.0
        mejor_flotante_r = 0.0
        for k in range(idx_entrada, idx_cierre + 1):
            if categoria_hueco.iloc[k] != 'intrasesion' and k != idx_entrada:
                break
            hi, lo = df['High'].iloc[k], df['Low'].iloc[k]
            spread_vela = df['Spread'].iloc[k] * point
            if direccion == 'largo':
                flotante_r_vela = (lo - precio_entrada) / riesgo
                favorable_r_vela = (hi - precio_entrada) / riesgo
                toca_sl = lo <= sl
                toca_tp = hi >= tp_fijo
            else:
                sl_bid_equiv = sl - spread_vela
                tp_bid_equiv = tp_fijo - spread_vela
                flotante_r_vela = (precio_entrada - hi) / riesgo
                favorable_r_vela = (precio_entrada - lo) / riesgo
                toca_sl = hi >= sl_bid_equiv
                toca_tp = lo <= tp_bid_equiv
            if toca_sl:
                flotante_r_vela = max(flotante_r_vela, -1.0)
            peor_flotante_r = min(peor_flotante_r, flotante_r_vela)
            # Mismo criterio conservador que la version original: en la vela
            # que dispara el SL no se acredita MFE (podria ser posterior a la
            # ejecucion del stop); en la que dispara el TP, se acota al R
            # realizado (+1R exacto, ejecucion confirmada).
            if toca_tp:
                favorable_r_vela = min(favorable_r_vela, TP_EN_R_FIJO)
                mejor_flotante_r = max(mejor_flotante_r, favorable_r_vela)
            elif not toca_sl:
                mejor_flotante_r = max(mejor_flotante_r, favorable_r_vela)
            if toca_sl:  # empate SL+TP en la misma vela -> gana SL (conservador, fijo)
                resultado_precio, motivo_salida, idx_salida = sl, 'SL', k
                break
            if toca_tp:
                resultado_precio, motivo_salida, idx_salida = tp_fijo, 'TP_1R', k
                break
        if resultado_precio is None:
            resultado_precio = df['Close'].iloc[idx_cierre]
            motivo_salida, idx_salida = 'CIERRE_SESION', idx_cierre

        ret_bruto_puntos = (resultado_precio - precio_entrada) if direccion == 'largo' else (precio_entrada - resultado_precio)

        operaciones.append(dict(
            dia=dia, anio=dia.year, direccion=direccion, banda_tocada=lado_banda,
            precio_entrada=precio_entrada, sl=sl, tp=tp_fijo,
            resultado_precio=resultado_precio, motivo_salida=motivo_salida,
            ret_bruto_puntos=ret_bruto_puntos, riesgo_puntos=riesgo,
            spread_entrada_precio=spread_entrada, peor_flotante_r=peor_flotante_r,
            mejor_flotante_r=mejor_flotante_r,
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

    print("\n  Distribucion por motivo de salida:")
    print(ops['motivo_salida'].value_counts().to_dict())
    print(f"  Riesgo medio por operacion (puntos de indice): {ops['riesgo_puntos'].mean():.2f}")
    print(f"  Spread medio en el momento de entrada (puntos de indice): {ops['spread_entrada_precio'].mean():.3f}")
    print(f"  Spread medio como fraccion del riesgo (cuanto 'come' el spread de cada 1R): "
          f"{(ops['spread_entrada_precio'] / ops['riesgo_puntos']).mean() * 100:.1f}%")
    print(f"  MFE media (ya excluyendo movimiento posterior al SL): {ops['mejor_flotante_r'].mean():.3f}R")


def main(rutas):
    resultados = {}
    for nombre, path in rutas.items():
        df = cargar_y_verificar(path, nombre)
        categoria_hueco = clasificar_huecos(df)
        tabla = detectar_apertura_caja_por_semana(df)
        reg = construir_regimenes(tabla)
        reg_conf = filtrar_regimenes_confiables(reg)

        point = 0.01

        ops, descartes = ejecutar_vwap_reversion_tp1r(df, categoria_hueco, reg_conf, point)
        print(f"\n[{nombre}] Descartes: {descartes}")
        resumen_instrumento(nombre, ops)
        resultados[nombre] = ops

    return resultados


if __name__ == '__main__':
    main({'USTEC': sys.argv[1], 'US500': sys.argv[2]})
