"""
FOMC Cycle Effect -- DISTINTO del Pre/Post-FOMC Drift ya probado
(ese mide el dia del anuncio en si; este mide la posicion dentro del
CICLO de 6-8 semanas entre reuniones). Fundamento academico real:
Cieslak, Morse & Vissing-Jorgensen (2019), "Stock Returns over the
FOMC Cycle", Journal of Finance 74(5):2201-2248 -- desde 1994, la
prima de riesgo de renta variable se concentra en las semanas PARES
del ciclo FOMC (semana 0, 2, 4, 6... contando desde la ultima reunion),
atribuido a comunicacion informal de la Fed, no a una prima de riesgo
clasica. Aplicable principalmente a renta variable (USTEC/US500); se
prueba tambien en XAUUSD declarando que el fundamento es mas indirecto
ahi.

VIABILIDAD: calendario FECHAS_FOMC ya verificado (32 fechas 2023-2026,
~8 reuniones/año, ciclos de ~6-7 semanas) -- cientos de dias
clasificables en semana par/impar, muestra razonable para una prueba
de Fase 1.

FASE 1: retorno diario medio en semanas PARES vs. IMPARES del ciclo,
bootstrap de bloques (5 dias, 2000 repeticiones) sobre la diferencia.
"""
import numpy as np
import pandas as pd

from hipotesis_fomc_drift import FECHAS_FOMC
from datos_multiactivo import cargar_universo

SEED = 20261015
REPETICIONES = 2000
BLOQUE = 5


def clasificar_semana_ciclo(dias, fechas_fomc):
    fechas_fomc = sorted(fechas_fomc)
    resultado = []
    for dia in dias:
        anteriores = [f for f in fechas_fomc if f <= dia]
        if not anteriores:
            resultado.append(np.nan)
            continue
        ultima = anteriores[-1]
        semanas = (dia - ultima).days // 7
        resultado.append(semanas % 2)  # 0 = par, 1 = impar
    return np.array(resultado)


def bootstrap_diferencia(pares, impares, bloque=BLOQUE, repeticiones=REPETICIONES, seed=SEED):
    rng = np.random.default_rng(seed)
    medias = []
    for _ in range(repeticiones):
        n_p, n_i = len(pares), len(impares)
        bp = pares[rng.integers(0, max(n_p - bloque, 1) + 1, size=int(np.ceil(n_p / bloque)))[:, None] +
                    np.arange(bloque)].flatten()[:n_p]
        bi = impares[rng.integers(0, max(n_i - bloque, 1) + 1, size=int(np.ceil(n_i / bloque)))[:, None] +
                      np.arange(bloque)].flatten()[:n_i]
        medias.append(np.nanmean(bp) - np.nanmean(bi))
    medias = np.array(medias)
    return np.percentile(medias, 2.5), np.percentile(medias, 97.5)


def main():
    universo = cargar_universo(['XAUUSD', 'USTEC', 'US500'])
    print("################ FOMC Cycle Effect (semanas pares vs impares) ################")
    for nombre, diario in universo.items():
        d = diario[diario['dia'] >= '2023-01-01'].copy().reset_index(drop=True)
        d['ret'] = d['Close'] / d['Close'].shift(1) - 1.0
        d['paridad_semana'] = clasificar_semana_ciclo(d['dia'].dt.date.to_numpy(), FECHAS_FOMC)
        pares = d.loc[d['paridad_semana'] == 0, 'ret'].dropna().to_numpy()
        impares = d.loc[d['paridad_semana'] == 1, 'ret'].dropna().to_numpy()
        media_pares, media_impares = np.mean(pares), np.mean(impares)
        lo, hi = bootstrap_diferencia(pares, impares)
        diff = media_pares - media_impares
        significativo = not (lo <= 0 <= hi)
        print(f"  {nombre}: n_par={len(pares)} media={media_pares*100:+.4f}%/dia   "
              f"n_impar={len(impares)} media={media_impares*100:+.4f}%/dia   "
              f"diferencia={diff*100:+.4f}%/dia  IC95%=[{lo*100:+.4f}%, {hi*100:+.4f}%]"
              f"{'  <-- excluye cero' if significativo else '  (no significativo)'}")


if __name__ == '__main__':
    main()
