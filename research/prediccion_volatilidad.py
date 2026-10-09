"""
Prediccion de volatilidad futura de XAUUSD M15 (h=4 y h=8 velas).
NO es una estrategia operativa, NO define entradas/SL/TP, NO es un EA.
Investigacion: ¿se puede predecir la MAGNITUD del movimiento futuro mejor
que baselines simples, usando solo informacion causal?

Modelos (todos aritmetica simple, nada de ML complejo):
 - Ingenuo: ultimas h velas = proximas h velas.
 - EWMA (lambda=0.94 FIJO, RiskMetrics estandar, no ajustado a estos datos).
 - Solo-hora: suma de medias horarias (entrenamiento) para las h horas futuras.
 - Combinado: ingenuo corregido por razon de carga estacional
   (futuro/pasado), NO por el multiplicador de una sola hora futura.

Walk-forward trimestral, ventana expandiente. Corte de entrenamiento
ESTRICTO: una fila de entrenamiento solo se usa si su propio horizonte
(hasta h=8, el mas largo, aplicado de forma uniforme) termina antes de
que empiece el bloque de evaluacion -- no solo que su timestamp sea
anterior.
"""
import sys
from datetime import timedelta

import numpy as np
import pandas as pd

HORIZONTES = [4, 8]
H_MAX = max(HORIZONTES)
LAMBDA_EWMA = 0.94          # RiskMetrics estandar, fijado antes de ver datos
MESES_MINIMOS_ENTRENAMIENTO = 3
SEED = 42
REPETICIONES_BOOTSTRAP = 1500
BLOQUES_SENSIBILIDAD = [10, 20]


# ----------------------------------------------------------------------------
# Carga, verificacion, huecos (reutilizado de scripts anteriores)
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
    cat = pd.Series('intrasesion', index=df.index)
    for i in df.index[diffs > timedelta(minutes=15)]:
        dur = diffs.iloc[i]
        cat.iloc[i] = 'cierre_diario' if dur <= timedelta(hours=2) else \
                      ('fin_de_semana' if dur <= timedelta(hours=60) else 'festivo_extendido')
    return cat


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
        medias[b] = np.concatenate([valores[s:s + bloque] for s in inicios])[:n].mean()
    return np.percentile(medias, 2.5), np.percentile(medias, 97.5)


# ----------------------------------------------------------------------------
# Features y objetivos (log-retornos, separando saltos)
# ----------------------------------------------------------------------------
def preparar_datos(df, categoria_hueco):
    n = len(df)
    log_ret = np.log(df['Close'] / df['Close'].shift(1)).values
    abs_ret = np.abs(log_ret)
    es_salto = (categoria_hueco != 'intrasesion').values
    hora = df['TimestampServidor'].dt.hour.values

    # EWMA causal de |log-retorno|, lambda fijo, recursion pura hacia atras
    ewma = np.full(n, np.nan)
    primer_valido = np.nanargmax(~np.isnan(abs_ret))
    ewma[primer_valido] = abs_ret[primer_valido]
    for i in range(primer_valido + 1, n):
        prev = ewma[i - 1] if not np.isnan(ewma[i - 1]) else abs_ret[i]
        ewma[i] = LAMBDA_EWMA * prev + (1 - LAMBDA_EWMA) * abs_ret[i]

    datos = dict(log_ret=log_ret, abs_ret=abs_ret, es_salto=es_salto, hora=hora, ewma=ewma)

    for h in HORIZONTES:
        y = np.full(n, np.nan)
        salto_fwd = np.zeros(n, dtype=bool)
        base = np.full(n, np.nan)
        salto_bwd = np.zeros(n, dtype=bool)
        for i in range(n):
            if i + h < n:
                y[i] = np.nansum(abs_ret[i + 1:i + h + 1])
                salto_fwd[i] = es_salto[i + 1:i + h + 1].any()
            if i - h + 1 >= 0:
                base[i] = np.nansum(abs_ret[i - h + 1:i + 1])
                salto_bwd[i] = es_salto[i - h + 1:i + 1].any()
        datos[f'Y_{h}'] = y
        datos[f'salto_fwd_{h}'] = salto_fwd
        datos[f'base_{h}'] = base
        datos[f'salto_bwd_{h}'] = salto_bwd

    return datos


def verificar_causalidad_targets(df, datos):
    """Recalculo manual en 15 filas aleatorias: Y_h e base_h solo deben
    tocar los indices que les corresponden."""
    n = len(df)
    rng = np.random.default_rng(SEED)
    muestra = rng.choice(np.arange(H_MAX, n - H_MAX), size=15, replace=False)
    abs_ret = datos['abs_ret']
    for h in HORIZONTES:
        for i in muestra:
            y_manual = sum(abs_ret[i + 1:i + h + 1])
            base_manual = sum(abs_ret[i - h + 1:i + 1])
            assert np.isclose(y_manual, datos[f'Y_{h}'][i], equal_nan=True), \
                f"ERROR GRAVE: Y_{h} no coincide en idx {i}"
            assert np.isclose(base_manual, datos[f'base_{h}'][i], equal_nan=True), \
                f"ERROR GRAVE: base_{h} no coincide en idx {i}"
    print(f"[OK] Y_h y base_h verificados manualmente en 15 indices aleatorios x {len(HORIZONTES)} horizontes")


# ----------------------------------------------------------------------------
# Walk-forward trimestral con corte de entrenamiento estricto (punto 2)
# ----------------------------------------------------------------------------
def bloques_trimestrales(df):
    trimestre = df['TimestampServidor'].dt.to_period('Q')
    cambios = trimestre.ne(trimestre.shift(1))
    inicios = df.index[cambios].tolist() + [len(df)]
    bloques = list(zip(inicios[:-1], inicios[1:]))
    return bloques, trimestre


def ejecutar_walk_forward(df, datos, categoria_hueco):
    n = len(df)
    bloques, trimestre_serie = bloques_trimestrales(df)
    hora = datos['hora']
    es_salto_simple = datos['es_salto']

    filas_entrenamiento_min = int(MESES_MINIMOS_ENTRENAMIENTO * 30 * 96)
    resultados = []
    primer_bloque_evaluado = None

    for (ini, fin) in bloques:
        # Corte ESTRICTO: una fila de entrenamiento r solo es valida si
        # r + H_MAX < ini (su propio horizonte mas largo ya ha terminado
        # antes de que empiece este bloque de evaluacion) -- no solo
        # timestamp(r) < timestamp(ini).
        idx_entrenamiento = np.arange(0, ini)
        idx_entrenamiento = idx_entrenamiento[idx_entrenamiento + H_MAX < ini]

        if len(idx_entrenamiento) < filas_entrenamiento_min:
            continue  # historico insuficiente, bloque no evaluable aun

        assert idx_entrenamiento.max() + H_MAX < ini, \
            "ERROR GRAVE: fila de entrenamiento con horizonte que no ha terminado antes del bloque"
        assert ini not in idx_entrenamiento and (idx_entrenamiento < ini).all(), \
            "ERROR GRAVE: contaminacion de indices entre entrenamiento y bloque"

        if primer_bloque_evaluado is None:
            primer_bloque_evaluado = trimestre_serie.iloc[ini]

        # --- estimacion de m(hora) SOLO con entrenamiento, excluyendo saltos ---
        hora_train = hora[idx_entrenamiento]
        abs_train = datos['abs_ret'][idx_entrenamiento]
        salto_train = es_salto_simple[idx_entrenamiento]
        valido = ~salto_train & ~np.isnan(abs_train)
        tabla_train = pd.DataFrame({'hora': hora_train[valido], 'abs_ret': abs_train[valido]})
        m_abs_hora = tabla_train.groupby('hora')['abs_ret'].mean()
        media_global = tabla_train['abs_ret'].mean()
        m_norm_hora = m_abs_hora / media_global

        # --- evaluacion fila a fila en el bloque [ini, fin) ---
        for h in HORIZONTES:
            y = datos[f'Y_{h}'][ini:fin]
            base = datos[f'base_{h}'][ini:fin]
            salto_fwd = datos[f'salto_fwd_{h}'][ini:fin]
            salto_bwd = datos[f'salto_bwd_{h}'][ini:fin]
            hora_bloque = hora[ini:fin]
            ewma_bloque = datos['ewma'][ini:fin]

            # Ŷ_hora: suma de medias horarias absolutas para las h horas FUTURAS
            # (hora(t+1)..hora(t+h) es aritmetica de calendario, no informacion
            # de precio futuro -- no hay lookahead en conocer que hora sera).
            yhat_hora = np.full(fin - ini, np.nan)
            # Ŷ_combinado: base * razon de carga estacional futuro/pasado
            yhat_comb = np.full(fin - ini, np.nan)
            for j, t in enumerate(range(ini, fin)):
                if t + h >= n or t - h + 1 < 0:
                    continue
                horas_fwd = hora[t + 1:t + h + 1]
                horas_bwd = hora[t - h + 1:t + 1]
                s_futuro = sum(m_abs_hora.get(hh, media_global) for hh in horas_fwd)
                s_pasado_norm = sum(m_norm_hora.get(hh, 1.0) for hh in horas_bwd)
                yhat_hora[j] = s_futuro
                if s_pasado_norm > 1e-9 and not np.isnan(base[j]):
                    razon = (sum(m_norm_hora.get(hh, 1.0) for hh in horas_fwd)) / s_pasado_norm
                    yhat_comb[j] = base[j] * razon

            yhat_ingenuo = base
            yhat_ewma = h * ewma_bloque

            resultados.append(pd.DataFrame({
                'idx': np.arange(ini, fin), 'h': h, 'trimestre': str(trimestre_serie.iloc[ini]),
                'anio': df['TimestampServidor'].iloc[ini:fin].dt.year.values,
                'Y': y, 'salto_fwd': salto_fwd, 'salto_bwd': salto_bwd,
                'yhat_ingenuo': yhat_ingenuo, 'yhat_ewma': yhat_ewma,
                'yhat_hora': yhat_hora, 'yhat_combinado': yhat_comb,
                'vol_reciente': base,
            }))

    print(f"\n[OK] Primer bloque evaluado: {primer_bloque_evaluado} "
          f"(tras exigir >= {MESES_MINIMOS_ENTRENAMIENTO} meses y horizonte de entrenamiento resuelto)")
    return pd.concat(resultados, ignore_index=True)


# ----------------------------------------------------------------------------
# Metricas: error, calibracion, incertidumbre, estabilidad
# ----------------------------------------------------------------------------
MODELOS = ['yhat_ingenuo', 'yhat_ewma', 'yhat_hora', 'yhat_combinado']
NOMBRES = {'yhat_ingenuo': 'Ingenuo (persistencia)', 'yhat_ewma': f'EWMA(lambda={LAMBDA_EWMA})',
           'yhat_hora': 'Solo-hora', 'yhat_combinado': 'Combinado (persistencia x estacionalidad)'}


def resumen_modelos(res, nombre_corte):
    print(f"\n--- {nombre_corte} (n={len(res)}) ---")
    if len(res) == 0:
        print("  (sin datos)")
        return
    errores = {}
    for m in MODELOS:
        err = (res[m] - res['Y']).abs()
        errores[m] = err
        mae = err.mean()
        rmse = np.sqrt(((res[m] - res['Y']) ** 2).mean())
        sesgo = (res[m].mean() - res['Y'].mean())
        print(f"  {NOMBRES[m]:<42} MAE={mae:.5f}  RMSE={rmse:.5f}  sesgo_medio={sesgo:+.5f}  n={err.notna().sum()}")

    base_err = errores['yhat_ingenuo']
    for m in MODELOS:
        if m == 'yhat_ingenuo':
            continue
        d = errores[m] - base_err  # negativo = modelo mejor que ingenuo
        d_validos = d.dropna().values
        if len(d_validos) < 50:
            continue
        ic10 = bootstrap_bloques_ic(d_validos, 10)
        ic20 = bootstrap_bloques_ic(d_validos, 20)
        ratio = errores[m].mean() / base_err.mean()
        print(f"    vs ingenuo: {NOMBRES[m]:<40} MAE_ratio={ratio:.4f}  "
              f"diff_media_abs_error={d_validos.mean():+.5f}  "
              f"IC95%(bloque10)=[{ic10[0]:+.5f},{ic10[1]:+.5f}]  IC95%(bloque20)=[{ic20[0]:+.5f},{ic20[1]:+.5f}]")


def calibracion(res, modelo, h):
    sub = res[res['h'] == h].dropna(subset=[modelo, 'Y'])
    if len(sub) < 100:
        print(f"    {NOMBRES[modelo]} h={h}: datos insuficientes para calibracion")
        return
    sub = sub.copy()
    sub['decil'] = pd.qcut(sub[modelo], 10, labels=False, duplicates='drop')
    tabla = sub.groupby('decil').agg(pred_media=(modelo, 'mean'), real_media=('Y', 'mean'), n=('Y', 'count'))
    print(f"    Calibracion {NOMBRES[modelo]} h={h}:")
    for d, row in tabla.iterrows():
        ratio = row['real_media'] / row['pred_media'] if row['pred_media'] > 0 else np.nan
        print(f"      decil={int(d)}  pred_media={row['pred_media']:.5f}  real_media={row['real_media']:.5f}  "
              f"ratio_real/pred={ratio:.3f}  n={int(row['n'])}")


def main(path):
    df = cargar_y_verificar(path)
    categoria_hueco = clasificar_huecos(df)
    datos = preparar_datos(df, categoria_hueco)
    verificar_causalidad_targets(df, datos)

    res = ejecutar_walk_forward(df, datos, categoria_hueco)

    # comprobacion de particion: ninguna fila evaluada dos veces
    assert res.groupby('h')['idx'].apply(lambda s: s.is_unique).all(), \
        "ERROR GRAVE: fila evaluada mas de una vez dentro del mismo horizonte"
    print(f"[OK] Particion walk-forward verificada: sin filas evaluadas dos veces por horizonte")

    print("\n\n################ INFORME: PREDICCION DE VOLATILIDAD XAUUSD M15 ################")

    for h in HORIZONTES:
        sub = res[res['h'] == h]
        print(f"\n\n========== HORIZONTE h={h} velas ==========")
        resumen_modelos(sub, f"TODAS (h={h})")

        print("\n  -- Por ventana limpia vs. con salto (hacia adelante) --")
        resumen_modelos(sub[~sub['salto_fwd']], f"  Ventana futura SIN salto (h={h})")
        resumen_modelos(sub[sub['salto_fwd']], f"  Ventana futura CON salto (h={h})")

        print("\n  -- Por año --")
        for anio, g in sub.groupby('anio'):
            resumen_modelos(g, f"  Año {anio} (h={h})")

        print("\n  -- Por tercil de volatilidad reciente (causal, propia fila) --")
        sub_validas = sub.dropna(subset=['vol_reciente']).copy()
        sub_validas['tercil'] = pd.qcut(sub_validas['vol_reciente'], 3, labels=['bajo', 'medio', 'alto'],
                                          duplicates='drop')
        for t in ['bajo', 'medio', 'alto']:
            resumen_modelos(sub_validas[sub_validas['tercil'] == t], f"  Tercil vol. reciente={t} (h={h})")

        print("\n  -- Calibracion (deciles de prediccion) --")
        for m in MODELOS:
            calibracion(sub, m, h)

    print("\n\n### NOTA METODOLOGICA FINAL ###")
    print("2023-2026 es historico de investigacion ya usado en Hipotesis A, B y los Bloques 1-5; "
          "este walk-forward, aunque metodologicamente correcto, NO constituye validacion prospectiva "
          "independiente. El umbral de mejora de 5% en MAE es orientativo, no una frontera absoluta -- "
          "la evaluacion real combina MAE, RMSE, calibracion, incertidumbre (bootstrap de bloques) y "
          "estabilidad anual/por regimen de volatilidad. No se ha ajustado nada retrospectivamente tras "
          "ver estos resultados.")


if __name__ == '__main__':
    main(sys.argv[1])
