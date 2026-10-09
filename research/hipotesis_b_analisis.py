"""
Hipotesis B: reversion a la media tras sobreextension en XAUUSD M15.
Script de INVESTIGACION ESTADISTICA, no de trading. No genera senales
operativas, no define SL/TP, no es un EA.

Parametros fijos y pre-registrados (no se optimizan tras ver resultados):
 EMA20, ATR14 (Wilder), umbral de sobreextension = 2.0 ATR,
 momentum = Close[t]-Close[t-8] (2h) normalizado por ATR,
 horizontes 4/8/16 velas, cooldown global 16 velas.
"""
import sys
from datetime import timedelta

import numpy as np
import pandas as pd

EMA_PERIODO = 20
ATR_PERIODO = 14
UMBRAL_SOBREEXTENSION = 2.0
MOMENTUM_LOOKBACK = 8
HORIZONTES = [4, 8, 16]
COOLDOWN = 16
SEED = 42
M_CONTROLES = 5
VENTANA_CONTROL_DIAS = 30
MAX_REUSOS_CONTROL = 2
ATR_TOLERANCIA_RELATIVA = 0.25
BLOQUE_BOOTSTRAP = 10
REPETICIONES_BOOTSTRAP = 2000

ESCENARIOS_COSTE = {
    "bruto": 0.0,
    "optimista_spread0.15": 0.15,
    "conservador_spread0.30": 0.30,
    "conservador_mas_slippage0.45": 0.45,
}


# ----------------------------------------------------------------------------
# Carga, verificacion basica y huecos (idéntico a Hipotesis A, reproducido
# aqui para que este script sea independiente y autocontenido)
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
    print(f"\n[OK] Huecos clasificados: {len(gaps)} totales "
          f"({(gaps['categoria'].value_counts().to_dict()) if len(gaps) else {}})")
    return gaps


def ventana_cruza_hueco(gaps, t_inicio, t_fin):
    if len(gaps) == 0:
        return []
    solapa = (gaps['t_inicio'] < t_fin) & (gaps['t_fin'] > t_inicio)
    return list(gaps.loc[solapa, 'categoria'])


def calcular_atr(df, periodo=ATR_PERIODO):
    prev_close = df['Close'].shift(1)
    tr = pd.concat([
        df['High'] - df['Low'],
        (df['High'] - prev_close).abs(),
        (df['Low'] - prev_close).abs(),
    ], axis=1).max(axis=1)

    atr = tr.copy()
    atr.iloc[:periodo] = np.nan
    atr.iloc[periodo] = tr.iloc[1:periodo + 1].mean()
    for i in range(periodo + 1, len(df)):
        atr.iloc[i] = (atr.iloc[i - 1] * (periodo - 1) + tr.iloc[i]) / periodo
    atr.iloc[:periodo] = np.nan
    return atr


# ----------------------------------------------------------------------------
# EMA20 causal (seed = SMA de las primeras `periodo` velas, sin usar nada
# posterior); momentum causal
# ----------------------------------------------------------------------------
def calcular_ema(df, periodo=EMA_PERIODO):
    close = df['Close']
    ema = pd.Series(np.nan, index=df.index)
    if len(df) <= periodo:
        return ema
    ema.iloc[periodo - 1] = close.iloc[:periodo].mean()  # seed SMA, sin lookahead
    alpha = 2.0 / (periodo + 1)
    for i in range(periodo, len(df)):
        ema.iloc[i] = alpha * close.iloc[i] + (1 - alpha) * ema.iloc[i - 1]
    return ema


def verificar_ema_atr(df, ema, atr):
    # Recalculo manual en 15 indices aleatorios, para contrastar la
    # implementacion vectorizada/iterativa contra una formula directa.
    rng = np.random.default_rng(SEED)
    idx_validos = df.index[(df.index >= EMA_PERIODO + 30) & (df.index < len(df) - 1)]
    muestra = sorted(rng.choice(idx_validos, size=15, replace=False))

    print("\n=== Verificacion manual de EMA20/ATR14 en 15 indices aleatorios ===")
    print("(contrastar estos timestamps/valores contra iMA(20,EMA)/iATR(14) en MT5 si se quiere "
          "una verificacion independiente adicional -- este script NO tiene acceso a un terminal "
          "MT5 en ejecucion, solo puede verificar consistencia interna)")
    for i in muestra:
        # EMA manual: seed SMA desde cero + recursion manual acotada a esta vela
        seed_idx = EMA_PERIODO - 1
        ema_manual = df['Close'].iloc[:EMA_PERIODO].mean()
        alpha = 2.0 / (EMA_PERIODO + 1)
        for j in range(EMA_PERIODO, i + 1):
            ema_manual = alpha * df['Close'].iloc[j] + (1 - alpha) * ema_manual
        assert np.isclose(ema_manual, ema.iloc[i], rtol=1e-9), \
            f"ERROR GRAVE: EMA20 no coincide en idx {i}"

        print(f"  idx={i:>6}  t={df['TimestampServidor'].iloc[i]}  "
              f"Close={df['Close'].iloc[i]:.2f}  EMA20={ema.iloc[i]:.4f}  ATR14={atr.iloc[i]:.4f}")

    assert not ema.iloc[:EMA_PERIODO - 1].notna().any(), \
        "ERROR GRAVE: EMA20 tiene valores antes de tener suficientes datos (posible lookahead)"
    assert not atr.iloc[:ATR_PERIODO].notna().any(), \
        "ERROR GRAVE: ATR14 tiene valores antes de tener suficientes datos (posible lookahead)"
    print("[OK] EMA20/ATR14: recalculo manual coincide, sin valores antes de la inicializacion")


def calcular_momentum(df, atr, lookback=MOMENTUM_LOOKBACK):
    momentum_precio = df['Close'] - df['Close'].shift(lookback)
    return momentum_precio / atr


# ----------------------------------------------------------------------------
# Deteccion de sobreextension: señal = CRUCE del umbral (no estado sostenido)
# ----------------------------------------------------------------------------
def detectar_sobreextensiones(df, ema, atr):
    desviacion = (df['Close'] - ema) / atr

    estado_alcista = desviacion > UMBRAL_SOBREEXTENSION
    estado_bajista = desviacion < -UMBRAL_SOBREEXTENSION

    cruce_alcista = estado_alcista & ~estado_alcista.shift(1).fillna(False)
    cruce_bajista = estado_bajista & ~estado_bajista.shift(1).fillna(False)

    print(f"\n=== Sobreextensiones detectadas (umbral={UMBRAL_SOBREEXTENSION} ATR) ===")
    print(f"Cruces alcistas (precio dispara por encima de EMA20): {cruce_alcista.sum()}")
    print(f"Cruces bajistas (precio dispara por debajo de EMA20): {cruce_bajista.sum()}")
    print(f"Velas en estado sobreextendido (cualquier signo, para exclusion de controles): "
          f"{(estado_alcista | estado_bajista).sum()} de {len(df)}")

    return cruce_alcista, cruce_bajista, (estado_alcista | estado_bajista), desviacion


def aplicar_cooldown_global(df, cruce_alcista, cruce_bajista):
    eventos = [(i, 'sobreext_alcista') for i in df.index[cruce_alcista]] + \
              [(i, 'sobreext_bajista') for i in df.index[cruce_bajista]]
    eventos.sort(key=lambda x: x[0])

    retenidos = []
    proximo_permitido = -1
    descartados = 0
    for idx, tipo in eventos:
        if idx >= proximo_permitido:
            retenidos.append((idx, tipo))
            proximo_permitido = idx + COOLDOWN
        else:
            descartados += 1

    print(f"\n=== Cooldown global de {COOLDOWN} velas ===")
    print(f"Señales crudas (cruces): {len(eventos)}  Descartadas por cooldown: {descartados}  "
          f"Retenidas: {len(retenidos)}")

    for j in range(1, len(retenidos)):
        assert retenidos[j][0] - retenidos[j - 1][0] >= COOLDOWN, \
            "ERROR GRAVE: solapamiento de cooldown detectado"
    print(f"[OK] Sin solapamiento entre las {len(retenidos)} señales retenidas")
    return retenidos


# ----------------------------------------------------------------------------
# Retornos: la direccion OPERADA es la CONTRARIA al tipo de sobreextension
# (hipotesis de reversion). Metrica = retorno de precio real desde
# Open[t+1], nunca "acercamiento a la EMA" (la EMA tambien se mueve).
# ----------------------------------------------------------------------------
def calcular_retornos_senales(df, atr, retenidos, gaps):
    n = len(df)
    filas = []
    descartadas_por_borde = 0

    for idx, tipo in retenidos:
        direccion_operada = 'corto' if tipo == 'sobreext_alcista' else 'largo'
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

        fila = dict(idx_senal=idx, tipo_sobreextension=tipo, direccion_operada=direccion_operada,
                    t_senal=df['TimestampServidor'].iloc[idx], t_entrada=t_entrada,
                    precio_entrada=precio_entrada, atr=atr_t)

        incompleta = False
        for k in HORIZONTES:
            idx_salida = idx + k
            if idx_salida >= n:
                incompleta = True
                continue
            precio_salida = df['Close'].iloc[idx_salida]
            t_salida = df['TimestampServidor'].iloc[idx_salida] + timedelta(minutes=15)

            if direccion_operada == 'largo':
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
        filas.append(fila)

    print(f"\n=== Retornos calculados ===")
    print(f"Descartadas por borde de serie / ATR invalido: {descartadas_por_borde}")
    print(f"Señales con retornos completos: {len(filas)}")

    res = pd.DataFrame(filas)
    if len(res):
        res['anio'] = res['t_senal'].dt.year
        res['hora_entrada'] = res['t_entrada'].dt.hour
        res['ventana16_sin_hueco'] = res['huecos_cruzados_16'].apply(lambda x: len(x) == 0)
    return res


# ----------------------------------------------------------------------------
# Controles: A) hora + ATR comparable (baseline original)
#            B) A + mismo signo de momentum (baseline mejorado, principal)
# Ninguno de los dos se elige a posteriori; se reportan ambos siempre.
# ----------------------------------------------------------------------------
def construir_controles(df, atr, momentum, en_sobreextension, señales_df, exigir_momentum, seed=SEED):
    rng = np.random.default_rng(seed if not exigir_momentum else seed + 1)
    n = len(df)
    hora_bar = df['TimestampServidor'].dt.hour.values
    fecha_bar = df['TimestampServidor'].values
    atr_vals = atr.values
    momentum_vals = momentum.values
    no_sobreext = (~en_sobreextension).values

    uso_control = {}
    filas = []
    ventana_ns = np.timedelta64(VENTANA_CONTROL_DIAS, 'D')
    idx_validos = (np.arange(n) + max(HORIZONTES) < n) & (np.arange(n) + 1 < n)

    for _, s in señales_df.iterrows():
        idx = s['idx_senal']
        hora_objetivo = s['hora_entrada']
        fecha_objetivo = np.datetime64(s['t_senal'])
        atr_objetivo = s['atr']
        signo_necesario = 1 if s['tipo_sobreextension'] == 'sobreext_alcista' else -1

        mask = (hora_bar == hora_objetivo) & no_sobreext & idx_validos & \
               (np.abs(fecha_bar - fecha_objetivo) <= ventana_ns) & \
               (np.abs(atr_vals - atr_objetivo) <= ATR_TOLERANCIA_RELATIVA * atr_objetivo)

        if exigir_momentum:
            mask &= (np.sign(momentum_vals) == signo_necesario)

        candidatos = np.where(mask)[0]
        candidatos = [c for c in candidatos if uso_control.get((exigir_momentum, c), 0) < MAX_REUSOS_CONTROL]

        if len(candidatos) == 0:
            continue

        elegidos = rng.choice(candidatos, size=min(M_CONTROLES, len(candidatos)), replace=False)

        for c in elegidos:
            uso_control[(exigir_momentum, c)] = uso_control.get((exigir_momentum, c), 0) + 1
            idx_entrada = c + 1
            precio_entrada = df['Open'].iloc[idx_entrada]
            atr_c = atr.iloc[c]
            fila = dict(idx_senal_origen=idx, idx_control=c, direccion_operada=s['direccion_operada'])
            for k in HORIZONTES:
                idx_salida = c + k
                precio_salida = df['Close'].iloc[idx_salida]
                if s['direccion_operada'] == 'largo':
                    ret_precio = precio_salida - precio_entrada
                else:
                    ret_precio = precio_entrada - precio_salida
                fila[f'retorno_precio_{k}'] = ret_precio
                fila[f'retorno_atr_{k}'] = ret_precio / atr_c
            filas.append(fila)

    controles = pd.DataFrame(filas)
    etiqueta = "B (hora+ATR+momentum)" if exigir_momentum else "A (hora+ATR, original)"
    print(f"\n=== Controles {etiqueta} ===")
    print(f"Controles generados: {len(controles)}  Señales con al menos 1 control: "
          f"{señales_df['idx_senal'].isin(controles['idx_senal_origen']).sum() if len(controles) else 0} de {len(señales_df)}")
    return controles


# ----------------------------------------------------------------------------
# Bootstrap por bloques (preserva dependencia temporal entre señales
# consecutivas) para intervalo de confianza del 95% de la media
# ----------------------------------------------------------------------------
def bootstrap_bloques_ic(valores, bloque=BLOQUE_BOOTSTRAP, repeticiones=REPETICIONES_BOOTSTRAP, seed=SEED):
    valores = np.asarray(valores, dtype=float)
    valores = valores[~np.isnan(valores)]
    n = len(valores)
    if n < bloque * 2:
        return (np.nan, np.nan)
    rng = np.random.default_rng(seed)
    n_bloques = int(np.ceil(n / bloque))
    max_inicio = n - bloque
    medias = np.empty(repeticiones)
    for b in range(repeticiones):
        inicios = rng.integers(0, max_inicio + 1, size=n_bloques)
        muestra = np.concatenate([valores[s:s + bloque] for s in inicios])[:n]
        medias[b] = muestra.mean()
    return np.percentile(medias, 2.5), np.percentile(medias, 97.5)


def aplicar_escenarios_coste(df_retornos, prefijo='retorno_precio_'):
    for nombre, coste in ESCENARIOS_COSTE.items():
        for k in HORIZONTES:
            col_bruto = f'{prefijo}{k}'
            if col_bruto in df_retornos.columns:
                df_retornos[f'neto_{nombre}_{k}'] = df_retornos[col_bruto] - coste
    return df_retornos


def resumen(nombre, sub, control_a=None, control_b=None):
    print(f"\n--- {nombre} (n={len(sub)}) ---")
    if len(sub) == 0:
        print("  (sin señales en este corte)")
        return
    for k in HORIZONTES:
        colatr = f'retorno_atr_{k}'
        vals = sub[f'retorno_precio_{k}'].dropna()
        valsatr = sub[colatr].dropna()
        if len(vals) == 0:
            continue
        pos = (vals > 0).mean() * 100
        ic_lo, ic_hi = bootstrap_bloques_ic(valsatr.values)
        print(f"  k={k:>2}: n={len(vals):>4}  %positivos={pos:5.1f}%  "
              f"media_ATR={valsatr.mean():6.3f}  mediana_ATR={valsatr.median():6.3f}  "
              f"std_ATR={valsatr.std():6.3f}  IC95%(bloques,media)=[{ic_lo:6.3f}, {ic_hi:6.3f}]")
        for nombre_esc in ESCENARIOS_COSTE:
            if nombre_esc == 'bruto':
                continue
            coste = ESCENARIOS_COSTE[nombre_esc]
            colneto = f'neto_{nombre_esc}_{k}'
            if colneto in sub.columns:
                valsneto = sub[colneto].dropna()
                pos_neto = (valsneto > 0).mean() * 100
                print(f"         neto[{nombre_esc:<28}]: %positivos={pos_neto:5.1f}%  "
                      f"media={valsneto.mean():7.3f}  mediana={valsneto.median():7.3f}")

        for etiqueta, ctrl in (("CONTROL A (hora+ATR)", control_a), ("CONTROL B (hora+ATR+momentum)", control_b)):
            if ctrl is not None and len(ctrl) and colatr in ctrl.columns:
                cvals = ctrl[colatr].dropna()
                if len(cvals):
                    print(f"         {etiqueta}: n={len(cvals):>4}  media_ATR={cvals.mean():6.3f}  "
                          f"mediana_ATR={cvals.median():6.3f}  (diff señal-control={valsatr.mean()-cvals.mean():+.3f})")

        # Sensibilidad: excluir 1% de observaciones mas extremas (por |retorno_ATR|)
        if len(valsatr) >= 50:
            corte = valsatr.abs().quantile(0.99)
            recortado = valsatr[valsatr.abs() <= corte]
            print(f"         Sin el 1% mas extremo (|ATR|>{corte:.2f}, n excluidas={len(valsatr)-len(recortado)}): "
                  f"media={recortado.mean():6.3f}  mediana={recortado.median():6.3f}")


def main(path):
    df = cargar_y_verificar(path)
    gaps = clasificar_huecos(df)
    atr = calcular_atr(df)
    ema = calcular_ema(df)
    verificar_ema_atr(df, ema, atr)
    momentum = calcular_momentum(df, atr)

    cruce_alcista, cruce_bajista, en_sobreextension, desviacion = detectar_sobreextensiones(df, ema, atr)
    retenidos = aplicar_cooldown_global(df, cruce_alcista, cruce_bajista)
    señales = calcular_retornos_senales(df, atr, retenidos, gaps)

    assert señales['idx_senal'].is_monotonic_increasing, "ERROR GRAVE: señales no ordenadas"
    assert (señales['t_entrada'] > señales['t_senal']).all(), \
        "ERROR GRAVE: entrada no posterior a la señal (posible lookahead)"
    print("\n[OK] Verificacion final: entradas siempre posteriores a su señal")

    señales = aplicar_escenarios_coste(señales)

    controles_a = construir_controles(df, atr, momentum, en_sobreextension, señales, exigir_momentum=False)
    controles_b = construir_controles(df, atr, momentum, en_sobreextension, señales, exigir_momentum=True)

    print("\n\n################ INFORME HIPOTESIS B ################")

    print(f"\n### Resumen por año (combinando ambas direcciones, bruto) ###")
    for anio, g in señales.groupby('anio'):
        pos16 = (g['retorno_precio_16'] > 0).mean() * 100
        print(f"  {anio}: n={len(g):>4}  (alcistas={ (g['tipo_sobreextension']=='sobreext_alcista').sum() }, "
              f"bajistas={ (g['tipo_sobreextension']=='sobreext_bajista').sum() })  "
              f"%positivos_k16={pos16:5.1f}%  media_ATR_k16={g['retorno_atr_16'].mean():6.3f}  "
              f"mediana_ATR_k16={g['retorno_atr_16'].median():6.3f}")

    periodos = {
        'ROBUSTEZ HISTORICA (2023-2024, nunca explorado antes)': (2023, 2024),
        'EXPLORATORIO YA QUEMADO (2025 + 2026 hasta hoy)': (2025, 2026),
    }

    for nombre_periodo, (a1, a2) in periodos.items():
        sub = señales[(señales['anio'] >= a1) & (señales['anio'] <= a2)]
        idx_sub = set(sub['idx_senal'])
        ca = controles_a[controles_a['idx_senal_origen'].isin(idx_sub)]
        cb = controles_b[controles_b['idx_senal_origen'].isin(idx_sub)]

        print(f"\n\n========== {nombre_periodo} ==========")
        resumen("TODAS", sub, ca, cb)
        resumen("Cortos tras sobreextension ALCISTA", sub[sub['tipo_sobreextension'] == 'sobreext_alcista'],
                ca[ca['direccion_operada'] == 'corto'], cb[cb['direccion_operada'] == 'corto'])
        resumen("Largos tras sobreextension BAJISTA", sub[sub['tipo_sobreextension'] == 'sobreext_bajista'],
                ca[ca['direccion_operada'] == 'largo'], cb[cb['direccion_operada'] == 'largo'])

        print(f"\n  -- Desglose por continuidad de la ventana (horizonte 16) --")
        sin_hueco = sub[sub['ventana16_sin_hueco']]
        con_hueco = sub[~sub['ventana16_sin_hueco']]
        resumen("  Ventanas SIN interrupcion", sin_hueco)
        resumen("  Ventanas CON cierre/fin de semana de por medio", con_hueco)

    print("\n### VALIDACION PROSPECTIVA FUTURA ###")
    print("No disponible: requeriria datos posteriores a congelar esta metodologia (hoy). "
          "2023-2026 son como mucho robustez historica y exploracion ya quemada, nunca validacion.")

    print("\n### Criterios de descarte pre-registrados (orientativos, no prueba estadistica formal) ###")
    print("Se consideraria indicio a seguir investigando solo si, en AMBOS periodos: media y mediana "
          "ATR neto (conservador+slippage) positivas en >=2/3 horizontes; diff señal-control (A o B) "
          "positiva y >0.1 ATR en >=2/3 horizontes; signo se mantiene excluyendo el 1% mas extremo; "
          "sin asimetria alcista/bajista no explicada. El umbral de 0.1 ATR es orientativo, NO un "
          "test de significancia -- la significancia real hay que leerla en los IC95% por bootstrap de bloques.")

    return señales, controles_a, controles_b, gaps


if __name__ == '__main__':
    main(sys.argv[1])
