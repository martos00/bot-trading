"""
FASE 1 -- Identificar la ventaja (NO construir estrategia todavia).

Hipotesis: en indices bursatiles en tendencia alcista (Close diario >
SMA200 diaria), una condicion de sobreventa de corto plazo (RSI(2) bajo)
va seguida de una recuperacion de precio estadisticamente mayor que la
de dias equivalentes SIN sobreventa, dentro de la MISMA tendencia.
Inspirado en el enfoque RSI(2)+SMA200 (Connors / difundido por Rubén
Martínez). Aqui solo se mide la existencia de la ventaja -- sin TP, SL
ni filtros de entrada/salida todavia.

PRE-REGISTRO (fijado antes de ejecutar, no se elige nada tras ver
resultados):
 - Barra: DIARIA, agregada desde M15 por fecha de calendario del
   SERVIDOR (Open=primera vela del dia, High/Low=max/min del dia,
   Close=ultima vela del dia) -- es la convencion D1 que veria un
   discrecional en el grafico diario de su propio broker. No se intenta
   reconstruir el cierre NY 16:00 ET (esa complejidad de reconstruccion
   horaria no aplica aqui, es un estudio de velas diarias, no intradia).
 - Tendencia: Close_diario[t] > SMA200_diario[t] (medido en la misma
   vela que genera la señal, causal).
 - RSI(2): formula de Wilder (suavizado exponencial alpha=1/2), igual
   convencion que el RSI estandar de MT5.
 - Sobreventa: TRES umbrales fijos, los tres se reportan siempre --
   RSI(2) < 5, < 10, < 15 (umbrales clasicos de la literatura Connors,
   no elegidos tras ver resultados).
 - Horizontes futuros: 1, 3, 5, 10 dias habiles (velas diarias)
   adelante -- los cuatro se reportan siempre.
 - Retorno futuro (sin lookahead): desde el Open del dia SIGUIENTE a la
   señal (primer punto de entrada realmente alcanzable) hasta el Close
   del dia h despues de la señal: ret_h = Close[t+h] / Open[t+1] - 1.
 - Grupo TRATAMIENTO: dias en tendencia alcista con RSI(2)<umbral.
 - Grupo CONTROL (mismo regimen de tendencia): dias en tendencia
   alcista con RSI(2)>=umbral -- para no confundir la deriva media del
   propio uptrend con informacion incremental del RSI(2). Se reporta
   tambien la media incondicional de TODOS los dias en tendencia alcista
   como referencia adicional.
 - Incertidumbre: bootstrap de bloques de 10 señales consecutivas (igual
   convencion que Hipotesis A/B de este proyecto), 2.000 repeticiones,
   para la media de retorno de cada grupo.
 - El periodo 2023-2026 ya se ha usado repetidamente en este proyecto
   para desarrollo -- este resultado se trata como investigacion
   exploratoria, NO como validacion independiente (ver README).
"""
import sys

import numpy as np
import pandas as pd

UMBRALES_RSI = [5, 10, 15]
HORIZONTES = [1, 3, 5, 10]
PERIODO_SMA = 200
PERIODO_RSI = 2
BLOQUE_BOOTSTRAP = 10
REPETICIONES_BOOTSTRAP = 2000
SEED = 20261014


def cargar_m15(path):
    df = pd.read_csv(path, sep=';', parse_dates=['TimestampServidor'],
                      date_format='%Y.%m.%d %H:%M:%S')
    assert df['TimestampServidor'].is_monotonic_increasing
    assert df['TimestampServidor'].duplicated().sum() == 0
    return df


def agregar_diario(df):
    d = df.copy()
    d['dia'] = d['TimestampServidor'].dt.normalize()
    diario = d.groupby('dia').agg(Open=('Open', 'first'), High=('High', 'max'),
                                   Low=('Low', 'min'), Close=('Close', 'last')).reset_index()
    return diario


def rsi_wilder(close, periodo):
    delta = close.diff()
    ganancia = delta.clip(lower=0.0)
    perdida = -delta.clip(upper=0.0)
    avg_gain = ganancia.ewm(alpha=1.0 / periodo, adjust=False).mean()
    avg_loss = perdida.ewm(alpha=1.0 / periodo, adjust=False).mean()
    rs = avg_gain / avg_loss
    return 100.0 - 100.0 / (1.0 + rs)


def bootstrap_bloques_ic(valores, bloque=BLOQUE_BOOTSTRAP, repeticiones=REPETICIONES_BOOTSTRAP, seed=SEED):
    valores = np.asarray(valores, dtype=float)
    valores = valores[~np.isnan(valores)]
    n = len(valores)
    if n < bloque * 2:
        return (np.nan, np.nan)
    rng = np.random.default_rng(seed)
    n_bloques = int(np.ceil(n / bloque))
    max_inicio = n - bloque
    medias = np.empty(repeticiones)
    for b in range(repeticiones):
        inicios = rng.integers(0, max_inicio + 1, size=n_bloques)
        medias[b] = np.concatenate([valores[s:s + bloque] for s in inicios])[:n].mean()
    return np.percentile(medias, 2.5), np.percentile(medias, 97.5)


def construir_tabla(diario):
    d = diario.copy()
    d['sma200'] = d['Close'].rolling(PERIODO_SMA).mean()
    d['rsi2'] = rsi_wilder(d['Close'], PERIODO_RSI)
    d['tendencia_alcista'] = d['Close'] > d['sma200']
    d['anio'] = d['dia'].dt.year

    for h in HORIZONTES:
        # ret_h = Close[t+h] / Open[t+1] - 1 -- entrada en el Open del dia
        # siguiente a la señal (primer punto realmente alcanzable, sin
        # lookahead), salida al Close h dias despues de la señal.
        open_t1 = d['Open'].shift(-1)
        close_th = d['Close'].shift(-h)
        d[f'ret_{h}d'] = close_th / open_t1 - 1.0

    # validas: SMA200 ya formada (warm-up) y existe suficiente futuro para el horizonte mas largo
    d['valida'] = d['sma200'].notna() & d[f'ret_{max(HORIZONTES)}d'].notna()
    return d


def resumen_grupo(nombre, sub, h):
    col = f'ret_{h}d'
    vals = sub[col].dropna().values
    n = len(vals)
    if n == 0:
        print(f"      {nombre:28s} n=0")
        return None
    media = vals.mean()
    mediana = np.median(vals)
    lo, hi = bootstrap_bloques_ic(vals)
    print(f"      {nombre:28s} n={n:4d}  media={media*100:+.3f}%  mediana={mediana*100:+.3f}%  "
          f"IC95% boot=[{lo*100:+.3f}%, {hi*100:+.3f}%]")
    return dict(n=n, media=media, mediana=mediana, ic_lo=lo, ic_hi=hi)


def bootstrap_diferencia_bloques(uptrend_ordenado, col_ret, es_tratamiento, bloque=BLOQUE_BOOTSTRAP,
                                  repeticiones=REPETICIONES_BOOTSTRAP, seed=SEED):
    """CORRECCION (verificacion punto 2): la version anterior bootstrapeaba
    tratamiento y control por SEPARADO (bloques de cada grupo tomados de
    dias distintos del calendario) y luego restaba los puntos estimados --
    eso NO es el IC de la diferencia, es solo ver si dos ICs separados se
    solapan. Aqui se resamplea en bloques de dias CONSECUTIVOS de la
    MISMA secuencia cronologica de dias en tendencia alcista (preservando
    que tratamiento y control estan entrelazados en el tiempo), y en cada
    repeticion se recalculan ambas medias con la etiqueta que le tocase a
    cada dia y se guarda la diferencia -- asi se obtiene el IC de la
    diferencia misma, no la comparacion de dos ICs independientes."""
    ret = uptrend_ordenado[col_ret].to_numpy(dtype=float)
    es_trat = uptrend_ordenado[es_tratamiento].to_numpy(dtype=bool)
    valido = ~np.isnan(ret)
    ret, es_trat = ret[valido], es_trat[valido]
    n = len(ret)
    if n < bloque * 2:
        return (np.nan, np.nan, 0)
    rng = np.random.default_rng(seed)
    n_bloques = int(np.ceil(n / bloque))
    max_inicio = n - bloque
    diffs = []
    for _ in range(repeticiones):
        inicios = rng.integers(0, max_inicio + 1, size=n_bloques)
        idx = np.concatenate([np.arange(s, s + bloque) for s in inicios])[:n]
        ret_b, trat_b = ret[idx], es_trat[idx]
        if trat_b.sum() == 0 or (~trat_b).sum() == 0:
            continue  # repeticion sin uno de los dos grupos -- se descarta, no se fuerza
        diffs.append(ret_b[trat_b].mean() - ret_b[~trat_b].mean())
    if not diffs:
        return (np.nan, np.nan, 0)
    diffs = np.array(diffs)
    return np.percentile(diffs, 2.5), np.percentile(diffs, 97.5), len(diffs)


def detectar_episodios(uptrend_ordenado, umbral):
    """CORRECCION (verificacion punto 3): cuenta cuantos EPISODIOS de caida
    distintos hay detras de las señales de un umbral, agrupando como un
    mismo episodio los dias de señal consecutivos (indice de dia habil
    consecutivo, sin huecos) -- para saber si el n reportado son eventos
    realmente independientes o la misma caida contada varias veces."""
    idx_señal = uptrend_ordenado.index[uptrend_ordenado['rsi2'] < umbral].to_numpy()
    if len(idx_señal) == 0:
        return [], []
    rupturas = np.where(np.diff(idx_señal) > 1)[0]
    limites = [0] + list(rupturas + 1) + [len(idx_señal)]
    episodios = [idx_señal[limites[i]:limites[i + 1]] for i in range(len(limites) - 1)]
    primer_dia_episodio = [ep[0] for ep in episodios]
    return episodios, primer_dia_episodio


def analizar_instrumento(nombre, path):
    print(f"\n\n################ FASE 1 -- {nombre} ################")
    df = cargar_m15(path)
    diario = agregar_diario(df)
    print(f"  {len(diario)} velas diarias agregadas, {diario['dia'].iloc[0].date()} -> {diario['dia'].iloc[-1].date()}")

    tabla = construir_tabla(diario)
    validas = tabla[tabla['valida']]
    uptrend = validas[validas['tendencia_alcista']]
    print(f"  Dias validos (SMA200 formada + horizonte disponible): {len(validas)}  "
          f"de los cuales en tendencia alcista: {len(uptrend)} ({len(uptrend)/len(validas)*100:.1f}%)")

    for h in HORIZONTES:
        print(f"\n  --- Horizonte +{h}d ---")
        print(f"    Referencia: TODOS los dias en tendencia alcista (deriva media del uptrend, sin filtrar por RSI)")
        resumen_grupo('uptrend (incondicional)', uptrend, h)

        for umbral in UMBRALES_RSI:
            tratamiento = uptrend[uptrend['rsi2'] < umbral]
            control = uptrend[uptrend['rsi2'] >= umbral]
            print(f"    Umbral RSI(2) < {umbral}:")
            r_t = resumen_grupo(f'tratamiento (RSI2<{umbral})', tratamiento, h)
            r_c = resumen_grupo(f'control (RSI2>={umbral}, mismo uptrend)', control, h)
            if r_t and r_c:
                efecto = r_t['media'] - r_c['media']
                uptrend_ord = uptrend.sort_values('dia').copy()
                uptrend_ord['es_tratamiento'] = uptrend_ord['rsi2'] < umbral
                lo_d, hi_d, n_rep = bootstrap_diferencia_bloques(uptrend_ord, f'ret_{h}d', 'es_tratamiento')
                print(f"        efecto (tratamiento - control) = {efecto*100:+.3f} pp  "
                      f"IC95% de la DIFERENCIA (bloques conjuntos, {n_rep} repeticiones validas)="
                      f"[{lo_d*100:+.3f} pp, {hi_d*100:+.3f} pp]")

    print("\n  --- Verificacion (punto 3): episodios distintos vs. señales repetidas en la misma caida ---")
    for umbral in UMBRALES_RSI:
        # OJO: se usa el indice ORIGINAL de la secuencia diaria completa
        # (sin resetear), no el de este subconjunto filtrado -- es lo que
        # permite detectar "dias de bolsa consecutivos" de verdad (el
        # indice de 'diario' ya no tiene huecos de fin de semana porque
        # solo contiene dias con datos reales).
        uptrend_ord = uptrend.sort_values('dia')
        episodios, primeros = detectar_episodios(uptrend_ord, umbral)
        n_señales = sum(len(e) for e in episodios)
        if not episodios:
            print(f"    RSI(2)<{umbral}: sin señales")
            continue
        vals_todas = uptrend_ord.loc[uptrend_ord['rsi2'] < umbral, 'ret_5d'].dropna()
        vals_primer_dia = uptrend_ord.loc[primeros, 'ret_5d'].dropna()
        print(f"    RSI(2)<{umbral}: {n_señales} señales repartidas en {len(episodios)} episodios distintos "
              f"(media {n_señales/len(episodios):.1f} señales/episodio)")
        print(f"      +5d usando TODAS las señales: n={len(vals_todas)} media={vals_todas.mean()*100:+.3f}%")
        print(f"      +5d usando solo el PRIMER dia de cada episodio: n={len(vals_primer_dia)} "
              f"media={vals_primer_dia.mean()*100:+.3f}%")

    print("\n  --- Persistencia por año (umbral RSI(2)<10, horizonte +5d, el mas citado en la literatura) ---")
    for anio, g in uptrend.groupby('anio'):
        tratamiento_anio = g[g['rsi2'] < 10]
        control_anio = g[g['rsi2'] >= 10]
        vals_t = tratamiento_anio['ret_5d'].dropna().values
        vals_c = control_anio['ret_5d'].dropna().values
        aviso = '  [incompleto]' if anio in (2023, 2025) else ''
        if len(vals_t) == 0:
            print(f"    {anio}: sin señales de tratamiento{aviso}")
            continue
        print(f"    {anio}: tratamiento n={len(vals_t)} media={vals_t.mean()*100:+.3f}%  "
              f"control n={len(vals_c)} media={vals_c.mean()*100:+.3f}% (si hay){aviso}")

    return tabla


def main(rutas):
    resultados = {}
    for nombre, path in rutas.items():
        resultados[nombre] = analizar_instrumento(nombre, path)
    return resultados


if __name__ == '__main__':
    main({'USTEC': sys.argv[1], 'US500': sys.argv[2]})
