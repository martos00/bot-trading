"""
Comprobacion pedida por el usuario tras revisar momentum transversal:
"No descartes una estrategia unicamente porque tenga una exposicion
persistente a determinados activos... compara la estrategia original
congelada contra una cartera ESTATICA equivalente... no optimices los
pesos para que parezca mejor NI peor."

REFERENCIA OBJETIVA (definida AHORA, antes de calcular ningun
resultado, para no poder ajustarla despues de verla):
 - Misma estructura de piernas que momentum transversal: 3 activos en
   la pierna larga, los activos restantes en la corta, mismo
   escalado de volatilidad (vol-targeting 10% anualizado, igual
   mecanismo que TSMOM/momentum transversal), mismo split 50/50 de
   capital entre piernas, mismo coste de spread real al rebalancear
   cada mes.
 - Pierna larga ESTATICA (nunca cambia): XAUUSD, US500, USTEC --
   exactamente los 3 activos que de hecho ocuparon la pierna larga de
   momentum transversal el 85-97% de los meses (ver README) -- esto NO
   es casualidad ni ajuste a posteriori, es la pieza concreta que el
   usuario pide aislar: "¿la rotacion aporta algo sobre ESTAR
   permanentemente en esta combinacion concreta?".
 - Pierna corta ESTATICA: los 6 pares Forex, equiponderados por riesgo
   TODOS (no se elige un subconjunto de 3 -- elegir cualquier
   subconjunto introduciria una decision arbitraria que el usuario
   pide evitar; usar los 6 es la opcion menos discrecional).
 - Se evalua para los 3 lookbacks ya usados en momentum transversal
   (1m/3m/12m) -- el foco especial esta en 12m, que fue el resultado
   que parecia prometedor (Sharpe 1,175, z=+2,93 frente al azar).

COMPARACION: se calcula la serie de retorno EXCEDENTE (momentum menos
estatica) mes a mes -- la pregunta correcta no es "¿bate momentum a la
estatica en Sharpe bruto?" sino "¿el excedente de rotar es
significativamente distinto de cero?", con bootstrap de bloques (3
meses, 2000 repeticiones) sobre esa serie pareada.
"""
import numpy as np
import pandas as pd

from datos_multiactivo import cargar_universo, UNIVERSO
from estrategia_tsmom import LOOKBACKS_DIAS, preparar_activo, fin_de_mes, VOL_OBJETIVO, LIMITE_POSICION, metricas_cartera
from estrategia_momentum_transversal import construir_tabla_retornos, construir_cartera

ACTIVOS_LARGOS_ESTATICOS = ['XAUUSD', 'US500', 'USTEC']
ACTIVOS_CORTOS_ESTATICOS = ['EURUSD', 'GBPUSD', 'USDJPY', 'USDCAD', 'USDCHF', 'USDSEK']
BLOQUE_BOOTSTRAP = 3
REPETICIONES_BOOTSTRAP = 2000
SEED = 20261015


def construir_señales_estaticas(universo_preparado):
    """Mismo mecanismo de vol-targeting que TSMOM, pero con signo FIJO
    (no depende de ningun retorno pasado) -- cartera que nunca rota."""
    señales_por_activo = {}
    for nombre, d in universo_preparado.items():
        point = UNIVERSO[nombre]['point']
        if nombre in ACTIVOS_LARGOS_ESTATICOS:
            signo_fijo = 1
        elif nombre in ACTIVOS_CORTOS_ESTATICOS:
            signo_fijo = -1
        else:
            continue
        idx_fin_mes = fin_de_mes(d)
        filas = []
        for pos, idx in enumerate(idx_fin_mes[:-1]):
            vol = d['vol_60d_anualizada'].iloc[idx]
            if pd.isna(vol) or vol <= 0:
                continue
            tamano = np.clip(signo_fijo * (VOL_OBJETIVO / vol), -LIMITE_POSICION, LIMITE_POSICION)
            idx_fin_siguiente = idx_fin_mes[pos + 1]
            ret_mes_siguiente = d['Close'].iloc[idx_fin_siguiente] / d['Close'].iloc[idx] - 1.0
            spread_precio = d['Spread'].iloc[idx] * point if pd.notna(d['Spread'].iloc[idx]) else 0.0
            coste_frac = (spread_precio / d['Close'].iloc[idx]) * abs(tamano)
            filas.append(dict(mes=d['anio_mes'].iloc[idx_fin_siguiente], anio=d['dia'].iloc[idx_fin_siguiente].year,
                               tamano_posicion=tamano, ret_bruto_mes=tamano * ret_mes_siguiente,
                               coste_frac=coste_frac, ret_neto_mes=tamano * ret_mes_siguiente - coste_frac))
        señales_por_activo[nombre] = pd.DataFrame(filas)
    return señales_por_activo


def cartera_estatica_mensual(señales_por_activo):
    todas = pd.concat([df.assign(activo=nombre) for nombre, df in señales_por_activo.items() if len(df) > 0],
                       ignore_index=True)
    # 50% capital en cada pierna: media dentro de la pierna, luego promedio de las 2 piernas
    filas = []
    for mes, g in todas.groupby('mes'):
        largos = g[g['activo'].isin(ACTIVOS_LARGOS_ESTATICOS)]
        cortos = g[g['activo'].isin(ACTIVOS_CORTOS_ESTATICOS)]
        if len(largos) == 0 or len(cortos) == 0:
            continue
        ret_pierna_larga = largos['ret_neto_mes'].mean()
        ret_pierna_corta = cortos['ret_neto_mes'].mean()
        ret_cartera = (ret_pierna_larga + ret_pierna_corta) / 2
        filas.append(dict(mes=mes, anio=g['anio'].iloc[0], ret_neto_mes=ret_cartera))
    return pd.DataFrame(filas).sort_values('mes').reset_index(drop=True)


def bootstrap_bloques_media(valores, bloque=BLOQUE_BOOTSTRAP, repeticiones=REPETICIONES_BOOTSTRAP, seed=SEED):
    valores = np.asarray(valores, dtype=float)
    n = len(valores)
    if n < bloque * 2:
        return np.nan, np.nan, np.nan
    rng = np.random.default_rng(seed)
    n_bloques = int(np.ceil(n / bloque))
    max_inicio = n - bloque
    medias = np.empty(repeticiones)
    for b in range(repeticiones):
        inicios = rng.integers(0, max_inicio + 1, size=n_bloques)
        medias[b] = np.concatenate([valores[s:s + bloque] for s in inicios])[:n].mean()
    lo, hi = np.percentile(medias, [2.5, 97.5])
    return medias.mean(), lo, hi


def main(lookback_nombre='12m'):
    lookback_dias = LOOKBACKS_DIAS[lookback_nombre]
    universo = cargar_universo()
    universo_preparado = {n: preparar_activo(d, UNIVERSO[n]['point']) for n, d in universo.items()}

    # Momentum transversal (ya probado, se recalcula aqui para alinear meses exactamente)
    from estrategia_momentum_transversal import construir_tabla_retornos
    tabla = construir_tabla_retornos(universo_preparado, lookback_dias)
    cartera_momentum = construir_cartera(tabla)

    señales_estaticas = construir_señales_estaticas(universo_preparado)
    cartera_estatica = cartera_estatica_mensual(señales_estaticas)

    pareado = pd.merge(cartera_momentum, cartera_estatica, on='mes', suffixes=('_momentum', '_estatica'))
    m_mom = metricas_cartera(pareado.rename(columns={'ret_neto_mes_momentum': 'ret_neto_mes'}))
    m_est = metricas_cartera(pareado.rename(columns={'ret_neto_mes_estatica': 'ret_neto_mes'}))

    print(f"\n######## Momentum transversal vs. cartera ESTATICA equivalente -- lookback={lookback_nombre} ########")
    print(f"Meses pareados (misma ventana para ambas): {len(pareado)}")
    print(f"  MOMENTUM : Sharpe={m_mom['sharpe']:.3f}  Ret.anualizado={m_mom['ret_anualizado']*100:+.2f}%  "
          f"Vol.anualizada={m_mom['vol_anualizada']*100:.2f}%  MaxDD={m_mom['max_drawdown']*100:.2f}%")
    print(f"  ESTATICA : Sharpe={m_est['sharpe']:.3f}  Ret.anualizado={m_est['ret_anualizado']*100:+.2f}%  "
          f"Vol.anualizada={m_est['vol_anualizada']*100:.2f}%  MaxDD={m_est['max_drawdown']*100:.2f}%")

    excedente = pareado['ret_neto_mes_momentum'] - pareado['ret_neto_mes_estatica']
    media_exc, lo, hi = bootstrap_bloques_media(excedente.to_numpy())
    significativo = not (lo <= 0 <= hi)
    print(f"\n  Excedente mensual (momentum - estatica): media={media_exc*100:+.4f}%  "
          f"IC95% bootstrap bloques=[{lo*100:+.4f}%, {hi*100:+.4f}%]"
          f"{'  <-- excluye cero' if significativo else '  (incluye cero, NO significativo)'}")
    for anio, g in pareado.groupby(pareado['mes'].apply(lambda p: p.year)):
        exc_año = (g['ret_neto_mes_momentum'] - g['ret_neto_mes_estatica']).sum()
        print(f"    {anio}: excedente acumulado año = {exc_año*100:+.2f}%  (n={len(g)})")


if __name__ == '__main__':
    for lb in LOOKBACKS_DIAS:
        main(lb)
