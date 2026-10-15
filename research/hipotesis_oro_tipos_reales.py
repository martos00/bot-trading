"""
Oro vs. Tipos de Interes Reales (TIPS 10 años) -- familia nueva,
desbloqueada con datos de FRED. Fundamento academico: el oro no paga
cupon/dividendo; mantenerlo tiene un coste de oportunidad igual al
tipo de interes REAL disponible en activos seguros (TIPS). Cuando el
tipo real cae, el coste de oportunidad de tener oro baja y tiende a
subir; cuando sube, tiende a bajar -- relacion documentada
explicitamente en Erb & Harvey (2013), "The Golden Dilemma",
Financial Analysts Journal 69(4):10-42. DISTINTA de USD-basket (tipo
nominal/divisa) y de FX Carry Trade (diferencial nominal entre
divisas) ya probados -- aqui la variable es el tipo REAL de EEUU en
si, no un diferencial entre divisas.

FASE 1 (antes de construir señal/SL/TP): correlacion contemporanea
(control de sanity, se espera negativa) y correlacion entre la
VARIACION del tipo real de HOY y el retorno del oro de MAÑANA (la
pieza accionable) -- con el mismo control de autocorrelacion propia
del oro ya usado en USD-basket.
"""
import numpy as np
import pandas as pd

from orb_backtest import calcular_r_multiplos, metricas_en_r
from validacion_independiente_volexp import calcular_equity_simultanea, control_direccion_aleatoria
from estrategia_gap_fade import calcular_atr_diario
from datos_multiactivo import cargar_universo, UNIVERSO

RUTA_TIPS = 'datos_externos/dfii10_real_yield.csv'
UMBRAL_Z = 1.0
RIESGO_EN_ATR = 1.5
TP_EN_R = 2.0
DIAS_MAX = 5
ESTRES_COSTE = [0.0, 1.0, 3.0]
SEED = 20261015


def cargar_tips():
    t = pd.read_csv(RUTA_TIPS)
    t.columns = ['dia', 'real_yield']
    t['dia'] = pd.to_datetime(t['dia'])
    t['real_yield'] = pd.to_numeric(t['real_yield'], errors='coerce')
    t = t.dropna().sort_values('dia').reset_index(drop=True)
    t['variacion'] = t['real_yield'].diff()
    t['z_variacion'] = t['variacion'] / t['variacion'].rolling(60).std()
    return t


def fase1(oro, tips):
    m = pd.merge(oro[['dia', 'Close']], tips, on='dia').sort_values('dia').reset_index(drop=True)
    m['ret_oro'] = m['Close'] / m['Close'].shift(1) - 1.0
    m['ret_oro_mañana'] = m['ret_oro'].shift(-1)
    m['ret_oro_ayer'] = m['ret_oro'].shift(1)

    corr_contemporanea = m['variacion'].corr(m['ret_oro'])
    corr_hoy_mañana = m['variacion'].corr(m['ret_oro_mañana'])
    corr_autocorr_oro = m['ret_oro_ayer'].corr(m['ret_oro'])
    print(f"  Correlacion contemporanea (variacion tipo real hoy, oro hoy): {corr_contemporanea:+.3f} (se espera negativa)")
    print(f"  Correlacion variacion tipo real HOY -> oro MAÑANA: {corr_hoy_mañana:+.3f}")
    print(f"  Control -- autocorrelacion propia del oro (ayer->hoy): {corr_autocorr_oro:+.3f}")
    return m


def ejecutar(oro, tips, point):
    d = pd.merge(oro, tips, on='dia').sort_values('dia').reset_index(drop=True)
    d['atr14_prev'] = calcular_atr_diario(d).shift(1)
    trades = []
    for i in range(1, len(d) - 1):
        z = d['z_variacion'].iloc[i]
        if pd.isna(z) or pd.isna(d['atr14_prev'].iloc[i]) or d['atr14_prev'].iloc[i] <= 0:
            continue
        if z > UMBRAL_Z:
            direccion = 'corto'  # tipo real subio fuerte -> oro menos atractivo
        elif z < -UMBRAL_Z:
            direccion = 'largo'
        else:
            continue

        idx_entrada = i + 1
        precio_entrada = d['Open'].iloc[idx_entrada]
        riesgo = RIESGO_EN_ATR * d['atr14_prev'].iloc[i]
        if direccion == 'largo':
            sl, tp = precio_entrada - riesgo, precio_entrada + TP_EN_R * riesgo
        else:
            sl, tp = precio_entrada + riesgo, precio_entrada - TP_EN_R * riesgo

        idx_fin = min(idx_entrada + DIAS_MAX, len(d) - 1)
        resultado, motivo, idx_salida = None, None, idx_fin
        for j in range(idx_entrada, idx_fin + 1):
            hi, lo = d['High'].iloc[j], d['Low'].iloc[j]
            if direccion == 'largo':
                toca_sl, toca_tp = lo <= sl, hi >= tp
            else:
                toca_sl, toca_tp = hi >= sl, lo <= tp
            if toca_sl:
                resultado, motivo, idx_salida = sl, 'SL', j
                break
            if toca_tp:
                resultado, motivo, idx_salida = tp, 'TP', j
                break
        if resultado is None:
            resultado, motivo, idx_salida = d['Close'].iloc[idx_fin], 'CIERRE_PLAZO', idx_fin

        ret_bruto = (resultado - precio_entrada) if direccion == 'largo' else (precio_entrada - resultado)
        spread_entrada = d['Spread'].iloc[idx_entrada] * point if pd.notna(d['Spread'].iloc[idx_entrada]) else 0.0
        trades.append(dict(dia=d['dia'].iloc[idx_entrada], anio=d['dia'].iloc[idx_entrada].year, direccion=direccion,
                            idx_entrada=idx_entrada, idx_salida=idx_salida, precio_entrada=precio_entrada,
                            riesgo_puntos=riesgo, ret_bruto_puntos=ret_bruto, spread_entrada_precio=spread_entrada,
                            motivo_salida=motivo, peor_flotante_r=np.nan))
    return pd.DataFrame(trades), d


def main():
    tips = cargar_tips()
    oro = cargar_universo(['XAUUSD'])['XAUUSD']
    point = UNIVERSO['XAUUSD']['point']

    print("################ Fase 1: Oro vs Tipos de Interes Reales (TIPS 10a) ################")
    fase1(oro, tips)

    ops, d = ejecutar(oro, tips, point)
    print(f"\nOperaciones: {len(ops)}")
    if len(ops) == 0:
        print("  SIN OPERACIONES.")
        return
    print(f"  Direccion: {ops['direccion'].value_counts().to_dict()}")
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
