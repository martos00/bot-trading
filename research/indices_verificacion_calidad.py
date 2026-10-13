"""
Verificacion de calidad del historial M15 de los indices candidatos
(US500, USTEC). Mismo criterio que XAUUSD y los 6 pares FX. NO genera
señales, NO es un EA.
"""
import sys
from datetime import timedelta

import numpy as np
import pandas as pd


def cargar_y_verificar(path, nombre):
    df = pd.read_csv(path, sep=';', parse_dates=['TimestampServidor'],
                      date_format='%Y.%m.%d %H:%M:%S')
    df = df.reset_index(drop=True)

    problemas = []
    if not df['TimestampServidor'].is_monotonic_increasing:
        problemas.append('timestamps no estrictamente crecientes')
    dup = df['TimestampServidor'].duplicated().sum()
    if dup > 0:
        problemas.append(f'{dup} timestamps duplicados')
    if not (df['High'] >= df[['Open', 'Close']].max(axis=1)).all():
        problemas.append('High < max(Open,Close) en alguna fila')
    if not (df['Low'] <= df[['Open', 'Close']].min(axis=1)).all():
        problemas.append('Low > min(Open,Close) en alguna fila')
    if not (df[['Open', 'High', 'Low', 'Close']] > 0).all().all():
        problemas.append('precio <= 0 en alguna fila')

    rango_cero = (df['High'] == df['Low']).sum()
    identico = (df['Open'] == df['Close']) & (df['High'] == df['Low']) & (df['Open'] == df['High'])
    racha_max, racha_actual = 0, 0
    for v in identico:
        racha_actual = racha_actual + 1 if v else 0
        racha_max = max(racha_max, racha_actual)

    print(f"\n=== {nombre} ===")
    print(f"Filas: {len(df)}  Rango: {df['TimestampServidor'].iloc[0]} -> {df['TimestampServidor'].iloc[-1]}")
    print("  [OK] Integridad basica correcta" if not problemas else f"  PROBLEMAS: {problemas}")
    print(f"  Velas de rango cero (High==Low): {rango_cero} ({rango_cero/len(df)*100:.2f}%)")
    print(f"  Racha maxima OHLC idéntico consecutivo: {racha_max} velas")
    print(f"  Spread: media={df['Spread'].mean():.2f}  min={df['Spread'].min()}  max={df['Spread'].max()}  "
          f"valores unicos={df['Spread'].nunique()}")
    print(f"  TickVolume: media={df['TickVolume'].mean():.1f}  velas con TickVolume==0: "
          f"{(df['TickVolume']==0).sum()}")
    return df


def clasificar_huecos(df):
    diffs = df['TimestampServidor'].diff()
    cat = pd.Series('intrasesion', index=df.index)
    for i in df.index[diffs > timedelta(minutes=15)]:
        dur = diffs.iloc[i]
        cat.iloc[i] = 'cierre_diario' if dur <= timedelta(hours=2) else \
                      ('fin_de_semana' if dur <= timedelta(hours=60) else 'festivo_extendido')
    return cat


def main(rutas):
    datos = {}
    for nombre, path in rutas.items():
        datos[nombre] = cargar_y_verificar(path, nombre)

    print("\n\n### Huecos por simbolo ###")
    for nombre, df in datos.items():
        cat = clasificar_huecos(df)
        print(f"  {nombre}: {cat.value_counts().to_dict()}")
        huecos_df = df.loc[cat != 'intrasesion'].copy()
        huecos_df['categoria'] = cat[cat != 'intrasesion']
        # Distribucion de la hora de INICIO de cada hueco (vela previa), util para ver el
        # patron horario de cierre de este instrumento concreto -- no asumir que coincide con oro/FX
        prev_idx = huecos_df.index - 1
        horas_inicio = df['TimestampServidor'].iloc[prev_idx].dt.strftime('%H:%M').value_counts().head(5)
        print(f"    Horas de inicio de hueco mas frecuentes: {horas_inicio.to_dict()}")

    print("\n\n### Cobertura cruzada entre los 2 indices ###")
    sets_tiempo = {n: set(d['TimestampServidor']) for n, d in datos.items()}
    universo = set.union(*sets_tiempo.values())
    comun = set.intersection(*sets_tiempo.values())
    print(f"  Universo combinado: {len(universo)}  Comun a ambos: {len(comun)} "
          f"({len(comun)/len(universo)*100:.2f}%)")
    for n, s in sets_tiempo.items():
        print(f"  {n}: {len(s)/len(universo)*100:.2f}% del universo")

    print("\n\n### Cobertura por año ###")
    for n, d in datos.items():
        print(f"  {n}:")
        print(d['TimestampServidor'].dt.year.value_counts().sort_index())


if __name__ == '__main__':
    main({'US500': sys.argv[1], 'USTEC': sys.argv[2]})
