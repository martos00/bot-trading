"""H70 — motor de trend following diversificado (PREREGISTRO_H70_trend_following.md, sección 4).

Funciones:
  mop_12m(panel)            versión Moskowitz-Ooi-Pedersen (2012) para validar contra AQR TSMOM
  hop(panel, clases, ...)   Hurst-Ooi-Pedersen (2017): señales 1/3/12m, vol objetivo 10%
Todas las posiciones decididas al cierre del mes t se aplican a la rentabilidad del mes t+1.
"""
import numpy as np
import pandas as pd

COM_VOL = 6           # centro de masa (meses) de la EWMA de rentabilidades al cuadrado
MIN_HIST = 24         # meses de historia antes de que un mercado entre
VENTANA_ESCALA = 36   # meses para estimar la vol ex-ante de la cartera
VOL_OBJETIVO = 0.10
LOOKBACKS = (1, 3, 12)


def vol_ex_ante(panel):
    """Vol anualizada EWMA (sin desmediar) conocida al cierre de cada mes; NaN hasta MIN_HIST meses de datos."""
    alfa = 1 / (1 + COM_VOL)
    v = (panel ** 2).ewm(alpha=alfa, adjust=False, ignore_na=True).mean()
    n = panel.notna().cumsum()
    return np.sqrt(12 * v).where(n >= MIN_HIST)


def exceso_acumulado(panel, k):
    """Exceso acumulado de los últimos k meses (exige los k meses con dato)."""
    acum = np.log1p(panel).rolling(k, min_periods=k).sum()
    return np.expm1(acum)


def mop_12m(panel):
    sig = np.sign(exceso_acumulado(panel, 12))
    sigma = vol_ex_ante(panel)
    w = (sig * 0.40 / sigma).where(sig.notna() & sigma.notna())
    r = (w.shift(1) * panel)
    return r.mean(axis=1, skipna=True).where(r.notna().sum(axis=1) > 0), w


def senal_hop(panel):
    s = sum(np.sign(exceso_acumulado(panel, k)) for k in LOOKBACKS) / len(LOOKBACKS)
    return s.where(exceso_acumulado(panel, max(LOOKBACKS)).notna())


def escalar(w_bruto, panel):
    """Escala cada fila de pesos a VOL_OBJETIVO usando los últimos VENTANA_ESCALA meses (simulación histórica).
    Los meses sin dato de un mercado cuentan como 0 dentro de la ventana."""
    R = panel.fillna(0.0).to_numpy()
    W = w_bruto.fillna(0.0).to_numpy()
    k = np.full(len(W), np.nan)
    for t in range(len(W)):
        if not W[t].any() or t + 1 < MIN_HIST:
            continue
        ini = max(0, t - VENTANA_ESCALA + 1)
        hist = R[ini:t + 1] @ W[t]
        sd = hist.std(ddof=1) * np.sqrt(12)
        if sd > 0:
            k[t] = VOL_OBJETIVO / sd
    return w_bruto.mul(k, axis=0)


def hop(panel, clases, signo_fijo=None):
    """Devuelve (rentabilidad mensual de la cartera, pesos escalados). signo_fijo=+1 da el benchmark
    'siempre largo con los mismos pesos de riesgo'; una matriz de signos permite el control aleatorio."""
    sigma = vol_ex_ante(panel)
    s = senal_hop(panel)
    if signo_fijo is not None:
        s = (s * 0 + signo_fijo) if np.isscalar(signo_fijo) else signo_fijo.where(s.notna())
    w_bruto = (s / sigma).where(s.notna() & sigma.notna())
    w = escalar(w_bruto, panel)
    r = (w.shift(1) * panel).sum(axis=1, min_count=1)
    return r, w


def costes(w, panel, clases, escenario):
    """Coste mensual (fracción de NAV) por rotación + rolls + recargo anual de financiación."""
    tabla = {
        'futuros': {'EQ': (0.0002, 4, 0.0), 'BD': (0.0002, 4, 0.0), 'FX': (0.0002, 4, 0.0), 'CM': (0.0004, 6, 0.0)},
        'cfd': {'EQ': (0.0001, 0, 0.025), 'BD': (0.0002, 0, 0.025), 'FX': (0.0001, 0, 0.010), 'CM': (0.0003, 0, 0.025)},
    }[escenario]
    c1 = pd.Series({a: tabla[clases[a]][0] for a in w.columns})
    rolls = pd.Series({a: tabla[clases[a]][1] for a in w.columns})
    fin = pd.Series({a: tabla[clases[a]][2] for a in w.columns})
    wf = w.fillna(0.0)
    # deriva de los pesos durante el mes antes de rebalancear
    deriva = wf.shift(1) * (1 + panel.fillna(0.0))
    rot = (wf - deriva).abs()
    coste_rot = (rot * c1).sum(axis=1)
    pos = wf.shift(1).abs()  # nocional mantenido durante el mes t
    coste_roll = (pos * c1 * 2 * rolls / 12).sum(axis=1)
    coste_fin = (pos * fin / 12).sum(axis=1)
    # el coste de la rotación al cierre de t se paga en t+1 (mismo mes al que se aplica la posición)
    return coste_rot.shift(1).fillna(0) + coste_roll + coste_fin
