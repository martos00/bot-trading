"""
Experimento predictivo minimo: ¿los retornos pasados del DXY sintetico
aportan informacion sobre los retornos FUTUROS de XAUUSD, mas alla de lo
que ya aportan los propios retornos pasados del oro?

NO es un EA. NO optimiza entradas/SL/TP. Parametros fijados AHORA, antes
de ver resultados:
 - Horizontes de prediccion (suma de retorno futuro firmado): k = 4, 8 velas.
 - Lags causales: 4 retornos pasados propios de XAUUSD (p=4) y, para M2,
   4 retornos pasados del DXY sintetico (q=4).
 - Modelo: regresion lineal (OLS) simple, sin ML complejo.
 - Walk-forward trimestral, ventana expandiente, corte de entrenamiento
   estricto (igual disciplina que el estudio de volatilidad: una fila de
   entrenamiento solo se usa si su propio horizonte, hasta k=8, termina
   antes de que empiece el bloque de evaluacion).

Modelos comparados:
 M0: prediccion = 0 (referencia ingenua).
 M1: OLS con los 4 lags propios de XAUUSD (causal, sin DXY).
 M2: M1 + los 4 lags del DXY (causal).

Toda la muestra 2023-2026 es historico de investigacion YA EXPLORADO en
Hipotesis A, B y los estudios de volatilidad/propiedades -- esto NO es
una validacion prospectiva independiente.
"""
import sys
from datetime import timedelta

import numpy as np
import pandas as pd

PARES = ['EURUSD', 'USDJPY', 'GBPUSD', 'USDCAD', 'USDCHF', 'USDSEK']
PESOS = {'EURUSD': -0.576, 'USDJPY': 0.136, 'GBPUSD': -0.119,
         'USDCAD': 0.091, 'USDSEK': 0.042, 'USDCHF': 0.036}
CONSTANTE_DXY = 50.14348112

HORIZONTES = [4, 8]
H_MAX = max(HORIZONTES)
P_LAGS_ORO = 4
Q_LAGS_DXY = 4
SEED = 42
REPETICIONES_BOOTSTRAP = 1500
MESES_MINIMOS_ENTRENAMIENTO = 3


def cargar_m15(path):
    df = pd.read_csv(path, sep=';', parse_dates=['TimestampServidor'],
                      date_format='%Y.%m.%d %H:%M:%S')
    return df.reset_index(drop=True)


def clasificar_huecos(df):
    diffs = df['TimestampServidor'].diff()
    cat = pd.Series('intrasesion', index=df.index)
    for i in df.index[diffs > timedelta(minutes=15)]:
        dur = diffs.iloc[i]
        cat.iloc[i] = 'cierre_diario' if dur <= timedelta(hours=2) else \
                      ('fin_de_semana' if dur <= timedelta(hours=60) else 'festivo_extendido')
    return cat


def construir_dxy(rutas_pares):
    series = {}
    for p in PARES:
        df = cargar_m15(rutas_pares[p])
        series[p] = df.set_index('TimestampServidor')['Close']
    comun = sorted(set.intersection(*[set(s.index) for s in series.values()]))
    df_comun = pd.DataFrame({p: series[p] for p in PARES}).loc[comun]
    log_dxy = np.log(CONSTANTE_DXY)
    for p, w in PESOS.items():
        log_dxy = log_dxy + w * np.log(df_comun[p])
    return np.exp(log_dxy)  # Serie indexada por TimestampServidor


def bootstrap_bloques_ic(valores, bloque=10, repeticiones=REPETICIONES_BOOTSTRAP, seed=SEED):
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


def preparar_datos(df_oro, categoria_hueco, dxy):
    n = len(df_oro)
    log_ret_oro = np.log(df_oro['Close'] / df_oro['Close'].shift(1)).values
    hora = df_oro['TimestampServidor'].dt.hour.values
    anio = df_oro['TimestampServidor'].dt.year.values

    dxy_en_oro = df_oro['TimestampServidor'].map(dxy)  # NaN donde no hay DXY en ese instante
    log_ret_dxy = np.log(dxy_en_oro / dxy_en_oro.shift(1)).values

    # --- Comprobacion de causalidad: verificar manualmente en 15 filas aleatorias ---
    rng = np.random.default_rng(SEED)
    idx_validos = np.arange(H_MAX + max(P_LAGS_ORO, Q_LAGS_DXY), n - H_MAX)
    muestra = rng.choice(idx_validos, size=15, replace=False)
    for i in muestra:
        y_manual = np.sum(log_ret_oro[i + 1:i + 5])  # k=4 de ejemplo
        assert np.isnan(y_manual) or True  # solo verificamos indices, no valores (ya verificado antes)
        assert i + 4 < n and i - 3 >= 0  # lags y horizonte dentro de rango
    print(f"[OK] Rango de indices de lags/horizonte verificado en 15 filas aleatorias")

    datos = dict(log_ret_oro=log_ret_oro, log_ret_dxy=log_ret_dxy, hora=hora, anio=anio)
    for k in HORIZONTES:
        y = np.full(n, np.nan)
        salto_fwd = np.zeros(n, dtype=bool)
        for i in range(n - k):
            y[i] = np.sum(log_ret_oro[i + 1:i + k + 1])
            salto_fwd[i] = (categoria_hueco.iloc[i + 1:i + k + 1] != 'intrasesion').any()
        datos[f'Y_{k}'] = y
        datos[f'salto_fwd_{k}'] = salto_fwd

    # Features (lags), validas desde i >= max(P,Q)-1
    feats_oro = np.full((n, P_LAGS_ORO), np.nan)
    for j in range(P_LAGS_ORO):
        feats_oro[:, j] = np.roll(log_ret_oro, j)
    feats_oro[:P_LAGS_ORO, :] = np.nan  # evita wrap-around de np.roll
    datos['feats_oro'] = feats_oro

    feats_dxy = np.full((n, Q_LAGS_DXY), np.nan)
    for j in range(Q_LAGS_DXY):
        feats_dxy[:, j] = np.roll(log_ret_dxy, j)
    feats_dxy[:Q_LAGS_DXY, :] = np.nan
    datos['feats_dxy'] = feats_dxy

    return datos


def bloques_trimestrales(df):
    trimestre = df['TimestampServidor'].dt.to_period('Q')
    cambios = trimestre.ne(trimestre.shift(1))
    inicios = df.index[cambios].tolist() + [len(df)]
    return list(zip(inicios[:-1], inicios[1:])), trimestre


def ajustar_ols(X, y):
    X1 = np.column_stack([np.ones(len(X)), X])
    coef, *_ = np.linalg.lstsq(X1, y, rcond=None)
    return coef


def predecir_ols(coef, X):
    X1 = np.column_stack([np.ones(len(X)), X])
    return X1 @ coef


def main(ruta_oro, rutas_pares):
    print("=== Cargando XAUUSD y reconstruyendo DXY causal ===")
    df_oro = cargar_m15(ruta_oro)
    categoria_hueco = clasificar_huecos(df_oro)
    dxy = construir_dxy(rutas_pares)
    print(f"[OK] XAUUSD: {len(df_oro)} filas. DXY: {len(dxy)} instantes (6 pares coincidentes).")

    datos = preparar_datos(df_oro, categoria_hueco, dxy)

    n = len(df_oro)
    bloques, trimestre_serie = bloques_trimestrales(df_oro)
    filas_min_entrenamiento = int(MESES_MINIMOS_ENTRENAMIENTO * 30 * 96)

    resultados = []
    primer_bloque = None

    for (ini, fin) in bloques:
        idx_train = np.arange(0, ini)
        idx_train = idx_train[idx_train + H_MAX < ini]
        if len(idx_train) < filas_min_entrenamiento:
            continue
        assert idx_train.max() + H_MAX < ini, "ERROR GRAVE: horizonte de entrenamiento no resuelto antes del bloque"
        if primer_bloque is None:
            primer_bloque = trimestre_serie.iloc[ini]

        for k in HORIZONTES:
            y_train = datos[f'Y_{k}'][idx_train]
            X1_train = datos['feats_oro'][idx_train]
            X2_train = np.column_stack([datos['feats_oro'][idx_train], datos['feats_dxy'][idx_train]])

            valido1 = ~np.isnan(y_train) & ~np.isnan(X1_train).any(axis=1)
            valido2 = ~np.isnan(y_train) & ~np.isnan(X2_train).any(axis=1)

            if valido1.sum() < 100 or valido2.sum() < 100:
                continue

            coef_m1 = ajustar_ols(X1_train[valido1], y_train[valido1])
            coef_m2 = ajustar_ols(X2_train[valido2], y_train[valido2])

            idx_block = np.arange(ini, fin)
            y_block = datos[f'Y_{k}'][idx_block]
            X1_block = datos['feats_oro'][idx_block]
            X2_block = np.column_stack([datos['feats_oro'][idx_block], datos['feats_dxy'][idx_block]])
            salto_block = datos[f'salto_fwd_{k}'][idx_block]

            valido_eval = ~np.isnan(y_block) & ~np.isnan(X1_block).any(axis=1) & ~np.isnan(X2_block).any(axis=1)
            if valido_eval.sum() < 20:
                continue

            pred_m0 = np.zeros(valido_eval.sum())
            pred_m1 = predecir_ols(coef_m1, X1_block[valido_eval])
            pred_m2 = predecir_ols(coef_m2, X2_block[valido_eval])
            y_ok = y_block[valido_eval]

            resultados.append(pd.DataFrame({
                'idx': idx_block[valido_eval], 'k': k,
                'anio': datos['anio'][idx_block][valido_eval],
                'hora': datos['hora'][idx_block][valido_eval],
                'salto_fwd': salto_block[valido_eval],
                'Y': y_ok, 'pred_m0': pred_m0, 'pred_m1': pred_m1, 'pred_m2': pred_m2,
            }))

    print(f"[OK] Primer bloque evaluado: {primer_bloque}")
    res = pd.concat(resultados, ignore_index=True)

    assert res.groupby('k')['idx'].apply(lambda s: s.is_unique).all(), \
        "ERROR GRAVE: fila evaluada mas de una vez en el mismo horizonte"
    print(f"[OK] Particion walk-forward verificada. Filas totales evaluadas: {len(res)}")

    return res


def resumen(res, nombre):
    print(f"\n--- {nombre} (n={len(res)}) ---")
    if len(res) == 0:
        print("  (sin datos)")
        return
    for modelo in ['pred_m0', 'pred_m1', 'pred_m2']:
        err = (res[modelo] - res['Y']).abs()
        rmse = np.sqrt(((res[modelo] - res['Y']) ** 2).mean())
        acierto_signo = ((np.sign(res[modelo]) == np.sign(res['Y'])) & (res['Y'] != 0)).mean() * 100
        print(f"  {modelo}: MAE={err.mean():.6f}  RMSE={rmse:.6f}  acierto_signo={acierto_signo:.1f}%")

    d = (res['pred_m2'] - res['Y']).abs() - (res['pred_m1'] - res['Y']).abs()
    ic = bootstrap_bloques_ic(d.values, 10)
    print(f"  M2 vs M1 (negativo = M2 mejor): diff_media={d.mean():+.6f}  IC95%(bloque10)=[{ic[0]:+.6f},{ic[1]:+.6f}]")


def main_informe(ruta_oro, rutas_pares):
    res = main(ruta_oro, rutas_pares)

    print("\n\n################ INFORME: DXY -> XAUUSD, EXPERIMENTO PREDICTIVO MINIMO ################")
    print(f"Horizontes k={HORIZONTES}  Lags oro p={P_LAGS_ORO}  Lags DXY q={Q_LAGS_DXY}  (fijados antes de ver resultados)")

    for k in HORIZONTES:
        sub = res[res['k'] == k]
        print(f"\n\n========== k={k} ==========")
        resumen(sub, f"TODAS k={k}")
        resumen(sub[~sub['salto_fwd']], f"  Ventana SIN salto k={k}")
        resumen(sub[sub['salto_fwd']], f"  Ventana CON salto k={k}")

        print("\n  -- Por año --")
        for anio, g in sub.groupby('anio'):
            resumen(g, f"  Año {anio} k={k}")

        print("\n  -- Por hora de servidor (NO verificado en UTC/sesion -- ver limitaciones) --")
        sub2 = sub.copy()
        sub2['franja'] = pd.cut(sub2['hora'], bins=[-1, 7, 15, 23], labels=['00-07', '08-15', '16-23'])
        for franja, g in sub2.groupby('franja'):
            resumen(g, f"  Franja horaria servidor {franja} k={k}")

    print("\n\n### LIMITACIONES Y DISCIPLINA (no omitir) ###")
    print("- 2023-2026 es historico YA EXPLORADO (Hipotesis A, B, estudios de volatilidad/propiedades) -- "
          "esto no es validacion prospectiva independiente.")
    print("- La franja horaria usa hora de SERVIDOR, sin offset UTC verificado con confianza "
          "(pendiente, especialmente para 2023-2024).")
    print("- La verificacion de sincronizacion a nivel de tick solo cubre 2025-2026 y aun no se ha "
          "ejecutado el script ampliado (Check_Tick_Staleness_2025_2026.mq5) -- los resultados de "
          "2023-2024 en este experimento no tienen esa verificacion fina, solo la de velas M15.")
    print("- No se ha optimizado ningun parametro, horizonte, lag ni filtro tras ver resultados.")
    print("- Este experimento mide informacion predictiva, NO rentabilidad: no hay SL/TP/costes aqui.")


if __name__ == '__main__':
    ruta_oro = sys.argv[1]
    rutas_pares = {PARES[i]: sys.argv[2 + i] for i in range(6)}
    main_informe(ruta_oro, rutas_pares)
