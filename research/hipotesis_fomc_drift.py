"""
FASE 1 -- Identificar la ventaja (NO construir estrategia todavia).
ULTIMA anomalia investigada sobre el historico 2023-2026 actual (ver
README) -- tras esta, se revisa metodologia/datos antes de seguir.

Hipotesis C: Pre-FOMC Announcement Drift (Lucca & Moench, 2015, "The
Pre-FOMC Announcement Drift", Journal of Finance) -- el S&P500 muestra
una deriva alcista anormal en las horas previas a cada anuncio
PROGRAMADO de la Fed (estadistica de politica monetaria a las 14:00
ET), frente a periodos equivalentes sin FOMC. Fundamento: resolucion de
la prima de riesgo por incertidumbre de politica monetaria antes de
conocerse la decision.

PASO 1 -- Calendario FOMC 2023-2026 (verificado por busqueda web, NO
inventado): fechas del segundo dia de cada reunion programada (dia de
publicacion del comunicado), de federalreserve.gov (2023 y 2026
confirmados directamente desde la pagina oficial) y de fuentes
secundarias que citan el calendario tentativo publicado por la Fed
(2024 y 2025, corroboradas por multiples fuentes independientes
coincidentes). Hora de publicacion: 14:00 ET, politica vigente desde
2013 (confirmada via busqueda).

PASO 2 -- Ventana pre-registrada (adaptada a los datos disponibles,
una sola version): retorno desde el CIERRE de la sesion RTH (16:00 ET)
del dia habil ANTERIOR al anuncio, hasta el precio justo antes de las
14:00 ET del propio dia del anuncio (Close de la vela 13:45-14:00 ET).
Es una adaptacion de la ventana original de ~24h de Lucca & Moench
(que en el paper usa futuros, con sesion casi continua) a la
disponibilidad de velas M15 de este proyecto -- declarado
explicitamente, no es una replica exacta.

PASO 4 -- USTEC/US500: solo dias (el del anuncio Y el habil anterior)
con offset horario CONFIRMADO (misma reconstruccion ya validada en
este proyecto). XAUUSD: EXCLUIDO de esta prueba intradia -- ya se
comprobo en la hipotesis de momentum intradia que el metodo robusto de
reconstruccion horaria solo cubre el 43.6% de los dias en XAUUSD con
regimenes inestables; no hay manera fiable de localizar las 14:00 ET en
su historico, asi que no se fuerza el analisis ahi.

PASO 6 -- Cada evento FOMC aporta UNA sola observacion (una ventana por
anuncio, no hay solapamiento dentro de un mismo evento). Incertidumbre
con bootstrap de CLUSTERS (mismo diseño que hipotesis_turno_mes.py):
cada cluster es un bloque contiguo de dias que termina justo en un
evento FOMC, incluyendo los dias de control desde el evento anterior.
"""
import sys
from datetime import date, timedelta

import numpy as np
import pandas as pd

from orb_backtest import (
    MINUTOS_SESION_REGULAR,
    cargar_y_verificar, clasificar_huecos, detectar_apertura_caja_por_semana,
    construir_regimenes, filtrar_regimenes_confiables,
)

# Dia de publicacion del comunicado (2º dia de cada reunion programada),
# verificado via busqueda web -- 2023 y 2026 desde federalreserve.gov
# directamente; 2024 y 2025 desde el calendario tentativo de la Fed
# citado por multiples fuentes secundarias coincidentes.
FECHAS_FOMC = [
    date(2023, 2, 1), date(2023, 3, 22), date(2023, 5, 3), date(2023, 6, 14),
    date(2023, 7, 26), date(2023, 9, 20), date(2023, 11, 1), date(2023, 12, 13),
    date(2024, 1, 31), date(2024, 3, 20), date(2024, 5, 1), date(2024, 6, 12),
    date(2024, 7, 31), date(2024, 9, 18), date(2024, 11, 7), date(2024, 12, 18),
    date(2025, 1, 29), date(2025, 3, 19), date(2025, 5, 7), date(2025, 6, 18),
    date(2025, 7, 30), date(2025, 9, 17), date(2025, 10, 29), date(2025, 12, 10),
    date(2026, 1, 28), date(2026, 3, 18), date(2026, 4, 29), date(2026, 6, 17),
    date(2026, 7, 29), date(2026, 9, 16), date(2026, 10, 28), date(2026, 12, 9),
]
FECHAS_FOMC_SET = set(FECHAS_FOMC)

MINUTOS_HASTA_1400 = 4 * 60 + 30  # 9:30 ET -> 14:00 ET
REPETICIONES_BOOTSTRAP = 2000
SEED = 20261016


def construir_tabla_fomc(df, categoria_hueco, regimenes_confiables):
    tiempos = df['TimestampServidor']
    idx_por_tiempo = {t: i for i, t in enumerate(tiempos)}
    n = len(df)
    dias = sorted(set(tiempos.dt.normalize()))

    filas = []
    descartes = dict(offset_no_confirmado=0, vela_1400_ausente=0, hueco_hasta_1400=0,
                      referencia_dia_anterior_no_disponible=0)
    dia_anterior_info = None  # (fecha, idx_cierre_rth)

    for dia in dias:
        if dia.dayofweek >= 5:
            continue
        reg = regimenes_confiables[(regimenes_confiables['inicio'] <= dia) & (regimenes_confiables['fin'] > dia)]
        if len(reg) == 0:
            descartes['offset_no_confirmado'] += 1
            dia_anterior_info = None
            continue

        slot = int(reg.iloc[0]['slot_apertura'])
        h, m = slot // 4, (slot % 4) * 15
        t_apertura = dia + timedelta(hours=h, minutes=m)
        t_1400 = t_apertura + timedelta(minutes=MINUTOS_HASTA_1400)
        t_cierre_rth = t_apertura + timedelta(minutes=MINUTOS_SESION_REGULAR) - timedelta(minutes=15)

        idx_apertura = idx_por_tiempo.get(t_apertura)
        idx_1400 = idx_por_tiempo.get(t_1400)
        idx_cierre_rth = idx_por_tiempo.get(t_cierre_rth)
        if idx_apertura is None or idx_1400 is None or idx_cierre_rth is None or idx_1400 >= n:
            descartes['vela_1400_ausente'] += 1
            dia_anterior_info = None
            continue
        if (categoria_hueco.iloc[idx_apertura:idx_1400 + 1] != 'intrasesion').any():
            descartes['hueco_hasta_1400'] += 1
            dia_anterior_info = None
            continue

        referencia_valida = (dia_anterior_info is not None and (dia - dia_anterior_info[0]).days <= 3)
        if not referencia_valida:
            descartes['referencia_dia_anterior_no_disponible'] += 1
            dia_anterior_info = (dia, idx_cierre_rth)
            continue

        idx_cierre_anterior = dia_anterior_info[1]
        ret = df['Close'].iloc[idx_1400] / df['Close'].iloc[idx_cierre_anterior] - 1.0
        es_fomc = dia.date() in FECHAS_FOMC_SET
        filas.append(dict(dia=dia, anio=dia.year, ret=ret, tratamiento=es_fomc))

        dia_anterior_info = (dia, idx_cierre_rth)

    return pd.DataFrame(filas), descartes


def construir_clusters(d):
    clusters = []
    inicio = 0
    idx_eventos = d.index[d['tratamiento']].to_numpy()
    for idx_ev in idx_eventos:
        if idx_ev < inicio:
            continue
        clusters.append((inicio, idx_ev))
        inicio = idx_ev + 1
    return clusters


def bootstrap_diferencia_clusters(d, clusters, repeticiones=REPETICIONES_BOOTSTRAP, seed=SEED):
    rng = np.random.default_rng(seed)
    ret = d['ret'].to_numpy()
    trat = d['tratamiento'].to_numpy()
    n_clusters = len(clusters)
    if n_clusters == 0:
        return (np.nan, np.nan, 0)
    diffs = []
    for _ in range(repeticiones):
        elegidos = rng.integers(0, n_clusters, size=n_clusters)
        idx = np.concatenate([np.arange(clusters[c][0], clusters[c][1] + 1) for c in elegidos])
        r, t = ret[idx], trat[idx]
        if t.sum() == 0 or (~t).sum() == 0:
            continue
        diffs.append(r[t].mean() - r[~t].mean())
    if not diffs:
        return (np.nan, np.nan, 0)
    diffs = np.array(diffs)
    return np.percentile(diffs, 2.5), np.percentile(diffs, 97.5), len(diffs)


def analizar(nombre, path):
    print(f"\n\n################ PRE-FOMC DRIFT -- {nombre} ################")
    df = cargar_y_verificar(path, nombre)
    categoria_hueco = clasificar_huecos(df)
    tabla_reg = detectar_apertura_caja_por_semana(df)
    reg = construir_regimenes(tabla_reg)
    reg_conf = filtrar_regimenes_confiables(reg)

    d, descartes = construir_tabla_fomc(df, categoria_hueco, reg_conf)
    print(f"  Descartes: {descartes}")

    n_fomc_calendario = sum(1 for f in FECHAS_FOMC if f <= df['TimestampServidor'].max().date())
    trat = d[d['tratamiento']]['ret']
    ctrl = d[~d['tratamiento']]['ret']
    print(f"  Eventos FOMC en el calendario dentro del rango de datos: {n_fomc_calendario}")
    print(f"  Eventos FOMC usables (offset confirmado + referencia dia anterior): n={len(trat)}")
    print(f"  Tratamiento (ventana pre-FOMC): media={trat.mean()*100:+.4f}%  mediana={trat.median()*100:+.4f}%")
    print(f"  Control (misma ventana, dias sin FOMC): n={len(ctrl)}  media={ctrl.mean()*100:+.4f}%  "
          f"mediana={ctrl.median()*100:+.4f}%")

    if len(trat) == 0:
        print("  SIN EVENTOS USABLES -- no se puede evaluar esta hipotesis en este mercado.")
        return None

    efecto = trat.mean() - ctrl.mean()
    clusters = construir_clusters(d)
    lo, hi, n_rep = bootstrap_diferencia_clusters(d, clusters)
    sig = not (lo <= 0 <= hi) if not np.isnan(lo) else False
    print(f"  Efecto (tratamiento-control) = {efecto*100:+.4f} pp   "
          f"IC95% diferencia (bootstrap de {len(clusters)} clusters, {n_rep} rep.) = "
          f"[{lo*100:+.4f}, {hi*100:+.4f}]  {'-> EXCLUYE CERO' if sig else '-> CRUZA CERO (no significativo)'}")

    vals = np.sort(trat.to_numpy())
    media_todos = vals.mean()
    media_sin_extremos = vals[1:-1].mean() if len(vals) >= 3 else np.nan
    print(f"  Sensibilidad: media con todos={media_todos*100:+.4f}%  "
          f"quitando el mejor y el peor evento={media_sin_extremos*100:+.4f}%  "
          f"(mejor={vals[-1]*100:+.4f}%, peor={vals[0]*100:+.4f}%)")

    print("  Por año:")
    for anio, g in d.groupby('anio'):
        t_a = g[g['tratamiento']]['ret']
        c_a = g[~g['tratamiento']]['ret']
        if len(t_a) == 0:
            print(f"    {anio}: sin eventos usables")
            continue
        print(f"    {anio}: n_eventos={len(t_a)} media={t_a.mean()*100:+.4f}%  "
              f"n_ctrl={len(c_a)} media={c_a.mean()*100:+.4f}%")

    return dict(n=len(trat), efecto=efecto, lo=lo, hi=hi, sig=sig)


def main(rutas):
    resumen = {}
    for nombre, path in rutas.items():
        resumen[nombre] = analizar(nombre, path)
    print("\n\n################ RESUMEN ################")
    for nombre, r in resumen.items():
        if r is None:
            print(f"  {nombre}: sin evaluar (sin eventos usables)")
            continue
        print(f"  {nombre}: n={r['n']}  efecto={r['efecto']*100:+.4f}pp  "
              f"IC95%=[{r['lo']*100:+.4f},{r['hi']*100:+.4f}]  {'SIGNIFICATIVO' if r['sig'] else 'no significativo'}")
    return resumen


if __name__ == '__main__':
    main({'USTEC': sys.argv[1], 'US500': sys.argv[2]})
