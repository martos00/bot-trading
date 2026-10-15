"""
VIX Spike Mean Reversion -- familia pospuesta por falta de datos,
desbloqueada con el historico VIX real de CBOE
(research/datos_externos/vix_history.csv, 1990-2026). Fundamento
academico: relacion documentada entre subidas abruptas del VIX
("fear gauge") y retornos posteriores del mercado de renta variable
(Giot 2005, "Relationships Between Implied Volatility Indexes and
Stock Index Returns", Journal of Portfolio Management; y la practica
extendida de "comprar el pico de miedo").

VIABILIDAD: VIX es un indice de EEUU (expectativa de volatilidad del
S&P 500) -- aplicable directamente a US500 y, por extension sectorial,
a USTEC (ambos indices de EEUU, altamente correlacionados en
episodios de risk-off). No se aplica a XAUUSD (el VIX no mide
volatilidad esperada del oro, aplicarlo ahi no tendria fundamento
economico directo).

REGLAS (unica version, pre-registrada, sin optimizar):
 - Señal: variacion diaria del VIX > percentil 90 de su propia
   distribucion de variaciones diarias de los ultimos 252 dias
   (causal) -- un "pico de miedo" inusual, no un umbral fijo
   arbitrario.
 - Direccion: SIEMPRE LARGO (comprar el pico de miedo, segun la
   literatura).
 - Entrada: Open del dia siguiente al pico. SL: 1,5xATR14. TP: 2R.
   Cierre forzoso: 5 dias de sesion. SL gana empates mismo dia.
 - Control: direccion aleatoria (mismo mecanismo, misma fecha/riesgo).
"""
import sys

import numpy as np
import pandas as pd

from orb_backtest import calcular_r_multiplos, metricas_en_r
from validacion_independiente_volexp import calcular_equity_simultanea, control_direccion_aleatoria
from estrategia_gap_fade import calcular_atr_diario
from datos_multiactivo import cargar_universo, UNIVERSO

RUTA_VIX = 'datos_externos/vix_history.csv'
PERCENTIL_PICO = 0.90
VENTANA_PERCENTIL = 252
RIESGO_EN_ATR = 1.5
TP_EN_R = 2.0
DIAS_MAX = 5
ESTRES_COSTE = [0.0, 1.0, 3.0]
SEED = 20261015


def cargar_vix():
    v = pd.read_csv(RUTA_VIX)
    v['dia'] = pd.to_datetime(v['DATE'], format='%m/%d/%Y')
    v = v.sort_values('dia').reset_index(drop=True)
    v['variacion'] = v['CLOSE'] / v['CLOSE'].shift(1) - 1.0
    v['percentil_variacion'] = v['variacion'].rolling(VENTANA_PERCENTIL).apply(
        lambda x: (x <= x.iloc[-1]).mean(), raw=False)
    return v[['dia', 'CLOSE', 'variacion', 'percentil_variacion']].rename(columns={'CLOSE': 'vix_close'})


def ejecutar(diario, vix, point):
    d = pd.merge(diario, vix, on='dia', how='inner').sort_values('dia').reset_index(drop=True)
    d['atr14_prev'] = calcular_atr_diario(d).shift(1)

    trades = []
    for i in range(1, len(d) - 1):
        if pd.isna(d['percentil_variacion'].iloc[i]) or d['percentil_variacion'].iloc[i] <= PERCENTIL_PICO:
            continue
        if pd.isna(d['atr14_prev'].iloc[i]) or d['atr14_prev'].iloc[i] <= 0:
            continue

        idx_entrada = i + 1
        precio_entrada = d['Open'].iloc[idx_entrada]
        riesgo = RIESGO_EN_ATR * d['atr14_prev'].iloc[i]
        sl = precio_entrada - riesgo
        tp = precio_entrada + TP_EN_R * riesgo

        idx_fin = min(idx_entrada + DIAS_MAX, len(d) - 1)
        resultado, motivo, idx_salida = None, None, idx_fin
        for j in range(idx_entrada, idx_fin + 1):
            hi, lo = d['High'].iloc[j], d['Low'].iloc[j]
            if lo <= sl:
                resultado, motivo, idx_salida = sl, 'SL', j
                break
            if hi >= tp:
                resultado, motivo, idx_salida = tp, 'TP', j
                break
        if resultado is None:
            resultado, motivo, idx_salida = d['Close'].iloc[idx_fin], 'CIERRE_PLAZO', idx_fin

        ret_bruto = resultado - precio_entrada
        spread_entrada = d['Spread'].iloc[idx_entrada] * point if pd.notna(d['Spread'].iloc[idx_entrada]) else 0.0
        trades.append(dict(dia=d['dia'].iloc[idx_entrada], anio=d['dia'].iloc[idx_entrada].year, direccion='largo',
                            idx_entrada=idx_entrada, idx_salida=idx_salida, precio_entrada=precio_entrada,
                            riesgo_puntos=riesgo, ret_bruto_puntos=ret_bruto, spread_entrada_precio=spread_entrada,
                            motivo_salida=motivo, peor_flotante_r=np.nan))
    return pd.DataFrame(trades), d


def main():
    vix = cargar_vix()
    universo = cargar_universo(['USTEC', 'US500'])
    for nombre, diario in universo.items():
        point = UNIVERSO[nombre]['point']
        ops, d = ejecutar(diario, vix, point)
        print(f"\n######## VIX Spike Mean Reversion -- {nombre} ########")
        print(f"Operaciones: {len(ops)}")
        if len(ops) == 0:
            print("  SIN OPERACIONES.")
            continue
        print(f"  Motivo salida: {ops['motivo_salida'].value_counts().to_dict()}")
        for extra in ESTRES_COSTE:
            etiqueta = "solo spread real" if extra == 0.0 else f"spread real + {extra:.0f}$ estres"
            ops_r = calcular_r_multiplos(ops, extra)
            m = metricas_en_r(ops_r)
            print(f"\n--- {etiqueta} ---")
            print(f"  n={m['n']}  Media R={m['media_R']:+.4f}  PF={m['profit_factor']:.3f}  "
                  f"%Acierto={m['pct_acierto']:.1f}%  Drawdown={m['max_drawdown_balance_R']:.2f}R")
            if extra == 0.0:
                for anio, g in ops_r.groupby('anio'):
                    mg = metricas_en_r(g)
                    print(f"    {anio}: n={mg['n']}  Media R={mg['media_R']:+.4f}  PF={mg['profit_factor']:.3f}")

        eq = calcular_equity_simultanea(ops, d)
        print(f"\n  Drawdown equity: {eq['max_drawdown_equity_R']:.2f}R")
        rng = np.random.default_rng(SEED)
        media_real, media_ctrl, std_ctrl, z = control_direccion_aleatoria(ops, rng)
        print(f"  Control direccion aleatoria: media real={media_real:+.4f}  media aleatoria={media_ctrl:+.4f}  z={z:+.2f}")


if __name__ == '__main__':
    main()
