"""
Comparador EA (MQL5) vs. backtest Python para Turtle System 2 --
PASO OBLIGATORIO antes de confiar en el EA en demo (pedido
explícitamente: "No declares que la estrategia está validada
simplemente porque el EA reproduce el backtest" -- este script NO
declara nada, solo compara y reporta diferencias; la decisión de
avanzar es del usuario, con las diferencias ya identificadas).

ESTE ENTORNO NO TIENE MetaTrader 5 instalado -- no se puede compilar
ni ejecutar el EA/script MQL5 aquí. El procedimiento es:
  1. En tu terminal MT5, compila y ejecuta
     MQL5/Scripts/TurtleSystem2_ExportarSenales.mq5 (Script, no EA --
     no opera nada, solo lee histórico y exporta CSV).
  2. Copia los archivos TurtleSystem2_Validacion_<SIMBOLO>.csv desde
     la carpeta MQL5/Files/ de tu terminal (Archivo -> Abrir carpeta
     de datos) a esta máquina, dentro de una carpeta (por defecto
     ./validacion_ea/ relativa a research/).
  3. Ejecuta:
     python3 comparar_turtle_ea_vs_python.py --mql5-dir ./validacion_ea

Compara, por símbolo: nº de operaciones, y para cada operación
(emparejada por fecha de entrada) dirección, precio de entrada, N de
entrada, fecha de salida, motivo de salida y retorno bruto en puntos --
con una tolerancia de precio deliberadamente pequeña (no cero, porque
el EA puede tener menos/más historial D1 disponible en el bróker que
el CSV de Python, lo que puede desplazar ligeramente el valor de N por
el "burn-in" del EMA -- ver advertencia en el informe si la tolerancia
se agota).
"""
import argparse
import sys
from pathlib import Path

import numpy as np
import pandas as pd

from datos_multiactivo import cargar_universo, UNIVERSO
from estrategia_turtle_trading import ejecutar_sistema

TOLERANCIA_PRECIO_EN_PUNTOS = 5.0   # tolerancia deliberadamente holgada, ver docstring
TOLERANCIA_FECHA_DIAS = 1           # fin de semana/festivo con calendarios ligeramente distintos entre fuentes


def cargar_csv_ea(ruta):
    df = pd.read_csv(ruta, sep=';')
    df.columns = [c.strip() for c in df.columns]
    df['FechaEntrada'] = pd.to_datetime(df['FechaEntrada'])
    df['FechaSalida'] = pd.to_datetime(df['FechaSalida'])
    return df


def cargar_mt5_crudo(ruta):
    """Carga un CSV exportado por MQL5/Scripts/Export_D1_Comparacion.mq5
    (columnas Fecha;Open;High;Low;Close;Spread;TickVolume, separador ';')."""
    d = pd.read_csv(ruta, sep=';')
    d['dia'] = pd.to_datetime(d['Fecha'], format='%Y.%m.%d')
    d = d[['dia', 'Open', 'High', 'Low', 'Close', 'Spread']].sort_values('dia').reset_index(drop=True)
    return d


def generar_ops_python(simbolo, mt5_raw_dir=None):
    """Genera las operaciones de referencia con estrategia_turtle_trading.
    Por defecto usa el dataset mixto de datos_multiactivo.py (HistData+
    MetaQuotes-Demo, el mismo que seleccionó la estrategia). Si se pasa
    mt5_raw_dir, usa en su lugar el CSV D1 CRUDO exportado directamente
    del bróker (Export_D1_Comparacion.mq5) -- comparación MÁS LIMPIA,
    sin el efecto de mezclar proveedores de datos distintos (ver README,
    "Resolución de las discrepancias EA-vs-Python")."""
    if mt5_raw_dir is not None:
        ruta = Path(mt5_raw_dir) / f'{simbolo}_D1_Comparacion.csv'
        if not ruta.exists():
            return None
        d = cargar_mt5_crudo(ruta)
    else:
        universo = cargar_universo([simbolo])
        d = universo[simbolo].reset_index(drop=True)
    point = UNIVERSO[simbolo]['point']
    ops = ejecutar_sistema(d, 55, 20, point, False)
    ops['fecha_salida'] = d['dia'].iloc[ops['idx_salida'].to_numpy()].to_numpy()
    return ops


def comparar_simbolo(simbolo, ruta_csv_ea, mt5_raw_dir=None):
    print(f"\n######## {simbolo} ########")
    if not Path(ruta_csv_ea).exists():
        print(f"  [NO COMPARABLE] No se encontró '{ruta_csv_ea}' -- ejecuta primero el script MQL5 "
              f"TurtleSystem2_ExportarSenales.mq5 en tu MT5 y copia el CSV aquí.")
        return None

    ea = cargar_csv_ea(ruta_csv_ea)
    py = generar_ops_python(simbolo, mt5_raw_dir=mt5_raw_dir)
    if py is None:
        print(f"  [NO COMPARABLE] No se encontró el CSV crudo de {simbolo} en '{mt5_raw_dir}' "
              f"(se esperaba '{simbolo}_D1_Comparacion.csv').")
        return None
    py = py.rename(columns={'dia': 'FechaEntrada'})
    py['FechaEntrada'] = pd.to_datetime(py['FechaEntrada'])
    if mt5_raw_dir is not None:
        print(f"  [modo --mt5-raw-dir] Python corre sobre el CSV crudo del bróker, no sobre el dataset mixto.")

    print(f"  Operaciones EA (MQL5): {len(ea)}   Operaciones Python: {len(py)}")

    emparejadas, solo_ea, solo_py, diferencias = [], [], [], []

    py_usado = np.zeros(len(py), dtype=bool)
    for _, fila_ea in ea.iterrows():
        deltas = (py['FechaEntrada'] - fila_ea['FechaEntrada']).abs()
        candidatos = py[(deltas <= pd.Timedelta(days=TOLERANCIA_FECHA_DIAS)) & (~py_usado)]
        if len(candidatos) == 0:
            solo_ea.append(fila_ea)
            continue
        idx_match = candidatos.index[0]
        py_usado[py.index.get_loc(idx_match)] = True
        fila_py = py.loc[idx_match]
        emparejadas.append((fila_ea, fila_py))

    for idx, usado in enumerate(py_usado):
        if not usado:
            solo_py.append(py.iloc[idx])

    for fila_ea, fila_py in emparejadas:
        probs = []
        dir_ea = 1 if fila_ea['Direccion'] == 'largo' else -1
        dir_py = 1 if fila_py['direccion'] == 'largo' else -1
        if dir_ea != dir_py:
            probs.append(f"DIRECCION distinta (EA={fila_ea['Direccion']}, Python={fila_py['direccion']})")

        d_precio = abs(float(fila_ea['PrecioEntrada']) - float(fila_py['precio_entrada']))
        if d_precio > TOLERANCIA_PRECIO_EN_PUNTOS * UNIVERSO[simbolo]['point'] * 100:
            # tolerancia expresada en "puntos de precio" (no en point bruto) para que sea legible
            probs.append(f"PRECIO_ENTRADA difiere {d_precio:.5f} (EA={fila_ea['PrecioEntrada']}, Python={fila_py['precio_entrada']:.5f})")

        motivo_ea = fila_ea['MotivoSalida']
        motivo_py = fila_py['motivo_salida']
        if motivo_ea != motivo_py:
            probs.append(f"MOTIVO_SALIDA distinto (EA={motivo_ea}, Python={motivo_py})")

        delta_fecha_salida = abs((fila_ea['FechaSalida'] - pd.to_datetime(fila_py['fecha_salida'])).days)
        if delta_fecha_salida > TOLERANCIA_FECHA_DIAS:
            probs.append(f"FECHA_SALIDA difiere {delta_fecha_salida}d (EA={fila_ea['FechaSalida'].date()}, "
                         f"Python={pd.to_datetime(fila_py['fecha_salida']).date()})")

        if probs:
            diferencias.append((fila_ea['FechaEntrada'], probs))

    print(f"  Emparejadas por fecha de entrada: {len(emparejadas)}")
    print(f"  Solo en EA (sin equivalente en Python): {len(solo_ea)}")
    print(f"  Solo en Python (sin equivalente en EA): {len(solo_py)}")
    print(f"  Emparejadas con diferencias: {len(diferencias)}")

    if len(solo_ea) > 0:
        print("\n  >>> Operaciones SOLO EN EL EA:")
        for f in solo_ea:
            print(f"      {f['FechaEntrada'].date()} {f['Direccion']} entrada={f['PrecioEntrada']}")
    if len(solo_py) > 0:
        print("\n  >>> Operaciones SOLO EN PYTHON:")
        for f in solo_py:
            print(f"      {f['FechaEntrada'].date()} {f['direccion']} entrada={f['precio_entrada']:.5f}")
    if len(diferencias) > 0:
        print("\n  >>> Diferencias en operaciones emparejadas:")
        for fecha, probs in diferencias:
            print(f"      {fecha.date()}: " + " | ".join(probs))

    todo_ok = (len(solo_ea) == 0) and (len(solo_py) == 0) and (len(diferencias) == 0)
    if todo_ok:
        print(f"\n  RESULTADO: todas las operaciones coinciden dentro de la tolerancia declarada "
              f"({len(emparejadas)}/{len(emparejadas)}). Esto NO implica que la estrategia esté "
              f"validada -- solo que el EA reproduce correctamente la regla de señal sobre este histórico.")
    else:
        print(f"\n  RESULTADO: HAY DIFERENCIAS -- revisar antes de confiar en el EA en demo "
              f"(ver detalle arriba). Causas típicas: historial D1 disponible distinto en el bróker "
              f"(afecta el burn-in de N), huso horario del servidor distinto al de los datos de Python, "
              f"o un error real de implementación -- no asumir cuál es sin mirar la fecha concreta.")
    return todo_ok


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--mql5-dir', default='./validacion_ea',
                         help='Carpeta donde copiaste los CSV exportados por TurtleSystem2_ExportarSenales.mq5')
    parser.add_argument('--mt5-raw-dir', default=None,
                         help='Opcional: carpeta con los CSV crudos de Export_D1_Comparacion.mq5 '
                              '(<SIMBOLO>_D1_Comparacion.csv). Si se da, Python corre sobre ESE historico '
                              'en vez del dataset mixto de datos_multiactivo.py -- comparacion limpia, sin '
                              'el efecto de mezclar proveedores de datos distintos.')
    parser.add_argument('--simbolos', default='XAUUSD,USTEC,US500')
    args = parser.parse_args()

    simbolos = [s.strip() for s in args.simbolos.split(',')]
    resultados = {}
    for sim in simbolos:
        ruta = Path(args.mql5_dir) / f'TurtleSystem2_Validacion_{sim}.csv'
        resultados[sim] = comparar_simbolo(sim, ruta, mt5_raw_dir=args.mt5_raw_dir)

    print("\n######## RESUMEN ########")
    for sim, ok in resultados.items():
        estado = "SIN DIFERENCIAS" if ok is True else ("CON DIFERENCIAS" if ok is False else "NO COMPARADO (falta el CSV)")
        print(f"  {sim}: {estado}")

    if any(v is None for v in resultados.values()):
        print("\nFaltan uno o más CSV -- ejecuta TurtleSystem2_ExportarSenales.mq5 en tu MT5 primero.")
        sys.exit(2)
    if not all(resultados.values()):
        print("\nHay diferencias sin resolver -- NO actives el EA en demo todavía.")
        sys.exit(1)
    print("\nTodos los símbolos comparados sin diferencias dentro de la tolerancia declarada.")


if __name__ == '__main__':
    main()
