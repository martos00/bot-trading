"""
FX Carry Trade -- familia pospuesta por falta de datos, ahora
desbloqueada con tipos de interes reales de FRED
(research/datos_externos/tipos_interes.csv, ver
research/descargar_fred_tipos.py). Fundamento academico: "forward
premium puzzle"/desviacion de la paridad de interes descubierta --
las divisas de tipo de interes alto tienden a NO depreciarse lo
suficiente para compensar el diferencial, dejando un exceso de
retorno sistematico (Jurek; Burnside-Eichenbaum-Kleshchelski-Rebelo;
Lustig-Verdelhan) -- ya documentado en la comparacion de 5 estrategias
de este proyecto, antes sin datos para programarlo.

REGLAS (unica version, pre-registrada, sin optimizar):
 - Diferencial de carry (mensual, causal -- usa el tipo de interes
   conocido al CIERRE del mes anterior, nunca el del propio mes en
   curso): para EURUSD/GBPUSD, diff = r_EUR(o r_GBP) - r_USD; para
   USDJPY/USDCAD/USDCHF/USDSEK, diff = r_USD - r_JPY(o r_CAD/CHF/SEK)
   -- en ambos casos, diff>0 significa "la divisa que se compra en
   LARGO de este par rinde mas que la otra".
 - Posicion: signo(diff) escalado por volatilidad inversa (mismo
   mecanismo de vol-targeting 10% anualizado que TSMOM, para que sea
   comparable con el resto de estrategias multi-activo de este
   proyecto).
 - Rebalanceo mensual, mismo coste de spread real que TSMOM/momentum
   transversal. Cartera = media de los 6 pares con señal valida.
 - Control: mismo mecanismo con el signo del diferencial invertido
   aleatoriamente cada mes.
"""
import numpy as np
import pandas as pd

from datos_multiactivo import cargar_universo, UNIVERSO
from estrategia_tsmom import preparar_activo, fin_de_mes, VOL_OBJETIVO, LIMITE_POSICION, metricas_cartera

PARES = {
    'EURUSD': ('EUR', 'USD'), 'GBPUSD': ('GBP', 'USD'),
    'USDJPY': ('USD', 'JPY'), 'USDCAD': ('USD', 'CAD'),
    'USDCHF': ('USD', 'CHF'), 'USDSEK': ('USD', 'SEK'),
}
RUTA_TIPOS = 'datos_externos/tipos_interes.csv'
SEED = 20261015
REPETICIONES_CONTROL = 1000


def cargar_tipos():
    t = pd.read_csv(RUTA_TIPOS)
    t['anio_mes'] = pd.PeriodIndex(t['anio_mes'], freq='M')
    return t.set_index('anio_mes')


def construir_señales_carry(universo_preparado, tipos):
    señales = {}
    for par, (base, cotizada) in PARES.items():
        d = universo_preparado[par]
        point = UNIVERSO[par]['point']
        idx_fin_mes = fin_de_mes(d)
        filas = []
        for pos, idx in enumerate(idx_fin_mes[:-1]):
            vol = d['vol_60d_anualizada'].iloc[idx]
            if pd.isna(vol) or vol <= 0:
                continue
            mes_actual = d['anio_mes'].iloc[idx]
            mes_anterior = mes_actual - 1
            if mes_anterior not in tipos.index or base not in tipos.columns or cotizada not in tipos.columns:
                continue
            r_base, r_cotizada = tipos.loc[mes_anterior, base], tipos.loc[mes_anterior, cotizada]
            if pd.isna(r_base) or pd.isna(r_cotizada):
                continue
            diff = r_base - r_cotizada
            if diff == 0:
                continue
            signo = np.sign(diff)
            tamano = np.clip(signo * (VOL_OBJETIVO / vol), -LIMITE_POSICION, LIMITE_POSICION)

            idx_fin_siguiente = idx_fin_mes[pos + 1]
            ret_mes_siguiente = d['Close'].iloc[idx_fin_siguiente] / d['Close'].iloc[idx] - 1.0
            spread_precio = d['Spread'].iloc[idx] * point if pd.notna(d['Spread'].iloc[idx]) else 0.0
            coste_frac = (spread_precio / d['Close'].iloc[idx]) * abs(tamano)
            filas.append(dict(mes=d['anio_mes'].iloc[idx_fin_siguiente], anio=d['dia'].iloc[idx_fin_siguiente].year,
                               diff_tipos=diff, tamano_posicion=tamano, ret_bruto_mes=tamano * ret_mes_siguiente,
                               coste_frac=coste_frac, ret_neto_mes=tamano * ret_mes_siguiente - coste_frac))
        señales[par] = pd.DataFrame(filas)
    return señales


def cartera_mensual(señales):
    todas = pd.concat([df.assign(activo=n) for n, df in señales.items() if len(df) > 0], ignore_index=True)
    cartera = todas.groupby('mes').agg(ret_neto_mes=('ret_neto_mes', 'mean'), n_pares=('activo', 'nunique')).reset_index()
    cartera['anio'] = cartera['mes'].apply(lambda p: p.year)
    return cartera.sort_values('mes').reset_index(drop=True)


def control_signo_aleatorio(señales, rng):
    medias = []
    for _ in range(REPETICIONES_CONTROL):
        copia = {}
        for n, df in señales.items():
            if len(df) == 0:
                continue
            df2 = df.copy()
            signo_aleatorio = rng.choice([-1, 1], size=len(df2))
            ret_puro = df2['ret_bruto_mes'] / df2['tamano_posicion']
            tamano_aleatorio = df2['tamano_posicion'].abs() * signo_aleatorio
            df2['ret_neto_mes'] = tamano_aleatorio * ret_puro - df2['coste_frac']
            copia[n] = df2
        medias.append(cartera_mensual(copia)['ret_neto_mes'].mean())
    return np.array(medias)


def main():
    tipos = cargar_tipos()
    universo = cargar_universo(list(PARES.keys()))
    universo_preparado = {n: preparar_activo(d, UNIVERSO[n]['point']) for n, d in universo.items()}
    señales = construir_señales_carry(universo_preparado, tipos)

    print("################ FX Carry Trade ################")
    for par, df in señales.items():
        if len(df) == 0:
            print(f"  {par}: sin señales validas")
            continue
        print(f"  {par}: n={len(df)}  %largo={ (df['tamano_posicion']>0).mean()*100:.0f}%  "
              f"media mensual neta={df['ret_neto_mes'].mean()*100:+.3f}%")

    cartera = cartera_mensual(señales)
    m = metricas_cartera(cartera)
    print(f"\nMeses evaluables: {m['n_meses']}")
    if m['n_meses'] == 0:
        return
    print(f"  Retorno anualizado: {m['ret_anualizado']*100:+.2f}%  Vol.anualizada: {m['vol_anualizada']*100:.2f}%  "
          f"Sharpe: {m['sharpe']:.3f}  MaxDD: {m['max_drawdown']*100:.2f}%  %Meses+: {m['pct_meses_positivos']:.1f}%")
    for anio, g in cartera.groupby('anio'):
        mg = metricas_cartera(g)
        print(f"    {anio}: n={mg['n_meses']}  Ret.año={mg['ret_acumulado']*100:+.2f}%  Sharpe={mg['sharpe']:.3f}")

    rng = np.random.default_rng(SEED)
    medias_control = control_signo_aleatorio(señales, rng)
    media_real = cartera['ret_neto_mes'].mean()
    z = (media_real - medias_control.mean()) / medias_control.std() if medias_control.std() > 0 else np.nan
    print(f"\n  Control signo aleatorio ({REPETICIONES_CONTROL} rep.): media real={media_real*100:+.4f}%/mes  "
          f"media aleatoria={medias_control.mean()*100:+.4f}%/mes  z={z:+.2f}")


if __name__ == '__main__':
    main()
