"""
Halloween Effect / "Sell in May and Go Away" -- familia estacional
documentada en literatura academica REVISADA POR PARES (Bouman &
Jacobsen 2002, American Economic Review, 92(5):1618-1635 -- muestra
1970-1998, indices de 37 paises, efecto presente en 36 de 37;
extension posterior Jacobsen & Zhang, 108 mercados, retorno invierno
4,52pp mayor que verano, t=9,69). DISTINTA de Turno de Mes (ya
cerrada, efecto de unos pocos dias) y de la ventana Dic/Ene (ya
cerrada por falta de potencia) -- aqui el efecto es de SEMESTRE
completo (Nov-Abr vs. May-Oct), documentado principalmente en indices
de RENTA VARIABLE (el fundamento para materias primas como el oro es
mas debil/indirecto -- se declara esta diferencia, no se finge
igual de solido para XAUUSD que para USTEC/US500).

LECCION APLICADA de CPI Drift (recien descubierta): para un
mantenimiento de varios MESES, usar contabilidad de retorno RAW (%),
NO un marco de R-multiplo con stop-loss diario ajustado -- ese marco
amplifica artificialmente cualquier resultado (como se encontro en
CPI Drift). Aqui se reporta retorno simple de temporada, sin SL.

REGLAS (unica version, pre-registrada, sin optimizar):
 - "Invierno" = Open del primer dia de cotizacion de noviembre -> Close
   del ultimo dia de cotizacion de abril (LARGO).
 - "Verano" = Open del primer dia de cotizacion de mayo -> Close del
   ultimo dia de cotizacion de octubre (SIN POSICION -- la version mas
   conservadora del hallazgo original: "el verano no aporta", no se
   asume que apostar corto en verano funcione, eso es una extension
   mas debil del hallazgo).
 - Coste: spread real de las 2 fechas de entrada/salida por temporada
   de invierno (entrada en noviembre, salida en abril).
 - Comparacion: retorno de invierno vs. retorno de verano del MISMO
   año, bootstrap pareado (2000 repeticiones) sobre los pares
   disponibles.
"""
import numpy as np
import pandas as pd

from datos_multiactivo import cargar_universo, UNIVERSO

SEED = 20261015
REPETICIONES = 2000


def construir_temporadas(diario, point):
    d = diario.sort_values('dia').reset_index(drop=True)
    d['anio'], d['mes'] = d['dia'].dt.year, d['dia'].dt.month

    temporadas = []
    for anio in sorted(d['anio'].unique()):
        # Invierno: nov(anio) -> abr(anio+1)
        inv = d[((d['anio'] == anio) & (d['mes'] == 11)) | ((d['anio'] == anio + 1) & (d['mes'].between(1, 4)))]
        if len(inv) < 20:
            continue
        idx_ini, idx_fin = inv.index[0], inv.index[-1]
        ret_bruto = d['Close'].iloc[idx_fin] / d['Open'].iloc[idx_ini] - 1.0
        coste = ((d['Spread'].iloc[idx_ini] * point if pd.notna(d['Spread'].iloc[idx_ini]) else 0.0) +
                 (d['Spread'].iloc[idx_fin] * point if pd.notna(d['Spread'].iloc[idx_fin]) else 0.0)) / d['Open'].iloc[idx_ini]
        ret_invierno = ret_bruto - coste

        ver = d[(d['anio'] == anio) & (d['mes'].between(5, 10))]
        if len(ver) < 20:
            continue
        idx_ini_v, idx_fin_v = ver.index[0], ver.index[-1]
        ret_verano = d['Close'].iloc[idx_fin_v] / d['Open'].iloc[idx_ini_v] - 1.0

        temporadas.append(dict(anio=anio, ret_invierno=ret_invierno, ret_verano=ret_verano))
    return pd.DataFrame(temporadas)


def bootstrap_pareado(diferencias, repeticiones=REPETICIONES, seed=SEED):
    rng = np.random.default_rng(seed)
    n = len(diferencias)
    if n < 3:
        return np.nan, np.nan
    medias = [rng.choice(diferencias, size=n, replace=True).mean() for _ in range(repeticiones)]
    return np.percentile(medias, 2.5), np.percentile(medias, 97.5)


def main():
    universo = cargar_universo(['XAUUSD', 'USTEC', 'US500'])
    for nombre, diario in universo.items():
        point = UNIVERSO[nombre]['point']
        temporadas = construir_temporadas(diario, point)
        print(f"\n######## Halloween Effect -- {nombre} ({len(temporadas)} pares invierno/verano) ########")
        if len(temporadas) == 0:
            print("  SIN TEMPORADAS COMPLETAS.")
            continue
        print(temporadas.to_string(index=False, formatters={'ret_invierno': '{:+.2%}'.format, 'ret_verano': '{:+.2%}'.format}))
        media_inv, media_ver = temporadas['ret_invierno'].mean(), temporadas['ret_verano'].mean()
        diffs = (temporadas['ret_invierno'] - temporadas['ret_verano']).to_numpy()
        lo, hi = bootstrap_pareado(diffs)
        print(f"\n  Media invierno={media_inv*100:+.2f}%  Media verano={media_ver*100:+.2f}%  "
              f"Diferencia media={diffs.mean()*100:+.2f}%  IC95% bootstrap=[{lo*100:+.2f}%, {hi*100:+.2f}%]"
              f"{'  <-- excluye cero' if not (lo <= 0 <= hi) else '  (incluye cero, no significativo)'}")
        print(f"  Temporadas de invierno positivas: {(temporadas['ret_invierno']>0).sum()}/{len(temporadas)}  "
              f"Temporadas de verano positivas: {(temporadas['ret_verano']>0).sum()}/{len(temporadas)}")


if __name__ == '__main__':
    main()
