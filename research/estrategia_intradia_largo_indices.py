"""
Hipotesis F (continuacion tras Fase 1): construir la pieza que paso el
criterio pre-registrado -- LARGO intradia (Open->Close) todos los dias
en USTEC/US500, mismo mecanismo de riesgo ya usado en Efecto Lunes
(SL=1.5xATR14, cierre al Close si no se toca el SL, sin TP explicito
-- el objetivo natural de esta pieza ES el cierre del propio dia).

ADVERTENCIA METODOLOGICA (importante, no ocultar): esta pieza NO es una
señal condicional -- es LARGO INCONDICIONAL todos los dias de sesion.
Que el componente "overnight" tambien sea positivo (aunque no
significativo) en la Fase 1 implica que NO hay una asimetria real
donde evitar el overnight mejore el resultado total frente a estar
simplemente largo todo el tiempo -- lo que esta pieza captura es, en
gran parte, el hecho de que ambos indices subieron de forma sostenida
en 2023-2026 (mercado alcista), concentrado en la sesion diurna. Un
control de "direccion aleatoria" no es el contraste correcto aqui
(apostar por una direccion fija TODOS los dias no es comparable a
apostar aleatoriamente); el contraste relevante es frente al retorno
total Close-a-Close (si el intradia-solo no mejora el Sharpe/drawdown
frente a estar expuesto tambien overnight, no hay ninguna ventaja real
en esta construccion, solo beta).
"""
import sys

import numpy as np
import pandas as pd

from orb_backtest import calcular_r_multiplos, metricas_en_r
from validacion_independiente_volexp import calcular_equity_simultanea
from datos_ciclo2 import cargar_ustec_2023_2026, cargar_us500_2023_2026

SL_EN_ATR = 1.5
ESTRES_COSTE = [0.0, 1.0, 3.0]


def ejecutar(d, point):
    d = d.copy().reset_index(drop=True)
    trades = []
    for i in range(1, len(d)):
        row = d.iloc[i]
        if pd.isna(row['atr14_prev']) or row['atr14_prev'] <= 0:
            continue
        precio_entrada = row['Open']
        riesgo = SL_EN_ATR * row['atr14_prev']
        sl = precio_entrada - riesgo
        if row['Low'] <= sl:
            resultado, motivo = sl, 'SL'
        else:
            resultado, motivo = row['Close'], 'CIERRE_MISMO_DIA'
        ret_bruto = resultado - precio_entrada
        spread_entrada = row['Spread'] * point if pd.notna(row['Spread']) else 0.0
        trades.append(dict(
            dia=row['dia'], anio=row['dia'].year, direccion='largo',
            idx_entrada=i, idx_salida=i, precio_entrada=precio_entrada, riesgo_puntos=riesgo,
            ret_bruto_puntos=ret_bruto, spread_entrada_precio=spread_entrada, motivo_salida=motivo,
            regimen=row['regimen'], peor_flotante_r=np.nan,
        ))
    return pd.DataFrame(trades), d


def analizar(nombre, d, point):
    print(f"\n\n######## Largo intradia incondicional -- {nombre} ########")
    ops, d_full = ejecutar(d, point)
    print(f"Operaciones: {len(ops)}  Motivo salida: {ops['motivo_salida'].value_counts().to_dict()}")

    for extra in ESTRES_COSTE:
        etiqueta = "solo spread real" if extra == 0.0 else f"spread real + {extra:.0f}$ estres"
        ops_r = calcular_r_multiplos(ops, extra)
        m = metricas_en_r(ops_r)
        print(f"\n--- {etiqueta} ---")
        print(f"  n={m['n']}  Media R={m['media_R']:+.4f}  PF={m['profit_factor']:.3f}  "
              f"%Acierto={m['pct_acierto']:.1f}%  Drawdown balance={m['max_drawdown_balance_R']:.2f}R")
        for anio, g in ops_r.groupby('anio'):
            mg = metricas_en_r(g)
            print(f"    {anio}: n={mg['n']}  Media R={mg['media_R']:+.4f}  PF={mg['profit_factor']:.3f}")

    eq = calcular_equity_simultanea(ops, d_full)
    print(f"\n  Drawdown equity (nota: aqui no hay solapamiento real, 1 operacion/dia): {eq['max_drawdown_equity_R']:.2f}R")


def main():
    analizar('USTEC 2023-2026 (exploratorio)', cargar_ustec_2023_2026(), 0.01)
    analizar('US500 2023-2026 (exploratorio)', cargar_us500_2023_2026(), 0.01)


if __name__ == '__main__':
    main()
