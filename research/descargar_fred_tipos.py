"""
Descarga tipos de interes de corto plazo oficiales de FRED (Federal
Reserve Economic Data, Banco de la Reserva Federal de San Luis) --
fuente gratuita, sin API key para la descarga CSV directa
(fred.stlouisfed.org/graph/fredgraph.csv?id=<SERIE>). Confirmado
accesible desde esta sesion.

Series elegidas (verificadas una a una: existen, cubren 2015-2026 sin
huecos grandes, frecuencia mensual salvo donde se indica diaria):
 - USD: IRSTCI01USM156N (tipo interbancario 3m, OCDE, mensual)
 - EUR: ECBDFR (tipo de deposito del BCE, DIARIO -- mas actual que la
   serie mensual de la OCDE, que se quedaba en 2026-01)
 - GBP: IRSTCI01GBM156N
 - JPY: IRSTCI01JPM156N
 - CAD: IRSTCI01CAM156N
 - CHF: IR3TIB01CHM156N (la serie OCDE generica se quedaba en 2024-03)
 - SEK: IR3TIB01SEM156N (la serie OCDE generica se quedaba en 2020-10)

Guarda research/datos_externos/tipos_interes.csv con una fila por mes
y una columna por divisa (ultimo valor del mes para ECBDFR, que es
diaria).
"""
from pathlib import Path

import pandas as pd
import requests

SALIDA = Path(__file__).parent / 'datos_externos' / 'tipos_interes.csv'

SERIES = {
    'USD': 'IRSTCI01USM156N',
    'EUR': 'ECBDFR',
    'GBP': 'IRSTCI01GBM156N',
    'JPY': 'IRSTCI01JPM156N',
    'CAD': 'IRSTCI01CAM156N',
    'CHF': 'IR3TIB01CHM156N',
    'SEK': 'IR3TIB01SEM156N',
}


def descargar_serie(serie_id):
    url = f"https://fred.stlouisfed.org/graph/fredgraph.csv?id={serie_id}"
    r = requests.get(url, timeout=30)
    r.raise_for_status()
    from io import StringIO
    df = pd.read_csv(StringIO(r.text))
    df.columns = ['fecha', 'valor']
    df['fecha'] = pd.to_datetime(df['fecha'])
    return df


def main():
    piezas = {}
    for divisa, serie_id in SERIES.items():
        print(f"Descargando {divisa} ({serie_id})...")
        df = descargar_serie(serie_id)
        df['anio_mes'] = df['fecha'].dt.to_period('M')
        mensual = df.groupby('anio_mes')['valor'].last()  # ultimo valor conocido del mes (causal)
        piezas[divisa] = mensual
        print(f"  {divisa}: {len(mensual)} meses, {mensual.index.min()} -> {mensual.index.max()}")

    tabla = pd.DataFrame(piezas).sort_index()
    tabla.index.name = 'anio_mes'
    SALIDA.parent.mkdir(parents=True, exist_ok=True)
    tabla.to_csv(SALIDA)
    print(f"\nGuardado {SALIDA}")
    print(tabla.tail(8))


if __name__ == '__main__':
    main()
