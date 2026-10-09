"""
Verificacion de calidad de los 6 pares FX (componentes del DXY sintetico)
y reconstruccion causal del indice. NO genera señales, NO es un EA.

Formula DXY (fuente: coincide en Wikipedia, TradingView, Forex.com -- NO
es la documentacion propia de ICE, que no ha podido verificarse de forma
independiente; tratar como la mejor aproximacion publica disponible):

  DXY = 50.14348112
        * EURUSD^(-0.576) * USDJPY^(0.136) * GBPUSD^(-0.119)
        * USDCAD^(0.091)  * USDSEK^(0.042)  * USDCHF^(0.036)

Principio: el indice solo se calcula en los instantes donde los 6 pares
tienen una vela M15 real simultanea. Si falta uno solo, ese instante se
marca como NO calculable -- nunca se rellena con el valor anterior.
"""
import sys
from datetime import timedelta

import numpy as np
import pandas as pd

PARES = ['EURUSD', 'USDJPY', 'GBPUSD', 'USDCAD', 'USDCHF', 'USDSEK']
PESOS = {'EURUSD': -0.576, 'USDJPY': 0.136, 'GBPUSD': -0.119,
         'USDCAD': 0.091, 'USDSEK': 0.042, 'USDCHF': 0.036}
CONSTANTE_DXY = 50.14348112


def cargar_y_verificar(path, nombre):
    df = pd.read_csv(path, sep=';', parse_dates=['TimestampServidor'],
                      date_format='%Y.%m.%d %H:%M:%S')
    df = df.reset_index(drop=True)

    problemas = []
    if not df['TimestampServidor'].is_monotonic_increasing:
        problemas.append('timestamps no estrictamente crecientes')
    if df['TimestampServidor'].duplicated().sum() > 0:
        problemas.append(f"{df['TimestampServidor'].duplicated().sum()} timestamps duplicados")
    if not (df['High'] >= df[['Open', 'Close']].max(axis=1)).all():
        problemas.append('High < max(Open,Close) en alguna fila')
    if not (df['Low'] <= df[['Open', 'Close']].min(axis=1)).all():
        problemas.append('Low > min(Open,Close) en alguna fila')
    if not (df[['Open', 'High', 'Low', 'Close']] > 0).all().all():
        problemas.append('precio <= 0 en alguna fila')

    # velas de rango cero (posible feed congelado) -- especialmente relevante para USDSEK
    rango_cero = (df['High'] == df['Low']).sum()

    # rachas de OHLC idéntico consecutivo (fuerte indicio de feed congelado, no solo baja vol)
    identico = (df['Open'] == df['Close']) & (df['High'] == df['Low']) & (df['Open'] == df['High'])
    racha_max = 0
    racha_actual = 0
    for v in identico:
        racha_actual = racha_actual + 1 if v else 0
        racha_max = max(racha_max, racha_actual)

    print(f"\n=== {nombre} ===")
    print(f"Filas: {len(df)}  Rango: {df['TimestampServidor'].iloc[0]} -> {df['TimestampServidor'].iloc[-1]}")
    if problemas:
        print(f"  PROBLEMAS DE INTEGRIDAD: {problemas}")
    else:
        print("  [OK] Integridad basica (duplicados/orden/OHLC/precios) correcta")
    print(f"  Velas de rango cero (High==Low): {rango_cero} ({rango_cero/len(df)*100:.2f}%)")
    print(f"  Racha maxima de OHLC idéntico consecutivo (posible feed congelado): {racha_max} velas")
    if racha_max >= 8:  # >= 2h seguidas sin variacion de precio
        print("  AVISO: racha larga de OHLC idéntico -- verificar manualmente si el feed estaba "
              "realmente congelado en ese tramo, no asumir que es solo 'mercado muy tranquilo'.")

    return df


def clasificar_huecos(df):
    diffs = df['TimestampServidor'].diff()
    cat = pd.Series('intrasesion', index=df.index)
    for i in df.index[diffs > timedelta(minutes=15)]:
        dur = diffs.iloc[i]
        cat.iloc[i] = 'cierre_diario' if dur <= timedelta(hours=2) else \
                      ('fin_de_semana' if dur <= timedelta(hours=60) else 'festivo_extendido')
    return cat


def main(ruta_oro, rutas_pares, ruta_tick_sync=None):
    print("############ VERIFICACION DE CALIDAD: 6 PARES FX + XAUUSD ############")

    datos = {}
    datos['XAUUSD'] = cargar_y_verificar(ruta_oro, 'XAUUSD (referencia ya verificada)')
    for par in PARES:
        if par in rutas_pares:
            datos[par] = cargar_y_verificar(rutas_pares[par], par)

    print("\n\n### Huecos por simbolo (clasificados, igual criterio que XAUUSD) ###")
    gaps_por_simbolo = {}
    for nombre, df in datos.items():
        cat = clasificar_huecos(df)
        gaps_por_simbolo[nombre] = cat
        print(f"  {nombre}: {cat.value_counts().to_dict()}")

    print("\n\n### Cobertura cruzada: ¿coinciden los timestamps entre los 6 pares y el oro? ###")
    sets_tiempo = {n: set(d['TimestampServidor']) for n, d in datos.items()}
    universo = set.union(*sets_tiempo.values())
    tabla_cobertura = {n: len(s) / len(universo) * 100 for n, s in sets_tiempo.items()}
    for n, pct in sorted(tabla_cobertura.items(), key=lambda x: x[1]):
        print(f"  {n}: {pct:.2f}% del universo combinado de timestamps")

    if 'USDSEK' in datos:
        comunes_sin_sek = set.intersection(*[sets_tiempo[p] for p in PARES if p != 'USDSEK'])
        comunes_con_sek = comunes_sin_sek & sets_tiempo['USDSEK']
        perdido_por_sek = len(comunes_sin_sek) - len(comunes_con_sek)
        print(f"\n  Timestamps donde los otros 5 pares coinciden: {len(comunes_sin_sek)}")
        print(f"  De esos, cuantos pierde USDSEK (no tiene vela): {perdido_por_sek} "
              f"({perdido_por_sek/max(len(comunes_sin_sek),1)*100:.2f}%)")

    # --- Reconstruccion causal del DXY: solo en timestamps con los 6 pares presentes ---
    print("\n\n### Reconstruccion del DXY sintetico (solo donde los 6 pares coinciden) ###")
    pares_presentes = [p for p in PARES if p in datos]
    if len(pares_presentes) < 6:
        faltan = set(PARES) - set(pares_presentes)
        print(f"  NO SE PUEDE RECONSTRUIR: faltan ficheros de {faltan}")
        return

    comun = set.intersection(*[sets_tiempo[p] for p in PARES])
    print(f"  Timestamps con los 6 pares simultaneamente disponibles: {len(comun)} "
          f"de {len(universo)} del universo combinado ({len(comun)/len(universo)*100:.2f}%)")

    tablas = {p: datos[p].set_index('TimestampServidor')['Close'] for p in PARES}
    df_comun = pd.DataFrame({p: tablas[p] for p in PARES}).loc[sorted(comun)]
    assert df_comun.notna().all().all(), "ERROR GRAVE: NaN tras el intersect -- no deberia pasar"

    log_dxy = np.log(CONSTANTE_DXY)
    for p, w in PESOS.items():
        log_dxy = log_dxy + w * np.log(df_comun[p])
    dxy = np.exp(log_dxy)

    print(f"  DXY reconstruido: n={len(dxy)}  media={dxy.mean():.3f}  "
          f"min={dxy.min():.3f}  max={dxy.max():.3f}  std={dxy.std():.3f}")
    print(f"  Primeros valores:\n{dxy.head()}")
    print(f"  Ultimos valores:\n{dxy.tail()}")
    print(f"  Cobertura por año:")
    print(dxy.groupby(dxy.index.year).count())

    print("\n  PENDIENTE (no se hace aqui): contrastar estos valores contra una referencia DXY "
          "independiente (serie publica real) antes de confiar en la reconstruccion. Sin esa "
          "verificacion, esto es solo una reconstruccion causal internamente consistente, no un "
          "DXY validado.")

    if ruta_tick_sync:
        print("\n\n### Muestra de sincronizacion a nivel de tick ###")
        ts = pd.read_csv(ruta_tick_sync, sep=';')
        sin_datos = ts[ts['SinDatos'] != '']
        print(f"  Ventanas totales: {len(ts)}  Sin ticks disponibles: {len(sin_datos)} "
              f"({len(sin_datos)/len(ts)*100:.1f}%)")
        print("  Sin ticks disponibles, por simbolo:")
        print(sin_datos['Simbolo'].value_counts())
        con_datos = ts[ts['SinDatos'] == ''].copy()
        if len(con_datos):
            con_datos['NumTicks'] = pd.to_numeric(con_datos['NumTicks'])
            con_datos['GapMaxSeg'] = pd.to_numeric(con_datos['GapMaxSeg'])
            print("\n  Densidad de ticks por simbolo (media de NumTicks por ventana de muestra):")
            print(con_datos.groupby('Simbolo')['NumTicks'].mean().sort_values())
            print("\n  Gap maximo entre ticks consecutivos por simbolo (media, segundos):")
            print(con_datos.groupby('Simbolo')['GapMaxSeg'].mean().sort_values(ascending=False))


if __name__ == '__main__':
    # Uso: python3 dxy_verificacion_calidad.py <oro.csv> <EURUSD.csv> <USDJPY.csv> <GBPUSD.csv> \
    #        <USDCAD.csv> <USDCHF.csv> <USDSEK.csv> [tick_sync.csv]
    args = sys.argv[1:]
    ruta_oro = args[0]
    rutas_pares = {PARES[i]: args[1 + i] for i in range(6)}
    ruta_tick_sync = args[7] if len(args) > 7 else None
    main(ruta_oro, rutas_pares, ruta_tick_sync)
