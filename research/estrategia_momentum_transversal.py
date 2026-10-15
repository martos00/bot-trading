"""
Momentum transversal (cross-sectional), siguiendo Jegadeesh & Titman
(1993, Journal of Finance) sobre el universo de 9 activos disponible.
Segunda estrategia de la fase "Opcion B" (ver README).

DIFERENCIA DE MECANISMO frente a TSMOM (ya probada, resultado debil):
TSMOM apuesta por el SIGNO absoluto de cada activo por separado,
escalado por su propia volatilidad; el momentum transversal es
RELATIVO -- ordena los 9 activos por su retorno pasado y apuesta LARGO
en los mejores, CORTO en los peores, dólar-neutral (sin escalado de
volatilidad, igual que el diseño original del estudio, que ordena por
retorno bruto, no por retorno ajustado a riesgo).

REGLAS (unica version por horizonte, pre-registradas, sin optimizar):
 - En cada fin de mes: ordenar los 9 activos por su retorno LOGARITMICO
   de los ultimos LOOKBACK_DIAS dias (21/63/252 -- los tres siempre).
 - LARGO en los 3 de mejor retorno relativo, CORTO en los 3 peores
   (tercios aproximados con 9 activos), dólar-neutral: +1/3 en cada
   largo, -1/3 en cada corto (suma +1 todos los largos, -1 todos los
   cortos).
 - Se mantiene 1 mes (hasta el siguiente rebalanceo). Coste: spread
   real/Close al rebalancear cada pata.
 - Control: mismo mecanismo pero con el RANKING aleatorizado cada mes
   (mismo numero de activos largos/cortos) -- aisla si el ORDEN por
   momentum aporta algo frente a elegir 3 largos/3 cortos al azar cada
   mes.

LIMITACION DECLARADA: con solo 9 activos (6 de ellos cruces del USD,
por tanto NO independientes entre si) la dispersion transversal real
es mucho menor que en el estudio original (cientos de acciones). Esto
se declara ANTES de ver resultados, no se usa para justificar un
resultado negativo a posteriori.
"""
import numpy as np
import pandas as pd

from datos_multiactivo import cargar_universo, UNIVERSO
from estrategia_tsmom import LOOKBACKS_DIAS, preparar_activo, fin_de_mes

N_LARGOS = 3
N_CORTOS = 3
SEED = 20261015
REPETICIONES_CONTROL = 1000


def construir_tabla_retornos(universo_preparado, lookback_dias):
    """Para cada activo, serie mensual: mes, retorno_lookback (señal),
    retorno_mes_siguiente (bruto), coste_frac (al rebalancear ese mes)."""
    filas = []
    for nombre, d in universo_preparado.items():
        point = UNIVERSO[nombre]['point']
        idx_fin_mes = fin_de_mes(d)
        for pos, idx in enumerate(idx_fin_mes[:-1]):
            idx_prev = idx - lookback_dias
            if idx_prev < 0:
                continue
            ret_lookback = np.log(d['Close'].iloc[idx] / d['Close'].iloc[idx_prev])
            idx_sig = idx_fin_mes[pos + 1]
            ret_mes_siguiente = d['Close'].iloc[idx_sig] / d['Close'].iloc[idx] - 1.0
            spread_precio = d['Spread'].iloc[idx] * point if pd.notna(d['Spread'].iloc[idx]) else 0.0
            coste_frac = spread_precio / d['Close'].iloc[idx]
            filas.append(dict(activo=nombre, mes=d['anio_mes'].iloc[idx_sig], anio=d['dia'].iloc[idx_sig].year,
                               ret_lookback=ret_lookback, ret_mes_siguiente=ret_mes_siguiente, coste_frac=coste_frac))
    return pd.DataFrame(filas)


def construir_cartera(tabla, rng=None, aleatorizar_ranking=False):
    carteras = []
    for mes, g in tabla.groupby('mes'):
        if len(g) < N_LARGOS + N_CORTOS:
            continue
        if aleatorizar_ranking:
            orden = rng.permutation(g.index.to_numpy())
            largos_idx, cortos_idx = orden[:N_LARGOS], orden[-N_CORTOS:]
        else:
            g_ordenado = g.sort_values('ret_lookback', ascending=False)
            largos_idx = g_ordenado.index[:N_LARGOS]
            cortos_idx = g_ordenado.index[-N_CORTOS:]
        ret_largos = g.loc[largos_idx, 'ret_mes_siguiente'].mean() - g.loc[largos_idx, 'coste_frac'].mean()
        ret_cortos = -g.loc[cortos_idx, 'ret_mes_siguiente'].mean() - g.loc[cortos_idx, 'coste_frac'].mean()
        ret_cartera = (ret_largos + ret_cortos) / 2  # 50% capital en cada pata, dolar-neutral
        anio = g['anio'].iloc[0]
        carteras.append(dict(mes=mes, anio=anio, ret_neto_mes=ret_cartera))
    return pd.DataFrame(carteras).sort_values('mes').reset_index(drop=True)


def metricas_cartera(cartera):
    from estrategia_tsmom import metricas_cartera as _m
    return _m(cartera)


def main(lookback_nombre='12m'):
    lookback_dias = LOOKBACKS_DIAS[lookback_nombre]
    universo = cargar_universo()
    universo_preparado = {n: preparar_activo(d, UNIVERSO[n]['point']) for n, d in universo.items()}
    tabla = construir_tabla_retornos(universo_preparado, lookback_dias)

    cartera = construir_cartera(tabla)
    m = metricas_cartera(cartera)
    print(f"\n######## Momentum transversal lookback={lookback_nombre} ({lookback_dias} dias) ########")
    print(f"Meses evaluables: {m['n_meses']}")
    if m['n_meses'] == 0:
        print("  SIN DATOS SUFICIENTES.")
        return
    print(f"  Retorno acumulado neto: {m['ret_acumulado']*100:+.1f}%  Retorno anualizado: {m['ret_anualizado']*100:+.2f}%")
    print(f"  Volatilidad anualizada: {m['vol_anualizada']*100:.2f}%  Sharpe: {m['sharpe']:.3f}")
    print(f"  Max drawdown: {m['max_drawdown']*100:.2f}%  %Meses positivos: {m['pct_meses_positivos']:.1f}%")
    for anio, g in cartera.groupby('anio'):
        mg = metricas_cartera(g)
        print(f"    {anio}: n={mg['n_meses']}  Ret. acumulado año={mg['ret_acumulado']*100:+.2f}%  Sharpe={mg['sharpe']:.3f}")

    rng = np.random.default_rng(SEED)
    medias_control = np.array([construir_cartera(tabla, rng, aleatorizar_ranking=True)['ret_neto_mes'].mean()
                                for _ in range(REPETICIONES_CONTROL)])
    media_real = cartera['ret_neto_mes'].mean()
    z = (media_real - medias_control.mean()) / medias_control.std() if medias_control.std() > 0 else np.nan
    print(f"\n  Control ranking aleatorio ({REPETICIONES_CONTROL} rep.): media real={media_real*100:+.4f}%/mes  "
          f"media aleatoria={medias_control.mean()*100:+.4f}%/mes  z={z:+.2f}")
    return cartera


if __name__ == '__main__':
    for lb in LOOKBACKS_DIAS:
        main(lb)
