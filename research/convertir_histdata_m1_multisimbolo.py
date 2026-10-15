"""
Version generalizada de convertir_histdata_m1_a_m15.py (usado para
XAUUSD 2015-2022) para los 6 pares Forex nuevos, EN UN SOLO PASO --
no hace falta organizar los ficheros por carpeta ni procesarlos uno a
uno: el script BUSCA RECURSIVAMENTE todos los "DAT_MT_<SIMBOLO>_M1_<AÑO>.csv"
dentro de la carpeta que se le indique (tal cual quedan tras
descomprimir los .zip de histdata.com, en cualquier subcarpeta), los
agrupa por simbolo, construye velas M15 en Bid (igual convencion que
el resto del proyecto) y escribe UN CSV por simbolo con TODOS los años
encontrados ya concatenados, listo para research/datos_multiactivo.py.

INSTALACION PREVIA (una sola vez, en tu ordenador):
    pip install pandas

DESCARGA (en histdata.com/download-free-forex-historical-data/?/metatrader/1-minute-bar-quotes):
    Simbolos necesarios: EURUSD, GBPUSD, USDJPY, USDCAD, USDCHF, USDSEK
    Años: 2015, 2016, 2017, 2018, 2019, 2020, 2021, 2022 (8 descargas
    por simbolo = 48 .zip en total -- mismo rango que ya se hizo para
    XAUUSD, para tener un universo de 9 activos con la MISMA ventana
    2015-2026 completa).
    Formato: "MetaTrader 4/5 Historical M1 Bar Data" (Generic ASCII,
    el mismo que ya usamos para XAUUSD -- NO hace falta elegir Bid/Ask,
    el paquete M1 gratuito ya es Bid).

USO (una vez descargados y descomprimidos TODOS los .zip en una misma
carpeta, sin importar si quedan en subcarpetas):
    python3 convertir_histdata_m1_multisimbolo.py carpeta_con_todos_los_csv carpeta_salida

Esto escribe, en carpeta_salida/, un fichero por simbolo:
    EURUSD_M15_histdata_2015_2022.csv
    GBPUSD_M15_histdata_2015_2022.csv
    ... etc (los que encuentre -- si falta algun año/simbolo, se avisa
    y se continua con el resto, no se detiene ni se inventa el hueco).

Sube aqui esos 6 ficheros (o la carpeta_salida completa) y se integran
en research/datos_multiactivo.py sin tocar nada mas del motor.
"""
import re
import sys
from pathlib import Path

import pandas as pd

CABECERA = ['TimestampServidor', 'Open', 'High', 'Low', 'Close', 'TickVolume', 'Spread', 'RealVolume']
PATRON_FICHERO = re.compile(r'^DAT_MT_([A-Z]{6})_M1_(\d{4})\.csv$')


def localizar_ficheros(carpeta_raiz):
    """Busca recursivamente, agrupa por simbolo -> lista de (año, path) ordenada."""
    por_simbolo = {}
    for path in Path(carpeta_raiz).rglob('DAT_MT_*_M1_*.csv'):
        m = PATRON_FICHERO.match(path.name)
        if not m:
            continue
        simbolo, anio = m.group(1), int(m.group(2))
        por_simbolo.setdefault(simbolo, []).append((anio, path))
    for simbolo in por_simbolo:
        por_simbolo[simbolo].sort(key=lambda t: t[0])
    return por_simbolo


def velas_m15_desde_m1(path_csv):
    m1 = pd.read_csv(path_csv, header=None, names=['Fecha', 'Hora', 'Open', 'High', 'Low', 'Close', 'Volumen'])
    m1['TimestampEST'] = pd.to_datetime(m1['Fecha'] + ' ' + m1['Hora'], format='%Y.%m.%d %H:%M')
    m1 = m1.sort_values('TimestampEST').reset_index(drop=True)
    bucket = m1['TimestampEST'].dt.floor('15min')
    g = m1.groupby(bucket)
    m15 = g.agg(Open=('Open', 'first'), High=('High', 'max'), Low=('Low', 'min'),
                Close=('Close', 'last'), TickVolume=('Open', 'size')).reset_index()
    m15 = m15.rename(columns={'TimestampEST': 'TimestampServidor'})
    m15['Spread'] = pd.NA
    m15['RealVolume'] = 0
    return m15[CABECERA]


def procesar_simbolo(simbolo, años_y_paths, carpeta_salida):
    piezas = []
    print(f"\n{simbolo}:")
    for anio, path in años_y_paths:
        m15 = velas_m15_desde_m1(path)
        print(f"  {anio}: {len(m15)} velas M15 (desde {path.name})")
        piezas.append(m15)
    todo = pd.concat(piezas, ignore_index=True).sort_values('TimestampServidor').reset_index(drop=True)
    dup = todo['TimestampServidor'].duplicated().sum()
    if dup > 0:
        print(f"  [AVISO] {dup} timestamps duplicados -- se eliminan quedandose con el primero.")
        todo = todo.drop_duplicates(subset='TimestampServidor', keep='first')
    assert todo['TimestampServidor'].is_monotonic_increasing

    anio_ini, anio_fin = años_y_paths[0][0], años_y_paths[-1][0]
    salida = Path(carpeta_salida) / f"{simbolo}_M15_histdata_{anio_ini}_{anio_fin}.csv"
    todo.to_csv(salida, sep=';', index=False, date_format='%Y.%m.%d %H:%M:%S')
    print(f"  -> {salida} ({len(todo)} velas, {todo['TimestampServidor'].min()} .. {todo['TimestampServidor'].max()})")


def main(carpeta_raiz, carpeta_salida):
    Path(carpeta_salida).mkdir(parents=True, exist_ok=True)
    por_simbolo = localizar_ficheros(carpeta_raiz)
    if not por_simbolo:
        print(f"No se encontro ningun DAT_MT_<SIMBOLO>_M1_<AÑO>.csv dentro de {carpeta_raiz} (¿descomprimiste los .zip?)")
        return
    print(f"Simbolos encontrados: {sorted(por_simbolo.keys())}")
    for simbolo, años_y_paths in sorted(por_simbolo.items()):
        procesar_simbolo(simbolo, años_y_paths, carpeta_salida)
    print(f"\nListo. Sube aqui los ficheros de {carpeta_salida}/ (uno por simbolo) para integrarlos.")


if __name__ == '__main__':
    if len(sys.argv) != 3:
        print("Uso: python3 convertir_histdata_m1_multisimbolo.py carpeta_con_csvs_descomprimidos carpeta_salida")
        sys.exit(1)
    main(sys.argv[1], sys.argv[2])
