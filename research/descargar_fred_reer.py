"""
Descarga el Real Broad Effective Exchange Rate (REER, base BIS,
redistribuido via FRED con el mismo endpoint ya usado para tipos de
interés/VIX/DGS10/WTI -- fredgraph.csv, sin API key) de EEUU y de las
6 contrapartes de nuestro universo Forex (EUR/GBP/JPY/CAD/CHF/SEK).

USO: insumo para la estrategia de "valor FX" (PPP/REER, Menkhoff-
Sarno-Schmeling-Schrimpf 2017, Review of Financial Studies) --
ver research/estrategia_fx_valor_reer.py.

Cada serie verificada individualmente (igual disciplina que
descargar_fred_tipos.py): frecuencia mensual, cobertura desde 1994,
mismo proveedor BIS para los 7 países/áreas -- comparable entre sí sin
mezclar metodologías.
"""
import time
import urllib.request

SERIES = {
    'US': 'RBUSBIS', 'EUR': 'RBXMBIS', 'GBP': 'RBGBBIS', 'JPY': 'RBJPBIS',
    'CAD': 'RBCABIS', 'CHF': 'RBCHBIS', 'SEK': 'RBSEBIS',
}

RUTA_SALIDA = 'datos_externos/reer_bis.csv'


def descargar_serie(id_serie):
    url = f'https://fred.stlouisfed.org/graph/fredgraph.csv?id={id_serie}'
    with urllib.request.urlopen(url, timeout=30) as resp:
        return resp.read().decode('utf-8')


def main():
    import pandas as pd
    from io import StringIO

    series = {}
    for moneda, id_serie in SERIES.items():
        print(f"Descargando {moneda} ({id_serie})...")
        texto = descargar_serie(id_serie)
        df = pd.read_csv(StringIO(texto))
        df.columns = ['fecha', moneda]
        df['fecha'] = pd.to_datetime(df['fecha'])
        df[moneda] = pd.to_numeric(df[moneda], errors='coerce')
        series[moneda] = df.set_index('fecha')[moneda]
        print(f"  {moneda}: {series[moneda].dropna().index.min().date()} -> "
              f"{series[moneda].dropna().index.max().date()}, {series[moneda].dropna().shape[0]} meses")
        time.sleep(0.5)

    tabla = pd.DataFrame(series)
    tabla.to_csv(RUTA_SALIDA)
    print(f"\nGuardado en {RUTA_SALIDA}: {tabla.shape[0]} filas, columnas={list(tabla.columns)}")


if __name__ == '__main__':
    main()
