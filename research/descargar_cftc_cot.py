"""
Descarga y filtra los informes COT (Commitments of Traders) de la
CFTC -- fuente oficial, gratuita, sin necesidad de cuenta ni API key
(cftc.gov/files/dea/history/...). Confirmado accesible desde esta
sesion (a diferencia de Dukascopy/stooq.com, bloqueados).

Dos tipos de informe de la CFTC, cada uno con categorias de trader
distintas:
 - "Disaggregated" (fut_disagg_txt_<año>.zip): materias primas fisicas
   -- se usa para ORO (categoria "Managed Money" = especulativo).
 - "Traders in Financial Futures"/TFF (fut_fin_txt_<año>.zip): divisas
   e indices financieros -- se usa para EUR/GBP/JPY/CAD/CHF y los
   futuros de Nasdaq-100/S&P 500 (categoria "Leveraged Money" =
   especulativo, nomenclatura distinta a la de "Disaggregated").

LIMITACION DECLARADA: no existe futuro de Corona Sueca (SEK) en CME
con informe COT -- confirmado buscando en los nombres de mercado
disponibles, no se inventa un proxy. USDSEK queda fuera de cualquier
hipotesis basada en COT.

Guarda, por cada mercado, SOLO las columnas necesarias (fecha, interes
abierto, posicion larga/corta especulativa) en
research/datos_externos/cot_<MERCADO>.csv -- el crudo de la CFTC son
~20MB/año con cientos de mercados, aqui se reduce a unas pocas decenas
de KB por mercado relevante.
"""
import io
import zipfile
from pathlib import Path

import pandas as pd
import requests

SALIDA = Path(__file__).parent / 'datos_externos'

MERCADOS_DISAGG = {
    'XAUUSD': 'GOLD - COMMODITY EXCHANGE INC.',
}
MERCADOS_FIN = {
    'EURUSD': ['EURO FX - CHICAGO MERCANTILE EXCHANGE'],
    # CME renombro el contrato ~2022: "BRITISH POUND STERLING" (antes) -> "BRITISH POUND" (despues).
    # Se aceptan ambos nombres para tener el historico completo, no es un mercado distinto.
    'GBPUSD': ['BRITISH POUND - CHICAGO MERCANTILE EXCHANGE', 'BRITISH POUND STERLING - CHICAGO MERCANTILE EXCHANGE'],
    'USDJPY': ['JAPANESE YEN - CHICAGO MERCANTILE EXCHANGE'],
    'USDCAD': ['CANADIAN DOLLAR - CHICAGO MERCANTILE EXCHANGE'],
    'USDCHF': ['SWISS FRANC - CHICAGO MERCANTILE EXCHANGE'],
    'USTEC': ['NASDAQ-100 Consolidated - CHICAGO MERCANTILE EXCHANGE'],
    'US500': ['S&P 500 Consolidated - CHICAGO MERCANTILE EXCHANGE'],
}
AÑOS = range(2015, 2027)


def descargar_año(tipo, año):
    url = f"https://www.cftc.gov/files/dea/history/fut_{tipo}_txt_{año}.zip"
    r = requests.get(url, timeout=30)
    if r.status_code != 200 or len(r.content) < 1000:
        print(f"  [AVISO] {tipo} {año}: HTTP {r.status_code} o vacio -- se omite, no se inventa")
        return None
    with zipfile.ZipFile(io.BytesIO(r.content)) as z:
        nombre_txt = [n for n in z.namelist() if n.endswith('.txt')][0]
        with z.open(nombre_txt) as f:
            return pd.read_csv(f, low_memory=False)


def extraer_disagg(df, nombre_mercado):
    sub = df[df['Market_and_Exchange_Names'] == nombre_mercado].copy()
    if len(sub) == 0:
        return None
    sub['fecha'] = pd.to_datetime(sub['Report_Date_as_YYYY-MM-DD'])
    sub['neto_especulativo'] = sub['M_Money_Positions_Long_All'] - sub['M_Money_Positions_Short_All']
    sub['open_interest'] = sub['Open_Interest_All']
    return sub[['fecha', 'neto_especulativo', 'open_interest']].sort_values('fecha')


def extraer_fin(df, nombres_mercado):
    sub = df[df['Market_and_Exchange_Names'].isin(nombres_mercado)].copy()
    if len(sub) == 0:
        return None
    sub['fecha'] = pd.to_datetime(sub['Report_Date_as_YYYY-MM-DD'])
    sub['neto_especulativo'] = sub['Lev_Money_Positions_Long_All'] - sub['Lev_Money_Positions_Short_All']
    sub['open_interest'] = sub['Open_Interest_All']
    return sub[['fecha', 'neto_especulativo', 'open_interest']].sort_values('fecha')


def main():
    SALIDA.mkdir(parents=True, exist_ok=True)
    acumulado = {m: [] for m in list(MERCADOS_DISAGG) + list(MERCADOS_FIN)}

    for año in AÑOS:
        print(f"Descargando disaggregated {año}...")
        df_d = descargar_año('disagg', año)
        if df_d is not None:
            for mercado, nombre in MERCADOS_DISAGG.items():
                r = extraer_disagg(df_d, nombre)
                if r is not None:
                    acumulado[mercado].append(r)

        print(f"Descargando financial futures {año}...")
        df_f = descargar_año('fin', año)
        if df_f is not None:
            for mercado, nombre in MERCADOS_FIN.items():
                r = extraer_fin(df_f, nombre)
                if r is not None:
                    acumulado[mercado].append(r)

    for mercado, piezas in acumulado.items():
        if not piezas:
            print(f"{mercado}: SIN DATOS")
            continue
        todo = pd.concat(piezas, ignore_index=True).drop_duplicates('fecha').sort_values('fecha')
        salida = SALIDA / f'cot_{mercado}.csv'
        todo.to_csv(salida, index=False)
        print(f"{mercado}: {len(todo)} semanas, {todo['fecha'].min().date()} -> {todo['fecha'].max().date()} -> {salida}")


if __name__ == '__main__':
    main()
