"""
Pre/Post-FOMC Drift, extendido a los 9 activos del universo (ya se
habia probado en USTEC/US500/XAUUSD intradia -- cerrada; aqui se
reformula en BARRA DIARIA, sin necesitar la reconstruccion de sesion
de NY, precisamente para poder incluir los 6 pares Forex nunca
probados frente a este calendario). Fundamento: el anuncio de tipos de
la Fed (14:00 ET) mueve sistematicamente el USD y los activos de
riesgo; la literatura de "pre-FOMC drift" (Lucca & Moench 2015) y de
reaccion post-anuncio documenta deriva direccional en los dias
alrededor del anuncio.

FASE 1 (identificar la ventaja antes de construir señal/SL/TP):
calendario FECHAS_FOMC ya verificado (hipotesis_fomc_drift.py, via
busqueda web). Se mide el retorno Open->Close del propio dia de FOMC y
el retorno Open(FOMC)->Close(FOMC+1) para cada activo, comparado contra
un benchmark de dias aleatorios NO-FOMC del mismo tamaño de muestra
(1000 repeticiones) -- igual disciplina de control que el resto del
proyecto.
"""
import numpy as np
import pandas as pd

from hipotesis_fomc_drift import FECHAS_FOMC
from datos_multiactivo import cargar_universo

SEED = 20261015
REPETICIONES = 1000


def medir(diario, fechas_fomc):
    d = diario.copy().reset_index(drop=True)
    d['dia_fecha'] = d['dia'].dt.date
    es_fomc = d['dia_fecha'].isin(fechas_fomc)
    idx_fomc = d.index[es_fomc].to_numpy()

    ret_dia_fomc, ret_fomc_mas1 = [], []
    for idx in idx_fomc:
        ret_dia_fomc.append(d['Close'].iloc[idx] / d['Open'].iloc[idx] - 1.0)
        if idx + 1 < len(d):
            ret_fomc_mas1.append(d['Close'].iloc[idx + 1] / d['Open'].iloc[idx] - 1.0)

    ret_dia_fomc, ret_fomc_mas1 = np.array(ret_dia_fomc), np.array(ret_fomc_mas1)

    ret_dia_todos = (d['Close'] / d['Open'] - 1.0).dropna().to_numpy()
    ret_2d_todos = []
    for idx in range(len(d) - 1):
        ret_2d_todos.append(d['Close'].iloc[idx + 1] / d['Open'].iloc[idx] - 1.0)
    ret_2d_todos = np.array(ret_2d_todos)

    rng = np.random.default_rng(SEED)

    def z_contra_aleatorio(valor_medio, poblacion, n_muestra):
        medias = [rng.choice(poblacion, size=n_muestra, replace=False).mean() for _ in range(REPETICIONES)]
        medias = np.array(medias)
        return (valor_medio - medias.mean()) / medias.std() if medias.std() > 0 else np.nan

    z_dia = z_contra_aleatorio(ret_dia_fomc.mean(), ret_dia_todos, len(ret_dia_fomc)) if len(ret_dia_fomc) >= 5 else np.nan
    z_2d = z_contra_aleatorio(ret_fomc_mas1.mean(), ret_2d_todos, len(ret_fomc_mas1)) if len(ret_fomc_mas1) >= 5 else np.nan

    return dict(n=len(ret_dia_fomc), media_dia_fomc=ret_dia_fomc.mean(), z_dia=z_dia,
                media_fomc_mas1=ret_fomc_mas1.mean(), z_2d=z_2d)


def main():
    universo = cargar_universo()
    print("################ FOMC drift -- 9 activos (barra diaria) ################")
    print(f"{'Activo':<8}{'n':>4}  {'Dia FOMC (Open->Close)':>26}  {'FOMC->+1d (Open->Close+1)':>28}")
    for nombre, diario in universo.items():
        r = medir(diario, FECHAS_FOMC)
        if r['n'] == 0:
            print(f"{nombre:<8}  sin fechas FOMC en el rango de datos")
            continue
        marca_dia = " <-- |z|>2" if abs(r['z_dia']) > 2 else ""
        marca_2d = " <-- |z|>2" if abs(r['z_2d']) > 2 else ""
        print(f"{nombre:<8}{r['n']:>4}  media={r['media_dia_fomc']*100:+.3f}% z={r['z_dia']:+.2f}{marca_dia}"
              f"      media={r['media_fomc_mas1']*100:+.3f}% z={r['z_2d']:+.2f}{marca_2d}")


if __name__ == '__main__':
    main()
