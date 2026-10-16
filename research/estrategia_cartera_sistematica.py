"""
Sistema de cartera diversificada -- nuevo enfoque pedido por el
usuario tras ~60 hipótesis de señal/entrada-salida: en vez de buscar
una señal rentable en un activo, se investiga la CONSTRUCCIÓN DE
CARTERA (risk parity / vol-targeting, trend-following diversificado,
combinación de primas de riesgo distintas).

UNIVERSO NÚCLEO (activos con prima de riesgo de largo plazo
justificada para estar SIEMPRE LARGO -- a diferencia de FX, que no
tiene una prima "larga" universal, solo carry/trend direccionales ya
probados y descartados): XAUUSD (metal), USTEC+US500 (renta
variable), BONO_US10Y (tipos, sintético declarado), WTI (energía).
Los 6 pares Forex se tratan como un SLEEVE adicional de trend-
following (no como posiciones largas permanentes) -- ver parte 3.

METODOLOGÍA (pre-registrada, igual disciplina que el resto del
proyecto):
 1. CARTERA PASIVA risk-parity: peso inverso a la volatilidad
    (ventana 60 días, rebalanceo mensual) de los 5 activos núcleo,
    SIEMPRE LARGO (sin señal de dirección) -- esto mide el beneficio
    de DIVERSIFICACIÓN/EXPOSICIÓN, no habilidad de timing. Se compara
    contra (a) la misma cesta equiponderada (sin ajustar por riesgo) y
    (b) 100% un solo activo (US500) -- para separar "diversificar
    ayuda" de "elegir el activo correcto ayuda".
 2. OVERLAY ACTIVO: mismo universo núcleo, pero con signo de
    tendencia (señal TSMOM ya validada en este proyecto, sin
    modificar su definición) en vez de "siempre largo". Se mide el
    EXCEDENTE sobre la cartera pasiva (1), con bootstrap pareado --
    la pregunta correcta no es "¿tiene buen Sharpe?" sino "¿el timing
    aporta algo sobre la mera exposición diversificada?".
 3. SLEEVE FX (trend-following, ya probado individualmente y
    descartado en solitario): se añade como diversificador de la
    cartera 1/2, no como apuesta aislada -- se reporta de forma
    transparente si el cambio viene del RETORNO o de la VOLATILIDAD,
    para no disfrazar una reducción de varianza como "mejora".
"""
import numpy as np
import pandas as pd

from cartera_diversificada import cargar_universo_diversificado
from estrategia_tsmom import LOOKBACKS_DIAS, VOL_OBJETIVO, LIMITE_POSICION

NUCLEO = ['XAUUSD', 'USTEC', 'US500', 'BONO_US10Y', 'WTI']
VENTANA_VOL = 60
SEED = 20261015
REPETICIONES_BOOTSTRAP = 2000
BLOQUE_BOOTSTRAP = 3


def preparar(universo):
    prep = {}
    for nombre, d in universo.items():
        d = d.copy().reset_index(drop=True)
        d['vol_60d'] = d['ret'].rolling(VENTANA_VOL).std() * np.sqrt(252)
        d['anio_mes'] = d['dia'].dt.to_period('M')
        prep[nombre] = d
    return prep


def fin_de_mes(d):
    return d.groupby('anio_mes').tail(1).index.to_numpy()


def señales_mensuales(d, point, signo_fn):
    """signo_fn(row_señal) -> +1/-1/0 (0 = sin posicion ese mes)."""
    idx_fin_mes = fin_de_mes(d)
    filas = []
    for pos, idx in enumerate(idx_fin_mes[:-1]):
        vol = d['vol_60d'].iloc[idx]
        if pd.isna(vol) or vol <= 0:
            continue
        signo = signo_fn(d, idx)
        if signo == 0:
            continue
        tamano = np.clip(signo * (VOL_OBJETIVO / vol), -LIMITE_POSICION, LIMITE_POSICION)
        idx_sig = idx_fin_mes[pos + 1]
        ret_mes = d['Close'].iloc[idx_sig] / d['Close'].iloc[idx] - 1.0
        spread_precio = d['Spread'].iloc[idx] * point if point is not None and pd.notna(d['Spread'].iloc[idx]) else 0.0
        coste = (spread_precio / d['Close'].iloc[idx]) * abs(tamano) if spread_precio else 0.0
        filas.append(dict(mes=d['anio_mes'].iloc[idx_sig], anio=d['dia'].iloc[idx_sig].year,
                           tamano=tamano, ret_neto=tamano * ret_mes - coste))
    return pd.DataFrame(filas)


def cartera_igual_riesgo(señales_por_activo):
    todas = pd.concat([df.assign(activo=n) for n, df in señales_por_activo.items() if len(df) > 0], ignore_index=True)
    cartera = todas.groupby('mes').agg(ret_neto_mes=('ret_neto', 'mean'), n=('activo', 'nunique')).reset_index()
    cartera['anio'] = cartera['mes'].apply(lambda p: p.year)
    return cartera.sort_values('mes').reset_index(drop=True)


def metricas(cartera, col='ret_neto_mes'):
    r = cartera[col].to_numpy()
    if len(r) == 0:
        return dict(n=0)
    curva = np.cumprod(1 + r)
    pico = np.maximum.accumulate(curva)
    dd = (1 - curva / pico).max()
    ret_anual = curva[-1] ** (12 / len(r)) - 1 if curva[-1] > 0 else np.nan
    vol_anual = r.std() * np.sqrt(12)
    sharpe = (r.mean() / r.std()) * np.sqrt(12) if r.std() > 0 else np.nan
    bajadas = r[r < 0]
    sortino = (r.mean() / bajadas.std()) * np.sqrt(12) if len(bajadas) > 1 and bajadas.std() > 0 else np.nan
    return dict(n=len(r), ret_acumulado=curva[-1] - 1, ret_anualizado=ret_anual, vol_anualizada=vol_anual,
                sharpe=sharpe, sortino=sortino, max_drawdown=dd, pct_meses_positivos=(r > 0).mean() * 100)


def imprimir_metricas(nombre, m):
    if m['n'] == 0:
        print(f"  {nombre}: sin datos")
        return
    print(f"  {nombre}: n={m['n']}  Ret.anualizado={m['ret_anualizado']*100:+.2f}%  "
          f"Vol.anualizada={m['vol_anualizada']*100:.2f}%  Sharpe={m['sharpe']:.3f}  Sortino={m['sortino']:.3f}  "
          f"MaxDD={m['max_drawdown']*100:.2f}%  %Meses+={m['pct_meses_positivos']:.1f}%")


def bootstrap_bloques_media(valores, bloque=BLOQUE_BOOTSTRAP, repeticiones=REPETICIONES_BOOTSTRAP, seed=SEED):
    valores = np.asarray(valores, dtype=float)
    n = len(valores)
    if n < bloque * 2:
        return np.nan, np.nan
    rng = np.random.default_rng(seed)
    n_bloques = int(np.ceil(n / bloque))
    max_inicio = n - bloque
    medias = np.empty(repeticiones)
    for b in range(repeticiones):
        inicios = rng.integers(0, max_inicio + 1, size=n_bloques)
        medias[b] = np.concatenate([valores[s:s + bloque] for s in inicios])[:n].mean()
    return np.percentile(medias, 2.5), np.percentile(medias, 97.5)


def main():
    universo = cargar_universo_diversificado()
    prep = preparar(universo)

    # recortar al tramo comun a TODOS los activos nucleo (USTEC/US500 desde 2023-01)
    inicio_comun = max(prep[n]['dia'].min() for n in NUCLEO)
    for n in NUCLEO:
        prep[n] = prep[n][prep[n]['dia'] >= inicio_comun].reset_index(drop=True)
        prep[n]['vol_60d'] = prep[n]['ret'].rolling(VENTANA_VOL).std() * np.sqrt(252)
        prep[n]['anio_mes'] = prep[n]['dia'].dt.to_period('M')
    print(f"Tramo común para los 5 activos núcleo: desde {inicio_comun.date()}\n")

    # --- 1. Cartera pasiva risk-parity (siempre largo) ---
    print("################ 1. Cartera PASIVA risk-parity (sin señal, siempre largo) ################")
    señales_pasivas = {n: señales_mensuales(prep[n], None, lambda d, i: 1) for n in NUCLEO}
    cartera_rp = cartera_igual_riesgo(señales_pasivas)
    imprimir_metricas('Risk-parity (vol inversa)', metricas(cartera_rp))
    for anio, g in cartera_rp.groupby('anio'):
        imprimir_metricas(f'  {anio}', metricas(g))

    # equiponderada (mismo universo, peso fijo 1/5 en vez de vol inversa)
    señales_eq = {}
    for n in NUCLEO:
        d = prep[n]
        idx_fin_mes = fin_de_mes(d)
        filas = []
        for pos, idx in enumerate(idx_fin_mes[:-1]):
            idx_sig = idx_fin_mes[pos + 1]
            ret_mes = d['Close'].iloc[idx_sig] / d['Close'].iloc[idx] - 1.0
            filas.append(dict(mes=d['anio_mes'].iloc[idx_sig], anio=d['dia'].iloc[idx_sig].year, ret_neto=ret_mes))
        señales_eq[n] = pd.DataFrame(filas)
    cartera_eq = cartera_igual_riesgo(señales_eq)
    print()
    imprimir_metricas('Equiponderada (sin ajuste por riesgo)', metricas(cartera_eq))

    # 100% US500 solo
    us500_solo = señales_eq['US500'].rename(columns={'ret_neto': 'ret_neto_mes'})
    print()
    imprimir_metricas('100% US500 (referencia de un solo activo)', metricas(us500_solo))

    # --- 2. Overlay activo: señal de tendencia (TSMOM, 12m) en vez de "siempre largo" ---
    print("\n################ 2. Overlay ACTIVO: señal de tendencia 12m sobre el mismo núcleo ################")
    lookback = LOOKBACKS_DIAS['12m']

    def signo_tendencia(d, idx):
        idx_prev = idx - lookback
        if idx_prev < 0:
            return 0
        ret_lb = np.log(d['Close'].iloc[idx] / d['Close'].iloc[idx_prev])
        return np.sign(ret_lb)

    señales_activas = {n: señales_mensuales(prep[n], None, signo_tendencia) for n in NUCLEO}
    cartera_activa = cartera_igual_riesgo(señales_activas)
    imprimir_metricas('Núcleo + tendencia 12m', metricas(cartera_activa))
    for anio, g in cartera_activa.groupby('anio'):
        imprimir_metricas(f'  {anio}', metricas(g))

    pareado = pd.merge(cartera_rp[['mes', 'ret_neto_mes']], cartera_activa[['mes', 'ret_neto_mes']],
                        on='mes', suffixes=('_pasiva', '_activa'))
    excedente = (pareado['ret_neto_mes_activa'] - pareado['ret_neto_mes_pasiva']).to_numpy()
    lo, hi = bootstrap_bloques_media(excedente)
    print(f"\n  Excedente mensual (activa - pasiva): media={excedente.mean()*100:+.4f}%  "
          f"IC95%=[{lo*100:+.4f}%, {hi*100:+.4f}%]{'  <-- excluye cero' if not (lo <= 0 <= hi) else '  (no significativo)'}")


if __name__ == '__main__':
    main()
