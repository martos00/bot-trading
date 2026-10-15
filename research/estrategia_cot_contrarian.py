"""
COT Positioning Contrarian -- familia pospuesta por falta de datos,
desbloqueada con los informes CFTC (research/datos_externos/cot_*.csv,
ver research/descargar_cftc_cot.py). Fundamento: posicionamiento
especulativo extremo (Managed Money en materias primas, Leveraged
Money en divisas/indices financieros) como señal de sentimiento/
crowding -- cuando el posicionamiento neto alcanza un extremo
historico, suele preceder una reversion (ampliamente usado en la
practica de commodity trading; respaldo academico en la teoria de
presion de cobertura, de Roon/Nijman/Veld 2000, Journal of Finance,
"Hedging Pressure Effects in Futures Markets").

LAG DE PUBLICACION (critico, declarado, no lookahead): el informe
COT mide posiciones a fecha de MARTES pero se publica el VIERNES
siguiente a las 15:30 ET -- la señal solo esta disponible para operar
a partir del LUNES siguiente (report_date + 6 dias de calendario,
conservador). No se opera con la fecha del propio informe.

REGLAS (unica version por activo, pre-registrada, sin optimizar):
 - Extremo: percentil EXPANDIDO (causal, min. 156 semanas/3 años de
   historial) del neto especulativo dentro de su propio historial.
   percentil>0.90 => CORTO (fade de posicionamiento largo extremo).
   percentil<0.10 => LARGO (fade de posicionamiento corto extremo).
 - Entrada: Open del primer dia de cotizacion >= report_date + 6 dias.
 - Tamaño: escalado por volatilidad inversa (mismo mecanismo de
   vol-targeting 10% que TSMOM/carry, para comparabilidad).
 - Mantenimiento: 1 semana (hasta la siguiente señal), coste de
   spread real al entrar.
 - Control: mismo mecanismo con el signo de la señal invertido
   aleatoriamente cada semana.
"""
import sys
from datetime import timedelta

import numpy as np
import pandas as pd

from datos_multiactivo import cargar_universo, UNIVERSO
from estrategia_tsmom import VOL_OBJETIVO, LIMITE_POSICION, metricas_cartera

MERCADOS = ['XAUUSD', 'EURUSD', 'GBPUSD', 'USDJPY', 'USDCAD', 'USDCHF', 'USTEC', 'US500']
VENTANA_MIN_SEMANAS = 156
PERCENTIL_ALTO = 0.90
PERCENTIL_BAJO = 0.10
LAG_PUBLICACION_DIAS = 6
VENTANA_VOL_DIAS = 60
SEED = 20261015
REPETICIONES_CONTROL = 1000


def percentil_expandido_causal(valores, minimo=VENTANA_MIN_SEMANAS):
    out = np.full(len(valores), np.nan)
    for i in range(len(valores)):
        if i + 1 < minimo:
            continue
        ventana = valores[:i + 1]
        out[i] = (ventana <= valores[i]).mean()
    return out


def construir_señales(nombre, diario, cot):
    point = UNIVERSO[nombre]['point']
    d = diario.copy().reset_index(drop=True)
    d['ret_log'] = np.log(d['Close'] / d['Close'].shift(1))
    d['vol_60d'] = d['ret_log'].rolling(VENTANA_VOL_DIAS).std() * np.sqrt(252)

    cot = cot.sort_values('fecha').reset_index(drop=True)
    # CORRECCION (practica estandar del "COT Index"): se normaliza el neto
    # especulativo por el interes abierto ANTES del percentil -- el neto
    # RAW no es estacionario en mercados con interes abierto creciente
    # (ej. futuros de indice), lo que convertia el percentil en un proxy
    # de tendencia, no de "extremo de posicionamiento" (encontrado al
    # comprobar por que USTEC/US500 salian permanentemente largos).
    cot['neto_sobre_oi'] = cot['neto_especulativo'] / cot['open_interest']
    cot['percentil'] = percentil_expandido_causal(cot['neto_sobre_oi'].to_numpy())
    cot['fecha_operable'] = cot['fecha'] + timedelta(days=LAG_PUBLICACION_DIAS)

    tiempos = d['dia']
    filas = []
    for i in range(len(cot) - 1):
        pct = cot['percentil'].iloc[i]
        if pd.isna(pct):
            continue
        if pct > PERCENTIL_ALTO:
            signo = -1
        elif pct < PERCENTIL_BAJO:
            signo = 1
        else:
            continue

        idx_entrada_candidatos = d.index[tiempos >= cot['fecha_operable'].iloc[i]]
        if len(idx_entrada_candidatos) == 0:
            continue
        idx_entrada = idx_entrada_candidatos[0]
        vol = d['vol_60d'].iloc[idx_entrada]
        if pd.isna(vol) or vol <= 0:
            continue

        fecha_operable_siguiente = cot['fecha_operable'].iloc[i + 1]
        idx_salida_candidatos = d.index[tiempos >= fecha_operable_siguiente]
        if len(idx_salida_candidatos) == 0 or idx_salida_candidatos[0] <= idx_entrada:
            continue
        idx_salida = idx_salida_candidatos[0]

        tamano = np.clip(signo * (VOL_OBJETIVO / vol), -LIMITE_POSICION, LIMITE_POSICION)
        ret_bruto = d['Close'].iloc[idx_salida] / d['Open'].iloc[idx_entrada] - 1.0
        spread_precio = d['Spread'].iloc[idx_entrada] * point if pd.notna(d['Spread'].iloc[idx_entrada]) else 0.0
        coste_frac = (spread_precio / d['Open'].iloc[idx_entrada]) * abs(tamano)
        filas.append(dict(semana=cot['fecha'].iloc[i], anio=d['dia'].iloc[idx_entrada].year,
                           percentil=pct, tamano_posicion=tamano, ret_bruto=tamano * ret_bruto,
                           coste_frac=coste_frac, ret_neto=tamano * ret_bruto - coste_frac))
    return pd.DataFrame(filas)


def cartera_semanal(señales):
    todas = pd.concat([df.assign(activo=n) for n, df in señales.items() if len(df) > 0], ignore_index=True)
    if len(todas) == 0:
        return pd.DataFrame()
    cartera = todas.groupby('semana').agg(ret_neto_mes=('ret_neto', 'mean'), n=('activo', 'nunique')).reset_index()
    cartera['anio'] = cartera['semana'].apply(lambda f: f.year)
    return cartera.sort_values('semana').reset_index(drop=True)


def control_signo_aleatorio(señales, rng):
    medias = []
    for _ in range(REPETICIONES_CONTROL):
        copia = {}
        for n, df in señales.items():
            if len(df) == 0:
                continue
            df2 = df.copy()
            signo_aleatorio = rng.choice([-1, 1], size=len(df2))
            ret_puro = df2['ret_bruto'] / df2['tamano_posicion']
            tamano_aleatorio = df2['tamano_posicion'].abs() * signo_aleatorio
            df2['ret_neto'] = tamano_aleatorio * ret_puro - df2['coste_frac']
            copia[n] = df2
        cart = cartera_semanal(copia)
        if len(cart) > 0:
            medias.append(cart['ret_neto_mes'].mean())
    return np.array(medias)


def main():
    universo = cargar_universo(MERCADOS)
    señales = {}
    for nombre in MERCADOS:
        cot = pd.read_csv(f'datos_externos/cot_{nombre}.csv', parse_dates=['fecha'])
        señales[nombre] = construir_señales(nombre, universo[nombre], cot)

    print("################ COT Positioning Contrarian ################")
    for nombre, df in señales.items():
        if len(df) == 0:
            print(f"  {nombre}: sin señales validas")
            continue
        print(f"  {nombre}: n={len(df)}  media semanal neta={df['ret_neto'].mean()*100:+.3f}%  "
              f"%largo={(df['tamano_posicion']>0).mean()*100:.0f}%")

    cartera = cartera_semanal(señales)
    if len(cartera) == 0:
        print("SIN CARTERA.")
        return
    m = metricas_cartera(cartera.rename(columns={'ret_neto_mes': 'ret_neto_mes'}))
    # metricas_cartera asume periodos "mensuales" para anualizar (x12) -- aqui son semanales,
    # se anualiza aparte correctamente abajo en vez de reutilizar el factor x12.
    r = cartera['ret_neto_mes'].to_numpy()
    curva = np.cumprod(1 + r)
    ret_anualizado = curva[-1] ** (52 / len(r)) - 1 if curva[-1] > 0 else np.nan
    sharpe = (r.mean() / r.std()) * np.sqrt(52) if r.std() > 0 else np.nan
    pico = np.maximum.accumulate(curva)
    dd = (1 - curva / pico).max()
    print(f"\nSemanas evaluables: {len(r)}  Ret. acumulado: {(curva[-1]-1)*100:+.1f}%  "
          f"Ret. anualizado: {ret_anualizado*100:+.2f}%  Sharpe: {sharpe:.3f}  MaxDD: {dd*100:.2f}%  "
          f"%Semanas+: {(r>0).mean()*100:.1f}%")
    for anio, g in cartera.groupby('anio'):
        rg = g['ret_neto_mes'].to_numpy()
        print(f"    {anio}: n={len(rg)}  Media semanal={rg.mean()*100:+.3f}%  Suma={rg.sum()*100:+.2f}%")

    rng = np.random.default_rng(SEED)
    medias_control = control_signo_aleatorio(señales, rng)
    media_real = r.mean()
    z = (media_real - medias_control.mean()) / medias_control.std() if medias_control.std() > 0 else np.nan
    print(f"\n  Control signo aleatorio ({REPETICIONES_CONTROL} rep.): media real={media_real*100:+.4f}%/sem  "
          f"media aleatoria={medias_control.mean()*100:+.4f}%/sem  z={z:+.2f}")


if __name__ == '__main__':
    main()
