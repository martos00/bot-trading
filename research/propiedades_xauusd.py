"""
Investigacion de propiedades estadisticas de XAUUSD M15 (2023-2026).
NO es un EA, NO define reglas de entrada/SL/TP. Puramente descriptivo.

5 bloques fijos, parametros pre-registrados, sin seleccion retrospectiva:
 1. Persistencia de retornos y volatilidad (autocorrelacion, log-retornos,
    separando intrasesion de saltos entre sesiones).
 2. Diferencias horarias -- con intento de verificacion independiente del
    offset UTC via fechas de publicacion del dato de empleo de EEUU (NFP),
    NO solo por la hora de cierre de sesion. Si no es concluyente, se
    conserva hora de servidor y se declara la limitacion.
 3. Comportamiento tras expansiones de volatilidad (umbral relativo fijo),
    contra control emparejado por hora, sin asumir direccion operable.
 4/5. Regimen H1 (EMA200+estructura, 100% causal) como estratificador de
    los bloques 1, y estabilidad por año en todos los bloques.

Marco de 3 niveles (no se exige rentabilidad neta salvo que exista una
regla operativa definida, que este estudio no define):
 Nivel 1: propiedad estadistica reproducible.
 Nivel 2: propiedad potencialmente util para una futura hipotesis.
 Nivel 3: ventaja operativa tras costes -- FUERA DE ALCANCE aqui.
"""
import sys
from datetime import timedelta

import numpy as np
import pandas as pd

ATR_PERIODO = 14
EMA_H1_PERIODO = 200
SWING_LEFT_H1 = 3
SWING_RIGHT_H1 = 3
LAGS_AUTOCORR = [1, 4, 8, 16, 96]
UMBRAL_EXPANSION = 1.5          # ATR14 / mediana_movil_100(ATR14)
VENTANA_MEDIANA_EXPANSION = 100
COOLDOWN = 16
HORIZONTES = [4, 8, 16]
SEED = 42
BLOQUES_BOOTSTRAP_SENSIBILIDAD = [5, 10, 20]
REPETICIONES_BOOTSTRAP = 1500
M_CONTROLES = 5
VENTANA_CONTROL_DIAS = 30
MAX_REUSOS_CONTROL = 2
ATR_TOLERANCIA_RELATIVA = 0.25

# Fechas de publicacion del "Employment Situation" (NFP) de EEUU dentro de
# nuestro rango de datos, confirmadas contra el calendario oficial de BLS
# (bls.gov/schedule) -- no se asumen "primer viernes del mes" sin mas,
# varias de estas son excepciones por cierres de gobierno / festivos.
NFP_FECHAS = [
    ("2024-01-05", "EST"),
    ("2024-02-02", "EST"),
    ("2025-02-07", "EST"),
    ("2026-03-06", "EST"),   # antes del cambio de horario EEUU (8 marzo 2026)
    ("2026-05-08", "EDT"),
    ("2026-07-02", "EDT"),
    ("2026-08-07", "EDT"),
    ("2026-09-04", "EDT"),
    ("2026-10-02", "EDT"),
]


# ----------------------------------------------------------------------------
# Carga, verificacion e infraestructura reutilizada de Hipotesis A/B
# ----------------------------------------------------------------------------
def cargar_y_verificar(path):
    df = pd.read_csv(path, sep=';', parse_dates=['TimestampServidor'],
                      date_format='%Y.%m.%d %H:%M:%S')
    df = df.reset_index(drop=True)
    assert df['TimestampServidor'].is_monotonic_increasing
    assert df['TimestampServidor'].duplicated().sum() == 0
    assert (df['High'] >= df[['Open', 'Close']].max(axis=1)).all()
    assert (df['Low'] <= df[['Open', 'Close']].min(axis=1)).all()
    assert (df[['Open', 'High', 'Low', 'Close']] > 0).all().all()
    print(f"[OK] Carga: {len(df)} filas, {df['TimestampServidor'].iloc[0]} -> {df['TimestampServidor'].iloc[-1]}")
    return df


def clasificar_huecos(df):
    diffs = df['TimestampServidor'].diff()
    es_hueco = diffs > timedelta(minutes=15)
    cat = pd.Series('intrasesion', index=df.index)
    for i in df.index[es_hueco]:
        dur = diffs.iloc[i]
        if dur <= timedelta(hours=2):
            cat.iloc[i] = 'cierre_diario'
        elif dur <= timedelta(hours=60):
            cat.iloc[i] = 'fin_de_semana'
        else:
            cat.iloc[i] = 'festivo_extendido'
    return cat


def calcular_atr(df, periodo=ATR_PERIODO):
    prev_close = df['Close'].shift(1)
    tr = pd.concat([df['High'] - df['Low'], (df['High'] - prev_close).abs(),
                     (df['Low'] - prev_close).abs()], axis=1).max(axis=1)
    atr = tr.copy()
    atr.iloc[:periodo] = np.nan
    atr.iloc[periodo] = tr.iloc[1:periodo + 1].mean()
    for i in range(periodo + 1, len(df)):
        atr.iloc[i] = (atr.iloc[i - 1] * (periodo - 1) + tr.iloc[i]) / periodo
    atr.iloc[:periodo] = np.nan
    return atr


def bootstrap_bloques_ic(valores, bloque, repeticiones=REPETICIONES_BOOTSTRAP, seed=SEED):
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


# ----------------------------------------------------------------------------
# BLOQUE 1: log-retornos, separando intrasesion de saltos
# ----------------------------------------------------------------------------
def calcular_log_retornos(df, categoria_hueco):
    log_ret = np.log(df['Close'] / df['Close'].shift(1))
    es_salto = categoria_hueco != 'intrasesion'
    return log_ret, es_salto


def autocorrelacion_intrasesion(log_ret, es_salto, lag):
    """Autocorrelacion entre r(t) y r(t+lag) usando SOLO pares donde todos
    los retornos entre t y t+lag (inclusive) son intrasesion -- evita que
    un hueco de fin de semana/festivo contamine el lag."""
    n = len(log_ret)
    valido = np.ones(n, dtype=bool)
    # marca como invalido cualquier t tal que exista un salto en (t, t+lag]
    salto_arr = es_salto.values
    ventana_tiene_salto = pd.Series(salto_arr).rolling(lag).max().shift(-lag + 1).fillna(1).astype(bool).values \
        if lag > 0 else np.zeros(n, dtype=bool)
    # recalculo directo y simple (mas lento pero inequivoco) via suma acumulada
    salto_cumsum = np.cumsum(salto_arr.astype(int))
    salto_en_ventana = np.zeros(n, dtype=bool)
    idx = np.arange(n)
    idx_fin = idx + lag
    dentro = idx_fin < n
    suma_ventana = np.full(n, 999)
    suma_ventana[dentro] = salto_cumsum[idx_fin[dentro]] - salto_cumsum[idx[dentro]]
    salto_en_ventana = suma_ventana > 0

    x = log_ret.values
    x_fin_seguro = x[np.clip(idx_fin, 0, n - 1)]
    pares_validos = dentro & (~salto_en_ventana) & ~np.isnan(x) & ~np.isnan(x_fin_seguro)
    x1 = x[pares_validos]
    x2 = x[idx_fin[pares_validos]]
    if len(x1) < 50:
        return np.nan, 0, (np.nan, np.nan)
    r = np.corrcoef(x1, x2)[0, 1]
    return r, len(x1), (x1, x2)


def resumen_bloque1(nombre, log_ret, es_salto, categoria_hueco, anios_serie):
    print(f"\n### BLOQUE 1 -- {nombre} ###")
    print("Autocorrelacion de log-retornos (persistencia direccional), SOLO pares intrasesion:")
    for lag in LAGS_AUTOCORR:
        r, n, (x1, x2) = autocorrelacion_intrasesion(log_ret, es_salto, lag)
        if np.isnan(r):
            print(f"  lag={lag:>3}: n insuficiente")
            continue
        prod = x1 * x2
        ics = {b: bootstrap_bloques_ic(prod, b) for b in BLOQUES_BOOTSTRAP_SENSIBILIDAD}
        ics_txt = "  ".join(f"bloque{b}=[{lo:.2e},{hi:.2e}]" for b, (lo, hi) in ics.items())
        print(f"  lag={lag:>3}: r={r:+.4f}  n={n:>6}  IC95%(media prod, sensibilidad bloque): {ics_txt}")

    print("\nAutocorrelacion de |log-retorno| (persistencia de volatilidad), SOLO pares intrasesion:")
    abs_ret = log_ret.abs()
    for lag in LAGS_AUTOCORR:
        r, n, (x1, x2) = autocorrelacion_intrasesion(abs_ret, es_salto, lag)
        if np.isnan(r):
            print(f"  lag={lag:>3}: n insuficiente")
            continue
        prod = x1 * x2
        ics = {b: bootstrap_bloques_ic(prod, b) for b in BLOQUES_BOOTSTRAP_SENSIBILIDAD}
        ics_txt = "  ".join(f"bloque{b}=[{lo:.2e},{hi:.2e}]" for b, (lo, hi) in ics.items())
        print(f"  lag={lag:>3}: r={r:+.4f}  n={n:>6}  IC95%(media prod, sensibilidad bloque): {ics_txt}")

    print("\nPor año (autocorrelacion lag=1 y lag=96, log-retorno y |log-retorno|):")
    for anio in sorted(anios_serie.unique()):
        mask = anios_serie == anio
        lr = log_ret[mask].reset_index(drop=True)
        sal = es_salto[mask].reset_index(drop=True)
        r1, n1, _ = autocorrelacion_intrasesion(lr, sal, 1)
        r96, n96, _ = autocorrelacion_intrasesion(lr, sal, 96)
        ra1, na1, _ = autocorrelacion_intrasesion(lr.abs(), sal, 1)
        ra96, na96, _ = autocorrelacion_intrasesion(lr.abs(), sal, 96)
        print(f"  {anio}: retorno lag1 r={r1:+.4f}(n={n1})  lag96 r={r96:+.4f}(n={n96})  |  "
              f"|retorno| lag1 r={ra1:+.4f}(n={na1})  lag96 r={ra96:+.4f}(n={na96})")

    print("\nDistribucion de los SALTOS (log-retorno), por categoria -- NO mezclados con lo anterior:")
    for cat in ['cierre_diario', 'fin_de_semana', 'festivo_extendido']:
        vals = log_ret[categoria_hueco == cat].dropna()
        if len(vals):
            print(f"  {cat:<20} n={len(vals):>5}  media={vals.mean():+.5f}  "
                  f"std={vals.std():.5f}  mediana={vals.median():+.5f}  "
                  f"min={vals.min():+.5f}  max={vals.max():+.5f}")


# ----------------------------------------------------------------------------
# BLOQUE 2: verificacion independiente de UTC via fechas NFP (no solo cierre)
# ----------------------------------------------------------------------------
def verificar_utc_via_nfp(df, log_ret):
    print("\n### BLOQUE 2 -- Intento de verificacion independiente del offset UTC (via NFP) ###")
    print("Para cada fecha de publicacion NFP confirmada contra el calendario oficial BLS, "
          "se busca la vela M15 de mayor |log-retorno| dentro de ese dia de calendario (hora "
          "de servidor), sin asumir de antemano el offset.")

    resultados = []
    for fecha_str, regimen_us in NFP_FECHAS:
        fecha = pd.Timestamp(fecha_str)
        dia = df[(df['TimestampServidor'] >= fecha) & (df['TimestampServidor'] < fecha + timedelta(days=1))]
        if len(dia) == 0:
            print(f"  {fecha_str} ({regimen_us}): sin datos ese dia, omitido")
            continue
        lr_dia = log_ret.loc[dia.index].abs()
        idx_pico = lr_dia.idxmax()
        hora_pico = df['TimestampServidor'].loc[idx_pico]
        resultados.append((fecha_str, regimen_us, hora_pico.strftime('%H:%M'), lr_dia.loc[idx_pico]))
        print(f"  {fecha_str} ({regimen_us}): pico de |log-retorno| a las {hora_pico.strftime('%H:%M')} "
              f"hora servidor (|r|={lr_dia.loc[idx_pico]:.5f})")

    horas_est = [r[2] for r in resultados if r[1] == 'EST']
    horas_edt = [r[2] for r in resultados if r[1] == 'EDT']
    print(f"\n  Horas de pico en fechas EST (EEUU en horario de invierno): {horas_est}")
    print(f"  Horas de pico en fechas EDT (EEUU en horario de verano):   {horas_edt}")

    conjunto_est = set(horas_est)
    conjunto_edt = set(horas_edt)
    concluyente = len(conjunto_est) <= 2 and len(conjunto_edt) <= 2 and conjunto_est != conjunto_edt
    if concluyente:
        print("  [RESULTADO] Las horas de pico difieren de forma consistente entre fechas EST y EDT: "
              "el servidor SI parece desplazarse con el cambio de horario de EEUU. Aun asi, con "
              f"{len(resultados)} fechas de referencia la confianza es limitada -- se trata como "
              "indicio, no como calibracion exacta confirmada.")
    else:
        print("  [RESULTADO] NO CONCLUYENTE: las horas de pico no muestran un patron limpio y "
              "consistente entre fechas EST/EDT (ruido de otros eventos de mercado, variabilidad "
              "del minuto exacto de reaccion, numero de fechas de referencia limitado). "
              "Por la instruccion de no asumir el offset sin verificacion independiente fiable, "
              "SE CONSERVA LA HORA DE SERVIDOR sin convertir a UTC, y se declara esta limitacion "
              "en el informe final.")
    return concluyente, resultados


def resumen_bloque2_horario(df, atr, categoria_hueco, anios_serie):
    print("\n### BLOQUE 2 -- Volatilidad y retorno medio por hora DE SERVIDOR (no UTC) ###")
    print("(conversion a UTC no verificada con confianza suficiente -- ver bloque anterior; "
          "se reporta en hora de servidor, limitacion declarada explicitamente)")

    log_ret = np.log(df['Close'] / df['Close'].shift(1))
    hora = df['TimestampServidor'].dt.hour
    deriva_anual = log_ret.groupby(anios_serie).mean()
    log_ret_detrend = log_ret - anios_serie.map(deriva_anual)

    tabla = pd.DataFrame({'hora': hora, 'atr': atr, 'ret_detrend': log_ret_detrend,
                           'salto': categoria_hueco != 'intrasesion'})
    tabla = tabla[~tabla['salto']]  # excluye saltos del patron horario intradia

    agg = tabla.groupby('hora').agg(atr_medio=('atr', 'mean'), n=('atr', 'count'),
                                     ret_medio_detrend=('ret_detrend', 'mean'),
                                     ret_std=('ret_detrend', 'std'))
    for hr, row in agg.iterrows():
        ic_lo, ic_hi = bootstrap_bloques_ic(tabla.loc[tabla['hora'] == hr, 'ret_detrend'].values, 10)
        print(f"  hora_servidor={hr:02d}: n={int(row['n']):>5}  ATR_medio={row['atr_medio']:.3f}  "
              f"retorno_medio_detrend={row['ret_medio_detrend']:+.6f}  IC95%=[{ic_lo:+.2e},{ic_hi:+.2e}]")


# ----------------------------------------------------------------------------
# BLOQUE 3: expansiones de volatilidad vs control por hora, sin asumir direccion
# ----------------------------------------------------------------------------
def detectar_expansiones(atr):
    mediana_movil = atr.rolling(VENTANA_MEDIANA_EXPANSION).median()
    ratio = atr / mediana_movil
    estado = ratio > UMBRAL_EXPANSION
    cruce = estado & ~estado.shift(1).fillna(False)
    print(f"\n### BLOQUE 3 -- Expansiones de volatilidad (ATR14 > {UMBRAL_EXPANSION}x mediana_100) ###")
    print(f"Cruces detectados: {cruce.sum()}")
    return cruce, estado


def cooldown_simple(df, cruce):
    idxs = df.index[cruce]
    retenidos = []
    proximo = -1
    for i in idxs:
        if i >= proximo:
            retenidos.append(i)
            proximo = i + COOLDOWN
    print(f"Tras cooldown global de {COOLDOWN} velas: {len(retenidos)} eventos retenidos "
          f"(de {len(idxs)} crudos)")
    return retenidos


def analizar_expansiones(df, atr, retenidos, categoria_hueco, anios_serie):
    n = len(df)
    hora_bar = df['TimestampServidor'].dt.hour.values
    atr_vals = atr.values
    rng = np.random.default_rng(SEED)
    uso = {}

    filas = []
    for idx in retenidos:
        if idx + max(HORIZONTES) >= n or idx + 1 >= n:
            continue
        atr_t = atr_vals[idx]
        if np.isnan(atr_t):
            continue
        fila = dict(idx=idx, anio=anios_serie.iloc[idx], hora=hora_bar[idx])
        precio_entrada = df['Open'].iloc[idx + 1]
        for k in HORIZONTES:
            fila[f'atr_fwd_{k}'] = atr_vals[idx + k] / atr_t if not np.isnan(atr_vals[idx + k]) else np.nan
            ret = df['Close'].iloc[idx + k] - precio_entrada
            fila[f'ret_atr_{k}'] = ret / atr_t
        filas.append(fila)
    señales = pd.DataFrame(filas)

    # controles: misma hora, ATR comparable, fuera de estado de expansion, ventana +-30d
    fecha_bar = df['TimestampServidor'].values
    ventana_ns = np.timedelta64(VENTANA_CONTROL_DIAS, 'D')
    idx_validos = (np.arange(n) + max(HORIZONTES) < n) & (np.arange(n) + 1 < n)
    filas_c = []
    for _, s in señales.iterrows():
        idx = int(s['idx'])
        atr_obj = atr_vals[idx]
        mask = (hora_bar == s['hora']) & idx_validos & \
               (np.abs(fecha_bar - fecha_bar[idx]) <= ventana_ns) & \
               (np.abs(atr_vals - atr_obj) <= ATR_TOLERANCIA_RELATIVA * atr_obj)
        candidatos = np.where(mask)[0]
        candidatos = [c for c in candidatos if uso.get(c, 0) < MAX_REUSOS_CONTROL]
        if len(candidatos) == 0:
            continue
        elegidos = rng.choice(candidatos, size=min(M_CONTROLES, len(candidatos)), replace=False)
        for c in elegidos:
            uso[c] = uso.get(c, 0) + 1
            precio_entrada = df['Open'].iloc[c + 1]
            atr_c = atr_vals[c]
            filac = dict(idx_origen=idx)
            for k in HORIZONTES:
                filac[f'atr_fwd_{k}'] = atr_vals[c + k] / atr_c if not np.isnan(atr_vals[c + k]) else np.nan
                ret = df['Close'].iloc[c + k] - precio_entrada
                filac[f'ret_atr_{k}'] = ret / atr_c
            filas_c.append(filac)
    controles = pd.DataFrame(filas_c)

    print(f"\nSeñales con datos completos: {len(señales)}  Controles generados: {len(controles)}")
    for k in HORIZONTES:
        sv = señales[f'atr_fwd_{k}'].dropna()
        cv = controles[f'atr_fwd_{k}'].dropna()
        rv = señales[f'ret_atr_{k}'].dropna()
        rc = controles[f'ret_atr_{k}'].dropna()
        ic_lo, ic_hi = bootstrap_bloques_ic(rv.values, 10)
        print(f"  k={k:>2}: ATR_fwd/ATR_t señal media={sv.mean():.3f}  control media={cv.mean():.3f}  "
              f"(¿persiste volatilidad? diff={sv.mean()-cv.mean():+.3f})")
        print(f"         retorno_ATR señal media={rv.mean():+.3f} mediana={rv.median():+.3f}  "
              f"IC95%(bloque10)=[{ic_lo:+.3f},{ic_hi:+.3f}]  control media={rc.mean():+.3f}  "
              f"-- NO se interpreta como direccion operable, solo descriptivo")

    print("\nPor año:")
    for anio, g in señales.groupby('anio'):
        print(f"  {anio}: n={len(g)}  ATR_fwd16/ATR_t media={g['atr_fwd_16'].mean():.3f}  "
              f"retorno_ATR_16 media={g['ret_atr_16'].mean():+.3f}")
    return señales, controles


# ----------------------------------------------------------------------------
# BLOQUE 4/5: regimen H1 causal (EMA200 + estructura), proyectado a M15
# ----------------------------------------------------------------------------
def construir_h1(df):
    hora_floor = df['TimestampServidor'].dt.floor('h')
    g = df.groupby(hora_floor)
    h1 = g.agg(Open=('Open', 'first'), High=('High', 'max'), Low=('Low', 'min'),
               Close=('Close', 'last'), n_velas=('Close', 'count')).reset_index()
    h1 = h1.rename(columns={'TimestampServidor': 'Tiempo'})
    incompletas = (h1['n_velas'] < 4).sum()
    print(f"\n### BLOQUE 4/5 -- Resampleo M15->H1: {len(h1)} velas H1, {incompletas} incompletas "
          f"(<4 velas M15, por huecos de sesion -- se usan igualmente con los datos disponibles, "
          f"sin inventar valores)")
    return h1


def calcular_ema_simple(serie, periodo):
    ema = pd.Series(np.nan, index=serie.index)
    if len(serie) <= periodo:
        return ema
    ema.iloc[periodo - 1] = serie.iloc[:periodo].mean()
    alpha = 2.0 / (periodo + 1)
    for i in range(periodo, len(serie)):
        ema.iloc[i] = alpha * serie.iloc[i] + (1 - alpha) * ema.iloc[i - 1]
    return ema


def swings_confirmados(serie_high, serie_low, left, right):
    n = len(serie_high)
    es_swing_high = pd.Series(False, index=serie_high.index)
    es_swing_low = pd.Series(False, index=serie_low.index)
    for i in range(left, n - right):
        ventana_h = serie_high.iloc[i - left:i + right + 1]
        if serie_high.iloc[i] == ventana_h.max() and (ventana_h == serie_high.iloc[i]).sum() == 1:
            es_swing_high.iloc[i] = True
        ventana_l = serie_low.iloc[i - left:i + right + 1]
        if serie_low.iloc[i] == ventana_l.min() and (ventana_l == serie_low.iloc[i]).sum() == 1:
            es_swing_low.iloc[i] = True
    # confirmado `right` velas despues del propio swing (shift adelante en el tiempo)
    confirmado_en = pd.Series(np.nan, index=serie_high.index)
    for i in serie_high.index[es_swing_high]:
        if i + right < n:
            confirmado_en.loc[i] = i + right
    return es_swing_high, es_swing_low, confirmado_en


def calcular_regimen_h1_causal(h1):
    ema200 = calcular_ema_simple(h1['Close'], EMA_H1_PERIODO)
    es_sh, es_sl, _ = swings_confirmados(h1['High'], h1['Low'], SWING_LEFT_H1, SWING_RIGHT_H1)

    n = len(h1)
    regimen = pd.Series('indefinido', index=h1.index)
    ultimos_highs, ultimos_lows = [], []
    transiciones = 0
    regimen_actual = 'indefinido'

    for i in range(n):
        # Solo se incorpora un swing a la lista una vez CONFIRMADO (i.e. `right`
        # velas despues), nunca en el momento del propio pivote -- sin lookahead.
        idx_confirmable = i - SWING_RIGHT_H1
        if idx_confirmable >= SWING_LEFT_H1:
            if es_sh.iloc[idx_confirmable]:
                ultimos_highs.append(h1['High'].iloc[idx_confirmable])
                ultimos_highs = ultimos_highs[-2:]
            if es_sl.iloc[idx_confirmable]:
                ultimos_lows.append(h1['Low'].iloc[idx_confirmable])
                ultimos_lows = ultimos_lows[-2:]

        estructura_alcista = len(ultimos_highs) == 2 and len(ultimos_lows) == 2 and \
            ultimos_highs[1] > ultimos_highs[0] and ultimos_lows[1] > ultimos_lows[0]
        estructura_bajista = len(ultimos_highs) == 2 and len(ultimos_lows) == 2 and \
            ultimos_highs[1] < ultimos_highs[0] and ultimos_lows[1] < ultimos_lows[0]

        ema_i = ema200.iloc[i]
        nuevo_regimen = 'indefinido'
        if not np.isnan(ema_i):
            if h1['Close'].iloc[i] > ema_i and estructura_alcista:
                nuevo_regimen = 'alcista'
            elif h1['Close'].iloc[i] < ema_i and estructura_bajista:
                nuevo_regimen = 'bajista'

        if nuevo_regimen != regimen_actual:
            transiciones += 1
            regimen_actual = nuevo_regimen
        regimen.iloc[i] = regimen_actual

    print(f"Transiciones de regimen H1 detectadas: {transiciones} en {n} velas H1 "
          f"({n/max(transiciones,1):.1f} velas H1 de media por regimen)")
    print(regimen.value_counts())
    return regimen


def proyectar_regimen_a_m15(df, h1, regimen_h1):
    h1_tiempo = h1['TimestampServidor'] if 'TimestampServidor' in h1.columns else h1.iloc[:, 0]
    # CRITICO: regimen_h1.iloc[i] depende del Close de la propia vela H1 i,
    # que no esta disponible hasta que esa vela CIERRA (una hora despues de
    # su timestamp de apertura). Si se empareja por el timestamp de apertura,
    # las 3 primeras velas M15 de esa hora verian su "propio futuro" cierre
    # H1 -- se desplaza +1h para exponer el regimen solo desde el cierre real.
    h1_tiempo_cierre = h1_tiempo + pd.Timedelta(hours=1)
    tabla = pd.DataFrame({'Tiempo': h1_tiempo_cierre, 'regimen': regimen_h1}).set_index('Tiempo')
    # merge_asof: para cada vela M15, usa el regimen de la ULTIMA vela H1 ya
    # cerrada estrictamente antes de su propio cierre -- causal, sin lookahead.
    m15_tiempo = df[['TimestampServidor']].copy()
    m15_tiempo['orden'] = range(len(m15_tiempo))
    proyectado = pd.merge_asof(m15_tiempo.sort_values('TimestampServidor'),
                                tabla.reset_index().rename(columns={'Tiempo': 'TimestampServidor'}),
                                on='TimestampServidor', direction='backward')
    proyectado = proyectado.sort_values('orden')
    return proyectado['regimen'].fillna('indefinido').reset_index(drop=True)


def resumen_bloque5_por_regimen(log_ret, es_salto, regimen_m15, anios_serie):
    print("\n### BLOQUE 4/5 -- Autocorrelacion (lag=1 y lag=16) estratificada por regimen H1 ###")
    for reg in ['alcista', 'bajista', 'indefinido']:
        mask = (regimen_m15 == reg).values
        lr = log_ret[mask].reset_index(drop=True)
        sal = es_salto[mask].reset_index(drop=True)
        r1, n1, _ = autocorrelacion_intrasesion(lr, sal, 1)
        r16, n16, _ = autocorrelacion_intrasesion(lr, sal, 16)
        ra1, na1, _ = autocorrelacion_intrasesion(lr.abs(), sal, 1)
        print(f"  regimen={reg:<10} n_velas={mask.sum():>6}  retorno lag1 r={r1:+.4f}(n={n1})  "
              f"lag16 r={r16:+.4f}(n={n16})  |retorno| lag1 r={ra1:+.4f}(n={na1})")


def main(path):
    df = cargar_y_verificar(path)
    categoria_hueco = clasificar_huecos(df)
    atr = calcular_atr(df)
    log_ret, es_salto = calcular_log_retornos(df, categoria_hueco)
    anios_serie = df['TimestampServidor'].dt.year

    print("\n\n################ INFORME: PROPIEDADES ESTADISTICAS XAUUSD M15 ################")

    periodos = {'ROBUSTEZ HISTORICA 2023-2024': (2023, 2024), 'EXPLORATORIO 2025-2026': (2025, 2026)}
    for nombre, (a1, a2) in periodos.items():
        mask = (anios_serie >= a1) & (anios_serie <= a2)
        resumen_bloque1(nombre, log_ret[mask].reset_index(drop=True), es_salto[mask].reset_index(drop=True),
                        categoria_hueco[mask].reset_index(drop=True), anios_serie[mask].reset_index(drop=True))

    concluyente, _ = verificar_utc_via_nfp(df, log_ret)
    resumen_bloque2_horario(df, atr, categoria_hueco, anios_serie)

    cruce, estado = detectar_expansiones(atr)
    retenidos = cooldown_simple(df, cruce)
    señales_exp, controles_exp = analizar_expansiones(df, atr, retenidos, categoria_hueco, anios_serie)

    h1 = construir_h1(df)
    regimen_h1 = calcular_regimen_h1_causal(h1)
    regimen_m15 = proyectar_regimen_a_m15(df, h1, regimen_h1)
    resumen_bloque5_por_regimen(log_ret, es_salto, regimen_m15, anios_serie)

    print("\n\n### NOTA METODOLOGICA FINAL ###")
    print("Todo el histórico 2023-2026 forma parte de este mismo proceso de investigación "
          "(ya se usó en Hipótesis A y B); nada de lo anterior se presenta como validación "
          "prospectiva independiente. Nivel 3 (ventaja operativa tras costes) queda fuera de "
          "alcance: no se ha definido ninguna regla operativa en este estudio.")
    if not concluyente:
        print("LIMITACION DECLARADA: el offset UTC del servidor no pudo verificarse con "
              "confianza suficiente via NFP; el Bloque 2 horario se reporta en hora de "
              "servidor sin convertir.")


if __name__ == '__main__':
    main(sys.argv[1])
