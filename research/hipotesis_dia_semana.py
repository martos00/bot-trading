"""
Hipotesis D del nuevo ciclo: estacionalidad por dia de la semana.

FASE 1 SOLAMENTE (identificar la ventaja antes de construir nada) --
igual disciplina que se aplico a RSI(2): no se construye SL/TP/riesgo
hasta confirmar que existe una señal medible y consistente. Distinta
del "efecto lunes" ya cerrado (estrategia_lunes.py): aqui se reportan
los 5 dias de la semana siempre (nunca se elige a posteriori cual
mostrar), sobre retorno Close-a-Close (definicion estandar de
estacionalidad por dia de semana en la literatura, incluye el hueco de
fin de semana atribuido al lunes).

PRE-REGISTRO:
 - ret_t = Close[t]/Close[t-1] - 1, agrupado por dia de la semana de t.
 - Incertidumbre: bootstrap de bloques de 10 dias consecutivos (misma
   convencion ya usada en RSI(2)), 2000 repeticiones, IC 95%.
 - XAUUSD se reporta en sus DOS tramos por separado (2015-2022 y
   2023-2026) -- no se trata 2015-2022 como holdout virgen, pero
   exigir que el mismo dia sea significativo y de MISMO SIGNO en
   ambos tramos es la barra para considerar que hay señal real y no
   ruido de un tramo concreto.
 - USTEC/US500 (solo 2023-2026, exploratorio) se reportan tambien,
   nunca como confirmacion independiente.
 - DECISION (fijada ahora, antes de ver ningun numero): solo se
   construye una estrategia completa (señal+SL+TP+coste) si al menos
   un dia tiene IC que excluye cero Y el mismo signo en AMBOS tramos de
   XAUUSD. Si no, se cierra aqui mismo sin backtest completo.
"""
import numpy as np
import pandas as pd

from hipotesis_rsi2_sma200 import bootstrap_bloques_ic
from datos_ciclo2 import cargar_xauusd_completo, cargar_ustec_2023_2026, cargar_us500_2023_2026

DIAS = ['Lunes', 'Martes', 'Miercoles', 'Jueves', 'Viernes']


def tabla_dia_semana(d, etiqueta):
    d = d.copy()
    d['ret'] = d['Close'] / d['Close'].shift(1) - 1.0
    d['dow'] = d['dia'].dt.dayofweek  # 0=Lunes
    print(f"\n--- {etiqueta} (n total={d['ret'].notna().sum()}) ---")
    resultados = {}
    for i, nombre in enumerate(DIAS):
        vals = d.loc[d['dow'] == i, 'ret'].dropna()
        if len(vals) < 20:
            print(f"  {nombre}: n={len(vals)} -- insuficiente, se omite")
            continue
        lo, hi = bootstrap_bloques_ic(vals.values)
        media = vals.mean()
        significativo = not (lo <= 0 <= hi)
        resultados[nombre] = dict(media=media, ic=(lo, hi), n=len(vals), significativo=significativo)
        marca = "  <-- IC excluye cero" if significativo else ""
        print(f"  {nombre}: n={len(vals)}  media={media*100:+.4f}%  IC95%=[{lo*100:+.4f}%, {hi*100:+.4f}%]{marca}")
    return resultados


def main():
    print("################ Hipotesis D: estacionalidad por dia de la semana ################")
    x = cargar_xauusd_completo()
    x_2015_2022 = x[x['dia'] < '2023-01-01']
    x_2023_2026 = x[x['dia'] >= '2023-01-01']
    r1 = tabla_dia_semana(x_2015_2022, 'XAUUSD 2015-2022')
    r2 = tabla_dia_semana(x_2023_2026, 'XAUUSD 2023-2026 (muy usado, exploratorio)')
    tabla_dia_semana(cargar_ustec_2023_2026(), 'USTEC 2023-2026 (exploratorio)')
    tabla_dia_semana(cargar_us500_2023_2026(), 'US500 2023-2026 (exploratorio)')

    print("\n--- Comprobacion de la regla de decision pre-registrada (XAUUSD, ambos tramos) ---")
    candidatos = []
    for nombre in DIAS:
        if nombre in r1 and nombre in r2 and r1[nombre]['significativo']:
            mismo_signo = np.sign(r1[nombre]['media']) == np.sign(r2[nombre]['media'])
            print(f"  {nombre}: significativo en 2015-2022 (media={r1[nombre]['media']*100:+.4f}%); "
                  f"2023-2026 media={r2[nombre]['media']*100:+.4f}%, mismo signo={mismo_signo}, "
                  f"significativo tambien en 2023-2026={r2[nombre]['significativo']}")
            if mismo_signo and r2[nombre]['significativo']:
                candidatos.append(nombre)
    if candidatos:
        print(f"\n  CANDIDATOS que pasan el criterio pre-registrado: {candidatos} -- proceder a construir estrategia completa.")
    else:
        print("\n  NINGUN dia cumple el criterio pre-registrado (significativo y mismo signo en ambos "
              "tramos de XAUUSD) -- SE CIERRA esta hipotesis aqui, sin construir señal/SL/TP/coste.")


if __name__ == '__main__':
    main()
