"""
FASE 1 -- Identificar la ventaja (NO construir estrategia todavia).

Hipotesis B: efecto de cambio de mes ("Turn-of-the-Month Effect").

DEFINICION ORIGINAL EN LA LITERATURA (revisada antes de programar, sin
inventar reglas):
 - Ariel (1987), "A Monthly Effect in Stock Returns": encuentra que el
   retorno medio positivo del indice se concentra en la PRIMERA MITAD
   del mes de sesiones bursatiles (el ultimo dia de sesion del mes
   anterior + los primeros dias de sesion del mes en curso), mientras
   que la segunda mitad del mes no muestra retorno medio distinguible
   de cero.
 - Lakonishok & Smidt (1988), "Are Seasonal Anomalies Real? A
   Ninety-Year Perspective" (Dow Jones, 1897-1986): definen y
   popularizan la ventana de "cambio de mes" de forma mas concreta y
   es la que se usa aqui -- el ULTIMO dia de sesion del mes M mas los
   TRES primeros dias de sesion del mes M+1 (4 sesiones en total).

VENTANA PRE-REGISTRADA (una sola, fijada antes de ejecutar, en
SESIONES BURSATILES -- no dias naturales): tratamiento = {ultimo dia
de sesion del mes M, dias de sesion 1, 2 y 3 del mes M+1}. Control =
el resto de sesiones.

Retorno por sesion: close-to-close, ret[t] = Close[t]/Close[t-1] - 1
(convencion estandar de la literatura original, incluye el hueco de
cierre a cierre, no es un retorno intradia open-to-close).

XAUUSD: se analiza para comprobar si el efecto se EXTIENDE a otro tipo
de activo (materia prima) -- no es una replica del estudio original,
que es especifico de indices de acciones.

Incertidumbre (punto 6 -- los dias de una misma ventana de cambio de
mes NO son independientes entre si): bootstrap de CLUSTERS, donde cada
cluster es un bloque CONTIGUO de sesiones que termina justo al cierre
de una ventana de cambio de mes y empieza justo despues de que termine
la ventana anterior (es decir, cada cluster contiene exactamente una
ventana de tratamiento de 4 sesiones mas las sesiones de control que la
preceden desde el cluster anterior). Se resamplean los clusters
completos (con reemplazo), preservando la dependencia dentro de cada
ventana mensual.

No se optimiza la ventana ni el umbral tras ver resultados -- una sola
definicion, fijada arriba, para los 3 mercados.
"""
import sys

import numpy as np
import pandas as pd

from hipotesis_rsi2_sma200 import cargar_m15, agregar_diario

N_DIAS_MES_SIGUIENTE = 3  # primeros N dias de sesion del mes M+1
REPETICIONES_BOOTSTRAP = 2000
SEED = 20261015


def construir_tabla_turno_mes(diario):
    d = diario.copy().reset_index(drop=True)
    d['ret'] = d['Close'] / d['Close'].shift(1) - 1.0
    d['anio'] = d['dia'].dt.year
    d['mes'] = d['dia'].dt.month
    d = d[d['ret'].notna()].reset_index(drop=True)

    # localizar el ULTIMO dia de sesion de cada mes (cambio de mes == fila
    # siguiente tiene un mes distinto)
    cambia_mes = d['mes'].shift(-1) != d['mes']
    idx_ultimo_dia_mes = d.index[cambia_mes & d['mes'].shift(-1).notna()].to_numpy()

    tratamiento_idx = set()
    episodios = []  # (idx_inicio_ventana, idx_fin_ventana)
    for idx_ult in idx_ultimo_dia_mes:
        ventana = [idx_ult] + [idx_ult + k for k in range(1, N_DIAS_MES_SIGUIENTE + 1)]
        if ventana[-1] >= len(d):
            continue  # ventana incompleta al final de la serie -- se descarta, no se rellena
        tratamiento_idx.update(ventana)
        episodios.append((ventana[0], ventana[-1]))

    d['tratamiento'] = d.index.isin(tratamiento_idx)
    return d, sorted(episodios)


def construir_clusters(d, episodios):
    """Cada cluster = bloque contiguo que termina justo al final de una
    ventana de cambio de mes y empieza justo despues del final de la
    ventana anterior (incluye sus dias de control + su propia ventana de
    tratamiento) -- la unidad de resampleo para el bootstrap."""
    clusters = []
    inicio = 0
    for _, fin_ventana in episodios:
        if fin_ventana < inicio:
            continue
        clusters.append((inicio, fin_ventana))
        inicio = fin_ventana + 1
    return clusters


def bootstrap_diferencia_clusters(d, clusters, repeticiones=REPETICIONES_BOOTSTRAP, seed=SEED):
    rng = np.random.default_rng(seed)
    ret = d['ret'].to_numpy()
    trat = d['tratamiento'].to_numpy()
    n_clusters = len(clusters)
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


def sensibilidad_episodios_extremos(d, episodios):
    medias_episodio = []
    for ini, fin in episodios:
        medias_episodio.append(d['ret'].iloc[ini:fin + 1].mean())
    medias_episodio = np.array(medias_episodio)
    orden = np.sort(medias_episodio)
    media_todos = orden.mean()
    media_sin_extremos = orden[1:-1].mean() if len(orden) >= 3 else np.nan
    return media_todos, media_sin_extremos, orden[-1], orden[0]


def analizar(nombre, path, nota=''):
    print(f"\n\n################ TURNO DE MES -- {nombre} ################{nota}")
    df = cargar_m15(path)
    diario = agregar_diario(df)
    d, episodios = construir_tabla_turno_mes(diario)
    clusters = construir_clusters(d, episodios)

    trat = d[d['tratamiento']]['ret']
    ctrl = d[~d['tratamiento']]['ret']
    n_episodios = len(episodios)
    print(f"  Cambios de mes analizados (ventanas completas de 4 sesiones): {n_episodios}")
    print(f"  Tratamiento (turno de mes): n={len(trat)} sesiones  media={trat.mean()*100:+.4f}%  "
          f"mediana={trat.median()*100:+.4f}%")
    print(f"  Control (resto de sesiones): n={len(ctrl)} sesiones  media={ctrl.mean()*100:+.4f}%  "
          f"mediana={ctrl.median()*100:+.4f}%")

    efecto = trat.mean() - ctrl.mean()
    lo, hi, n_rep = bootstrap_diferencia_clusters(d, clusters)
    sig = not (lo <= 0 <= hi) if not np.isnan(lo) else False
    print(f"  Efecto (tratamiento-control) = {efecto*100:+.4f} pp/sesion   "
          f"IC95% diferencia (bootstrap de {len(clusters)} clusters mensuales, {n_rep} rep.) = "
          f"[{lo*100:+.4f}, {hi*100:+.4f}]  {'-> EXCLUYE CERO' if sig else '-> CRUZA CERO (no significativo)'}")

    media_todos, media_sin_extremos, mejor, peor = sensibilidad_episodios_extremos(d, episodios)
    print(f"  Sensibilidad: media de retorno POR EPISODIO con todos={media_todos*100:+.4f}%  "
          f"quitando el mejor y el peor episodio={media_sin_extremos*100:+.4f}%  "
          f"(mejor episodio={mejor*100:+.4f}%, peor={peor*100:+.4f}%)")

    print("  Por año:")
    for anio, g in d.groupby('anio'):
        t_a = g[g['tratamiento']]['ret']
        c_a = g[~g['tratamiento']]['ret']
        aviso = '  [incompleto]' if anio in (2023, 2025) else ''
        if len(t_a) == 0:
            print(f"    {anio}: sin ventanas completas{aviso}")
            continue
        print(f"    {anio}: n_trat={len(t_a)} media={t_a.mean()*100:+.4f}%  "
              f"n_ctrl={len(c_a)} media={c_a.mean()*100:+.4f}%{aviso}")

    print(f"  Limitacion de muestra: {n_episodios} episodios independientes es una muestra pequeña "
          f"para un bootstrap de clusters -- los IC seran anchos por construccion, no solo por ausencia de efecto.")

    return dict(n_episodios=n_episodios, efecto=efecto, lo=lo, hi=hi, sig=sig)


def main(rutas):
    resumen = {}
    for nombre, (path, nota) in rutas.items():
        resumen[nombre] = analizar(nombre, path, nota)
    print("\n\n################ RESUMEN ################")
    for nombre, r in resumen.items():
        print(f"  {nombre}: episodios={r['n_episodios']}  efecto={r['efecto']*100:+.4f}pp/sesion  "
              f"IC95%=[{r['lo']*100:+.4f},{r['hi']*100:+.4f}]  {'SIGNIFICATIVO' if r['sig'] else 'no significativo'}")
    return resumen


if __name__ == '__main__':
    main({
        'USTEC': (sys.argv[1], ''),
        'US500': (sys.argv[2], ''),
        'XAUUSD': (sys.argv[3], '  (extension a otra clase de activo, no replica del estudio original)'),
    })
