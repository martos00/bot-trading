"""
Dual Momentum GEM (Global Equities Momentum) -- Gary Antonacci,
*Dual Momentum Investing* (2014), formalizado 2012. Segunda
estrategia de la fase de metodos documentados de traders/gestores
sistematicos reales.

1. ESTRATEGIA ORIGINAL: cada fin de mes, comparar el retorno TOTAL a
   12 meses de renta variable EEUU vs. renta variable internacional
   (ex-EEUU); quedarse con el que tenga mejor retorno (momentum
   RELATIVO). Si ese retorno no supera el de la liquidez/letras del
   tesoro (momentum ABSOLUTO), pasar a bonos en vez de renta variable.
   Antonacci usa S&P500, MSCI ACWI ex-US y Bloomberg Barclays US
   Aggregate Bond como proxies, con backtest propio 1974-2013
   (ampliado despues a 1950-2018 por el propio autor).

2. REGLAS AUTOMATIZADAS: señal mensual causal (cierre del mes
   anterior), momentum a 12 meses, mantiene 1 mes, sin stop-loss
   (el "stop" es el propio rebalanceo mensual que puede cambiar de
   activo).

3. SUSTITUCIONES Y SU EFECTO ESPERADO (declaradas, NO una
   reproduccion exacta del universo de Antonacci):
   - "EEUU": SP500 de FRED (precio, NO total return -- falta el
     dividendo, ~1,5-2%/año, podria SUBESTIMAR ligeramente su
     momentum absoluto frente al original). FRED solo cubre desde
     2016 (no 1974) -- limitacion de muestra declarada.
   - "Internacional ex-EEUU": NIKKEI225 (Japon, un SOLO pais) en vez
     de la cesta MSCI ACWI ex-US (decenas de paises desarrollados+
     emergentes). Esto es una simplificacion MATERIAL: concentra el
     riesgo "internacional" en Japon especificamente, cuyo
     comportamiento historico (décadas perdidas, política monetaria
     extrema) no es representativo de la cesta diversificada
     original -- se declara explicitamente, no se presenta como
     equivalente.
   - "Liquidez": tipo de interes de EEUU de corto plazo (FRED,
     IRSTCI01USM156N, ya usado en Carry Trade).
   - "Bonos": BONO_US10Y sintetico (ya construido y declarado en la
     fase de cartera diversificada) en vez del Bloomberg Barclays US
     Aggregate (que incluye credito, no solo Tesoro).
   Efecto esperado de estas sustituciones: el resultado AQUI es una
   prueba de la LOGICA de Dual Momentum sobre proxies disponibles, NO
   una replica de las cifras publicadas por Antonacci -- no se debe
   comparar directamente con su resultado 1974-2018.

4. INFORMACION PERDIDA POR OHLC: ninguna adicional relevante (todo el
   calculo es sobre Close mensual).

EVIDENCIA DEL TRACK RECORD: el backtest de Antonacci es SIMULADO,
publicado por el propio creador de la estrategia (no es un fondo
auditado de forma independiente) -- se declara como tal, no como
"rentabilidad verificada".
"""
import numpy as np
import pandas as pd

RUTA_SP500 = 'datos_externos/sp500_fred.csv'
RUTA_NIKKEI = 'datos_externos/nikkei225.csv'
RUTA_TIPOS = 'datos_externos/tipos_interes.csv'
LOOKBACK_MESES = 12


def cargar_serie_mensual(ruta, col_valor):
    s = pd.read_csv(ruta)
    s.columns = ['dia', col_valor]
    s['dia'] = pd.to_datetime(s['dia'])
    s[col_valor] = pd.to_numeric(s[col_valor], errors='coerce')
    s = s.dropna().sort_values('dia').reset_index(drop=True)
    s['anio_mes'] = s['dia'].dt.to_period('M')
    mensual = s.groupby('anio_mes')[col_valor].last()
    return mensual


def cargar_bono_sintetico_mensual():
    from cartera_diversificada import cargar_bono_sintetico
    b = cargar_bono_sintetico()
    b['anio_mes'] = b['dia'].dt.to_period('M')
    return b.groupby('anio_mes')['Close'].last()


def main():
    us = cargar_serie_mensual(RUTA_SP500, 'us')
    jp = cargar_serie_mensual(RUTA_NIKKEI, 'jp')
    tipos = pd.read_csv(RUTA_TIPOS)
    tipos['anio_mes'] = pd.PeriodIndex(tipos['anio_mes'], freq='M')
    cash = tipos.set_index('anio_mes')['USD'] / 100.0  # anualizado, decimal
    bono = cargar_bono_sintetico_mensual()

    df = pd.DataFrame({'us': us, 'jp': jp, 'bono': bono}).dropna()
    df['cash_anual'] = cash.reindex(df.index)
    df = df.dropna()
    print(f"Meses con los 4 datos disponibles: {len(df)} ({df.index.min()} -> {df.index.max()})")

    df['ret_us_12m'] = df['us'] / df['us'].shift(LOOKBACK_MESES) - 1.0
    df['ret_jp_12m'] = df['jp'] / df['jp'].shift(LOOKBACK_MESES) - 1.0
    df['cash_ret_12m'] = (1 + df['cash_anual'].shift(LOOKBACK_MESES)) ** (LOOKBACK_MESES / 12) - 1.0

    df['ret_us_mes'] = df['us'] / df['us'].shift(1) - 1.0
    df['ret_jp_mes'] = df['jp'] / df['jp'].shift(1) - 1.0
    df['ret_bono_mes'] = df['bono'] / df['bono'].shift(1) - 1.0

    filas = []
    for i in range(LOOKBACK_MESES + 1, len(df) - 1):
        ret_us_12m, ret_jp_12m, cash_12m = df['ret_us_12m'].iloc[i], df['ret_jp_12m'].iloc[i], df['cash_ret_12m'].iloc[i]
        if pd.isna(ret_us_12m) or pd.isna(ret_jp_12m) or pd.isna(cash_12m):
            continue
        ganador = 'us' if ret_us_12m >= ret_jp_12m else 'jp'
        momentum_absoluto_ok = (ret_us_12m if ganador == 'us' else ret_jp_12m) > cash_12m
        activo = ganador if momentum_absoluto_ok else 'bono'

        mes_siguiente = df.index[i + 1]
        ret_mes_siguiente = dict(us=df['ret_us_mes'].iloc[i + 1], jp=df['ret_jp_mes'].iloc[i + 1],
                                  bono=df['ret_bono_mes'].iloc[i + 1])[activo]
        filas.append(dict(mes=mes_siguiente, anio=mes_siguiente.year, activo=activo, ret_mes=ret_mes_siguiente))

    cartera = pd.DataFrame(filas)
    print(f"\nMeses operados: {len(cartera)}")
    print(f"  Distribución de activo elegido: {cartera['activo'].value_counts().to_dict()}")

    r = cartera['ret_mes'].to_numpy()
    curva = np.cumprod(1 + r)
    pico = np.maximum.accumulate(curva)
    dd = (1 - curva / pico).max()
    ret_anual = curva[-1] ** (12 / len(r)) - 1 if curva[-1] > 0 else np.nan
    sharpe = (r.mean() / r.std()) * np.sqrt(12) if r.std() > 0 else np.nan
    print(f"\nGEM: Ret.anualizado={ret_anual*100:+.2f}%  Vol.anualizada={r.std()*np.sqrt(12)*100:.2f}%  "
          f"Sharpe={sharpe:.3f}  MaxDD={dd*100:.2f}%  %Meses+={ (r>0).mean()*100:.1f}%")
    for anio, g in cartera.groupby('anio'):
        rg = g['ret_mes'].to_numpy()
        curva_g = np.cumprod(1 + rg)
        print(f"    {anio}: n={len(rg)}  Ret.año={(curva_g[-1]-1)*100:+.2f}%  activos={g['activo'].value_counts().to_dict()}")

    # Referencia: 100% US500(SP500 FRED) buy&hold, mismo periodo
    ref = df['ret_us_mes'].iloc[LOOKBACK_MESES + 2:].dropna().to_numpy()
    curva_ref = np.cumprod(1 + ref)
    ret_ref_anual = curva_ref[-1] ** (12 / len(ref)) - 1 if curva_ref[-1] > 0 else np.nan
    sharpe_ref = (ref.mean() / ref.std()) * np.sqrt(12) if ref.std() > 0 else np.nan
    pico_ref = np.maximum.accumulate(curva_ref)
    dd_ref = (1 - curva_ref / pico_ref).max()
    print(f"\nReferencia 100% US stock (buy&hold, mismo periodo): Ret.anualizado={ret_ref_anual*100:+.2f}%  "
          f"Sharpe={sharpe_ref:.3f}  MaxDD={dd_ref*100:.2f}%")


if __name__ == '__main__':
    main()
