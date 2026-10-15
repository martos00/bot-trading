"""
Candidata (ciclo autonomo): Rotacion Risk-On/Risk-Off Oro-Equity.
Fundamento: el oro actua como activo refugio; cuando supera a la renta
variable en el ultimo mes (señal de aversion al riesgo), se espera
continuacion del patron defensivo; cuando la renta variable supera al
oro (apetito de riesgo), se espera continuacion risk-on. Familia
cross-asset, distinta de momentum de un solo activo.

Viabilidad: mismos datos diarios ya usados, sin dependencia horaria
intradia; variacion esperada en el signo de la diferencia de retornos
mensuales oro-equity (a diferencia del momentum puro, que no vario).

REGLAS: al cierre de cada mes, dif = ret_mensual(XAUUSD) - ret_mensual(USTEC).
Si dif>0 (oro ganó, risk-off) => LARGO USTEC el mes siguiente (apuesta a
reversion del sentimiento risk-off, igual mecanismo direccional simple
que ya usamos). Si dif<0 (equity ganó, risk-on) => tambien LARGO USTEC
(continuacion risk-on). Es decir, LARGO siempre que risk-on domine o
se espere reversion -- para separar bien de "siempre largo", se define
en realidad como: largo USTEC si dif<0 (equity ya ganaba, continua
risk-on), CORTO USTEC si dif>0 (oro ganaba, se espera que el malestar
continue y equity siga rezagado). SL=2xATR20, cierre a fin del mes
siguiente.
"""
import sys

import numpy as np
import pandas as pd

from orb_backtest import EXTRA_PUNTOS_ESTRES, calcular_r_multiplos, metricas_en_r
from hipotesis_rsi2_sma200 import cargar_m15, agregar_diario
from estrategia_gap_fade import agregar_diario_con_spread, calcular_atr_diario
from estrategia_momentum_series_temporales import construir_tabla_momentum


def main(path_ustec, path_oro):
    df_ustec = cargar_m15(path_ustec)
    diario_ustec = agregar_diario_con_spread(df_ustec)
    diario_ustec['atr20'] = calcular_atr_diario(diario_ustec, periodo=20)

    df_oro = cargar_m15(path_oro)
    diario_oro = agregar_diario(df_oro)

    # meses: usar la misma funcion de deteccion de fin de mes que momentum
    d_ustec, idx_fin_mes = construir_tabla_momentum(diario_ustec)

    # mapear cada dia de USTEC a su retorno mensual acumulado hasta ese fin de mes, y lo mismo para oro por fecha
    d_oro = diario_oro.set_index('dia')['Close']

    operaciones = []
    for k in range(len(idx_fin_mes) - 1):
        idx_fin_actual = idx_fin_mes[k]
        idx_fin_siguiente = idx_fin_mes[k + 1]
        idx_inicio_mes = (idx_fin_mes[k - 1] + 1) if k > 0 else 0
        idx_entrada = idx_fin_actual + 1
        if idx_entrada > idx_fin_siguiente or idx_entrada >= len(d_ustec):
            continue

        dia_fin = d_ustec['dia'].iloc[idx_fin_actual]
        dia_inicio = d_ustec['dia'].iloc[idx_inicio_mes]
        try:
            close_oro_fin = d_oro.asof(dia_fin)
            close_oro_inicio = d_oro.asof(dia_inicio)
        except KeyError:
            continue
        if pd.isna(close_oro_fin) or pd.isna(close_oro_inicio) or close_oro_inicio == 0:
            continue
        ret_oro = close_oro_fin / close_oro_inicio - 1.0
        ret_ustec = d_ustec['Close'].iloc[idx_fin_actual] / d_ustec['Close'].iloc[idx_inicio_mes] - 1.0
        dif = ret_oro - ret_ustec

        direccion = 'corto' if dif > 0 else 'largo'  # oro ganó -> corto equity; equity ganaba -> largo (continuacion)
        atr_entrada = d_ustec['atr20'].iloc[idx_fin_actual]
        if pd.isna(atr_entrada) or atr_entrada <= 0:
            continue
        precio_entrada = d_ustec['Open'].iloc[idx_entrada]
        riesgo = 2.0 * atr_entrada
        sl = precio_entrada - riesgo if direccion == 'largo' else precio_entrada + riesgo

        resultado_precio, motivo = None, None
        for j in range(idx_entrada, idx_fin_siguiente + 1):
            hi, lo = d_ustec['High'].iloc[j], d_ustec['Low'].iloc[j]
            toca_sl = (lo <= sl) if direccion == 'largo' else (hi >= sl)
            if toca_sl:
                resultado_precio, motivo = sl, 'SL'
                break
        if resultado_precio is None:
            resultado_precio, motivo = d_ustec['Close'].iloc[idx_fin_siguiente], 'CIERRE_MES'

        ret_bruto = (resultado_precio - precio_entrada) if direccion == 'largo' else (precio_entrada - resultado_precio)
        spread_entrada = d_ustec['Spread'].iloc[idx_entrada] * 0.01 if pd.notna(d_ustec['Spread'].iloc[idx_entrada]) else 0.0
        operaciones.append(dict(
            dia=d_ustec['dia'].iloc[idx_entrada], anio=d_ustec['dia'].iloc[idx_entrada].year,
            direccion=direccion, ret_bruto_puntos=ret_bruto, riesgo_puntos=riesgo,
            spread_entrada_precio=spread_entrada, motivo_salida=motivo, peor_flotante_r=np.nan,
        ))

    ops = pd.DataFrame(operaciones)
    print(f"\n\n######## USTEC (señal cruzada con XAUUSD) ########")
    print(f"Operaciones totales: {len(ops)}")
    if len(ops) == 0:
        print("  SIN OPERACIONES.")
        return
    print(f"  Direccion: {ops['direccion'].value_counts().to_dict()}")
    for extra in EXTRA_PUNTOS_ESTRES:
        etiqueta = f"spread real + {extra:.0f} pts estres" if extra > 0 else "SOLO spread real"
        ops_r = calcular_r_multiplos(ops, extra)
        m = metricas_en_r(ops_r)
        print(f"\n--- {etiqueta} ---")
        print(f"  n={m['n']}  Suma R={m['suma_R']:+.2f}  Media R={m['media_R']:+.4f}  "
              f"PF={m['profit_factor']:.3f}  %Acierto={m['pct_acierto']:.1f}%  Drawdown={m['max_drawdown_balance_R']:.2f}R")
        for anio, g in ops_r.groupby('anio'):
            mg = metricas_en_r(g)
            print(f"    {anio}: n={mg['n']}  Suma R={mg['suma_R']:+.2f}  Media R={mg['media_R']:+.4f}  PF={mg['profit_factor']:.3f}")
    print("  Motivo salida:", ops['motivo_salida'].value_counts().to_dict())


if __name__ == '__main__':
    main(sys.argv[1], sys.argv[2])
