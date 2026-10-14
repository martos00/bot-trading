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
                print(f"        efecto (tratamiento - control) = {(r_t['media']-r_c['media'])*100:+.3f} pp")

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
