"""
Hipotesis A: continuacion tras ruptura de rango M15(20).
Script de INVESTIGACION ESTADISTICA, no de trading. No genera senales de
entrada operativas, no define SL/TP, no es un EA.

Disciplina:
 - N=20 y horizontes {4,8,16} FIJOS, no se optimizan mirando resultados.
 - Cooldown GLOBAL de 16 velas compartido entre ambas direcciones.
 - Entrada en Open[t+1], nunca en Close[t] (evita lookahead doble).
 - Costes de spread/slippage son ESCENARIOS estimados, no mediciones exactas.
 - El script se detiene (assert/raise) ante errores graves de integridad.
"""
import sys
from datetime import timedelta

import numpy as np
import pandas as pd

N_RUPTURA = 20
HORIZONTES = [4, 8, 16]
COOLDOWN = 16
ATR_PERIODO = 14
SEED = 42
M_CONTROLES = 5
VENTANA_CONTROL_DIAS = 30
MAX_REUSOS_CONTROL = 2

ESCENARIOS_COSTE = {
    "bruto": 0.0,
    "optimista_spread0.15": 0.15,
    "conservador_spread0.30": 0.30,
    "conservador_mas_slippage0.45": 0.45,
}


# ----------------------------------------------------------------------------
# 1. Carga y verificacion basica (ya hecha antes, se repite aqui como guardia)
# ----------------------------------------------------------------------------
def cargar_y_verificar(path):
    df = pd.read_csv(path, sep=';', parse_dates=['TimestampServidor'],
                      date_format='%Y.%m.%d %H:%M:%S')
    df = df.reset_index(drop=True)

    assert df['TimestampServidor'].is_monotonic_increasing, \
        "ERROR GRAVE: timestamps no estrictamente crecientes"
    assert df['TimestampServidor'].duplicated().sum() == 0, \
        "ERROR GRAVE: timestamps duplicados"
    assert (df['High'] >= df[['Open', 'Close']].max(axis=1)).all(), \
        "ERROR GRAVE: High < max(Open,Close) en alguna fila"
    assert (df['Low'] <= df[['Open', 'Close']].min(axis=1)).all(), \
        "ERROR GRAVE: Low > min(Open,Close) en alguna fila"
    assert (df[['Open', 'High', 'Low', 'Close']] > 0).all().all(), \
        "ERROR GRAVE: precio <= 0 en alguna fila"

    print(f"[OK] Carga y verificacion basica: {len(df)} filas, "
          f"{df['TimestampServidor'].iloc[0]} -> {df['TimestampServidor'].iloc[-1]}")
    return df


# ----------------------------------------------------------------------------
# 2. Clasificacion de huecos (heuristica por duracion, declarada como tal)
# ----------------------------------------------------------------------------
def clasificar_huecos(df):
    diffs = df['TimestampServidor'].diff()
    es_hueco = diffs > timedelta(minutes=15)
    idx_huecos = df.index[es_hueco]

    registros = []
    for i in idx_huecos:
        t_prev = df['TimestampServidor'].iloc[i - 1]
        t_curr = df['TimestampServidor'].iloc[i]
        dur = t_curr - t_prev
        if dur <= timedelta(hours=2):
            categoria = 'cierre_diario'
        elif dur <= timedelta(hours=60):
            categoria = 'fin_de_semana'
        else:
            categoria = 'festivo_extendido'
        registros.append(dict(idx_antes=i - 1, idx_despues=i, t_inicio=t_prev,
                               t_fin=t_curr, duracion=dur, categoria=categoria))
    gaps = pd.DataFrame(registros)

    print("\n=== Clasificacion de huecos (heuristica por duracion, no exacta) ===")
    print(f"Huecos totales (>15 min): {len(gaps)}")
    if len(gaps):
        print(gaps['categoria'].value_counts())
        print("\nNota: 'cierre_diario' (<=2h) y 'fin_de_semana' (<=60h) son umbrales "
              "empiricos basados en la distribucion observada, no una regla de calendario "
              "exacta. 'festivo_extendido' agrupa cierres >60h (festivos que se fusionan "
              "con el fin de semana).")
    return gaps


def ventana_cruza_hueco(gaps, t_inicio, t_fin):
    """Devuelve la lista de categorias de huecos que caen dentro de [t_inicio, t_fin)."""
    if len(gaps) == 0:
        return []
    solapa = (gaps['t_inicio'] < t_fin) & (gaps['t_fin'] > t_inicio)
    return list(gaps.loc[solapa, 'categoria'])


# ----------------------------------------------------------------------------
# 3. ATR14 (Wilder, igual que iATR de MT5) sin lookahead
# ----------------------------------------------------------------------------
def calcular_atr(df, periodo=ATR_PERIODO):
    prev_close = df['Close'].shift(1)
    tr = pd.concat([
        df['High'] - df['Low'],
        (df['High'] - prev_close).abs(),
        (df['Low'] - prev_close).abs(),
    ], axis=1).max(axis=1)

    atr = tr.copy()
    atr.iloc[:periodo] = np.nan
    primer_valor = tr.iloc[1:periodo + 1].mean()  # primeras `periodo` TR validas (fila 0 no tiene prev_close)
    atr.iloc[periodo] = primer_valor
    for i in range(periodo + 1, len(df)):
        atr.iloc[i] = (atr.iloc[i - 1] * (periodo - 1) + tr.iloc[i]) / periodo
    atr.iloc[:periodo] = np.nan
    return atr


# ----------------------------------------------------------------------------
# 4. Deteccion de rupturas M15(20), sin lookahead
# ----------------------------------------------------------------------------
def detectar_rupturas(df):
    max_n = df['High'].shift(1).rolling(N_RUPTURA).max()
    min_n = df['Low'].shift(1).rolling(N_RUPTURA).min()

    alcista = df['Close'] > max_n
    bajista = df['Close'] < min_n
    alcista = alcista.fillna(False)
    bajista = bajista.fillna(False)

    # --- comprobacion de integridad: recalculo manual en 20 indices aleatorios ---
    rng = np.random.default_rng(SEED)
    idx_validos = df.index[(df.index >= N_RUPTURA) & (df.index < len(df) - 1)]
    muestra = rng.choice(idx_validos, size=min(20, len(idx_validos)), replace=False)
    for i in muestra:
        manual_max = df['High'].iloc[i - N_RUPTURA:i].max()
        manual_min = df['Low'].iloc[i - N_RUPTURA:i].min()
        assert np.isclose(manual_max, max_n.iloc[i]), \
            f"ERROR GRAVE: MaxN no coincide en idx {i} (lookahead o desalineacion de ventana)"
        assert np.isclose(manual_min, min_n.iloc[i]), \
            f"ERROR GRAVE: MinN no coincide en idx {i}"
    print(f"[OK] Verificacion de ventana rodante MaxN/MinN contra calculo manual "
          f"en {len(muestra)} indices aleatorios")

    print(f"\n=== Rupturas crudas detectadas (N={N_RUPTURA}, antes de cooldown) ===")
    print(f"Alcistas: {alcista.sum()}  Bajistas: {bajista.sum()}  Total: {alcista.sum() + bajista.sum()}")

    return alcista, bajista


# ----------------------------------------------------------------------------
# 5. Cooldown global (comparte alcistas y bajistas)
# ----------------------------------------------------------------------------
def aplicar_cooldown_global(df, alcista, bajista):
    eventos = []
    for i in df.index[alcista]:
        eventos.append((i, 'alcista'))
    for i in df.index[bajista]:
        eventos.append((i, 'bajista'))
    eventos.sort(key=lambda x: x[0])

    retenidos = []
    proximo_permitido = -1
    descartados_por_cooldown = 0
    for idx, direccion in eventos:
        if idx >= proximo_permitido:
            retenidos.append((idx, direccion))
            proximo_permitido = idx + COOLDOWN
        else:
            descartados_por_cooldown += 1

    print(f"\n=== Cooldown global de {COOLDOWN} velas (compartido entre direcciones) ===")
    print(f"Senales crudas totales: {len(eventos)}")
    print(f"Descartadas por cooldown: {descartados_por_cooldown}")
    print(f"Senales retenidas: {len(retenidos)}")

    # --- comprobacion de integridad: ninguna senal retenida solapa con la anterior ---
    for j in range(1, len(retenidos)):
        assert retenidos[j][0] - retenidos[j - 1][0] >= COOLDOWN, \
            f"ERROR GRAVE: solapamiento de cooldown entre indices {retenidos[j-1][0]} y {retenidos[j][0]}"
    print(f"[OK] Verificacion de no-solapamiento entre las {len(retenidos)} senales retenidas")

    return retenidos


# ----------------------------------------------------------------------------
# 6. Calculo de retornos (bruto, neto por escenario, ATR, tiempo real)
# ----------------------------------------------------------------------------
def calcular_retornos_senales(df, atr, retenidos, gaps):
    n = len(df)
    filas = []
    descartadas_por_borde = 0

    for idx, direccion in retenidos:
        idx_entrada = idx + 1
        if idx_entrada >= n:
            descartadas_por_borde += 1
            continue

        atr_t = atr.iloc[idx]
        if pd.isna(atr_t) or atr_t <= 0:
            descartadas_por_borde += 1
            continue

        precio_entrada = df['Open'].iloc[idx_entrada]
        t_entrada = df['TimestampServidor'].iloc[idx_entrada]

        fila = dict(idx_senal=idx, direccion=direccion, t_senal=df['TimestampServidor'].iloc[idx],
                    t_entrada=t_entrada, precio_entrada=precio_entrada, atr=atr_t)

        incompleta = False
        for k in HORIZONTES:
            idx_salida = idx + k
            if idx_salida >= n:
                incompleta = True
                fila[f'retorno_precio_{k}'] = np.nan
                fila[f'retorno_atr_{k}'] = np.nan
                fila[f'tiempo_real_min_{k}'] = np.nan
                fila[f'huecos_cruzados_{k}'] = None
                continue

            precio_salida = df['Close'].iloc[idx_salida]
            t_salida = df['TimestampServidor'].iloc[idx_salida] + timedelta(minutes=15)

            if direccion == 'alcista':
                ret_precio = precio_salida - precio_entrada
            else:
                ret_precio = precio_entrada - precio_salida

            fila[f'retorno_precio_{k}'] = ret_precio
            fila[f'retorno_atr_{k}'] = ret_precio / atr_t
            fila[f'tiempo_real_min_{k}'] = (t_salida - t_entrada).total_seconds() / 60.0
            fila[f'huecos_cruzados_{k}'] = tuple(sorted(set(ventana_cruza_hueco(gaps, t_entrada, t_salida))))

        if incompleta:
            descartadas_por_borde += 1
            continue

        # Hueco en la propia ventana de lookback (20 velas previas a la senal)
        t_inicio_lookback = df['TimestampServidor'].iloc[max(0, idx - N_RUPTURA)]
        t_fin_lookback = df['TimestampServidor'].iloc[idx]
        fila['hueco_en_lookback'] = len(ventana_cruza_hueco(gaps, t_inicio_lookback, t_fin_lookback)) > 0

        filas.append(fila)

    print(f"\n=== Retornos calculados ===")
    print(f"Senales con horizonte 16 incompleto (fin de la serie) o ATR invalido, descartadas: {descartadas_por_borde}")
    print(f"Senales con retornos completos usadas en el analisis: {len(filas)}")

    res = pd.DataFrame(filas)
    if len(res):
        res['anio'] = res['t_senal'].dt.year
        res['hora_entrada'] = res['t_entrada'].dt.hour
    return res


# ----------------------------------------------------------------------------
# 7. Controles emparejados (direccion + hora de servidor, sin ruptura activa)
# ----------------------------------------------------------------------------
def construir_controles(df, atr, alcista, bajista, señales_df, seed=SEED):
    rng = np.random.default_rng(seed)
    n = len(df)
    es_ruptura = (alcista | bajista).values
    hora_bar = df['TimestampServidor'].dt.hour.values
    fecha_bar = df['TimestampServidor'].values  # datetime64[ns]

    uso_control = {}
    filas = []

    ventana_ns = np.timedelta64(VENTANA_CONTROL_DIAS, 'D')

    for _, s in señales_df.iterrows():
        idx = s['idx_senal']
        hora_objetivo = s['hora_entrada']
        fecha_objetivo = np.datetime64(s['t_senal'])

        candidatos = np.where(
            (hora_bar == hora_objetivo) &
            (~es_ruptura) &
            (np.arange(n) + max(HORIZONTES) < n) &
            (np.arange(n) + 1 < n) &
            (np.abs(fecha_bar - fecha_objetivo) <= ventana_ns)
        )[0]

        candidatos = [c for c in candidatos if uso_control.get(c, 0) < MAX_REUSOS_CONTROL
                      and not pd.isna(atr.iloc[c]) and atr.iloc[c] > 0]

        if len(candidatos) == 0:
            continue

        elegidos = rng.choice(candidatos, size=min(M_CONTROLES, len(candidatos)), replace=False)

        for c in elegidos:
            uso_control[c] = uso_control.get(c, 0) + 1
            idx_entrada = c + 1
            precio_entrada = df['Open'].iloc[idx_entrada]
            atr_c = atr.iloc[c]
            fila = dict(idx_senal_origen=idx, idx_control=c, direccion=s['direccion'])
            for k in HORIZONTES:
                idx_salida = c + k
                precio_salida = df['Close'].iloc[idx_salida]
                if s['direccion'] == 'alcista':
                    ret_precio = precio_salida - precio_entrada
                else:
                    ret_precio = precio_entrada - precio_salida
                fila[f'retorno_precio_{k}'] = ret_precio
                fila[f'retorno_atr_{k}'] = ret_precio / atr_c
            filas.append(fila)

    controles = pd.DataFrame(filas)
    print(f"\n=== Controles emparejados ===")
    print(f"Controles generados: {len(controles)} (objetivo {M_CONTROLES} por senal, "
          f"{len(señales_df)} senales -> hasta {len(señales_df) * M_CONTROLES} posibles)")
    print(f"Puntos de control distintos usados: {len(uso_control)}")
    reutilizados = sum(1 for v in uso_control.values() if v > 1)
    print(f"Puntos de control reutilizados mas de una vez (maximo permitido {MAX_REUSOS_CONTROL}): {reutilizados}")
    return controles


# ----------------------------------------------------------------------------
# 8. Coste neto por escenario
# ----------------------------------------------------------------------------
def aplicar_escenarios_coste(df_retornos, prefijo='retorno_precio_'):
    for nombre, coste in ESCENARIOS_COSTE.items():
        for k in HORIZONTES:
            col_bruto = f'{prefijo}{k}'
            if col_bruto in df_retornos.columns:
                df_retornos[f'neto_{nombre}_{k}'] = df_retornos[col_bruto] - coste
    return df_retornos


# ----------------------------------------------------------------------------
# 9. Resumen estadistico
# ----------------------------------------------------------------------------
def resumen(nombre, sub, controles_sub=None):
    print(f"\n--- {nombre} (n={len(sub)}) ---")
    if len(sub) == 0:
        print("  (sin senales en este corte)")
        return
    for k in HORIZONTES:
        col = f'retorno_precio_{k}'
        colatr = f'retorno_atr_{k}'
        vals = sub[col].dropna()
        valsatr = sub[colatr].dropna()
        if len(vals) == 0:
            continue
        pos = (vals > 0).mean() * 100
        print(f"  k={k:>2}: n={len(vals):>4}  %positivos={pos:5.1f}%  "
              f"media_precio={vals.mean():7.3f}  mediana_precio={vals.median():7.3f}  "
              f"media_ATR={valsatr.mean():6.3f}  mediana_ATR={valsatr.median():6.3f}  "
              f"std_ATR={valsatr.std():6.3f}")
        for nombre_esc in ESCENARIOS_COSTE:
            if nombre_esc == 'bruto':
                continue
            colneto = f'neto_{nombre_esc}_{k}'
            if colneto in sub.columns:
                valsneto = sub[colneto].dropna()
                pos_neto = (valsneto > 0).mean() * 100
                print(f"         neto[{nombre_esc:<28}]: %positivos={pos_neto:5.1f}%  "
                      f"media={valsneto.mean():7.3f}  mediana={valsneto.median():7.3f}")

        tcol = f'tiempo_real_min_{k}'
        if tcol in sub.columns:
            t = sub[tcol].dropna()
            nominal = k * 15
            exceso = t - nominal
            print(f"         tiempo real (min): nominal={nominal}  media={t.mean():.1f}  "
                  f"mediana={t.median():.1f}  max={t.max():.1f}  "
                  f"ventanas con exceso>30min={(exceso > 30).sum()}")

        if controles_sub is not None and len(controles_sub):
            cvals = controles_sub[colatr].dropna() if colatr in controles_sub.columns else pd.Series(dtype=float)
            if len(cvals):
                print(f"         CONTROL  k={k}: n={len(cvals):>4}  "
                      f"media_ATR={cvals.mean():6.3f}  mediana_ATR={cvals.median():6.3f}  "
                      f"(diff señal-control media_ATR = {valsatr.mean() - cvals.mean():+.3f})")


def main(path):
    df = cargar_y_verificar(path)
    gaps = clasificar_huecos(df)
    atr = calcular_atr(df)
    alcista, bajista = detectar_rupturas(df)
    retenidos = aplicar_cooldown_global(df, alcista, bajista)
    señales = calcular_retornos_senales(df, atr, retenidos, gaps)

    assert señales['idx_senal'].is_monotonic_increasing, "ERROR GRAVE: senales no ordenadas tras el pipeline"
    assert (señales['t_entrada'] > señales['t_senal']).all(), \
        "ERROR GRAVE: alguna entrada no es posterior a la senal (posible lookahead)"
    print("\n[OK] Verificacion final: todas las entradas son posteriores a su senal, orden correcto")

    señales = aplicar_escenarios_coste(señales)

    controles = construir_controles(df, atr, alcista, bajista, señales)

    print("\n\n################ INFORME POR PERIODO ################")

    print("\n### Huecos en ventana de lookback (posible contaminacion de MaxN/MinU por fin de semana) ###")
    print(f"Senales cuya ventana de 20 velas previas cruza algun hueco: "
          f"{señales['hueco_en_lookback'].sum()} de {len(señales)}")

    print("\n### Huecos en la ventana de medicion (horizonte 16) ###")
    cruces16 = señales['huecos_cruzados_16'].value_counts()
    print(cruces16)

    periodos = {
        'ROBUSTEZ HISTORICA (2023-2024, nunca explorado antes)': (2023, 2024),
        'EXPLORATORIO YA QUEMADO (2025 + 2026 hasta hoy, usado por H1-H3)': (2025, 2026),
    }

    for nombre_periodo, (a1, a2) in periodos.items():
        sub = señales[(señales['anio'] >= a1) & (señales['anio'] <= a2)]
        sub_idx = set(sub['idx_senal'])
        controles_sub = controles[controles['idx_senal_origen'].isin(sub_idx)]

        print(f"\n\n========== {nombre_periodo} ==========")
        resumen("TODAS", sub, controles_sub)
        resumen("ALCISTAS", sub[sub['direccion'] == 'alcista'],
                controles_sub[controles_sub['direccion'] == 'alcista'])
        resumen("BAJISTAS", sub[sub['direccion'] == 'bajista'],
                controles_sub[controles_sub['direccion'] == 'bajista'])

    print("\n\n### VALIDACION PROSPECTIVA FUTURA ###")
    print("No disponible todavia: requeriria datos posteriores al momento de congelar esta "
          "metodologia (hoy). Los resultados de 2023-2026 NO deben interpretarse como validacion "
          "de que la ruptura M15(20) tiene ventaja predictiva; son, como mucho, hallazgos "
          "exploratorios e historicos.")

    return señales, controles, gaps


if __name__ == '__main__':
    main(sys.argv[1])
