"""
Intervalo de confianza de la Media R del candidato Turtle System 2
(72 operaciones, XAUUSD+USTEC+US500) via cluster-bootstrap por AÑO, en
vez de bootstrap i.i.d. sobre operaciones individuales. Motivado por el
caveat ya documentado en el README: USTEC y US500 disparan señal en
fechas casi idénticas repetidamente, por lo que tratar las 72
operaciones como sorteos independientes (como hace el z vs. dirección
aleatoria de `estrategia_turtle_trading.analizar`) sobreestima la
confianza. Resamplear por AÑO (en vez de por operación) respeta que la
correlación cruzada entre mercados y la autocorrelación de régimen
ocurren DENTRO de cada año.
"""
import numpy as np
import pandas as pd

from datos_multiactivo import cargar_universo, UNIVERSO
from estrategia_turtle_trading import ejecutar_sistema
from orb_backtest import calcular_r_multiplos

SEED = 20261016
REPETICIONES = 5000


def construir_pool():
    mercados = ['XAUUSD', 'USTEC', 'US500']
    universo = cargar_universo(mercados)
    todas = []
    for m in mercados:
        ops = ejecutar_sistema(universo[m], 55, 20, UNIVERSO[m]['point'], False)
        ops['mercado'] = m
        todas.append(ops)
    pool = pd.concat(todas, ignore_index=True)
    return calcular_r_multiplos(pool, 0.0)


def bootstrap_iid(r, rng, reps=REPETICIONES):
    n = len(r)
    return np.array([r[rng.integers(0, n, size=n)].mean() for _ in range(reps)])


def bootstrap_cluster_anio(pool_r, rng, reps=REPETICIONES):
    anios = sorted(pool_r['anio'].unique())
    por_anio = {a: pool_r[pool_r['anio'] == a]['R'].to_numpy() for a in anios}
    medias = np.empty(reps)
    for b in range(reps):
        anios_resampleados = rng.choice(anios, size=len(anios), replace=True)
        valores = np.concatenate([por_anio[a] for a in anios_resampleados])
        medias[b] = valores.mean()
    return medias, len(anios)


def main():
    pool_r = construir_pool()
    r = pool_r['R'].to_numpy()
    media_real = r.mean()
    print(f"n={len(r)}  Media R real={media_real:+.4f}\n")

    print("Contribución por año:")
    for anio, g in pool_r.groupby('anio'):
        print(f"  {anio}: n={len(g)}  suma_R={g['R'].sum():+.3f}  media_R={g['R'].mean():+.3f}")

    rng = np.random.default_rng(SEED)
    medias_iid = bootstrap_iid(r, rng)
    lo_iid, hi_iid = np.percentile(medias_iid, 2.5), np.percentile(medias_iid, 97.5)
    print(f"\nBootstrap i.i.d. (asume {len(r)} sorteos independientes): "
          f"IC95%=[{lo_iid:+.4f}, {hi_iid:+.4f}]  P(media<=0)={(medias_iid<=0).mean()*100:.1f}%")

    medias_cluster, n_clusters = bootstrap_cluster_anio(pool_r, rng)
    lo_c, hi_c = np.percentile(medias_cluster, 2.5), np.percentile(medias_cluster, 97.5)
    print(f"Cluster-bootstrap por año (n_clusters={n_clusters}): "
          f"IC95%=[{lo_c:+.4f}, {hi_c:+.4f}]  P(media<=0)={(medias_cluster<=0).mean()*100:.1f}%")


if __name__ == '__main__':
    main()
