"""
Turtle Trading System -- primera candidata de la nueva fase (metodos
usados por traders sistematicos reales, no hipotesis generadas desde
cero). Reproduccion fiel, con las 4 distinciones que pidio el usuario
explicitas:

1. ESTRATEGIA ORIGINAL: sistema de Richard Dennis & William Eckhardt
   (programa de entrenamiento "Turtles", 1983-1988), documentado
   publicamente en Curtis Faith, "Way of the Turtle" (2007) y Michael
   Covel, "The Complete TurtleTrader" (2007). Original: cartera
   diversificada de ~30+ mercados de futuros (materias primas,
   divisas, financieros, metales) con limites de "heat" de cartera
   por correlacion entre mercados.
2. REGLAS AUTOMATIZABLES (verificadas cruzando varias fuentes
   secundarias, con discrepancias menores declaradas abajo):
   - N = ATR de 20 dias (media exponencial del rango verdadero).
   - Sistema 1: entrada en ruptura del canal Donchian de 20 dias,
     salida en ruptura del canal Donchian de 10 dias en sentido
     contrario.
   - Sistema 2: entrada en ruptura de 55 dias, salida en ruptura de
     20 dias en sentido contrario.
   - Stop: 2N desde la entrada.
   - Piramidación: +1 unidad cada 0,5N a favor, hasta 4 unidades:
     se prueba CON y SIN piramidación, por separado, no se asume que
     una sea "la version correcta".
3. SIMPLIFICACIONES Y SU POSIBLE EFECTO (declaradas, no ocultas):
   - Sin limite de "heat" de cartera entre mercados correlacionados
     (USTEC/US500 se prueban independientes, cuando el sistema
     original los habria tratado como el mismo riesgo correlacionado
     y limitado la exposicion conjunta) -- podria SOBREESTIMAR el
     riesgo real de una cartera multi-mercado fiel.
   - Tamaño de posicion en R-multiplos (riesgo=2N=1R), no en %
     cuenta/valor de tick real -- equivalente en espiritu, pierde el
     mecanismo exacto de "1% arriesgado por unidad" en dinero real.
   - No se implementa el filtro de "saltar entrada tras ganadora
     anterior en el mismo canal" -- una fuente lo menciona, otras no
     lo confirman como regla original (ver busqueda), se omite en vez
     de inventar su existencia.
   - Se opera CFD (MetaQuotes-Demo) en vez de futuros reales -- mismo
     spread real ya usado en el proyecto, swap/financiacion no
     confirmados (igual disciplina que el resto del proyecto).
4. INFORMACION PERDIDA POR USAR SOLO OHLC: NINGUNA relevante -- los
   canales Donchian y el ATR son, por diseño, puramente funciones de
   OHLC. Es una de las pocas estrategias de este proyecto donde la
   limitacion de datos no aplica.

EVIDENCIA DEL TRACK RECORD ORIGINAL (distincion pedida explicitamente
por el usuario): las cifras de rentabilidad de los Turtles originales
(~80%/año compuesto citado en varios libros/articulos) son
PROMOCIONALES/ANECDOTICAS -- relatadas por los propios participantes y
popularizadas en libros, NO una cifra auditada de forma independiente
como un CTA regulado por NFA reportaria. El backtest de abajo NO
pretende replicar esa cifra (mercados, era y costes distintos) --
es una prueba de las REGLAS sobre nuestros datos actuales.
"""
import sys

import numpy as np
import pandas as pd

from orb_backtest import calcular_r_multiplos, metricas_en_r
from validacion_independiente_volexp import calcular_equity_simultanea, control_direccion_aleatoria
from datos_multiactivo import cargar_universo, UNIVERSO

SISTEMAS = {'S1': dict(entrada=20, salida=10), 'S2': dict(entrada=55, salida=20)}
PERIODO_N = 20
STOP_EN_N = 2.0
PASO_PIRAMIDE_N = 0.5
MAX_UNIDADES = 4
ESTRES_COSTE = [0.0, 1.0, 3.0]
SEED = 20261016


def calcular_n(d, periodo=PERIODO_N):
    hi, lo, cl_prev = d['High'], d['Low'], d['Close'].shift(1)
    tr = pd.concat([hi - lo, (hi - cl_prev).abs(), (lo - cl_prev).abs()], axis=1).max(axis=1)
    return tr.ewm(span=periodo, adjust=False).mean()


def canal_donchian(d, periodo):
    alto = d['High'].rolling(periodo).max().shift(1)
    bajo = d['Low'].rolling(periodo).min().shift(1)
    return alto, bajo


def ejecutar_sistema(d, entrada_dias, salida_dias, point, con_piramide):
    d = d.copy().reset_index(drop=True)
    d['N'] = calcular_n(d)
    d['canal_entrada_alto'], d['canal_entrada_bajo'] = canal_donchian(d, entrada_dias)
    d['canal_salida_alto'], d['canal_salida_bajo'] = canal_donchian(d, salida_dias)

    trades = []
    i = max(entrada_dias, PERIODO_N) + 1
    n_filas = len(d)
    while i < n_filas - 1:
        n_actual = d['N'].iloc[i]
        if pd.isna(n_actual) or n_actual <= 0 or pd.isna(d['canal_entrada_alto'].iloc[i]):
            i += 1
            continue

        direccion = None
        if d['Close'].iloc[i] > d['canal_entrada_alto'].iloc[i]:
            direccion = 'largo'
        elif d['Close'].iloc[i] < d['canal_entrada_bajo'].iloc[i]:
            direccion = 'corto'
        if direccion is None:
            i += 1
            continue

        idx_entrada = i + 1
        if idx_entrada >= n_filas:
            break
        precio_entrada_u1 = d['Open'].iloc[idx_entrada]
        n_entrada = n_actual
        unidades = [dict(precio=precio_entrada_u1, idx=idx_entrada)]
        stop = precio_entrada_u1 - STOP_EN_N * n_entrada if direccion == 'largo' else precio_entrada_u1 + STOP_EN_N * n_entrada

        idx_salida, motivo, resultado = None, None, None
        j = idx_entrada
        while j < n_filas:
            hi, lo, close_j = d['High'].iloc[j], d['Low'].iloc[j], d['Close'].iloc[j]
            toca_stop = (lo <= stop) if direccion == 'largo' else (hi >= stop)
            if toca_stop and j > idx_entrada:
                idx_salida, motivo, resultado = j, 'STOP', stop
                break
            canal_sal_alto, canal_sal_bajo = d['canal_salida_alto'].iloc[j], d['canal_salida_bajo'].iloc[j]
            toca_canal_salida = (close_j < canal_sal_bajo) if direccion == 'largo' else (close_j > canal_sal_alto)
            if toca_canal_salida and j > idx_entrada and pd.notna(canal_sal_bajo):
                idx_salida_real = min(j + 1, n_filas - 1)
                idx_salida, motivo, resultado = idx_salida_real, 'CANAL_SALIDA', d['Open'].iloc[idx_salida_real]
                break
            if con_piramide and len(unidades) < MAX_UNIDADES:
                ultimo_precio = unidades[-1]['precio']
                avance = (close_j - ultimo_precio) if direccion == 'largo' else (ultimo_precio - close_j)
                if avance >= PASO_PIRAMIDE_N * n_entrada:
                    nueva_unidad_precio = d['Open'].iloc[min(j + 1, n_filas - 1)]
                    unidades.append(dict(precio=nueva_unidad_precio, idx=j + 1))
                    stop = nueva_unidad_precio - STOP_EN_N * n_entrada if direccion == 'largo' else nueva_unidad_precio + STOP_EN_N * n_entrada
            j += 1
        if idx_salida is None:
            idx_salida, motivo, resultado = n_filas - 1, 'FIN_DATOS', d['Close'].iloc[-1]

        riesgo_por_unidad = STOP_EN_N * n_entrada
        rets = []
        for u in unidades:
            ret_u = (resultado - u['precio']) if direccion == 'largo' else (u['precio'] - resultado)
            rets.append(ret_u)
        ret_bruto_medio = np.mean(rets)
        spread_entrada = d['Spread'].iloc[idx_entrada] * point if pd.notna(d['Spread'].iloc[idx_entrada]) else 0.0

        trades.append(dict(
            dia=d['dia'].iloc[idx_entrada], anio=d['dia'].iloc[idx_entrada].year, direccion=direccion,
            idx_entrada=idx_entrada, idx_salida=idx_salida, precio_entrada=precio_entrada_u1,
            riesgo_puntos=riesgo_por_unidad, ret_bruto_puntos=ret_bruto_medio, spread_entrada_precio=spread_entrada,
            motivo_salida=motivo, n_unidades=len(unidades), peor_flotante_r=np.nan,
        ))
        i = idx_salida + 1
    return pd.DataFrame(trades)


def analizar(nombre_sistema, mercado, ops, point):
    print(f"\n######## Turtle {nombre_sistema} -- {mercado} ########")
    print(f"Operaciones: {len(ops)}")
    if len(ops) == 0:
        print("  SIN OPERACIONES.")
        return
    print(f"  Direccion: {ops['direccion'].value_counts().to_dict()}")
    print(f"  Motivo salida: {ops['motivo_salida'].value_counts().to_dict()}")
    print(f"  Unidades medias por operacion: {ops['n_unidades'].mean():.2f}")
    for extra in ESTRES_COSTE:
        etiqueta = "solo spread real" if extra == 0.0 else f"spread real + {extra:.0f} estres"
        ops_r = calcular_r_multiplos(ops, extra)
        m = metricas_en_r(ops_r)
        print(f"  [{etiqueta}] n={m['n']}  Media R={m['media_R']:+.4f}  PF={m['profit_factor']:.3f}  "
              f"%Acierto={m['pct_acierto']:.1f}%  Drawdown={m['max_drawdown_balance_R']:.2f}R")
        if extra == 0.0:
            for anio, g in ops_r.groupby('anio'):
                mg = metricas_en_r(g)
                print(f"      {anio}: n={mg['n']}  Media R={mg['media_R']:+.4f}  PF={mg['profit_factor']:.3f}")
    rng = np.random.default_rng(SEED)
    media_real, media_ctrl, std_ctrl, z = control_direccion_aleatoria(ops, rng)
    print(f"  Control direccion aleatoria: media real={media_real:+.4f}  media aleatoria={media_ctrl:+.4f}  z={z:+.2f}")


def main():
    mercados = ['XAUUSD', 'USTEC', 'US500', 'EURUSD', 'GBPUSD', 'USDJPY', 'USDCAD', 'USDCHF', 'USDSEK']
    universo = cargar_universo(mercados)
    for con_piramide in [False, True]:
        print(f"\n\n================ {'CON' if con_piramide else 'SIN'} PIRAMIDACION ================")
        for nombre_sis, cfg in SISTEMAS.items():
            for mercado in mercados:
                point = UNIVERSO[mercado]['point']
                ops = ejecutar_sistema(universo[mercado], cfg['entrada'], cfg['salida'], point, con_piramide)
                analizar(f"{nombre_sis} ({'piramide' if con_piramide else 'sin piramide'})", mercado, ops, point)


if __name__ == '__main__':
    main()
