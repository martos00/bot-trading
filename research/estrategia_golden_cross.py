"""
Cruce de medias moviles 50/200 ("Golden Cross"/"Death Cross") -- tercera
candidata de la fase de metodos documentados. Elegida deliberadamente
como CASO DE ESTUDIO de calidad de evidencia, no solo como "otro
indicador popular": tiene evidencia academica a favor Y evidencia
academica en contra (el propio fenomeno de data-snooping que este
proyecto intenta evitar en cada hipotesis).

1. ESTRATEGIA ORIGINAL: regla de cruce de medias moviles, de uso
   extendido entre operadores tecnicos desde principios del s.XX.
   Formalizada y sometida a prueba estadistica rigurosa por Brock,
   Lakonishok & LeBaron (1992), "Simple Technical Trading Rules and the
   Stochastic Properties of Stock Returns", Journal of Finance --
   familia de reglas de media movil (entre ellas variantes de 50/200
   dias) sobre el Dow Jones 1897-1986: encontraron rentabilidad
   superior a comprar-y-mantener, ESTADISTICAMENTE SIGNIFICATIVA bajo
   varios modelos de bootstrap (random walk, AR(1), GARCH-M, EGARCH).
   SIN EMBARGO: Sullivan, Timmermann & White (1999), "Data-Snooping,
   Technical Trading Rule Performance, and the Bootstrap", Journal of
   Finance, re-examinaron ~26.000 reglas tecnicas (incluidas las
   mejores de BLL92) sobre el MISMO indice y, aplicando el "Reality
   Check" de White (que corrige por el sesgo de haber probado miles de
   reglas y reportar solo la mejor), encontraron que la ventaja de las
   mejores reglas de BLL92 DESAPARECE fuera de muestra (1986-1996) una
   vez corregido el sesgo de seleccion. Es decir: la propia literatura
   academica sobre esta estrategia documenta EXACTAMENTE el riesgo que
   este proyecto trata de evitar en cada hipotesis (sesgo de multiples
   comparaciones). Se elige por esto como caso de prueba, no a pesar de
   ello.

2. REGLAS AUTOMATIZADAS: SMA(50) y SMA(200) del cierre diario. Señal
   "stop-and-reverse" (no largo/plano): +1 cuando SMA50 > SMA200
   ("Golden Cross"), -1 cuando SMA50 < SMA200 ("Death Cross"). Señal
   evaluada de forma CAUSAL al cierre de cada fin de mes (mismo punto
   de rebalanceo que TSMOM, para comparabilidad directa), aplicada al
   mes siguiente completo. Tamaño de posicion con el MISMO motor de
   vol-targeting que TSMOM (VOL_OBJETIVO/LIMITE_POSICION ya validados
   en ese modulo, sin modificar), para que cualquier diferencia de
   resultado frente a TSMOM se deba al MECANISMO de señal (cruce de
   medias vs. signo de retorno a 12m), no al motor de cartera.

3. SIMPLIFICACIONES Y SU EFECTO ESPERADO (declaradas): BLL92/STW99
   evaluan la regla long/short SIN escalado de volatilidad y SIN coste
   de transaccion realista (BLL92 explicitamente no resta costes;
   STW99 si considera costes y eso reduce aun mas la significancia
   encontrada) -- aqui SI se resta spread real, lo que es una prueba
   MAS ESTRICTA que el estudio original. Rebalanceo mensual en vez de
   diario (evita coste de turnover diario irrealista combinado con el
   escalado de volatilidad) -- podria retrasar la reaccion a un cruce
   real hasta 1 mes frente a una ejecucion diaria fiel.

4. INFORMACION PERDIDA POR OHLC: ninguna -- SMA50/SMA200 son, por
   diseño, funciones puras de Close diario.

EVIDENCIA DEL TRACK RECORD: MIXTA, documentada explicitamente mas
arriba -- positiva en estudio original (BLL92, 1897-1986, un solo
indice), **refutada fuera de muestra por el propio sesgo de
multiples comparaciones** en el estudio posterior (STW99). No es una
cifra promocional de un practicante: es un ejemplo academico publicado
de como una señal "significativa" puede dejar de serlo al corregir
sesgo de seleccion -- el resultado de abajo se interpreta con ese
precedente en mente, no se presenta la señal como "probada" solo por
ser conocida.
"""
import numpy as np
import pandas as pd

from datos_multiactivo import cargar_universo, UNIVERSO
from estrategia_tsmom import (VOL_OBJETIVO, LIMITE_POSICION, SEED, REPETICIONES_CONTROL,
                               fin_de_mes, cartera_mensual, metricas_cartera, control_signo_aleatorio)

SMA_RAPIDA = 50
SMA_LENTA = 200
VENTANA_VOL_DIAS = 60


def preparar_activo_cruce(diario):
    d = diario.copy().reset_index(drop=True)
    d['ret_log'] = np.log(d['Close'] / d['Close'].shift(1))
    d['vol_60d_anualizada'] = d['ret_log'].rolling(VENTANA_VOL_DIAS).std() * np.sqrt(252)
    d['sma_rapida'] = d['Close'].rolling(SMA_RAPIDA).mean()
    d['sma_lenta'] = d['Close'].rolling(SMA_LENTA).mean()
    d['anio_mes'] = d['dia'].dt.to_period('M')
    return d


def construir_señales_cruce(d, point):
    idx_fin_mes = fin_de_mes(d)
    filas = []
    for pos, idx in enumerate(idx_fin_mes[:-1]):
        sma_r, sma_l, vol = d['sma_rapida'].iloc[idx], d['sma_lenta'].iloc[idx], d['vol_60d_anualizada'].iloc[idx]
        if pd.isna(sma_r) or pd.isna(sma_l) or pd.isna(vol) or vol <= 0:
            continue
        signo = 1 if sma_r > sma_l else (-1 if sma_r < sma_l else 0)
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


def main():
    universo = cargar_universo()
    señales_por_activo = {}
    for nombre, diario in universo.items():
        point = UNIVERSO[nombre]['point']
        d = preparar_activo_cruce(diario)
        señales_por_activo[nombre] = construir_señales_cruce(d, point)

    print("######## Golden Cross / Death Cross (SMA50/SMA200), rebalanceo mensual ########")
    for nombre, df in señales_por_activo.items():
        if len(df) == 0:
            print(f"  {nombre}: sin señales validas")
            continue
        pct_cruces = (df['tamano_posicion'].apply(np.sign).diff() != 0).sum()
        print(f"  {nombre}: n={len(df)}  media mensual neta={df['ret_neto_mes'].mean()*100:+.3f}%  "
              f"%largo={(df['tamano_posicion']>0).mean()*100:.0f}%  cambios de señal={pct_cruces}")

    cartera, todas = cartera_mensual(señales_por_activo)
    m = metricas_cartera(cartera)
    print(f"\nCartera combinada (igual ponderacion, {m['n_meses']} meses):")
    print(f"  Retorno acumulado neto: {m['ret_acumulado']*100:+.1f}%  Retorno anualizado: {m['ret_anualizado']*100:+.2f}%")
    print(f"  Volatilidad anualizada: {m['vol_anualizada']*100:.2f}%  Sharpe: {m['sharpe']:.3f}")
    print(f"  Max drawdown: {m['max_drawdown']*100:.2f}%  %Meses positivos: {m['pct_meses_positivos']:.1f}%")
    for anio, g in cartera.groupby('anio'):
        mg = metricas_cartera(g)
        print(f"    {anio}: n={mg['n_meses']}  Ret. acumulado año={mg['ret_acumulado']*100:+.2f}%  Sharpe={mg['sharpe']:.3f}")

    rng = np.random.default_rng(SEED)
    medias_control = control_signo_aleatorio(señales_por_activo, rng)
    media_real = cartera['ret_neto_mes'].mean()
    z = (media_real - medias_control.mean()) / medias_control.std() if medias_control.std() > 0 else np.nan
    print(f"\n  Control signo aleatorio ({REPETICIONES_CONTROL} rep.): media real={media_real*100:+.4f}%/mes  "
          f"media aleatoria={medias_control.mean()*100:+.4f}%/mes  z={z:+.2f}")
    return cartera, señales_por_activo


if __name__ == '__main__':
    main()
