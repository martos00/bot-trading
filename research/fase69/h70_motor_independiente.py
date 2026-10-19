"""H70 — implementación INDEPENDIENTE de la cartera HOP (contraste de h70_motor.hop).
Bucle explícito mes a mes con numpy; no importa h70_motor. Mismas reglas del pre-registro.

Uso: python3 h70_motor_independiente.py PANEL_CSV SALIDA_CSV
"""
import sys
import numpy as np
import pandas as pd


def main():
    panel = pd.read_csv(sys.argv[1], index_col=0)
    R = panel.to_numpy(dtype=float)          # T x N, NaN = sin dato
    T, N = R.shape
    alfa = 1 / 7.0                           # centro de masa 6
    var = np.full(N, np.nan)
    nobs = np.zeros(N, int)
    logr = np.where(np.isnan(R), np.nan, np.log1p(R))
    pesos = np.zeros((T, N))
    for t in range(T):
        # EWMA: se actualiza solo con meses con dato
        for i in range(N):
            x = R[t, i]
            if not np.isnan(x):
                var[i] = x * x if np.isnan(var[i]) else (1 - alfa) * var[i] + alfa * x * x
                nobs[i] += 1
        w = np.zeros(N)
        for i in range(N):
            if nobs[i] < 24 or np.isnan(R[t, i]) or t < 11:
                continue
            ventanas = [logr[t - k + 1:t + 1, i] for k in (1, 3, 12)]
            if any(np.isnan(v).any() for v in ventanas):
                continue
            s = sum(np.sign(np.expm1(v.sum())) for v in ventanas) / 3
            sig = np.sqrt(12 * var[i])
            if sig > 0:
                w[i] = s / sig
        if w.any() and t + 1 >= 24:
            ini = max(0, t - 35)
            hist = np.nan_to_num(R[ini:t + 1]) @ w
            sd = hist.std(ddof=1) * np.sqrt(12)
            pesos[t] = w * (0.10 / sd) if sd > 0 else 0
    ret = np.full(T, np.nan)
    for t in range(1, T):
        mask = ~np.isnan(R[t]) & (pesos[t - 1] != 0)
        if mask.any():
            ret[t] = (pesos[t - 1][mask] * R[t][mask]).sum()
    pd.Series(ret, index=panel.index, name='hop_indep').to_csv(sys.argv[2])


if __name__ == '__main__':
    main()
