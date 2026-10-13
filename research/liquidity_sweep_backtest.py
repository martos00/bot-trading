"""
Backtest de Liquidity Sweep + Reversal en USTEC y US500. Reglas FIJAS,
pre-registradas antes de ver resultados -- no se optimiza nada.

Estrategia (version discrecional conocida que se traduce aqui a reglas
objetivas): operadores discrecionales (price action / "smart money
concepts") vigilan el High y el Low de la sesion regular del dia anterior
(PDH/PDL) como niveles de liquidez -- zonas donde se acumulan stops. Un
"barrido" (sweep) es que el precio perfore ese nivel intradia; si la propia
vela que perfora cierra de nuevo DENTRO del rango anterior (rechazo), se
interpreta como una caza de stops ("stop hunt") y se opera la reversion.

DEFINICION (fija):
 - Sesion = RTH 9:30-16:00 ET, localizada con la misma correspondencia
   servidor<->ET ya reconstruida semana a semana (ver orb_backtest.py);
   solo se opera en dias con offset CONFIRMADO (>=20 dias de duracion).
 - Nivel de liquidez: PDH/PDL = High/Low de la sesion RTH completa del
   DIA HABIL ANTERIOR (el dia de referencia debe estar a <=3 dias
   naturales del dia actual -- cubre fines de semana normales; tras un
   hueco mayor -festivo extendido o datos ausentes- se descarta el dia,
   no se adivina un PDH/PDL "viejo").
 - Barrido: la primera vela de la sesion RTH actual (empezando en la
   propia vela 9:30-9:45) cuyo High supera el PDH o cuyo Low perfora el
   PDL. Solo cuenta la primera vela que dispare, en cualquiera de las
   dos direcciones. Si una misma vela perfora AMBOS niveles a la vez
   (ambiguo, no se puede saber que paso primero intravela), se descarta
   el dia -- no se adivina el orden.
 - Confirmacion de reversion: la MISMA vela del barrido debe cerrar de
   nuevo dentro del rango anterior (Close < PDH tras barrer arriba, o
   Close > PDL tras barrer abajo). Si no cierra de vuelta dentro (el
   precio sigue la ruptura, no hay rechazo), no hay operacion ese dia --
   no se reintenta mas tarde en la misma sesion.
 - Direccion: opuesta al barrido -- barrido de PDH con rechazo => CORTO;
   barrido de PDL con rechazo => LARGO.
 - Entrada: Open de la vela SIGUIENTE a la del barrido/confirmacion (sin
   lookahead).
 - Stop-loss: el extremo de la propia vela de barrido (su High para el
   corto, su Low para el largo) -- justo mas alla de la caza de stops.
 - Take-profit: 2x la distancia de riesgo (2R), igual convencion que ORB
   para mantener comparabilidad.
 - Si ni SL ni TP se alcanzan, se cierra al Close de la vela de las 16:00
   ET (fin de sesion regular) -- nunca se mantiene overnight.
 - Si una vela toca SL y TP a la vez (ambiguedad OHLC M15), se asume el
   peor caso (SL) -- igual convencion conservadora que ORB.
 - Una operacion por dia como maximo.
 - Costes: mismo modelo que ORB -- R-multiplos, spread real de la vela
   de entrada + escenarios de estres (0/1/3 puntos) no confirmados, sin
   asumir valor de tick/contrato.
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


def ejecutar_liquidity_sweep(df, categoria_hueco, regimenes_confiables, point):
    """Recorre dia a dia (solo con offset confirmado) y simula Liquidity Sweep + Reversal."""
    tiempos = df['TimestampServidor']
    idx_por_tiempo = {t: i for i, t in enumerate(tiempos)}
    n = len(df)
    dias = sorted(set(tiempos.dt.normalize()))

    operaciones = []
    descartes = dict(
        offset_no_confirmado=0, vela_sesion_ausente=0, hueco_en_sesion=0,
        referencia_dia_anterior_no_disponible=0, barrido_ambiguo_misma_vela=0,
        sin_barrido_en_sesion=0, barrido_sin_confirmacion=0, entrada_ausente=0,
    )

    sesiones = {}
    dia_habil_anterior = None

    for dia in dias:
        if dia.dayofweek >= 5:
            continue

        reg = regimenes_confiables[(regimenes_confiables['inicio'] <= dia) & (regimenes_confiables['fin'] > dia)]
        if len(reg) == 0:
            descartes['offset_no_confirmado'] += 1
            dia_habil_anterior = None
            continue

        slot_apertura = int(reg.iloc[0]['slot_apertura'])
        hora_a, minuto_a = slot_apertura // 4, (slot_apertura % 4) * 15
        t_apertura = dia + timedelta(hours=hora_a, minutes=minuto_a)
        t_cierre = t_apertura + timedelta(minutes=MINUTOS_SESION_REGULAR) - timedelta(minutes=15)

        idx_apertura = idx_por_tiempo.get(t_apertura)
        idx_cierre = idx_por_tiempo.get(t_cierre)
        if idx_apertura is None or idx_cierre is None or idx_cierre >= n or idx_cierre <= idx_apertura:
            descartes['vela_sesion_ausente'] += 1
            dia_habil_anterior = None
            continue
        if (categoria_hueco.iloc[idx_apertura:idx_cierre + 1] != 'intrasesion').any():
            descartes['hueco_en_sesion'] += 1
            dia_habil_anterior = None
            continue

        sesion_high = df['High'].iloc[idx_apertura:idx_cierre + 1].max()
        sesion_low = df['Low'].iloc[idx_apertura:idx_cierre + 1].min()
        sesiones[dia] = dict(idx_apertura=idx_apertura, idx_cierre=idx_cierre, high=sesion_high, low=sesion_low)

        referencia_valida = (dia_habil_anterior is not None
                              and (dia - dia_habil_anterior).days <= 3
                              and dia_habil_anterior in sesiones)
        if not referencia_valida:
            descartes['referencia_dia_anterior_no_disponible'] += 1
            dia_habil_anterior = dia
            continue

        pdh = sesiones[dia_habil_anterior]['high']
        pdl = sesiones[dia_habil_anterior]['low']

        idx_barrido, direccion_barrido = None, None
        for j in range(idx_apertura, idx_cierre + 1):
            hi, lo = df['High'].iloc[j], df['Low'].iloc[j]
            barre_arriba = hi > pdh
            barre_abajo = lo < pdl
            if barre_arriba and barre_abajo:
                idx_barrido, direccion_barrido = j, 'ambiguo'
                break
            if barre_arriba:
                idx_barrido, direccion_barrido = j, 'arriba'
                break
            if barre_abajo:
                idx_barrido, direccion_barrido = j, 'abajo'
                break

        if idx_barrido is None:
            descartes['sin_barrido_en_sesion'] += 1
            dia_habil_anterior = dia
            continue
        if direccion_barrido == 'ambiguo':
            descartes['barrido_ambiguo_misma_vela'] += 1
            dia_habil_anterior = dia
            continue

        close_barrido = df['Close'].iloc[idx_barrido]
        if direccion_barrido == 'arriba':
            confirmado = close_barrido < pdh
            direccion = 'corto'
            sl = df['High'].iloc[idx_barrido]
        else:
            confirmado = close_barrido > pdl
            direccion = 'largo'
            sl = df['Low'].iloc[idx_barrido]

        if not confirmado:
            descartes['barrido_sin_confirmacion'] += 1
            dia_habil_anterior = dia
            continue

        idx_entrada = idx_barrido + 1
        if idx_entrada > idx_cierre or idx_entrada >= n or categoria_hueco.iloc[idx_entrada] != 'intrasesion':
            descartes['entrada_ausente'] += 1
            dia_habil_anterior = dia
            continue

        precio_entrada = df['Open'].iloc[idx_entrada]
        if direccion == 'largo':
            riesgo = precio_entrada - sl
            tp = precio_entrada + TP_EN_R * riesgo
        else:
            riesgo = sl - precio_entrada
            tp = precio_entrada - TP_EN_R * riesgo
        if riesgo <= 0:
            descartes['entrada_ausente'] += 1
            dia_habil_anterior = dia
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
            dia=dia, anio=dia.year, direccion=direccion, barrido_direccion=direccion_barrido,
            pdh=pdh, pdl=pdl, precio_entrada=precio_entrada, sl=sl, tp=tp,
            resultado_precio=resultado_precio, motivo_salida=motivo_salida,
            ret_bruto_puntos=ret_bruto_puntos, riesgo_puntos=riesgo,
            spread_entrada_precio=spread_entrada, peor_flotante_r=peor_flotante_r,
        ))

        dia_habil_anterior = dia

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

    print("\n  Distribucion por direccion de barrido:")
    print(ops['barrido_direccion'].value_counts().to_dict())
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

        ops, descartes = ejecutar_liquidity_sweep(df, categoria_hueco, reg_conf, point)
        print(f"\n[{nombre}] Descartes: {descartes}")
        resumen_instrumento(nombre, ops)
        resultados[nombre] = ops

    return resultados


if __name__ == '__main__':
    main({'USTEC': sys.argv[1], 'US500': sys.argv[2]})
