"""
Segunda auditoria, especifica de VWAP Mean Reversion, a peticion del
usuario tras los resultados de la auditoria general (research/auditoria_motor.py).
NO modifica las reglas de la estrategia (señal/confirmacion/SL/TP),
NO prueba TPs ni filtros nuevos. Objetivo: (1) explicar con precision la
referencia aleatoria original y corregir su sesgo de horario/tiempo
restante; (2) recalcular VWAP con la correccion Bid/Ask de ejecucion en
cortos ya aplicada en vwap_reversion_backtest.py; (3) revisar el efecto
de stops muy pequeños frente al spread (solo diagnostico, sin filtrar);
(4) MFE/MAE ya reportados por vwap_reversion_backtest.py tras el fix.
"""
import sys
from datetime import timedelta

import numpy as np
import pandas as pd

from orb_backtest import (
    MINUTOS_SESION_REGULAR,
    cargar_y_verificar, clasificar_huecos, detectar_apertura_caja_por_semana,
    construir_regimenes, filtrar_regimenes_confiables,
    calcular_r_multiplos, metricas_en_r,
)
from vwap_reversion_backtest import ejecutar_vwap_reversion, N_DESVIACIONES

RNG_SEED = 20261013
N_REPETICIONES = 200


def localizar_sesion(dia, regimenes_confiables, idx_por_tiempo, n):
    reg = regimenes_confiables[(regimenes_confiables['inicio'] <= dia) & (regimenes_confiables['fin'] > dia)]
    if len(reg) == 0:
        return None
    slot = int(reg.iloc[0]['slot_apertura'])
    h, m = slot // 4, (slot % 4) * 15
    t_apertura = dia + timedelta(hours=h, minutes=m)
    t_cierre = t_apertura + timedelta(minutes=MINUTOS_SESION_REGULAR) - timedelta(minutes=15)
    idx_apertura = idx_por_tiempo.get(t_apertura)
    idx_cierre = idx_por_tiempo.get(t_cierre)
    if idx_apertura is None or idx_cierre is None or idx_cierre >= n or idx_cierre <= idx_apertura:
        return None
    return idx_apertura, idx_cierre


def dias_sesion_valida(df, categoria_hueco, regimenes_confiables, idx_por_tiempo, n, dias):
    """Universo de dias habiles con sesion RTH completa y sin huecos --
    el mismo criterio de validez que usa ejecutar_vwap_reversion, pero
    para TODOS los dias (no solo los que dispararon señal real)."""
    validos = []
    for dia in dias:
        if dia.dayofweek >= 5:
            continue
        sesion = localizar_sesion(dia, regimenes_confiables, idx_por_tiempo, n)
        if sesion is None:
            continue
        idx_apertura, idx_cierre = sesion
        if (categoria_hueco.iloc[idx_apertura:idx_cierre + 1] != 'intrasesion').any():
            continue
        validos.append((dia, idx_apertura, idx_cierre))
    return validos


def recuperar_offset_entrada(df, precio_entrada, dia, regimenes_confiables, idx_por_tiempo, n):
    """Recupera idx_apertura e idx_entrada de una operacion real ya generada
    (sin tocar la logica de ejecutar_vwap_reversion), buscando la vela cuyo
    Open coincide exactamente con el precio de entrada ya registrado."""
    sesion = localizar_sesion(dia, regimenes_confiables, idx_por_tiempo, n)
    if sesion is None:
        return None
    idx_apertura, idx_cierre = sesion
    sub = df.iloc[idx_apertura + 1:idx_cierre + 1]
    candidatos = sub.index[sub['Open'] == precio_entrada]
    if len(candidatos) == 0:
        return None
    idx_entrada = candidatos[0]
    return idx_apertura, idx_cierre, idx_entrada


def construir_vwap_sesion(df, idx_apertura, idx_cierre):
    sub = df.iloc[idx_apertura:idx_cierre + 1]
    tp_precio = (sub['High'] + sub['Low'] + sub['Close']) / 3.0
    vol = sub['TickVolume'].astype(float)
    cum_vol = vol.cumsum()
    cum_pv = (tp_precio * vol).cumsum()
    return (cum_pv / cum_vol).to_numpy()


def simular_salida(df, categoria_hueco, idx_entrada, idx_cierre, point, precio_entrada, sl, direccion,
                    vwap_arr, idx_apertura):
    """Misma mecanica de salida que ejecutar_vwap_reversion (incluida la
    correccion Bid/Ask para cortos): SL/TP_VWAP/cierre de sesion, empate
    a favor de SL, costes de spread real de la vela de entrada."""
    for k in range(idx_entrada, idx_cierre + 1):
        if categoria_hueco.iloc[k] != 'intrasesion' and k != idx_entrada:
            break
        off_k = k - idx_apertura
        vwap_k = vwap_arr[off_k]
        hi, lo = df['High'].iloc[k], df['Low'].iloc[k]
        spread_vela = df['Spread'].iloc[k] * point
        if direccion == 'largo':
            toca_sl = lo <= sl
            toca_tp = hi >= vwap_k
        else:
            toca_sl = hi >= (sl - spread_vela)
            toca_tp = lo <= (vwap_k - spread_vela)
        if toca_sl:
            return sl, 'SL'
        if toca_tp:
            return vwap_k, 'TP_VWAP'
    resultado_precio = df['Close'].iloc[idx_cierre]
    return resultado_precio, 'CIERRE_SESION'


def referencia_aleatoria_original(df, categoria_hueco, regimenes_confiables, idx_por_tiempo, n, point,
                                   ops_reales, rng):
    """REPLICA EXACTA de la referencia usada en la auditoria anterior:
    misma sesion (mismo dia), mismo riesgo, MISMA regla de salida (VWAP),
    pero vela de entrada ALEATORIA UNIFORME dentro de la sesion completa
    (9:30-16:00) y direccion aleatoria 50/50. Esta es la version que el
    usuario pide verificar -- NO controla por hora del dia ni por tiempo
    restante hasta el cierre."""
    dias_riesgos = list(zip(ops_reales['dia'], ops_reales['riesgo_puntos']))
    medias = []
    for _ in range(N_REPETICIONES):
        ops = []
        for dia, riesgo in dias_riesgos:
            sesion = localizar_sesion(dia, regimenes_confiables, idx_por_tiempo, n)
            if sesion is None:
                continue
            idx_apertura, idx_cierre = sesion
            candidatos = [j for j in range(idx_apertura + 1, idx_cierre)
                          if categoria_hueco.iloc[j] == 'intrasesion' and categoria_hueco.iloc[j + 1] == 'intrasesion']
            if not candidatos:
                continue
            idx_entrada = int(rng.choice(candidatos)) + 1
            direccion = 'largo' if rng.random() < 0.5 else 'corto'
            precio_entrada = df['Open'].iloc[idx_entrada]
            sl = precio_entrada - riesgo if direccion == 'largo' else precio_entrada + riesgo
            vwap_arr = construir_vwap_sesion(df, idx_apertura, idx_cierre)
            resultado_precio, motivo = simular_salida(df, categoria_hueco, idx_entrada, idx_cierre, point,
                                                       precio_entrada, sl, direccion, vwap_arr, idx_apertura)
            spread_entrada = df['Spread'].iloc[idx_entrada] * point
            ret_bruto = (resultado_precio - precio_entrada) if direccion == 'largo' else (precio_entrada - resultado_precio)
            ops.append(dict(ret_bruto_puntos=ret_bruto, riesgo_puntos=riesgo, spread_entrada_precio=spread_entrada))
        if not ops:
            continue
        ops_df = pd.DataFrame(ops)
        ops_r = calcular_r_multiplos(ops_df, 0.0)
        medias.append(ops_r['R'].mean())
    return np.array(medias)


def referencia_aleatoria_emparejada(df, categoria_hueco, regimenes_confiables, idx_por_tiempo, n, point,
                                     ops_reales, dias_validos_universo, rng):
    """VERSION CORREGIDA: para cada operacion real, se recupera su offset
    exacto (velas desde la apertura de sesion = misma hora ET, mismo
    tiempo restante hasta el cierre de las 16:00 ET), y se sortea un DIA
    DISTINTO (de entre todos los dias con sesion valida) al que trasladar
    ESE MISMO offset -- mismo riesgo, misma hora, mismo tiempo restante,
    misma regla de salida y mismos costes; solo cambia el dia/accion de
    precio y la direccion (aleatoria 50/50). Si el offset no cabe en el
    dia donante (p.ej. sesion mas corta) o cae en un hueco, se redescarta
    esa operacion para esa repeticion (no se fuerza)."""
    offsets_riesgos = []
    for _, row in ops_reales.iterrows():
        rec = recuperar_offset_entrada(df, row['precio_entrada'], row['dia'], regimenes_confiables, idx_por_tiempo, n)
        if rec is None:
            continue
        idx_apertura_real, idx_cierre_real, idx_entrada_real = rec
        offsets_riesgos.append((idx_entrada_real - idx_apertura_real, row['riesgo_puntos']))

    medias = []
    for _ in range(N_REPETICIONES):
        ops = []
        for offset, riesgo in offsets_riesgos:
            dia_d, idx_apertura_d, idx_cierre_d = dias_validos_universo[rng.integers(len(dias_validos_universo))]
            idx_entrada = idx_apertura_d + offset
            if idx_entrada > idx_cierre_d or idx_entrada >= n:
                continue
            if categoria_hueco.iloc[idx_entrada] != 'intrasesion':
                continue
            direccion = 'largo' if rng.random() < 0.5 else 'corto'
            precio_entrada = df['Open'].iloc[idx_entrada]
            sl = precio_entrada - riesgo if direccion == 'largo' else precio_entrada + riesgo
            vwap_arr = construir_vwap_sesion(df, idx_apertura_d, idx_cierre_d)
            resultado_precio, motivo = simular_salida(df, categoria_hueco, idx_entrada, idx_cierre_d, point,
                                                       precio_entrada, sl, direccion, vwap_arr, idx_apertura_d)
            spread_entrada = df['Spread'].iloc[idx_entrada] * point
            ret_bruto = (resultado_precio - precio_entrada) if direccion == 'largo' else (precio_entrada - resultado_precio)
            ops.append(dict(ret_bruto_puntos=ret_bruto, riesgo_puntos=riesgo, spread_entrada_precio=spread_entrada))
        if not ops:
            continue
        ops_df = pd.DataFrame(ops)
        ops_r = calcular_r_multiplos(ops_df, 0.0)
        medias.append(ops_r['R'].mean())
    return np.array(medias)


def sensibilidad_spread_riesgo(nombre, ops):
    ops_r = calcular_r_multiplos(ops, 0.0)
    frac = ops['spread_entrada_precio'] / ops['riesgo_puntos']
    print(f"\n  [{nombre}] Sensibilidad a stops muy pequeños (SOLO diagnostico, "
          f"no se adopta ningun filtro):")
    for umbral in (0.10, 0.20):
        mask = frac > umbral
        print(f"    spread>{umbral*100:.0f}% del riesgo: n={mask.sum()} ({mask.mean()*100:.1f}% de las operaciones)  "
              f"media R EXCLUYENDO esas = {ops_r.loc[~mask, 'R'].mean():+.4f}  "
              f"(con todas las operaciones = {ops_r['R'].mean():+.4f})")


def auditar(nombre, path):
    df = cargar_y_verificar(path, nombre)
    categoria_hueco = clasificar_huecos(df)
    tabla = detectar_apertura_caja_por_semana(df)
    reg = construir_regimenes(tabla)
    reg_conf = filtrar_regimenes_confiables(reg)
    idx_por_tiempo = {t: i for i, t in enumerate(df['TimestampServidor'])}
    n = len(df)
    point = 0.01
    dias = sorted(set(df['TimestampServidor'].dt.normalize()))
    rng = np.random.default_rng(RNG_SEED + hash(nombre) % 1000)

    ops, _ = ejecutar_vwap_reversion(df, categoria_hueco, reg_conf, point)
    media_real = metricas_en_r(calcular_r_multiplos(ops, 0.0))['media_R']

    print(f"\n\n################ {nombre} -- VWAP Mean Reversion, auditoria profunda ################")
    print(f"  n={len(ops)}  Media R real (ya con fix Bid/Ask) = {media_real:+.4f}")

    # Distribucion horaria real vs la de la referencia original (para EVIDENCIAR el sesgo)
    horas = []
    for _, row in ops.iterrows():
        rec = recuperar_offset_entrada(df, row['precio_entrada'], row['dia'], reg_conf, idx_por_tiempo, n)
        if rec is not None:
            idx_ap, idx_ci, idx_en = rec
            horas.append(9.5 + (idx_en - idx_ap) * 0.25)
    horas = np.array(horas)
    print(f"\n  Distribucion horaria ET REAL de las señales: "
          f"{(horas <= 10.5).mean()*100:.1f}% entre 9:30-10:30, "
          f"mediana={np.median(horas):.2f}h, p90={np.quantile(horas,0.9):.2f}h")
    print(f"  (la referencia aleatoria ORIGINAL sortea uniformemente en TODA la sesion "
          f"9:30-16:00 -> solo ~{100/6.5:.0f}% caeria en 9:30-10:30 por azar: "
          f"las dos muestras NO tienen la misma distribucion horaria ni el mismo "
          f"tiempo restante hasta el cierre -- comparacion NO emparejada.)")

    medias_original = referencia_aleatoria_original(df, categoria_hueco, reg_conf, idx_por_tiempo, n, point, ops, rng)
    z_original = (media_real - medias_original.mean()) / medias_original.std() if medias_original.std() > 0 else np.nan
    print(f"\n  Referencia ORIGINAL (entrada uniforme en toda la sesion, {len(medias_original)} repeticiones utiles):")
    print(f"    media={medias_original.mean():+.4f}  std={medias_original.std():.4f}  z={z_original:+.2f}")

    dias_validos_universo = dias_sesion_valida(df, categoria_hueco, reg_conf, idx_por_tiempo, n, dias)
    medias_emparejada = referencia_aleatoria_emparejada(df, categoria_hueco, reg_conf, idx_por_tiempo, n, point,
                                                         ops, dias_validos_universo, rng)
    z_emparejada = (media_real - medias_emparejada.mean()) / medias_emparejada.std() if medias_emparejada.std() > 0 else np.nan
    print(f"\n  Referencia EMPAREJADA (mismo offset exacto desde la apertura -> misma hora ET "
          f"y mismo tiempo restante hasta el cierre, dia donante aleatorio, {len(medias_emparejada)} "
          f"repeticiones utiles):")
    print(f"    media={medias_emparejada.mean():+.4f}  std={medias_emparejada.std():.4f}  z={z_emparejada:+.2f}")

    sensibilidad_spread_riesgo(nombre, ops)


def main(rutas):
    for nombre, path in rutas.items():
        auditar(nombre, path)


if __name__ == '__main__':
    main({'USTEC': sys.argv[1], 'US500': sys.argv[2]})
