"""
Auditoria diagnostica del motor de backtest y de los resultados de las
4 familias de estrategias ya cerradas (ORB, Liquidity Sweep + Reversal,
VWAP Mean Reversion, Trend Continuation Pullback). NO modifica ninguna
estrategia, NO prueba parametros nuevos -- solo analiza lo ya producido
y añade una referencia de entradas aleatorias para comparar contra algo
mas estricto que cero. Ver README.md para la discusion completa.
"""
import sys
from datetime import timedelta

import numpy as np
import pandas as pd

from orb_backtest import (
    MINUTOS_SESION_REGULAR, TP_EN_R,
    cargar_y_verificar, clasificar_huecos, detectar_apertura_caja_por_semana,
    construir_regimenes, filtrar_regimenes_confiables,
    calcular_r_multiplos, metricas_en_r, ejecutar_orb,
)
from liquidity_sweep_backtest import ejecutar_liquidity_sweep
from vwap_reversion_backtest import ejecutar_vwap_reversion, N_DESVIACIONES
from trend_continuation_backtest import ejecutar_tendencia_pullback

RNG_SEED = 20261013
N_REPETICIONES_ALEATORIAS = 100


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


def anadir_hora_et_entrada(ops, df, idx_por_tiempo, regimenes_confiables, n):
    """Recupera, sin tocar la logica de la estrategia, a que hora ET (aprox.,
    en fraccion horaria desde 9:30) entro cada operacion real -- buscando,
    dentro de la sesion de ese dia, la vela cuyo Open coincide exactamente
    con el precio de entrada ya registrado (mismo float, sin redondeos)."""
    horas = []
    for _, row in ops.iterrows():
        sesion = localizar_sesion(row['dia'], regimenes_confiables, idx_por_tiempo, n)
        if sesion is None:
            horas.append(np.nan)
            continue
        idx_apertura, idx_cierre = sesion
        sub = df.iloc[idx_apertura + 1:idx_cierre + 1]
        candidatos = sub.index[sub['Open'] == row['precio_entrada']]
        if len(candidatos) == 0:
            horas.append(np.nan)
            continue
        idx_entrada = candidatos[0]
        horas.append(9.5 + (idx_entrada - idx_apertura) * 0.25)
    ops = ops.copy()
    ops['hora_et_entrada'] = horas
    return ops


def construir_vwap_por_dia(df, categoria_hueco, regimenes_confiables, idx_por_tiempo, n, dias):
    """Recalcula el VWAP de sesion (identico a vwap_reversion_backtest) para
    poder usarlo como regla de salida en la referencia aleatoria cuando se
    compara contra VWAP Mean Reversion."""
    vwaps = {}
    for dia in dias:
        sesion = localizar_sesion(dia, regimenes_confiables, idx_por_tiempo, n)
        if sesion is None:
            continue
        idx_apertura, idx_cierre = sesion
        if (categoria_hueco.iloc[idx_apertura:idx_cierre + 1] != 'intrasesion').any():
            continue
        sub = df.iloc[idx_apertura:idx_cierre + 1]
        tp_precio = (sub['High'] + sub['Low'] + sub['Close']) / 3.0
        vol = sub['TickVolume'].astype(float)
        cum_vol = vol.cumsum()
        cum_pv = (tp_precio * vol).cumsum()
        vwap = (cum_pv / cum_vol).to_numpy()
        vwaps[dia] = (idx_apertura, idx_cierre, vwap)
    return vwaps


def construir_ops_aleatorias(df, categoria_hueco, regimenes_confiables, idx_por_tiempo, n, point,
                              dias_riesgos, regla_salida, vwap_por_dia, rng):
    """Para cada (dia, riesgo_real) de la estrategia real, genera UNA operacion
    sustituta: misma sesion, mismo tamaño de riesgo (misma distancia de SL en
    puntos), entrada en una vela ALEATORIA de esa sesion, direccion aleatoria
    50/50, y la MISMA regla de salida que la estrategia real (2R fijo o
    reversion al VWAP de sesion) + el mismo coste de spread real de entrada.
    Es la referencia nula: mismos dias, misma frecuencia, mismo riesgo,
    mismos costes -- solo la señal de entrada/direccion es aleatoria."""
    operaciones = []
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

        if direccion == 'largo':
            sl = precio_entrada - riesgo
            tp = precio_entrada + TP_EN_R * riesgo
        else:
            sl = precio_entrada + riesgo
            tp = precio_entrada - TP_EN_R * riesgo

        spread_entrada = df['Spread'].iloc[idx_entrada] * point

        vwap_dia = None
        if regla_salida == 'vwap' and dia in vwap_por_dia:
            idx_ap_v, idx_ci_v, vwap_arr = vwap_por_dia[dia]
            if idx_ap_v == idx_apertura:
                vwap_dia = vwap_arr

        resultado_precio, motivo_salida = None, None
        for k in range(idx_entrada, idx_cierre + 1):
            if categoria_hueco.iloc[k] != 'intrasesion' and k != idx_entrada:
                break
            hi, lo = df['High'].iloc[k], df['Low'].iloc[k]
            if regla_salida == 'vwap' and vwap_dia is not None:
                objetivo = vwap_dia[k - idx_apertura]
            else:
                objetivo = tp
            if direccion == 'largo':
                toca_sl = lo <= sl
                toca_tp = hi >= objetivo
            else:
                toca_sl = hi >= sl
                toca_tp = lo <= objetivo
            if toca_sl:
                resultado_precio, motivo_salida = sl, 'SL'
                break
            if toca_tp:
                resultado_precio, motivo_salida = objetivo, 'TP'
                break
        if resultado_precio is None:
            resultado_precio = df['Close'].iloc[idx_cierre]
            motivo_salida = 'CIERRE_SESION'

        ret_bruto_puntos = (resultado_precio - precio_entrada) if direccion == 'largo' else (precio_entrada - resultado_precio)
        operaciones.append(dict(
            dia=dia, anio=dia.year, direccion=direccion,
            ret_bruto_puntos=ret_bruto_puntos, riesgo_puntos=riesgo,
            spread_entrada_precio=spread_entrada, motivo_salida=motivo_salida,
            peor_flotante_r=np.nan,  # no se usa en la comparacion (solo media_R), pero metricas_en_r lo espera
        ))
    return pd.DataFrame(operaciones)


def tabla_por_motivo_salida(nombre, ops):
    ops_r = calcular_r_multiplos(ops, 0.0)
    print(f"\n  [{nombre}] Desglose por motivo de salida (solo spread real):")
    for motivo, g in ops_r.groupby('motivo_salida'):
        print(f"    {motivo:14s} n={len(g):4d}  media R={g['R'].mean():+.3f}  mediana R={g['R'].median():+.3f}")


def analizar_distribucion_y_spread(nombre, ops):
    ops_r = calcular_r_multiplos(ops, 0.0)
    r = ops_r['R']
    frac_spread = ops['spread_entrada_precio'] / ops['riesgo_puntos']
    print(f"\n  [{nombre}] Distribucion de R (solo spread real): "
          f"min={r.min():.2f} p25={r.quantile(.25):.2f} mediana={r.median():.2f} "
          f"p75={r.quantile(.75):.2f} max={r.max():.2f}  std={r.std():.3f}")
    print(f"  [{nombre}] Spread/riesgo: media={frac_spread.mean()*100:.1f}%  "
          f"max={frac_spread.max()*100:.1f}%  "
          f"% operaciones con spread>10% del riesgo={ (frac_spread>0.10).mean()*100:.1f}%  "
          f"% operaciones con spread>20% del riesgo={ (frac_spread>0.20).mean()*100:.1f}%")


def analizar_por_hora(nombre, ops_con_hora):
    ops_r = calcular_r_multiplos(ops_con_hora.dropna(subset=['hora_et_entrada']), 0.0)
    ops_r['bloque_horario'] = pd.cut(
        ops_r['hora_et_entrada'],
        bins=[9.5, 10.5, 11.5, 13.0, 14.5, 16.0],
        labels=['09:30-10:30', '10:30-11:30', '11:30-13:00', '13:00-14:30', '14:30-16:00'],
        include_lowest=True,
    )
    print(f"\n  [{nombre}] Media R por bloque horario ET de entrada (solo descriptivo, "
          f"NO se usa para filtrar):")
    for bloque, g in ops_r.groupby('bloque_horario', observed=True):
        if len(g) == 0:
            continue
        print(f"    {str(bloque):14s} n={len(g):4d}  media R={g['R'].mean():+.3f}")


def comparar_con_aleatorio(nombre, ops_reales, df, categoria_hueco, regimenes_confiables,
                            idx_por_tiempo, n, point, regla_salida, vwap_por_dia, rng):
    dias_riesgos = list(zip(ops_reales['dia'], ops_reales['riesgo_puntos']))
    medias_nulas = []
    for _ in range(N_REPETICIONES_ALEATORIAS):
        ops_falsas = construir_ops_aleatorias(df, categoria_hueco, regimenes_confiables, idx_por_tiempo,
                                               n, point, dias_riesgos, regla_salida, vwap_por_dia, rng)
        if len(ops_falsas) == 0:
            continue
        m = metricas_en_r(calcular_r_multiplos(ops_falsas, 0.0))
        medias_nulas.append(m['media_R'])
    medias_nulas = np.array(medias_nulas)
    media_real = metricas_en_r(calcular_r_multiplos(ops_reales, 0.0))['media_R']
    z = (media_real - medias_nulas.mean()) / medias_nulas.std() if medias_nulas.std() > 0 else np.nan
    print(f"\n  [{nombre}] Referencia de entradas ALEATORIAS (mismos dias/riesgo/regla de salida/costes, "
          f"{N_REPETICIONES_ALEATORIAS} repeticiones):")
    print(f"    Media R real                 = {media_real:+.4f}")
    print(f"    Media R aleatoria: media={medias_nulas.mean():+.4f}  std={medias_nulas.std():.4f}  "
          f"rango=[{medias_nulas.min():+.4f}, {medias_nulas.max():+.4f}]")
    print(f"    z = (real - media_aleatoria) / std_aleatoria = {z:+.2f}")


def auditar_instrumento(nombre, path):
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

    vwap_por_dia = construir_vwap_por_dia(df, categoria_hueco, reg_conf, idx_por_tiempo, n, dias)

    estrategias = {}
    ops_orb, _ = ejecutar_orb(df, categoria_hueco, reg_conf, 2, point)
    estrategias['ORB'] = (ops_orb, '2R')
    ops_ls, _ = ejecutar_liquidity_sweep(df, categoria_hueco, reg_conf, point)
    estrategias['Liquidity Sweep'] = (ops_ls, '2R')
    ops_vwap, _ = ejecutar_vwap_reversion(df, categoria_hueco, reg_conf, point)
    estrategias['VWAP Mean Reversion'] = (ops_vwap, 'vwap')
    ops_tc, _ = ejecutar_tendencia_pullback(df, categoria_hueco, reg_conf, point,
                                             nivel_pullback=df['Close'].ewm(span=20, adjust=False).mean(),
                                             modo='precio_vs_nivel')
    estrategias['Trend Continuation (BASE EMA20)'] = (ops_tc, '2R')

    print(f"\n\n################ AUDITORIA -- {nombre} ################")
    for etiqueta, (ops, regla_salida) in estrategias.items():
        if len(ops) == 0:
            print(f"\n  [{etiqueta}] sin operaciones, se omite.")
            continue
        print(f"\n--- {etiqueta} (n={len(ops)}) ---")
        tabla_por_motivo_salida(etiqueta, ops)
        analizar_distribucion_y_spread(etiqueta, ops)
        ops_hora = anadir_hora_et_entrada(ops, df, idx_por_tiempo, reg_conf, n)
        analizar_por_hora(etiqueta, ops_hora)
        comparar_con_aleatorio(etiqueta, ops, df, categoria_hueco, reg_conf, idx_por_tiempo, n,
                                point, regla_salida, vwap_por_dia, rng)

    # Sanity check de integridad del motor: todo R realizado debe quedar
    # acotado por construccion (TP<=2R, SL=-1R exacto, cierre de sesion
    # puede estar en cualquier punto intermedio) -- confirma que no hay
    # valores imposibles colandose en ninguna de las 4 familias.
    print(f"\n--- Verificacion de integridad (rango de R realizado, todas las estrategias) ---")
    for etiqueta, (ops, _) in estrategias.items():
        if len(ops) == 0:
            continue
        r = calcular_r_multiplos(ops, 0.0)['R']
        print(f"  {etiqueta}: R realizado en [{r.min():.3f}, {r.max():.3f}]  "
              f"(se esperaba aprox. [-1.1, 2.1] permitiendo el coste de spread restado)")


def main(rutas):
    for nombre, path in rutas.items():
        auditar_instrumento(nombre, path)


if __name__ == '__main__':
    main({'USTEC': sys.argv[1], 'US500': sys.argv[2]})
