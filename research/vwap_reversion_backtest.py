"""
Backtest de VWAP Mean Reversion en USTEC y US500. Reglas FIJAS,
pre-registradas antes de ver resultados -- no se optimiza nada.

AVISO DE DATOS (importante, verificado antes de programar esto): esta
cuenta NO tiene volumen real de contratos -- `RealVolume` es 0 en el
100% de las velas de ambos instrumentos. El unico volumen disponible es
`TickVolume` (numero de cambios de precio por vela), que se usa aqui
como ponderacion. Es un VWAP APROXIMADO por tick-volume, NO
necesariamente equivalente al VWAP de futuros ES/NQ (que se calcula con
volumen de contratos realmente negociados). Se reporta asi de forma
explicita, sin pretender que sea el VWAP "oficial" de esos futuros.

Estrategia (version discrecional conocida, muy extendida entre
traders intradia de futuros/acciones): el VWAP de sesion actua como
"precio justo" medio; cuando el precio se aleja de el por encima de un
umbral de desviacion estandar y luego rechaza esa distancia (vela que
toca la banda pero cierra de vuelta hacia el VWAP), se opera la
reversion hacia el propio VWAP.

DEFINICION (fija):
 - Sesion para reiniciar el VWAP: RTH 9:30-16:00 ET, localizada con la
   misma correspondencia servidor<->ET ya reconstruida semana a semana
   (ver orb_backtest.py); solo dias con offset CONFIRMADO (>=20 dias).
   El VWAP se reinicia en la primera vela de cada sesion (9:30-9:45 ET)
   y se acumula vela a vela SOLO con datos de ESE dia -- sin arrastrar
   nada del dia anterior.
 - VWAP: precio tipico de cada vela = (High+Low+Close)/3, ponderado por
   TickVolume, acumulado causalmente (solo con velas ya cerradas hasta
   el momento, incluida la vela actual una vez cerrada).
 - Bandas: +-2 desviaciones estandar, calculadas tambien de forma
   acumulada/causal sobre el precio tipico ponderado por TickVolume
   (var_t = E[tp^2]_t - VWAP_t^2, ponderado), sin look-ahead -- cada
   vela usa solo el historial de sesion hasta ella misma.
 - Señal: la primera vela de la sesion cuyo High alcanza o supera la
   banda superior (candidata a reversion CORTA) o cuyo Low alcanza o
   perfora la banda inferior (candidata a reversion LARGA). Si una
   misma vela toca ambas bandas a la vez (posible solo con bandas muy
   estrechas al inicio de sesion), se descarta el dia -- no se adivina
   el orden intravela.
 - Confirmacion: la MISMA vela de la señal debe cerrar de vuelta dentro
   de la banda (Close < banda superior tras tocar arriba, o Close >
   banda inferior tras tocar abajo). Si no cierra de vuelta dentro, no
   hay operacion ese dia -- no se reintenta mas tarde en la sesion.
 - Direccion: opuesta al lado de la banda tocada -- banda superior
   rechazada => CORTO; banda inferior rechazada => LARGO.
 - Entrada: Open de la vela SIGUIENTE a la de confirmacion (sin
   lookahead).
 - Stop-loss: el extremo de la propia vela de la señal (su High para
   el corto, su Low para el largo).
 - Take-profit: reversion al propio VWAP -- se cierra la operacion en
   la primera vela (a partir de la de entrada, inclusive) cuyo rango
   toca el VWAP vigente EN ESA MISMA VELA (causal: el VWAP de la vela k
   solo usa datos hasta k). Target variable por construccion (es la
   esencia de "mean reversion"), no un R fijo.
 - Si ni SL ni VWAP se alcanzan, se cierra al Close de la vela de las
   16:00 ET (fin de sesion regular) -- nunca se mantiene overnight.
 - Si una vela toca SL y el VWAP a la vez (ambiguedad OHLC M15), se
   asume el peor caso (SL) -- misma convencion conservadora que ORB y
   Liquidity Sweep.
 - Una operacion por dia como maximo.
 - Costes: mismo motor que ORB/Liquidity Sweep -- R-multiplos, spread
   real de la vela de entrada + escenarios de estres (0/1/3 puntos) no
   confirmados, sin asumir valor de tick/contrato.
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

N_DESVIACIONES = 2.0


def ejecutar_vwap_reversion(df, categoria_hueco, regimenes_confiables, point):
    """Recorre dia a dia (solo con offset confirmado) y simula VWAP Mean Reversion."""
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
        # off=0 (primera vela de la sesion) se excluye: con una sola vela de
        # historial la varianza ponderada es 0 y las bandas coinciden con el
        # propio precio tipico de esa vela -> tocarian "ambas bandas" en
        # practicamente toda vela de apertura, de forma espuria (no es una
        # señal real, es un artefacto de no tener aun historial de sesion).
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

        spread_entrada = df['Spread'].iloc[idx_entrada] * point

        resultado_precio, motivo_salida, idx_salida = None, None, None
        peor_flotante_r = 0.0
        mejor_flotante_r = 0.0
        for k in range(idx_entrada, idx_cierre + 1):
            if categoria_hueco.iloc[k] != 'intrasesion' and k != idx_entrada:
                break
            off_k = k - idx_apertura
            vwap_k = vwap[off_k]
            hi, lo = df['High'].iloc[k], df['Low'].iloc[k]
            # CORRECCION Bid/Ask (auditoria): el OHLC exportado es Bid. Cerrar un
            # LARGO es vender a Bid (el propio High/Low ya es el precio correcto
            # para comprobar su SL/TP, sin ajuste). Cerrar un CORTO exige COMPRAR
            # a Ask=Bid+spread -- el SL/TP de un corto debe compararse con el
            # nivel equivalente en Bid, es decir sl-spread_vela / tp-spread_vela
            # (usando el spread REAL de cada vela, no solo el de entrada). Antes
            # se comparaba sl/tp directamente contra Bid, lo que retrasaba el
            # disparo del SL y adelantaba el del TP en cortos -- un sesgo
            # optimista, pequeño pero real, acotado por el spread de cada vela.
            spread_vela = df['Spread'].iloc[k] * point
            if direccion == 'largo':
                flotante_r_vela = (lo - precio_entrada) / riesgo
                favorable_r_vela = (hi - precio_entrada) / riesgo
                toca_sl = lo <= sl
                toca_tp = hi >= vwap_k
            else:
                sl_bid_equiv = sl - spread_vela
                tp_bid_equiv = vwap_k - spread_vela
                flotante_r_vela = (precio_entrada - hi) / riesgo
                favorable_r_vela = (precio_entrada - lo) / riesgo
                toca_sl = hi >= sl_bid_equiv
                toca_tp = lo <= tp_bid_equiv
            if toca_sl:
                flotante_r_vela = max(flotante_r_vela, -1.0)
            peor_flotante_r = min(peor_flotante_r, flotante_r_vela)
            if toca_tp:
                favorable_r_vela = min(favorable_r_vela, (vwap_k - precio_entrada) / riesgo if direccion == 'largo'
                                        else (precio_entrada - vwap_k) / riesgo)
            mejor_flotante_r = max(mejor_flotante_r, favorable_r_vela)
            if toca_sl:  # empate SL+TP en la misma vela -> gana SL (conservador, fijo)
                resultado_precio, motivo_salida, idx_salida = sl, 'SL', k
                break
            if toca_tp:
                resultado_precio, motivo_salida, idx_salida = vwap_k, 'TP_VWAP', k
                break
        if resultado_precio is None:
            resultado_precio = df['Close'].iloc[idx_cierre]
            motivo_salida, idx_salida = 'CIERRE_SESION', idx_cierre

        ret_bruto_puntos = (resultado_precio - precio_entrada) if direccion == 'largo' else (precio_entrada - resultado_precio)

        operaciones.append(dict(
            dia=dia, anio=dia.year, direccion=direccion, banda_tocada=lado_banda,
            vwap_senal=vwap[off_senal], precio_entrada=precio_entrada, sl=sl,
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

    print("\n  Distribucion por banda tocada:")
    print(ops['banda_tocada'].value_counts().to_dict())
    print("  Distribucion por motivo de salida:")
    print(ops['motivo_salida'].value_counts().to_dict())
    print(f"  Riesgo medio por operacion (puntos de indice): {ops['riesgo_puntos'].mean():.2f}")
    print(f"  Spread medio en el momento de entrada (puntos de indice): {ops['spread_entrada_precio'].mean():.3f}")
    print(f"  Spread medio como fraccion del riesgo (cuanto 'come' el spread de cada 1R): "
          f"{(ops['spread_entrada_precio'] / ops['riesgo_puntos']).mean() * 100:.1f}%")
    print(f"  MFE (excursion favorable maxima, equity intra-operacion): media={ops['mejor_flotante_r'].mean():.3f}R  "
          f"mediana={ops['mejor_flotante_r'].median():.3f}R  max={ops['mejor_flotante_r'].max():.3f}R")
    for motivo, g in ops.groupby('motivo_salida'):
        print(f"    MFE por motivo de salida -- {motivo:12s} n={len(g):4d}  "
              f"media MFE={g['mejor_flotante_r'].mean():.3f}R  media MAE={g['peor_flotante_r'].mean():.3f}R")


def main(rutas):
    resultados = {}
    for nombre, path in rutas.items():
        df = cargar_y_verificar(path, nombre)
        categoria_hueco = clasificar_huecos(df)
        tabla = detectar_apertura_caja_por_semana(df)
        reg = construir_regimenes(tabla)
        reg_conf = filtrar_regimenes_confiables(reg)

        point = 0.01  # US500 y USTEC: Digitos=2

        ops, descartes = ejecutar_vwap_reversion(df, categoria_hueco, reg_conf, point)
        print(f"\n[{nombre}] Descartes: {descartes}")
        resumen_instrumento(nombre, ops)
        resultados[nombre] = ops

    return resultados


if __name__ == '__main__':
    main({'USTEC': sys.argv[1], 'US500': sys.argv[2]})
