"""
Clasificador de regimenes de mercado -- PRE-REGISTRADO antes de construir
cualquier estrategia del nuevo ciclo (ver README, "Metodologia mejorada
con regimenes"). Fijo desde este commit: no se ajustan los umbrales ni
el metodo tras ver el rendimiento de ninguna candidata.

Dos ejes, ambos causales (solo informacion conocida al cierre del propio
dia t, sin lookahead):

 - TENDENCIA: Close[t] > SMA200[t] => 'alcista', si no 'bajista' (misma
   convencion ya usada en hipotesis_rsi2_sma200.py).
 - VOLATILIDAD: ATR14[t-1]/Close[t-1] (ratio de volatilidad normalizado
   por precio, conocido ANTES de operar el dia t, igual timing que el
   resto del proyecto) clasificado en terciles mediante un PERCENTIL
   EXPANDIDO (rank sobre todo el historial visto hasta t-1 inclusive,
   nunca sobre datos futuros) -- 'baja' (<=p33), 'media' (p33-p66),
   'alta' (>p66). Los primeros 252 dias de cada serie no tienen
   suficiente historial para un percentil expandido estable y se
   marcan NaN/'insuficiente' (no se usan en los informes por regimen).

6 regimenes combinados: {alcista,bajista} x {baja,media,alta}. Se
reporta siempre el desglose completo (las 6 celdas, o las que tengan
operaciones) -- nunca se elige a posteriori cual mostrar.
"""
import numpy as np
import pandas as pd

PERIODO_SMA = 200
PERIODO_ATR = 14
MIN_HISTORIAL_PERCENTIL = 252


def calcular_atr_diario(diario, periodo=PERIODO_ATR):
    hi, lo, cl_prev = diario['High'], diario['Low'], diario['Close'].shift(1)
    tr = pd.concat([hi - lo, (hi - cl_prev).abs(), (lo - cl_prev).abs()], axis=1).max(axis=1)
    return tr.ewm(alpha=1.0 / periodo, adjust=False).mean()


def _percentil_expandido_causal(serie):
    """Para cada posicion i, el percentil de serie[i] dentro de
    serie[0..i] (incluye el propio valor, nunca mira adelante)."""
    valores = serie.to_numpy(dtype=float)
    out = np.full(len(valores), np.nan)
    for i in range(len(valores)):
        if i + 1 < MIN_HISTORIAL_PERCENTIL or np.isnan(valores[i]):
            continue
        ventana = valores[:i + 1]
        ventana = ventana[~np.isnan(ventana)]
        out[i] = (ventana <= valores[i]).mean()
    return out


def clasificar_regimenes(diario):
    d = diario.copy().reset_index(drop=True)
    d['sma200'] = d['Close'].rolling(PERIODO_SMA).mean()
    d['tendencia'] = np.where(d['Close'] > d['sma200'], 'alcista', 'bajista')
    d.loc[d['sma200'].isna(), 'tendencia'] = np.nan

    d['atr14'] = calcular_atr_diario(d)
    d['atr14_prev'] = d['atr14'].shift(1)
    d['close_prev'] = d['Close'].shift(1)
    d['vol_ratio'] = d['atr14_prev'] / d['close_prev']

    percentil = _percentil_expandido_causal(d['vol_ratio'])
    d['vol_percentil'] = percentil
    regimen_vol = pd.Series(np.where(percentil <= 0.33, 'baja', np.where(percentil <= 0.66, 'media', 'alta')),
                             index=d.index, dtype=object)
    regimen_vol[np.isnan(percentil)] = None
    d['regimen_vol'] = regimen_vol

    valido = d['tendencia'].notna() & d['regimen_vol'].notna()
    d['regimen'] = None
    d.loc[valido, 'regimen'] = d.loc[valido, 'tendencia'].astype(str) + '_' + d.loc[valido, 'regimen_vol'].astype(str)
    return d


def resumen_por_regimen(ops_r, columna_regimen='regimen'):
    """ops_r debe incluir la columna de regimen del DIA DE ENTRADA
    (hecho por cada script de estrategia, uniendo con el 'dia' de la
    señal). Imprime SIEMPRE las 6 celdas presentes, nunca una subselección."""
    print(f"  Desglose por regimen ({columna_regimen}):")
    for reg, g in ops_r.groupby(columna_regimen):
        if len(g) == 0:
            continue
        r = g['R'].to_numpy()
        pf = r[r > 0].sum() / abs(r[r <= 0].sum()) if r[r <= 0].sum() != 0 else np.nan
        print(f"    {reg}: n={len(g)}  Media R={r.mean():+.4f}  PF={pf:.3f}  %Acierto={(r > 0).mean() * 100:.1f}%")
