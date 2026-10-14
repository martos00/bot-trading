"""
Comprobacion final de la hipotesis RSI(2)+SMA200 antes de construir la
estrategia (Fase 3). Alcance deliberadamente estrecho, a peticion del
usuario: SOLO RSI(2)<15, SOLO horizontes 1/3/5 dias, SOLO la PRIMERA
señal de cada episodio de sobreventa (operaciones independientes, no
una señal por dia dentro de la misma caida). No se prueban mas umbrales
ni se construye TP/SL -- es la ultima verificacion antes de decidir.

DEFINICION DE EPISODIO (igual criterio que hipotesis_rsi2_sma200.py,
restated aqui explicitamente): dentro de los dias en tendencia alcista
(Close diario > SMA200), un episodio de sobreventa es una racha MAXIMA
de dias de bolsa CONSECUTIVOS (sin hueco en la secuencia de dias
habiles reales, fines de semana no cuentan como hueco) con RSI(2)<15.
El episodio EMPIEZA en el primer dia de esa racha y TERMINA en el
ultimo dia consecutivo antes de que el RSI(2) suba a >=15 o el precio
deje de estar en tendencia alcista. Solo se usa el PRIMER dia de cada
episodio como señal (operacion independiente); los demas dias de la
misma racha se EXCLUYEN del analisis por completo (no cuentan ni como
tratamiento ni como control, para no contaminar el grupo de control con
dias de sobreventa continuada).

Grupo CONTROL: todos los demas dias en tendencia alcista con RSI(2)>=15
(sin tocar, igual que en el estudio original).

Incertidumbre: bootstrap de bloques CONJUNTO (bloques de 10 dias
consecutivos de la secuencia resultante tras excluir los dias de
continuacion de episodio), calculando directamente la distribucion de
(media tratamiento - media control) -- misma correccion aplicada tras
la verificacion anterior, no una nueva metodologia.

ESTE RESULTADO SIGUE SIENDO EXPLORATORIO: RSI(2)<15 se eligio despues
de ver los resultados de RSI(2)<5, <10 y <15 en el estudio anterior, no
antes. No sustituye la validacion fuera de muestra (Fase 3/pre-2023).
"""
import sys

import numpy as np
import pandas as pd

from hipotesis_rsi2_sma200 import (
    cargar_m15, agregar_diario, construir_tabla, detectar_episodios,
    bootstrap_diferencia_bloques, bootstrap_bloques_ic,
)

UMBRAL = 15
HORIZONTES_VERIF = [1, 3, 5]


def construir_conjunto_sin_continuaciones(uptrend_ord, umbral):
    episodios, primeros = detectar_episodios(uptrend_ord, umbral)
    idx_continuacion = set()
    for ep in episodios:
        idx_continuacion.update(ep[1:])  # todo salvo el primer dia de cada episodio
    mascara_fuera = uptrend_ord.index.isin(idx_continuacion)
    analisis = uptrend_ord[~mascara_fuera].copy()
    analisis['es_tratamiento'] = analisis['rsi2'] < umbral
    return analisis, episodios, primeros


def comprobar_sensibilidad_extremos(vals, nombre):
    vals = np.sort(vals)
    media_completa = vals.mean()
    if len(vals) >= 3:
        sin_extremos = vals[1:-1]  # quita el mejor y el peor episodio
        media_sin_extremos = sin_extremos.mean()
    else:
        media_sin_extremos = np.nan
    print(f"        sensibilidad: media con todos={media_completa*100:+.3f}%  "
          f"media quitando el mejor y el peor episodio={media_sin_extremos*100:+.3f}%  "
          f"(mejor={vals[-1]*100:+.3f}%, peor={vals[0]*100:+.3f}%)")


def analizar(nombre, path):
    print(f"\n\n################ COMPROBACION FINAL -- {nombre} (RSI(2)<{UMBRAL}, episodios) ################")
    df = cargar_m15(path)
    diario = agregar_diario(df)
    tabla = construir_tabla(diario)
    validas = tabla[tabla['valida']]
    uptrend = validas[validas['tendencia_alcista']].sort_values('dia')

    analisis, episodios, primeros = construir_conjunto_sin_continuaciones(uptrend, UMBRAL)
    n_episodios = len(episodios)
    n_señales_originales = sum(len(e) for e in episodios)
    print(f"  Episodios de sobreventa independientes (RSI(2)<{UMBRAL}): {n_episodios}  "
          f"(de {n_señales_originales} señales diarias originales -> se descartan "
          f"{n_señales_originales - n_episodios} dias de continuacion de la misma caida)")

    resultados_por_h = {}
    for h in HORIZONTES_VERIF:
        col = f'ret_{h}d'
        trat = analisis[analisis['es_tratamiento']][col].dropna()
        ctrl = analisis[~analisis['es_tratamiento']][col].dropna()
        lo, hi, n_rep = bootstrap_diferencia_bloques(analisis, col, 'es_tratamiento')
        efecto = trat.mean() - ctrl.mean()
        significativo = not (lo <= 0 <= hi) if not np.isnan(lo) else False
        print(f"\n  --- Horizonte +{h}d ---")
        print(f"    Tratamiento (1ª señal/episodio): n={len(trat)}  media={trat.mean()*100:+.3f}%  "
              f"mediana={trat.median()*100:+.3f}%")
        print(f"    Control (uptrend, RSI(2)>={UMBRAL}): n={len(ctrl)}  media={ctrl.mean()*100:+.3f}%  "
              f"mediana={ctrl.median()*100:+.3f}%")
        print(f"    Efecto (tratamiento-control) = {efecto*100:+.3f} pp   "
              f"IC95% diferencia (bloques conjuntos, {n_rep} rep.) = [{lo*100:+.3f} pp, {hi*100:+.3f} pp]  "
              f"{'-> EXCLUYE CERO' if significativo else '-> CRUZA CERO (no significativo)'}")
        comprobar_sensibilidad_extremos(trat.values, nombre)
        resultados_por_h[h] = dict(efecto=efecto, lo=lo, hi=hi, significativo=significativo, n=len(trat))

    print(f"\n  --- Por año (horizonte +5d) ---")
    analisis['anio'] = analisis['dia'].dt.year
    for anio, g in analisis.groupby('anio'):
        trat_a = g[g['es_tratamiento']]['ret_5d'].dropna()
        ctrl_a = g[~g['es_tratamiento']]['ret_5d'].dropna()
        aviso = '  [incompleto]' if anio in (2023, 2025) else ''
        if len(trat_a) == 0:
            print(f"    {anio}: sin episodios{aviso}")
            continue
        print(f"    {anio}: episodios={len(trat_a)}  media tratamiento={trat_a.mean()*100:+.3f}%  "
              f"media control={ctrl_a.mean()*100:+.3f}%{aviso}")

    return resultados_por_h


def main(rutas):
    resumen = {}
    for nombre, path in rutas.items():
        resumen[nombre] = analizar(nombre, path)

    print("\n\n################ RESUMEN FINAL (todas las combinaciones probadas) ################")
    for nombre, por_h in resumen.items():
        for h, r in por_h.items():
            estado = 'SIGNIFICATIVO' if r['significativo'] else 'no significativo'
            print(f"  {nombre} +{h}d: efecto={r['efecto']*100:+.3f}pp  n={r['n']}  {estado}")
    return resumen


if __name__ == '__main__':
    main({'USTEC': sys.argv[1], 'US500': sys.argv[2]})
