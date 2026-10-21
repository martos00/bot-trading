"""¿Qué riesgo diario maximiza lo que se cobra por cada "plaza" de cuenta FTMO de 100.000 $?

Ciclo de vida simulado durante HORIZONTE días hábiles: se paga la evaluación (585 $), se hacen las dos fases
(10% y 5%, pérdida diaria 5% y máxima 10% del capital inicial, mínimo 4 días); si se suspende se paga otra. En la
cuenta financiada, cada 21 días hábiles, si hay beneficio se cobra el 80% y el saldo vuelve a 100.000 $ (la devolución
de la evaluación llega con el primer pago); si se rompe un límite se pierde la cuenta y se vuelve a empezar pagando.

Serie diaria: estrategia E1 (`e1_estrategia.construir`) con el coste de FTMO (0,70 pb) y cada nivel de riesgo.
Remuestreo por bloques e incertidumbre de la ventaja (como `simulador_fondeo.montecarlo`). Escenarios: ventaja
histórica, ventaja a la mitad (lo habitual tras publicarse una anomalía) y ventaja cero (solo suerte).
AVISO: el nivel de riesgo se elige con la misma historia de la que sale la ventaja; por eso se dan los tres escenarios.
Uso: python3 riesgo_optimo_ftmo.py ../certificacion/e1_franjas.csv
"""
import os, sys
import numpy as np
import pandas as pd

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'certificacion'))
import e1_estrategia as E  # noqa: E402
import simulador_fondeo as SF  # noqa: E402

PRECIO, REPARTO, CAPITAL, HORIZONTE, PAGO_CADA = 585, 0.80, 100_000, 756, 21
REG = SF.REGLAS['FTMO_2step']
RIESGOS = [0.0025, 0.005, 0.0075, 0.01, 0.0125, 0.015, 0.02]


def vida(r, m, rng):
    """Una plaza durante HORIZONTE días. Devuelve (neto $, evaluaciones pagadas, días financiada)."""
    n, d, neto, pagadas, dias_fin = len(r), 0, 0.0, 0, 0
    nxt = lambda: SF._bloques(n, 5, rng, 1)[0]
    i = rng.integers(n)
    def dia():
        nonlocal i
        i = rng.integers(n) if rng.random() < 0.2 else (i + 1) % n
        return r[i], m[i]
    while d < HORIZONTE:
        neto -= PRECIO; pagadas += 1
        ok = True
        for obj in REG.objetivos:                       # evaluación
            saldo, dias_op, mejor = 1.0, 0, 0.0
            while d < HORIZONTE:
                rd, md = dia(); d += 1
                if saldo + md * saldo <= saldo - REG.perdida_diaria or saldo + md * saldo <= 1 - REG.perdida_maxima:
                    ok = False; break
                pnl = rd * saldo; saldo += pnl; dias_op += 1; mejor = max(mejor, pnl)
                if saldo - 1 >= obj and dias_op >= REG.dias_minimos and mejor <= REG.consistencia * (saldo - 1):
                    break
            else:
                ok = False
            if not ok:
                break
        if not ok or d >= HORIZONTE:
            continue
        saldo, k, primer_pago = 1.0, 0, True             # cuenta financiada
        while d < HORIZONTE:
            rd, md = dia(); d += 1; dias_fin += 1; k += 1
            if saldo + md * saldo <= saldo - REG.perdida_diaria or saldo + md * saldo <= 1 - REG.perdida_maxima:
                break
            saldo += rd * saldo
            if k % PAGO_CADA == 0 and saldo > 1:
                neto += (saldo - 1) * CAPITAL * REPARTO + (PRECIO if primer_pago else 0)
                primer_pago = False; saldo = 1.0
    return neto, pagadas, dias_fin


if __name__ == '__main__':
    x = pd.read_csv(sys.argv[1], index_col=0, parse_dates=True)
    rng = np.random.default_rng(20261021)
    N = 3000
    filas = []
    for esc, f in (('histórica', 1.0), ('mitad', 0.5), ('cero', 0.0)):
        for rk in RIESGOS:
            d = E.construir(x, rk, 0.70)
            mu = d.ret.mean()
            r0, m0 = d.ret.values - mu * (1 - f), d.peor.values - mu * (1 - f)
            se = r0.std(ddof=1) / np.sqrt(len(r0))
            res = []
            for _ in range(N):
                delta = rng.normal(0, se) if f > 0 else 0.0
                res.append(vida(r0 + delta, np.minimum(m0 + delta, np.minimum(r0 + delta, 0)), rng))
            v = np.array(res)
            anual = v[:, 0] / (HORIZONTE / 252)
            filas.append({'ventaja': esc, 'riesgo_%': rk * 100, 'rent_anual_cuenta_%': round(mu * f * 252 * 100, 1),
                          'neto_medio_$/año': int(anual.mean()), 'mediana_$/año': int(np.median(anual)),
                          'p10_$/año': int(np.percentile(anual, 10)), 'p90_$/año': int(np.percentile(anual, 90)),
                          'P(pierde_dinero_3a)': round((v[:, 0] < 0).mean(), 2), 'evaluaciones_pagadas_3a': round(v[:, 1].mean(), 1),
                          '%tiempo_financiada': round(v[:, 2].mean() / HORIZONTE * 100)})
            print(filas[-1], flush=True)
    t = pd.DataFrame(filas)
    pd.set_option('display.width', 250); pd.set_option('display.max_columns', 20)
    print('\nPor plaza de cuenta FTMO de 100.000 $ (horizonte 3 años; cifras por año):')
    print(t.to_string(index=False))
