"""
Motor de validacion independiente para Volatility Expansion Continuation
(XAUUSD) -- preparado para ejecutarse DIRECTAMENTE en cuanto haya
historico anterior a 2023 (mismo formato de CSV). NO modifica ninguna
regla de la estrategia congelada (señal, SL nominal, TP, cierre
forzoso a 5 dias siguen siendo exactamente los de
research/estrategia_volatilidad_expansion.py, commit 6873cc3) -- lo que
añade es una ejecucion mas realista de los COSTES/RIESGO/DRAWDOWN
alrededor de esas mismas reglas, pedida explicitamente para esta
validacion:

1. Exposicion y riesgo agregado de posiciones simultaneas (la
   estrategia original no impide solapamiento -- ya documentado).
2. Drawdown de EQUITY (marcado a mercado dia a dia, no solo al cierre).
3. Coste de swap/financiacion overnight -- NINGUN VALOR REAL confirmado
   para XAUUSD en este proyecto (distinto de US500/USTEC, donde si se
   confirmo via especificacion MT5 hace tiempo). Se trata EXCLUSIVAMENTE
   como escenario de estres etiquetado (puntos por noche de calendario
   mantenida), nunca como cifra real del broker.
4. Relleno de salida mas realista ante gaps: si el Open del dia de
   salida ya esta mas alla del SL nominal (gap real a traves del stop,
   ya detectado 1 vez de 33 en el periodo 2023-2026), el relleno pasa a
   ser ese Open (peor que el SL nominal) en vez de asumir ejecucion
   exacta en el SL -- permite R realizado por debajo de -1.0 cuando
   corresponda. La SEÑAL y el NIVEL del SL no cambian, solo el precio
   de relleno cuando la vela de salida ya gapeo mas alla.
5. Referencias de control: (A) misma fecha/riesgo, direccion aleatoria
   (ya usada en el ciclo de candidatas) -- aisla si la CONTINUACION
   (vs. aleatorio) aporta valor; (B) NUEVA -- dia de entrada aleatorio
   (no necesariamente un dia de expansion), mismo mecanismo de riesgo
   (SL en el extremo de la vela elegida, TP 2R, cierre a 5 dias) --
   aisla si elegir especificamente un DIA DE EXPANSION (vs. cualquier
   dia con el mismo tamaño de apuesta ligado a su propio rango) aporta
   valor, o si el resultado viene simplemente de estar expuesto al
   movimiento/volatilidad general del oro en este periodo.

Uso: main(ruta_csv) ejecuta todo sobre cualquier CSV con el mismo
formato ya usado en este proyecto. Se ejecuta primero sobre el propio
2023-2026 (para verificar que la metodologia de validacion no cambia el
resultado ya conocido salvo en los puntos declarados arriba) y despues,
sin tocar una linea, sobre el historico nuevo cuando llegue.
"""
import sys

import numpy as np
import pandas as pd

from orb_backtest import calcular_r_multiplos, metricas_en_r
from hipotesis_rsi2_sma200 import cargar_m15
from estrategia_gap_fade import agregar_diario_con_spread, calcular_atr_diario

UMBRAL_EXPANSION_ATR = 1.5
TP_EN_R = 2.0
DIAS_MAX_EN_MERCADO = 5
SWAP_ESTRES_PUNTOS_POR_NOCHE = [0.0, 0.5, 1.5]  # NO son valores reales del broker -- ver docstring
SEED = 20261016
REPETICIONES_CONTROL = 1000


def _riesgo_y_sl(row_señal, precio_entrada, direccion):
    if direccion == 'largo':
        sl = row_señal['Low']
        riesgo = precio_entrada - sl
        tp = precio_entrada + TP_EN_R * riesgo
    else:
        sl = row_señal['High']
        riesgo = sl - precio_entrada
        tp = precio_entrada - TP_EN_R * riesgo
    return sl, tp, riesgo


def _simular_salida_realista(d, idx_entrada, idx_fin, direccion, sl, tp):
    """Identica a la logica original (SL antes que TP en caso de empate),
    salvo que si el Open de la vela que dispara el SL ya habia gapeado
    mas alla del nivel nominal, el relleno es ese Open (R realizado puede
    superar -1.0), no el SL nominal."""
    for j in range(idx_entrada, idx_fin + 1):
        hi, lo, op = d['High'].iloc[j], d['Low'].iloc[j], d['Open'].iloc[j]
        if direccion == 'largo':
            gap_a_traves = op < sl
            toca_sl = lo <= sl
            toca_tp = hi >= tp
        else:
            gap_a_traves = op > sl
            toca_sl = hi >= sl
            toca_tp = lo <= tp
        if toca_sl:
            relleno = op if gap_a_traves else sl
            motivo = 'SL_GAP' if gap_a_traves else 'SL'
            return relleno, motivo, j
        if toca_tp:
            return tp, 'TP', j
    return d['Close'].iloc[idx_fin], 'CIERRE_PLAZO', idx_fin


def ejecutar_congelada_realista(diario, point):
    """Señal/SL/TP/cierre forzoso: IDENTICOS a estrategia_volatilidad_expansion.py.
    Unico cambio: relleno realista ante gap (punto 4). Devuelve tambien
    idx_entrada/idx_salida para poder construir la curva de equity."""
    d = diario.copy().reset_index(drop=True)
    d['atr14'] = calcular_atr_diario(d, periodo=14)
    d['atr14_prev'] = d['atr14'].shift(1)
    d['rango'] = d['High'] - d['Low']

    trades = []
    for i in range(1, len(d) - 1):
        row = d.iloc[i]
        if pd.isna(row['atr14_prev']) or row['atr14_prev'] <= 0:
            continue
        if row['rango'] <= UMBRAL_EXPANSION_ATR * row['atr14_prev']:
            continue

        direccion = 'largo' if row['Close'] > row['Open'] else 'corto'
        idx_entrada = i + 1
        precio_entrada = d['Open'].iloc[idx_entrada]
        sl, tp, riesgo = _riesgo_y_sl(row, precio_entrada, direccion)
        if riesgo <= 0:
            continue

        idx_fin = min(idx_entrada + DIAS_MAX_EN_MERCADO, len(d) - 1)
        resultado_precio, motivo, idx_salida = _simular_salida_realista(d, idx_entrada, idx_fin, direccion, sl, tp)

        ret_bruto = (resultado_precio - precio_entrada) if direccion == 'largo' else (precio_entrada - resultado_precio)
        spread_entrada = d['Spread'].iloc[idx_entrada] * point if pd.notna(d['Spread'].iloc[idx_entrada]) else 0.0
        noches = (d['dia'].iloc[idx_salida] - d['dia'].iloc[idx_entrada]).days

        trades.append(dict(
            dia=d['dia'].iloc[idx_entrada], anio=d['dia'].iloc[idx_entrada].year, direccion=direccion,
            idx_entrada=idx_entrada, idx_salida=idx_salida, precio_entrada=precio_entrada, riesgo_puntos=riesgo,
            ret_bruto_puntos=ret_bruto, spread_entrada_precio=spread_entrada, motivo_salida=motivo,
            noches_calendario=noches, peor_flotante_r=np.nan,
        ))

    return pd.DataFrame(trades), d


def calcular_equity_simultanea(ops, d):
    """Curva de equity dia a dia marcando a mercado TODAS las posiciones
    abiertas simultaneamente (no solo la ultima cerrada) -- punto 1 y 2."""
    nivel = np.zeros(len(d))
    max_simultaneas = np.zeros(len(d), dtype=int)
    trades = ops.to_dict('records')
    for j in range(len(d)):
        realizado, flotante, abiertas = 0.0, 0.0, 0
        for t in trades:
            close_s = d['Close'].iloc[t['idx_salida']]
            r_final = (close_s - t['precio_entrada']) / t['riesgo_puntos'] if t['direccion'] == 'largo' \
                else (t['precio_entrada'] - close_s) / t['riesgo_puntos']
            if t['idx_salida'] < j:
                realizado += np.clip(r_final, -3.0, TP_EN_R + 0.1)
            elif t['idx_entrada'] <= j <= t['idx_salida']:
                close_j = d['Close'].iloc[j]
                r = (close_j - t['precio_entrada']) / t['riesgo_puntos'] if t['direccion'] == 'largo' \
                    else (t['precio_entrada'] - close_j) / t['riesgo_puntos']
                flotante += r
                abiertas += 1
        nivel[j] = realizado + flotante
        max_simultaneas[j] = abiertas
    pico = np.maximum.accumulate(nivel)
    dd = pico - nivel
    return dict(max_drawdown_equity_R=dd.max(), dia_max_drawdown=d['dia'].iloc[np.argmax(dd)],
                max_posiciones_simultaneas=int(max_simultaneas.max()), curva_equity=nivel)


def sensibilidad_swap(ops):
    print("\n  Sensibilidad a swap/financiacion overnight (NO son valores reales del broker, "
          "solo estres etiquetado por noche de calendario mantenida):")
    for puntos_noche in SWAP_ESTRES_PUNTOS_POR_NOCHE:
        ops2 = ops.copy()
        coste_swap = ops2['noches_calendario'] * puntos_noche
        ops2['ret_bruto_puntos'] = ops2['ret_bruto_puntos'] - coste_swap
        ops_r = calcular_r_multiplos(ops2, 0.0)
        m = metricas_en_r(ops_r)
        etiqueta = "sin estres de swap" if puntos_noche == 0 else f"{puntos_noche} puntos/noche de estres"
        print(f"    {etiqueta}: Media R={m['media_R']:+.4f}  PF={m['profit_factor']:.3f}  "
              f"(noches medias mantenidas por operacion: {ops['noches_calendario'].mean():.1f})")


def control_direccion_aleatoria(ops, rng):
    riesgos = ops['riesgo_puntos'].to_numpy()
    ret_con_signo_mercado = ops['ret_bruto_puntos'].to_numpy() * np.where(ops['direccion'] == 'largo', 1, -1)
    spreads = ops['spread_entrada_precio'].to_numpy()
    medias = []
    for _ in range(REPETICIONES_CONTROL):
        direccion_aleatoria = rng.choice([1, -1], size=len(ops))
        ret_sim = ret_con_signo_mercado * direccion_aleatoria - spreads
        medias.append((ret_sim / riesgos).mean())
    medias = np.array(medias)
    media_real = calcular_r_multiplos(ops, 0.0)['R'].mean()
    z = (media_real - medias.mean()) / medias.std() if medias.std() > 0 else np.nan
    return media_real, medias.mean(), medias.std(), z


def control_dia_aleatorio(diario, point, n_trades_objetivo, rng):
    """Control B: dias de entrada ALEATORIOS (no necesariamente de
    expansion), mismo mecanismo de riesgo (SL en el extremo de la vela
    elegida, TP 2R, cierre a 5 dias) -- aisla si elegir un dia de
    EXPANSION especificamente aporta algo mas que simplemente apostar
    con el mismo tamaño de riesgo en dias cualquiera."""
    d = diario.copy().reset_index(drop=True)
    candidatos = list(range(1, len(d) - DIAS_MAX_EN_MERCADO - 2))
    medias = []
    for _ in range(REPETICIONES_CONTROL):
        elegidos = rng.choice(candidatos, size=min(n_trades_objetivo, len(candidatos)), replace=False)
        rs = []
        for i in elegidos:
            row = d.iloc[i]
            direccion = 'largo' if row['Close'] > row['Open'] else 'corto'
            idx_entrada = i + 1
            precio_entrada = d['Open'].iloc[idx_entrada]
            sl, tp, riesgo = _riesgo_y_sl(row, precio_entrada, direccion)
            if riesgo <= 0:
                continue
            idx_fin = min(idx_entrada + DIAS_MAX_EN_MERCADO, len(d) - 1)
            resultado, _, _ = _simular_salida_realista(d, idx_entrada, idx_fin, direccion, sl, tp)
            ret_bruto = (resultado - precio_entrada) if direccion == 'largo' else (precio_entrada - resultado)
            spread = d['Spread'].iloc[idx_entrada] * point if pd.notna(d['Spread'].iloc[idx_entrada]) else 0.0
            rs.append((ret_bruto - spread) / riesgo)
        if rs:
            medias.append(np.mean(rs))
    return np.array(medias)


def main(path, nombre='XAUUSD'):
    print(f"\n\n################ VALIDACION -- {nombre} ({path}) ################")
    df = cargar_m15(path)
    diario = agregar_diario_con_spread(df)
    ops, d = ejecutar_congelada_realista(diario, point=0.01)
    rng = np.random.default_rng(SEED)

    print(f"Operaciones: {len(ops)}")
    if len(ops) == 0:
        print("  SIN OPERACIONES -- no se puede validar en este historico.")
        return

    ops_r = calcular_r_multiplos(ops, 0.0)
    m = metricas_en_r(ops_r)
    print(f"\n--- Resultado (solo spread real, relleno realista ante gaps) ---")
    print(f"  n={m['n']}  Suma R={m['suma_R']:+.2f}  Media R={m['media_R']:+.4f}  "
          f"PF={m['profit_factor']:.3f}  %Acierto={m['pct_acierto']:.1f}%")
    for anio, g in ops_r.groupby('anio'):
        mg = metricas_en_r(g)
        print(f"    {anio}: n={mg['n']}  Media R={mg['media_R']:+.4f}  PF={mg['profit_factor']:.3f}")
    print("  Motivo de salida:", ops['motivo_salida'].value_counts().to_dict())
    n_gaps = (ops['motivo_salida'] == 'SL_GAP').sum()
    print(f"  Operaciones con gap real a traves del SL (R realizado < -1.0): {n_gaps}")
    if n_gaps > 0:
        peor = ops_r.loc[ops['motivo_salida'] == 'SL_GAP', :]
        peor_r = calcular_r_multiplos(peor, 0.0)
        print(f"    R realizado en esas operaciones: {peor_r['R'].tolist()}")

    eq = calcular_equity_simultanea(ops, d)
    print(f"\n--- Riesgo agregado y drawdown de equity ---")
    print(f"  Maximo de posiciones simultaneas abiertas: {eq['max_posiciones_simultaneas']} "
          f"(= {eq['max_posiciones_simultaneas']}R de riesgo agregado en el peor momento, "
          f"asumiendo 1R de riesgo por posicion)")
    print(f"  Drawdown de BALANCE (solo cierres secuenciales): {m['max_drawdown_balance_R']:.2f}R")
    print(f"  Drawdown de EQUITY (marcado a mercado, exposicion simultanea real): "
          f"{eq['max_drawdown_equity_R']:.2f}R  (el {eq['dia_max_drawdown'].date()})")

    sensibilidad_swap(ops)

    media_real, media_ctrl_a, std_ctrl_a, z_a = control_direccion_aleatoria(ops, rng)
    print(f"\n--- Control A: misma fecha/riesgo, DIRECCION aleatoria ({REPETICIONES_CONTROL} rep.) ---")
    print(f"  Media real={media_real:+.4f}  Media aleatoria={media_ctrl_a:+.4f} (std={std_ctrl_a:.4f})  z={z_a:+.2f}")

    medias_ctrl_b = control_dia_aleatorio(diario, 0.01, len(ops), rng)
    z_b = (media_real - medias_ctrl_b.mean()) / medias_ctrl_b.std() if medias_ctrl_b.std() > 0 else np.nan
    print(f"\n--- Control B: DIAS DE ENTRADA aleatorios (no necesariamente expansion), mismo mecanismo "
          f"de riesgo ({REPETICIONES_CONTROL} rep.) ---")
    print(f"  Media real={media_real:+.4f}  Media aleatoria={medias_ctrl_b.mean():+.4f} "
          f"(std={medias_ctrl_b.std():.4f})  z={z_b:+.2f}")
    print("  (si z_b es bajo, el resultado podria explicarse por el tamaño de apuesta ligado al "
          "rango diario en general, no por elegir especificamente dias de EXPANSION)")


if __name__ == '__main__':
    main(sys.argv[1], sys.argv[2] if len(sys.argv) > 2 else 'XAUUSD')
