"""
Convierte el historico XAUUSD M1 gratuito de HistData.com (2015-2022,
descargado por el usuario desde histdata.com/download-free-forex-data,
formato "Generic ASCII" para MetaTrader) al formato M15 exacto que usa
este proyecto (TimestampServidor;Open;High;Low;Close;TickVolume;Spread;
RealVolume), para poder ejecutar la validacion independiente de
Volatility Expansion Continuation (research/validacion_independiente_volexp.py)
SIN TOCAR ninguna linea de esa logica ni de la estrategia congelada
(research/estrategia_volatilidad_expansion.py).

FUENTE DE DATOS Y LIMITACIONES, verificadas en histdata.com/f-a-q/ antes
de usar este fichero (no asumidas de memoria):
 - Zona horaria: "Eastern Standard Time (EST) WITHOUT Day Light Savings
   adjustments" -- es decir GMT-5 fijo los 365 dias del año. Esto es
   DISTINTO de la hora de servidor EET/EEST de MetaQuotes-Demo usada en
   el resto del proyecto (2023-2026) y tambien distinto del UTC de
   Dukascopy. Aqui se agrega por "dia de calendario EST", no se convierte
   a otra zona horaria (una conversion horaria casera podria introducir
   su propio error) -- se declara la diferencia, no se corrige.
 - Precio: OHLC = precio BID (confirmado en la misma pagina: "the bar
   prices: Open, High, Low, Close in the data files are based on the
   tick Bid price") -- MISMA convencion que el resto del proyecto
   (MetaQuotes-Demo OHLC tambien es Bid), asi que aqui no hay diferencia
   metodologica.
 - Spread/Ask: el paquete M1 gratuito NO incluye precio Ask ni spread
   (columna Volumen = 0 siempre, no es tick volume real). A diferencia
   de Dukascopy (ticks Ask+Bid), aqui NO se puede calcular un spread
   real -- la columna Spread de salida se deja vacia (NaN) y el motor de
   validacion ya interpreta Spread NaN como coste de spread = 0 en la
   entrada (ver estrategia_gap_fade.agregar_diario_con_spread /
   validacion_independiente_volexp.ejecutar_congelada_realista). Esto se
   declara explicitamente: con este dataset el escenario "0 estres" NO
   es "solo spread real" (como en 2023-2026 con spread MT5 real), es
   "CERO coste" -- un limite optimista, no una estimacion de coste real.
   Los escenarios de estres en dolares (ver validacion_histdata_2015_2022.py)
   son la unica referencia de coste disponible para este tramo.
 - TickVolume de salida = NUMERO DE VELAS M1 agregadas en cada vela M15
   (0-15), NO es tick volume real (ese dato no esta en el fichero
   gratuito) -- se declara como proxy de actividad, no como cifra real.
 - Huecos: HistData publica un informe .txt propio por año listando los
   huecos >60s detectados en su construccion de M1 (ver
   DAT_MT_XAUUSD_M1_AAAA.txt junto a cada CSV) -- son huecos de segundos
   dentro de ticks de baja liquidez, no dias completos perdidos. Este
   script ademas verifica de forma independiente, por año, cuantos dias
   de calendario con actividad de mercado esperada NO tienen ninguna
   vela (ver verificar_cobertura()), sin asumir que la ausencia de error
   del proveedor implica cobertura completa.

USO:
    python3 convertir_histdata_m1_a_m15.py carpeta_con_csvs_m1 salida.csv 2015 2022
"""
import sys
from pathlib import Path

import pandas as pd

CABECERA = ['TimestampServidor', 'Open', 'High', 'Low', 'Close', 'TickVolume', 'Spread', 'RealVolume']


def cargar_m1_anio(path_csv):
    df = pd.read_csv(path_csv, header=None,
                      names=['Fecha', 'Hora', 'Open', 'High', 'Low', 'Close', 'Volumen'])
    df['TimestampEST'] = pd.to_datetime(df['Fecha'] + ' ' + df['Hora'], format='%Y.%m.%d %H:%M')
    return df[['TimestampEST', 'Open', 'High', 'Low', 'Close']]


def construir_m15(m1):
    m1 = m1.sort_values('TimestampEST').reset_index(drop=True)
    bucket = m1['TimestampEST'].dt.floor('15min')
    g = m1.groupby(bucket)
    m15 = g.agg(Open=('Open', 'first'), High=('High', 'max'),
                Low=('Low', 'min'), Close=('Close', 'last'), TickVolume=('Open', 'size')).reset_index()
    m15 = m15.rename(columns={'TimestampEST': 'TimestampServidor'})
    m15['Spread'] = pd.NA
    m15['RealVolume'] = 0
    return m15[CABECERA]


def verificar_cobertura(m15, anio):
    dias_con_datos = pd.Series(m15['TimestampServidor']).dt.normalize().unique()
    dias_con_datos = pd.to_datetime(dias_con_datos)
    rango_completo = pd.date_range(f'{anio}-01-01', f'{anio}-12-31', freq='D')
    # XAUUSD opera ~23/5h: cierra la tarde del viernes (hora EST) y no vuelve
    # a abrir hasta la tarde/noche del domingo -- se descartan sabados y la
    # mayor parte de los domingos del recuento de "dias esperados" (no se
    # afina la hora exacta de reapertura, solo se evita contar sabados
    # completos como hueco real).
    dias_esperados = rango_completo[rango_completo.dayofweek < 5]  # lunes-viernes
    faltantes = sorted(set(dias_esperados) - set(dias_con_datos))
    return dict(dias_con_datos=len(dias_con_datos), dias_esperados_lunes_viernes=len(dias_esperados),
                faltantes_lunes_viernes=faltantes)


def main(carpeta, salida, anio_inicio, anio_fin):
    carpeta = Path(carpeta)
    piezas = []
    print("Cobertura por año (verificada contra dias lunes-viernes del calendario, EST sin DST):")
    for anio in range(anio_inicio, anio_fin + 1):
        path_csv = carpeta / f"DAT_MT_XAUUSD_M1_{anio}.csv"
        if not path_csv.exists():
            print(f"  {anio}: FICHERO NO ENCONTRADO ({path_csv}) -- omitido, no se inventa.")
            continue
        m1 = cargar_m1_anio(path_csv)
        m15 = construir_m15(m1)
        cobertura = verificar_cobertura(m15, anio)
        n_falt = len(cobertura['faltantes_lunes_viernes'])
        primero = m15['TimestampServidor'].min()
        ultimo = m15['TimestampServidor'].max()
        print(f"  {anio}: {len(m15)} velas M15, {cobertura['dias_con_datos']}/"
              f"{cobertura['dias_esperados_lunes_viernes']} dias lunes-viernes con datos "
              f"({n_falt} sin ninguna vela), rango [{primero} .. {ultimo}]")
        if n_falt > 0 and n_falt <= 15:
            print(f"    dias lunes-viernes sin ninguna vela: {[d.date().isoformat() for d in cobertura['faltantes_lunes_viernes']]}")
        elif n_falt > 15:
            print(f"    (lista larga, primeros 10): {[d.date().isoformat() for d in cobertura['faltantes_lunes_viernes'][:10]]}")
        piezas.append(m15)

    todo = pd.concat(piezas, ignore_index=True).sort_values('TimestampServidor').reset_index(drop=True)
    dup = todo['TimestampServidor'].duplicated().sum()
    if dup > 0:
        print(f"\n[AVISO] {dup} timestamps M15 duplicados tras concatenar -- se eliminan quedandose con el primero.")
        todo = todo.drop_duplicates(subset='TimestampServidor', keep='first')
    assert todo['TimestampServidor'].is_monotonic_increasing

    todo.to_csv(salida, sep=';', index=False, date_format='%Y.%m.%d %H:%M:%S')
    print(f"\nGuardado {salida}: {len(todo)} velas M15, {todo['TimestampServidor'].min()} .. {todo['TimestampServidor'].max()}")


if __name__ == '__main__':
    if len(sys.argv) != 5:
        print("Uso: python3 convertir_histdata_m1_a_m15.py carpeta_csvs_m1 salida.csv anio_inicio anio_fin")
        sys.exit(1)
    main(sys.argv[1], sys.argv[2], int(sys.argv[3]), int(sys.argv[4]))
