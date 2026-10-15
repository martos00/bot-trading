"""
Time-Series Momentum (TSMOM), replicando el mecanismo de Moskowitz,
Ooi & Pedersen (2012, JFE) sobre el universo de 9 activos disponible
(ver research/datos_multiactivo.py). Primera estrategia de la fase
"Opcion B" (ver README).

DIFERENCIA DE MOTOR (declarada): esto NO es una estrategia de
señal+SL+TP discreta como el resto del proyecto -- es una cartera
REBALANCEADA MENSUALMENTE con tamaño de posicion ESCALADO POR
VOLATILIDAD (vol-targeting), igual que el mecanismo original. Se
construye un motor nuevo, especifico para este tipo de estrategia, en
vez de forzarla en el motor de R-multiplos del resto del proyecto.

REGLAS (unica version por lookback, pre-registradas, sin optimizar
tras ver resultados):
 - Señal en cada fin de mes M (ultimo dia de cotizacion del mes, por
   activo): signo del retorno LOGARITMICO de los ultimos LOOKBACK_DIAS
   dias de cotizacion (252~12m, tambien se reportan 21~1m y 63~3m,
   LOS TRES SIEMPRE, igual disciplina de "reportar todos los horizontes"
   que en RSI(2)/Turno de Mes).
 - Volatilidad: desviacion tipica de retornos logaritmicos diarios de
   los ultimos 60 dias, anualizada (x pizza252). Esta es una
   SIMPLIFICACION declarada del estimador EWM del paper original (centro
   de masa ~61 dias) -- mismo espiritu, formula mas simple.
 - Tamaño de posicion = signo(retorno_lookback) * (VOL_OBJETIVO /
   vol_60d), limitado a +-LIMITE_POSICION (salvaguarda contra
   apalancamiento degenerado en activos de volatilidad casi nula, fijada
   ANTES de ver resultados, no ajustada despues).
 - Se mantiene esa posicion todo el mes siguiente (de fin de mes M a
   fin de mes M+1), acumulando retorno diario simple (no logaritmico,
   para que el coste en precio se reste de forma coherente).
 - Coste: al rebalancear (cada fin de mes, con independencia de si la
   posicion cambia de signo) se resta spread_real/Close * |variacion de
   posicion| -- coste proporcional al cambio de exposicion, no un coste
   fijo por "operacion" (concepto de cartera, no de trade discreto).
 - Cartera: media simple (igual ponderacion) de los retornos mensuales
   netos de cada activo con señal valida ese mes.
 - Control: mismo mecanismo pero con el SIGNO de la señal aleatorizado
   (manteniendo el mismo escalado de volatilidad) -- aisla si la
   DIRECCION de la tendencia aporta valor frente a estar simplemente
   expuesto con ese tamaño de posicion.

LIMITACION DE MUESTRA (declarada, no oculta): salvo XAUUSD (2015-2026,
~142 meses), el resto del universo son ~45 meses (2023-2026) -- muy
por debajo de las decadas del estudio original. Los resultados de este
universo NO deben leerse como una replicacion del estudio academico,
solo como una prueba honesta con los datos de los que disponemos.
"""
import sys

import numpy as np
import pandas as pd

from datos_multiactivo import cargar_universo, UNIVERSO

LOOKBACKS_DIAS = {'1m': 21, '3m': 63, '12m': 252}
VENTANA_VOL_DIAS = 60
VOL_OBJETIVO = 0.10  # 10% anualizado por activo, igual que Hurst et al.
LIMITE_POSICION = 3.0
SEED = 20261015
REPETICIONES_CONTROL = 1000


def preparar_activo(diario, point):
    d = diario.copy().reset_index(drop=True)
    d['ret_log'] = np.log(d['Close'] / d['Close'].shift(1))
    d['vol_60d_anualizada'] = d['ret_log'].rolling(VENTANA_VOL_DIAS).std() * np.sqrt(252)
    d['anio_mes'] = d['dia'].dt.to_period('M')
    return d


def fin_de_mes(d):
    """Indice de la ULTIMA fila de cada mes calendario -- el punto de
    rebalanceo, causal (solo usa datos hasta ese cierre inclusive)."""
    return d.groupby('anio_mes').tail(1).index.to_numpy()


def construir_señales(d, lookback_dias, point):
    idx_fin_mes = fin_de_mes(d)
    filas = []
    for pos, idx in enumerate(idx_fin_mes[:-1]):
        idx_prev_lookback = idx - lookback_dias
        if idx_prev_lookback < VENTANA_VOL_DIAS:
            continue
        vol = d['vol_60d_anualizada'].iloc[idx]
        if pd.isna(vol) or vol <= 0:
            continue
        ret_lookback = np.log(d['Close'].iloc[idx] / d['Close'].iloc[idx_prev_lookback])
        signo = np.sign(ret_lookback)
        if signo == 0:
            continue
        tamano = np.clip(signo * (VOL_OBJETIVO / vol), -LIMITE_POSICION, LIMITE_POSICION)

        idx_fin_siguiente = idx_fin_mes[pos + 1]
        ret_mes_siguiente = d['Close'].iloc[idx_fin_siguiente] / d['Close'].iloc[idx] - 1.0
        spread_precio = d['Spread'].iloc[idx] * point if pd.notna(d['Spread'].iloc[idx]) else 0.0
        coste_frac = (spread_precio / d['Close'].iloc[idx]) * abs(tamano)

        filas.append(dict(
            mes=d['anio_mes'].iloc[idx_fin_siguiente], anio=d['dia'].iloc[idx_fin_siguiente].year,
            tamano_posicion=tamano, ret_bruto_mes=tamano * ret_mes_siguiente, coste_frac=coste_frac,
            ret_neto_mes=tamano * ret_mes_siguiente - coste_frac,
        ))
    return pd.DataFrame(filas)


def cartera_mensual(señales_por_activo):
    todas = pd.concat([df.assign(activo=nombre) for nombre, df in señales_por_activo.items() if len(df) > 0],
                       ignore_index=True)
    cartera = todas.groupby('mes').agg(ret_neto_mes=('ret_neto_mes', 'mean'),
                                        n_activos=('activo', 'nunique')).reset_index()
    cartera['anio'] = cartera['mes'].apply(lambda p: p.year)
    return cartera.sort_values('mes').reset_index(drop=True), todas


def metricas_cartera(cartera):
    r = cartera['ret_neto_mes'].to_numpy()
    if len(r) == 0:
        return dict(n_meses=0)
    curva = np.cumprod(1 + r)
    pico = np.maximum.accumulate(curva)
    dd = 1 - curva / pico
    media_mensual = r.mean()
    vol_mensual = r.std()
    ret_anualizado = (curva[-1]) ** (12 / len(r)) - 1 if curva[-1] > 0 else np.nan
    sharpe_anualizado = (media_mensual / vol_mensual) * np.sqrt(12) if vol_mensual > 0 else np.nan
    return dict(n_meses=len(r), ret_acumulado=curva[-1] - 1, ret_anualizado=ret_anualizado,
                vol_anualizada=vol_mensual * np.sqrt(12), sharpe=sharpe_anualizado,
                max_drawdown=dd.max(), pct_meses_positivos=(r > 0).mean() * 100)


def control_signo_aleatorio(señales_por_activo, rng):
    medias = []
    for _ in range(REPETICIONES_CONTROL):
        copia = {}
        for nombre, df in señales_por_activo.items():
            if len(df) == 0:
                continue
            df2 = df.copy()
            signo_aleatorio = rng.choice([-1, 1], size=len(df2))
            tamano_abs = df2['tamano_posicion'].abs() * signo_aleatorio
            ret_mes_implicito = df2['ret_bruto_mes'] / df2['tamano_posicion']  # recupera el retorno puro del activo
            df2['ret_neto_mes'] = tamano_abs * ret_mes_implicito - df2['coste_frac']
            copia[nombre] = df2
        cartera_sim, _ = cartera_mensual(copia)
        medias.append(cartera_sim['ret_neto_mes'].mean())
    return np.array(medias)


def main(lookback_nombre='12m'):
    lookback_dias = LOOKBACKS_DIAS[lookback_nombre]
    universo = cargar_universo()
    señales_por_activo = {}
    for nombre, diario in universo.items():
        point = UNIVERSO[nombre]['point']
        d = preparar_activo(diario, point)
        señales_por_activo[nombre] = construir_señales(d, lookback_dias, point)

    cartera, todas = cartera_mensual(señales_por_activo)
    m = metricas_cartera(cartera)
    print(f"\n######## TSMOM lookback={lookback_nombre} ({lookback_dias} dias) ########")
    print(f"Meses evaluables: {m['n_meses']}")
    if m['n_meses'] == 0:
        print("  SIN DATOS SUFICIENTES.")
        return
    print(f"  Retorno acumulado neto: {m['ret_acumulado']*100:+.1f}%  Retorno anualizado: {m['ret_anualizado']*100:+.2f}%")
    print(f"  Volatilidad anualizada: {m['vol_anualizada']*100:.2f}%  Sharpe (sin tasa libre de riesgo): {m['sharpe']:.3f}")
    print(f"  Max drawdown (cartera, mensual): {m['max_drawdown']*100:.2f}%  %Meses positivos: {m['pct_meses_positivos']:.1f}%")
    for anio, g in cartera.groupby('anio'):
        mg = metricas_cartera(g)
        print(f"    {anio}: n={mg['n_meses']}  Ret. acumulado año={mg['ret_acumulado']*100:+.2f}%  "
              f"Sharpe={mg['sharpe']:.3f}")

    print("\n  Por activo (media de retorno neto mensual, señal valida):")
    for nombre, df in señales_por_activo.items():
        if len(df) == 0:
            print(f"    {nombre}: sin señales validas")
            continue
        print(f"    {nombre}: n={len(df)}  media mensual neta={df['ret_neto_mes'].mean()*100:+.3f}%  "
              f"%largo={ (df['tamano_posicion']>0).mean()*100:.0f}%")

    rng = np.random.default_rng(SEED)
    medias_control = control_signo_aleatorio(señales_por_activo, rng)
    media_real = cartera['ret_neto_mes'].mean()
    z = (media_real - medias_control.mean()) / medias_control.std() if medias_control.std() > 0 else np.nan
    print(f"\n  Control signo aleatorio ({REPETICIONES_CONTROL} rep.): media real={media_real*100:+.4f}%/mes  "
          f"media aleatoria={medias_control.mean()*100:+.4f}%/mes  z={z:+.2f}")
    return cartera, señales_por_activo


if __name__ == '__main__':
    for lb in LOOKBACKS_DIAS:
        main(lb)
