"""
Hipotesis E del nuevo ciclo: Opening Range Breakout SEMANAL.

Fundamento economico: el primer dia de la semana de negociacion fija un
rango que refleja el posicionamiento/flujo de ordenes acumulado durante
el fin de semana; una ruptura de ese rango durante el resto de la
semana refleja conviccion direccional adicional -- analogo SEMANAL del
ORB intradia ya cerrado (ese operaba en apertura de sesion M15; este
opera en la unidad de tiempo semana/dia, sin ninguna reconstruccion
horaria intradia).

VIABILIDAD (comprobada antes de programar):
 - Toda semana tiene un primer dia de negociacion (lunes salvo festivo)
   -- rango bien definido todas las semanas.
 - Como mucho 1 señal por semana (evita señales correlacionadas por
   solapamiento dentro de la misma semana).
 - Ambiguedad declarada: si el mismo dia rompe ambos lados del rango de
   apertura, no se puede saber el orden intradia real -- ese dia se
   descarta sin señal (no se inventa cual ocurrio primero).

REGLAS (unica version, pre-registrada, sin optimizar):
 - Rango de apertura semanal = High/Low del PRIMER dia de negociacion
   de cada semana ISO.
 - Señal: el primer dia POSTERIOR de esa misma semana cuyo High supera
   el High de apertura (sin que tambien su Low rompa el Low de apertura
   el mismo dia -- ver ambiguedad arriba) => LARGO; simetrico para
   CORTO. Solo la PRIMERA ruptura de la semana cuenta.
 - Entrada: Open[t+1] (sin lookahead, mismo criterio del proyecto).
 - SL: el lado opuesto del rango de apertura semanal. TP: 2R. Cierre
   forzoso: 5 dias de sesion (igual convencion que el resto del
   proyecto, no limitado a "lo que queda de semana" para no añadir un
   parametro mas). SL gana empates mismo dia.
"""
import sys

import numpy as np
import pandas as pd

from orb_backtest import calcular_r_multiplos, metricas_en_r
from validacion_independiente_volexp import calcular_equity_simultanea, control_direccion_aleatoria
from regimenes_mercado import resumen_por_regimen
from datos_ciclo2 import MERCADOS

TP_EN_R = 2.0
DIAS_MAX_EN_MERCADO = 5
ESTRES_COSTE = [0.0, 1.0, 3.0]
SEED = 20261015


def ejecutar(d, point):
    d = d.copy().reset_index(drop=True)
    d['semana_iso'] = d['dia'].dt.isocalendar().year.astype(str) + '-' + d['dia'].dt.isocalendar().week.astype(str)
    primer_dia_semana = d.groupby('semana_iso')['dia'].idxmin()
    d['es_apertura_semana'] = d.index.isin(primer_dia_semana)

    trades = []
    semana_actual, hi_apertura, lo_apertura, ya_señalada = None, None, None, False
    for i in range(len(d) - 1):
        row = d.iloc[i]
        if row['es_apertura_semana']:
            semana_actual, hi_apertura, lo_apertura, ya_señalada = row['semana_iso'], row['High'], row['Low'], False
            continue
        if semana_actual is None or row['semana_iso'] != semana_actual or ya_señalada:
            continue

        rompe_arriba = row['High'] > hi_apertura
        rompe_abajo = row['Low'] < lo_apertura
        if rompe_arriba and rompe_abajo:
            continue  # ambiguo, no se inventa el orden intradia
        if not rompe_arriba and not rompe_abajo:
            continue

        direccion = 'largo' if rompe_arriba else 'corto'
        idx_entrada = i + 1
        precio_entrada = d['Open'].iloc[idx_entrada]
        if direccion == 'largo':
            sl = lo_apertura
            riesgo = precio_entrada - sl
            tp = precio_entrada + TP_EN_R * riesgo
        else:
            sl = hi_apertura
            riesgo = sl - precio_entrada
            tp = precio_entrada - TP_EN_R * riesgo
        if riesgo <= 0:
            ya_señalada = True
            continue
        ya_señalada = True

        idx_fin = min(idx_entrada + DIAS_MAX_EN_MERCADO, len(d) - 1)
        resultado_precio, motivo, idx_salida = None, None, idx_fin
        for j in range(idx_entrada, idx_fin + 1):
            hi, lo = d['High'].iloc[j], d['Low'].iloc[j]
            if direccion == 'largo':
                toca_sl, toca_tp = lo <= sl, hi >= tp
            else:
                toca_sl, toca_tp = hi >= sl, lo <= tp
            if toca_sl:
                resultado_precio, motivo, idx_salida = sl, 'SL', j
                break
            if toca_tp:
                resultado_precio, motivo, idx_salida = tp, 'TP', j
                break
        if resultado_precio is None:
            resultado_precio, motivo, idx_salida = d['Close'].iloc[idx_fin], 'CIERRE_PLAZO', idx_fin

        ret_bruto = (resultado_precio - precio_entrada) if direccion == 'largo' else (precio_entrada - resultado_precio)
        spread_entrada = d['Spread'].iloc[idx_entrada] * point if pd.notna(d['Spread'].iloc[idx_entrada]) else 0.0
        trades.append(dict(
            dia=d['dia'].iloc[idx_entrada], anio=d['dia'].iloc[idx_entrada].year, direccion=direccion,
            idx_entrada=idx_entrada, idx_salida=idx_salida, precio_entrada=precio_entrada, riesgo_puntos=riesgo,
            ret_bruto_puntos=ret_bruto, spread_entrada_precio=spread_entrada, motivo_salida=motivo,
            regimen=row['regimen'], peor_flotante_r=np.nan,
        ))
    return pd.DataFrame(trades), d


def analizar(nombre, d, point):
    print(f"\n\n######## Hipotesis E (ORB semanal) -- {nombre} ########")
    ops, d_full = ejecutar(d, point)
    print(f"Operaciones: {len(ops)}")
    if len(ops) == 0:
        print("  SIN OPERACIONES.")
        return
    print(f"  Direccion: {ops['direccion'].value_counts().to_dict()}")
    print("  Motivo salida:", ops['motivo_salida'].value_counts().to_dict())

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
        if extra == 0.0:
            resumen_por_regimen(ops_r)

    eq = calcular_equity_simultanea(ops, d_full)
    print(f"\n  Max posiciones simultaneas: {eq['max_posiciones_simultaneas']}  "
          f"Drawdown equity: {eq['max_drawdown_equity_R']:.2f}R ({eq['dia_max_drawdown'].date()})")

    rng = np.random.default_rng(SEED)
    media_real, media_ctrl, std_ctrl, z = control_direccion_aleatoria(ops, rng)
    print(f"  Control direccion aleatoria: media real={media_real:+.4f}  media aleatoria={media_ctrl:+.4f}  z={z:+.2f}")


def main():
    for nombre, cfg in MERCADOS.items():
        d = cfg['cargar']()
        analizar(f"{nombre} [{cfg['tramo']}]", d, cfg['point'])


if __name__ == '__main__':
    main()
