"""
Candidata (ciclo autonomo): Pairs/Spread Mean Reversion USTEC vs US500.
Fundamento: ambos indices son cestas de grandes empresas estadounidenses
altamente correlacionadas; desviaciones temporales de su ratio relativo
tienden a revertir (stat-arb clasico). Familia distinta: valor relativo
entre dos activos, no direccional en ninguno de los dos por separado.

Viabilidad: ambos tienen datos diarios ya verificados y alineados por
fecha; se opera un RATIO SINTETICO (adimensional) -- limitacion
declarada: ejecutar esto en real exigiria dos piernas con sus propios
costes de spread/financiacion, que este modelo no esta capturando con
precision (ver limitaciones).

REGLAS: ratio[t] = Close_USTEC[t]/Close_US500[t]; banda = media movil
20d +-2 desviaciones estandar moviles de ese ratio (igual mecanica de
bandas que VWAP mean reversion, aplicada aqui al ratio). Señal: ratio
toca la banda y CIERRA de vuelta dentro de ella en la misma vela (misma
confirmacion de rechazo que VWAP). Direccion: ratio en banda superior
(USTEC relativamente caro) => esperar reversion => corto del ratio
(equivalente a largo US500/corto USTEC, modelado aqui como una sola
serie de "retorno del ratio"). SL/TP en desviaciones del ratio mismo.
"""
import sys

import numpy as np
import pandas as pd

from orb_backtest import EXTRA_PUNTOS_ESTRES, calcular_r_multiplos, metricas_en_r
from hipotesis_rsi2_sma200 import cargar_m15, agregar_diario

PERIODO_BANDA = 20
N_DESVIACIONES = 2.0


def main(path_ustec, path_us500):
    d1 = agregar_diario(cargar_m15(path_ustec)).set_index('dia')
    d2 = agregar_diario(cargar_m15(path_us500)).set_index('dia')
    comun = d1.index.intersection(d2.index)
    d1, d2 = d1.loc[comun], d2.loc[comun]

    ratio = (d1['Close'] / d2['Close']).reset_index(drop=True)
    media = ratio.rolling(PERIODO_BANDA).mean()
    sigma = ratio.rolling(PERIODO_BANDA).std()
    banda_sup = media + N_DESVIACIONES * sigma
    banda_inf = media - N_DESVIACIONES * sigma

    dias = comun.to_numpy()
    operaciones = []
    i = PERIODO_BANDA
    while i < len(ratio) - 1:
        if pd.isna(banda_sup.iloc[i]):
            i += 1
            continue
        toca_sup = ratio.iloc[i] >= banda_sup.iloc[i]
        toca_inf = ratio.iloc[i] <= banda_inf.iloc[i]
        if toca_sup and toca_inf:
            i += 1
            continue
        if not (toca_sup or toca_inf):
            i += 1
            continue

        direccion = 'corto_ratio' if toca_sup else 'largo_ratio'
        entrada = ratio.iloc[i + 1] if i + 1 < len(ratio) else None
        if entrada is None:
            break
        riesgo = abs(ratio.iloc[i] - media.iloc[i])
        if riesgo <= 0:
            i += 1
            continue
        sl = entrada + riesgo if direccion == 'corto_ratio' else entrada - riesgo

        resultado, motivo = None, None
        for j in range(i + 1, min(i + 1 + 15, len(ratio))):
            tp_j = media.iloc[j] if not pd.isna(media.iloc[j]) else media.iloc[i]
            if direccion == 'corto_ratio':
                toca_sl_j, toca_tp_j = ratio.iloc[j] >= sl, ratio.iloc[j] <= tp_j
            else:
                toca_sl_j, toca_tp_j = ratio.iloc[j] <= sl, ratio.iloc[j] >= tp_j
            if toca_sl_j:
                resultado, motivo = sl, 'SL'
                break
            if toca_tp_j:
                resultado, motivo = tp_j, 'TP_MEDIA'
                break
        if resultado is None:
            resultado, motivo = ratio.iloc[min(i + 15, len(ratio) - 1)], 'CIERRE_PLAZO'

        ret_bruto = (resultado - entrada) if direccion == 'largo_ratio' else (entrada - resultado)
        operaciones.append(dict(
            dia=dias[i + 1] if i + 1 < len(dias) else dias[-1],
            anio=pd.Timestamp(dias[i + 1] if i + 1 < len(dias) else dias[-1]).year,
            direccion=direccion, ret_bruto_puntos=ret_bruto, riesgo_puntos=riesgo,
            spread_entrada_precio=0.0,  # LIMITACION: no se modela el coste real de las 2 piernas
            motivo_salida=motivo, peor_flotante_r=np.nan,
        ))
        i += 1

    ops = pd.DataFrame(operaciones)
    print(f"\n\n######## USTEC/US500 (ratio sintetico) ########")
    print(f"Operaciones totales: {len(ops)}")
    print("LIMITACION: no se modela el coste real de una operacion de 2 piernas (spread x2, "
          "posible financiacion de corto) -- estos resultados son SOLO un cribado de si existe "
          "reversion a la media en el spread, no un backtest ejecutable tal cual.")
    if len(ops) == 0:
        return
    print(f"  Direccion: {ops['direccion'].value_counts().to_dict()}")
    ops_r = calcular_r_multiplos(ops, 0.0)
    m = metricas_en_r(ops_r)
    print(f"  n={m['n']}  Suma R={m['suma_R']:+.2f}  Media R={m['media_R']:+.4f}  "
          f"PF={m['profit_factor']:.3f}  %Acierto={m['pct_acierto']:.1f}%  Drawdown={m['max_drawdown_balance_R']:.2f}R")
    for anio, g in ops_r.groupby('anio'):
        mg = metricas_en_r(g)
        print(f"    {anio}: n={mg['n']}  Suma R={mg['suma_R']:+.2f}  Media R={mg['media_R']:+.4f}  PF={mg['profit_factor']:.3f}")
    print("  Motivo salida:", ops['motivo_salida'].value_counts().to_dict())


if __name__ == '__main__':
    main(sys.argv[1], sys.argv[2])
