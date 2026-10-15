"""
Autocorrelacion de retornos SEMANALES (lag-1) -- frecuencia nueva en
este proyecto (se ha probado diaria e intradia, nunca semanal).
Fundamento: la literatura de autocorrelacion de retornos a distintos
horizontes (ej. Lo & MacKinlay 1990, "When Are Contrarian Profits Due
to Stock Market Overreaction?", Review of Financial Studies) documenta
autocorrelacion semanal detectable (positiva en indices por efectos de
no-sincronia/liquidez, negativa en reversion de corto plazo segun el
mercado) -- DISTINTA de RSI(2) (oscilador diario) y de Momentum
Intradia (horas) ya cerrados.

FASE 1 (antes de construir señal/SL/TP): retorno semanal = Close del
ultimo dia de cotizacion de la semana ISO / Close de la semana ISO
anterior - 1. Autocorrelacion lag-1 (semana t-1 -> semana t), con
bootstrap de bloques (4 semanas, 2000 repeticiones) sobre el propio
coeficiente de correlacion (remuestreo por bloques de observaciones
pareadas).
"""
import numpy as np
import pandas as pd

from datos_multiactivo import cargar_universo

BLOQUE_BOOTSTRAP = 4
REPETICIONES = 2000
SEED = 20261015


def retornos_semanales(diario):
    d = diario.copy()
    d['semana_iso'] = d['dia'].dt.to_period('W')
    cierre_semanal = d.groupby('semana_iso')['Close'].last()
    ret = (cierre_semanal / cierre_semanal.shift(1) - 1.0).dropna()
    return ret


def autocorr_lag1_bootstrap(ret, bloque=BLOQUE_BOOTSTRAP, repeticiones=REPETICIONES, seed=SEED):
    x, y = ret.shift(1).dropna(), ret.iloc[1:]
    x = x.loc[y.index]
    n = len(y)
    corr_real = np.corrcoef(x, y)[0, 1]
    rng = np.random.default_rng(seed)
    corrs = []
    n_bloques = int(np.ceil(n / bloque))
    max_inicio = n - bloque
    xv, yv = x.to_numpy(), y.to_numpy()
    for _ in range(repeticiones):
        inicios = rng.integers(0, max_inicio + 1, size=n_bloques)
        idxs = np.concatenate([np.arange(s, s + bloque) for s in inicios])[:n]
        corrs.append(np.corrcoef(xv[idxs], yv[idxs])[0, 1])
    corrs = np.array(corrs)
    lo, hi = np.percentile(corrs, [2.5, 97.5])
    return corr_real, lo, hi, n


def main():
    universo = cargar_universo(['XAUUSD', 'USTEC', 'US500'])
    print("################ Autocorrelacion semanal (lag-1) ################")
    for nombre, diario in universo.items():
        ret = retornos_semanales(diario)
        corr, lo, hi, n = autocorr_lag1_bootstrap(ret)
        significativo = not (lo <= 0 <= hi)
        print(f"  {nombre}: n={n} semanas  corr(lag-1)={corr:+.4f}  IC95% bootstrap bloques=[{lo:+.4f}, {hi:+.4f}]"
              f"{'  <-- excluye cero' if significativo else '  (incluye cero, no significativo)'}")
        # desglose por mitad de la muestra, para ver si es estable o se concentra en un tramo
        mitad = n // 2
        ret_1 = ret.iloc[:mitad + 1]
        ret_2 = ret.iloc[mitad:]
        c1, l1, h1, n1 = autocorr_lag1_bootstrap(ret_1) if len(ret_1) > BLOQUE_BOOTSTRAP * 2 else (np.nan,)*4
        c2, l2, h2, n2 = autocorr_lag1_bootstrap(ret_2) if len(ret_2) > BLOQUE_BOOTSTRAP * 2 else (np.nan,)*4
        print(f"    primera mitad: n={n1} corr={c1:+.4f}   segunda mitad: n={n2} corr={c2:+.4f}")


if __name__ == '__main__':
    main()
