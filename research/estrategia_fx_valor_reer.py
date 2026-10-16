"""
Estrategia de "valor" en divisas basada en el tipo de cambio efectivo
real (REER) -- cuarta estrategia de la fase de "métodos documentados
con evidencia externa verificable" (Turtle, GEM, Golden Cross ya
probadas). Universo: SOLO XAUUSD y los 6 pares Forex (EURUSD, GBPUSD,
USDJPY, USDCAD, USDCHF, USDSEK) -- USTEC/US500 excluidos por el hueco
de datos sin resolver (ver README).

1. ESTRATEGIA ORIGINAL: "Currency Value" -- Menkhoff, Sarno, Schmeling
   & Schrimpf (2017), *Review of Financial Studies* (ampliando la
   literatura clásica de reversión a la paridad de poder adquisitivo,
   PPP -- ver Taylor & Taylor 2004, *Journal of Economic Perspectives*,
   "The Purchasing Power Parity Debate"). Mecanismo: el tipo de cambio
   efectivo real (REER) de cada país se desvía de su media histórica
   de largo plazo por desequilibrios temporales (flujos de capital,
   política monetaria, shocks) que tienden a corregirse en horizontes
   de VARIOS AÑOS -- comprar la divisa más "barata" (REER muy por
   debajo de su media de largo plazo) y vender la más "cara" predice
   retorno positivo en el estudio original (dato de más de 40 años,
   docenas de divisas, ordenadas en quintiles).

2. REGLAS AUTOMATIZADAS (adaptadas a nuestro universo de 6 pares, NO
   una réplica exacta del ordenamiento por quintiles del estudio
   original, que necesita muchas más divisas de las que tenemos):
   - Señal mensual causal: desviación_relativa = ln(REER_moneda /
     media_móvil_60_meses(REER_moneda)) − ln(REER_USD /
     media_móvil_60_meses(REER_USD)).
   - Dirección: +1 (largo el par, la divisa extranjera "barata"
     relativo a USD) si desviación_relativa < 0; −1 si > 0.
   - Tamaño de posición: MISMO motor de vol-targeting que TSMOM
     (VOL_OBJETIVO/LIMITE_POSICION, sin modificar), para que cualquier
     diferencia de resultado se deba al MECANISMO de señal (valor/PPP
     vs. momentum de precio), no al motor de cartera.
   - Rezago de publicación: se asume 1 mes completo de rezago entre el
     cierre de un mes natural y la disponibilidad real de su dato REER
     (el BIS publica con rezago, no el mismo día) -- declarado,
     conservador, sin ajustar tras ver resultados.
   - Lookback de 60 meses (5 años) PRE-REGISTRADO, el estándar de la
     literatura citada -- no se prueban otros lookbacks para evitar
     buscar el que mejor funcione.

3. SIMPLIFICACIONES Y SU EFECTO ESPERADO (declaradas):
   - El estudio original ordena DOCENAS de divisas (mercados
     desarrollados Y emergentes) en quintiles; aquí solo hay 6 pares,
     todos frente a USD -- se usa una señal CONTINUA (magnitud de la
     desviación relativa) en vez de quintiles, simplificación
     razonable con pocos activos, pero MATERIAL: pierde la
     diversificación cruzada entre muchas divisas que es parte del
     mecanismo original.
   - Muestra de precios disponible: solo 2023-2026 (~3,75 años) para
     los 6 pares -- el propio mecanismo que se prueba actúa en
     horizontes de VARIOS AÑOS según la literatura citada, así que
     esta ventana es estructuralmente demasiado corta para que el
     efecto tenga tiempo de expresarse con fuerza completa (mismo tipo
     de limitación ya declarada para Hurst-Ooi-Pedersen/TSMOM de largo
     plazo). El resultado de abajo NO debe leerse como una réplica del
     estudio académico, solo como una prueba honesta con los datos
     disponibles.
   - El REER del BIS SÍ es la fuente de datos estándar de esa
     literatura (a diferencia de otras estrategias de este proyecto,
     aquí NO hay una sustitución de proxy -- es la misma fuente que
     usarían los propios autores).

4. INFORMACIÓN PERDIDA POR OHLC: ninguna adicional -- la señal viene
   de datos macroeconómicos externos (REER), no de OHLC.

EVIDENCIA DEL TRACK RECORD: académica, revisada por pares (*Review of
Financial Studies*, publicación de primer nivel en finanzas), con
muestra de décadas y muchas divisas en el estudio original -- la
evidencia de calidad MÁS ALTA de las estrategias "de traders/gestores"
probadas en este proyecto hasta ahora (Turtle=libros/promocional,
GEM=backtest propio del autor, Golden Cross=mixta ya documentada)."""
import numpy as np
import pandas as pd

from datos_multiactivo import cargar_universo, UNIVERSO
from estrategia_tsmom import (VOL_OBJETIVO, LIMITE_POSICION, SEED, REPETICIONES_CONTROL,
                               fin_de_mes, cartera_mensual, metricas_cartera, control_signo_aleatorio)

RUTA_REER = 'datos_externos/reer_bis.csv'
VENTANA_MESES_REER = 60
REZAGO_MESES_PUBLICACION = 1
VENTANA_VOL_DIAS = 60

PARES = {
    'EURUSD': ('EUR', 'US'), 'GBPUSD': ('GBP', 'US'), 'USDJPY': ('US', 'JPY'),
    'USDCAD': ('US', 'CAD'), 'USDCHF': ('US', 'CHF'), 'USDSEK': ('US', 'SEK'),
}


def cargar_desviaciones_reer():
    reer = pd.read_csv(RUTA_REER, index_col=0, parse_dates=True)
    media_movil = reer.rolling(VENTANA_MESES_REER, min_periods=VENTANA_MESES_REER).mean()
    desviacion = np.log(reer / media_movil)
    desviacion.index = desviacion.index.to_period('M')
    # rezago de publicacion: el dato del mes M solo se considera "conocido" a partir de M+REZAGO
    desviacion_disponible = desviacion.copy()
    desviacion_disponible.index = desviacion_disponible.index + REZAGO_MESES_PUBLICACION
    return desviacion_disponible


def preparar_activo(diario, point):
    d = diario.copy().reset_index(drop=True)
    d['ret_log'] = np.log(d['Close'] / d['Close'].shift(1))
    d['vol_60d_anualizada'] = d['ret_log'].rolling(VENTANA_VOL_DIAS).std() * np.sqrt(252)
    d['anio_mes'] = d['dia'].dt.to_period('M')
    return d


def construir_señales_valor(d, point, par, desviaciones):
    base, cotizada = PARES[par]
    idx_fin_mes = fin_de_mes(d)
    filas = []
    for pos, idx in enumerate(idx_fin_mes[:-1]):
        mes_actual = d['anio_mes'].iloc[idx]
        vol = d['vol_60d_anualizada'].iloc[idx]
        if pd.isna(vol) or vol <= 0:
            continue
        if mes_actual not in desviaciones.index:
            continue
        dev_base = desviaciones.loc[mes_actual, base] if base in desviaciones.columns else np.nan
        dev_cotizada = desviaciones.loc[mes_actual, cotizada] if cotizada in desviaciones.columns else np.nan
        if pd.isna(dev_base) or pd.isna(dev_cotizada):
            continue
        desviacion_relativa = dev_base - dev_cotizada
        signo = -1 if desviacion_relativa > 0 else (1 if desviacion_relativa < 0 else 0)
        if signo == 0:
            continue
        tamano = np.clip(signo * (VOL_OBJETIVO / vol), -LIMITE_POSICION, LIMITE_POSICION)

        idx_fin_siguiente = idx_fin_mes[pos + 1]
        ret_mes_siguiente = d['Close'].iloc[idx_fin_siguiente] / d['Close'].iloc[idx] - 1.0
        spread_precio = d['Spread'].iloc[idx] * point if pd.notna(d['Spread'].iloc[idx]) else 0.0
        coste_frac = (spread_precio / d['Close'].iloc[idx]) * abs(tamano)

        filas.append(dict(
            mes=d['anio_mes'].iloc[idx_fin_siguiente], anio=d['dia'].iloc[idx_fin_siguiente].year,
            tamano_posicion=tamano, desviacion_relativa=desviacion_relativa,
            ret_bruto_mes=tamano * ret_mes_siguiente, coste_frac=coste_frac,
            ret_neto_mes=tamano * ret_mes_siguiente - coste_frac,
        ))
    return pd.DataFrame(filas)


def benchmark_estatico(d, point):
    """Mismo motor de vol-targeting, SIEMPRE LARGO (sin señal de valor)
    -- benchmark de exposición pura, para no confundir "estar expuesto"
    con "la señal de valor aporta algo" (misma disciplina que
    momentum transversal/Golden Cross)."""
    idx_fin_mes = fin_de_mes(d)
    filas = []
    for pos, idx in enumerate(idx_fin_mes[:-1]):
        vol = d['vol_60d_anualizada'].iloc[idx]
        if pd.isna(vol) or vol <= 0:
            continue
        tamano = np.clip(VOL_OBJETIVO / vol, -LIMITE_POSICION, LIMITE_POSICION)
        idx_fin_sig = idx_fin_mes[pos + 1]
        ret_mes = d['Close'].iloc[idx_fin_sig] / d['Close'].iloc[idx] - 1.0
        spread_precio = d['Spread'].iloc[idx] * point if pd.notna(d['Spread'].iloc[idx]) else 0.0
        coste = (spread_precio / d['Close'].iloc[idx]) * abs(tamano)
        filas.append(dict(mes=d['anio_mes'].iloc[idx_fin_sig], anio=d['dia'].iloc[idx_fin_sig].year,
                           ret_neto_mes=tamano * ret_mes - coste))
    return pd.DataFrame(filas)


def main():
    desviaciones = cargar_desviaciones_reer()
    universo = cargar_universo(list(PARES.keys()))

    señales_por_par = {}
    bench_por_par = {}
    for par in PARES:
        point = UNIVERSO[par]['point']
        d = preparar_activo(universo[par], point)
        señales_por_par[par] = construir_señales_valor(d, point, par, desviaciones)
        bench_por_par[par] = benchmark_estatico(d, point)

    print("######## FX Valor/REER -- señal mensual causal, lookback 60 meses, rezago 1 mes ########")
    for par, df in señales_por_par.items():
        if len(df) == 0:
            print(f"  {par}: sin señales válidas")
            continue
        print(f"  {par}: n={len(df)}  media mensual neta={df['ret_neto_mes'].mean()*100:+.3f}%  "
              f"%largo={(df['tamano_posicion']>0).mean()*100:.0f}%  "
              f"desv.relativa media={df['desviacion_relativa'].mean():+.4f}")

    cartera, todas = cartera_mensual(señales_por_par)
    m = metricas_cartera(cartera)
    print(f"\nCartera FX-Valor combinada (igual ponderación, {m['n_meses']} meses):")
    print(f"  Retorno acumulado neto: {m['ret_acumulado']*100:+.1f}%  Retorno anualizado: {m['ret_anualizado']*100:+.2f}%")
    print(f"  Volatilidad anualizada: {m['vol_anualizada']*100:.2f}%  Sharpe: {m['sharpe']:.3f}")
    print(f"  Max drawdown: {m['max_drawdown']*100:.2f}%  %Meses positivos: {m['pct_meses_positivos']:.1f}%")
    for anio, g in cartera.groupby('anio'):
        mg = metricas_cartera(g)
        print(f"    {anio}: n={mg['n_meses']}  Ret.acum.año={mg['ret_acumulado']*100:+.2f}%  Sharpe={mg['sharpe']:.3f}")

    rng = np.random.default_rng(SEED)
    medias_control = control_signo_aleatorio(señales_por_par, rng)
    media_real = cartera['ret_neto_mes'].mean()
    z = (media_real - medias_control.mean()) / medias_control.std() if medias_control.std() > 0 else np.nan
    print(f"\n  Control signo aleatorio ({REPETICIONES_CONTROL} rep.): media real={media_real*100:+.4f}%/mes  "
          f"media aleatoria={medias_control.mean()*100:+.4f}%/mes  z={z:+.2f}")

    # Benchmark estático (siempre largo, mismo vol-target) -- la comprobación que ya exigió el usuario
    cartera_bench, _ = cartera_mensual(bench_por_par)
    m_bench = metricas_cartera(cartera_bench)
    print(f"\nBenchmark estático (siempre largo, mismo vol-target, {m_bench['n_meses']} meses):")
    print(f"  Retorno anualizado: {m_bench['ret_anualizado']*100:+.2f}%  Sharpe: {m_bench['sharpe']:.3f}  "
          f"MaxDD: {m_bench['max_drawdown']*100:.2f}%")

    pareado = pd.merge(cartera[['mes', 'ret_neto_mes']], cartera_bench[['mes', 'ret_neto_mes']],
                        on='mes', suffixes=('_valor', '_bench'))
    excedente = (pareado['ret_neto_mes_valor'] - pareado['ret_neto_mes_bench']).to_numpy()
    print(f"\n  Excedente mensual (valor - benchmark estático): media={excedente.mean()*100:+.4f}%  "
          f"(n={len(excedente)} meses emparejados)")


if __name__ == '__main__':
    main()
