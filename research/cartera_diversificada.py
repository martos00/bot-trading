"""
Universo multi-clase de activos para la fase de carteras sistemáticas
(trend-following diversificado, vol-targeting/risk parity, momentum de
cartera -- ver README). Añade DOS clases de activo que faltaban en el
universo anterior (XAUUSD+USTEC+US500+6FX, todos correlacionados entre
si via USD/riesgo EEUU): BONOS (duración/tipos) y PETRÓLEO (materia
prima distinta del oro) -- sin esto, cualquier "risk parity" se queda
repartiendo riesgo dentro de un conjunto de activos ya parecidos entre
si, no entre clases de activo genuinamente distintas (equity, tipos,
materias primas, divisas).

BONO SINTETICO (declarado explicitamente, NO es el retorno real de un
ETF/futuro de bonos): aproximacion estandar de libro de texto --
retorno_diario ~= carry (y/365) - duracion_modificada * variacion de
yield. Se usa una duracion modificada CONSTANTE de 7 (aproximacion
razonable para el punto de 10 años a los niveles de yield de esta
muestra, NO calibrada/ajustada con resultados) sobre el yield real del
Tesoro a 10 años (FRED, DGS10). Esto es una aproximacion de manual, no
el retorno real de TLT/IEF (que incluye flujos de caja, rebalanceo del
indice, etc.) -- declarado para que no se confunda con datos reales de
un instrumento.

PETROLEO: precio real WTI (FRED, DCOILWTICO) -- retorno real, no
sintetico. Sin datos de spread real (FRED no los tiene) -- coste
modelado como ESTRES ETIQUETADO, igual disciplina que el resto del
proyecto con swap/slippage no confirmados.
"""
from pathlib import Path

import numpy as np
import pandas as pd

from datos_multiactivo import cargar_diario as cargar_diario_mt, UNIVERSO as UNIVERSO_MT

DUR_MOD_BONO = 7.0
ESTRES_OIL_PCT = 0.0005  # 0.05% por operacion, ESTRES ETIQUETADO, no spread real confirmado

RUTA_EXTERNOS = Path(__file__).parent / 'datos_externos'

ACTIVOS_MT = ['XAUUSD', 'USTEC', 'US500', 'EURUSD', 'GBPUSD', 'USDJPY', 'USDCAD', 'USDCHF', 'USDSEK']


def cargar_bono_sintetico():
    y = pd.read_csv(RUTA_EXTERNOS / 'dgs10_treasury10y.csv')
    y.columns = ['dia', 'yield_pct']
    y['dia'] = pd.to_datetime(y['dia'])
    y['yield_pct'] = pd.to_numeric(y['yield_pct'], errors='coerce')
    y = y.dropna().sort_values('dia').reset_index(drop=True)
    y['yield_dec'] = y['yield_pct'] / 100.0
    carry = y['yield_dec'].shift(1) / 365.0
    impacto_precio = -DUR_MOD_BONO * (y['yield_dec'] - y['yield_dec'].shift(1))
    y['ret'] = carry + impacto_precio
    y['Close'] = 100 * (1 + y['ret']).cumprod()  # nivel sintetico, solo para calcular High/Low/Open triviales
    y['Open'], y['High'], y['Low'] = y['Close'].shift(1).fillna(y['Close']), y[['Close']].max(axis=1), y[['Close']].min(axis=1)
    y['High'] = y[['Open', 'Close']].max(axis=1)
    y['Low'] = y[['Open', 'Close']].min(axis=1)
    y['Spread'] = np.nan
    return y.dropna(subset=['ret'])[['dia', 'Open', 'High', 'Low', 'Close', 'Spread', 'ret']].reset_index(drop=True)


def cargar_wti():
    w = pd.read_csv(RUTA_EXTERNOS / 'wti_oil.csv')
    w.columns = ['dia', 'Close']
    w['dia'] = pd.to_datetime(w['dia'])
    w['Close'] = pd.to_numeric(w['Close'], errors='coerce')
    w = w.dropna().sort_values('dia').reset_index(drop=True)
    w['ret'] = w['Close'] / w['Close'].shift(1) - 1.0
    w['Open'] = w['Close'].shift(1)
    w['High'] = w[['Open', 'Close']].max(axis=1)
    w['Low'] = w[['Open', 'Close']].min(axis=1)
    w['Spread'] = np.nan
    return w.dropna(subset=['ret'])[['dia', 'Open', 'High', 'Low', 'Close', 'Spread', 'ret']].reset_index(drop=True)


def cargar_universo_diversificado():
    """Devuelve dict nombre -> DataFrame con columnas dia,Open,High,Low,Close,Spread,ret,point,clase.
    Incluye los 9 activos ya usados (MetaQuotes-Demo/HistData) + bono
    sintetico (BONO_US10Y) + petroleo real (WTI)."""
    universo = {}
    for nombre in ACTIVOS_MT:
        d = cargar_diario_mt(nombre)
        d = d.copy()
        d['ret'] = d['Close'] / d['Close'].shift(1) - 1.0
        d['point'] = UNIVERSO_MT[nombre]['point']
        d['clase'] = UNIVERSO_MT[nombre]['clase']
        universo[nombre] = d.dropna(subset=['ret'])

    bono = cargar_bono_sintetico()
    bono['point'], bono['clase'] = np.nan, 'bono_sintetico'
    universo['BONO_US10Y'] = bono

    oil = cargar_wti()
    oil['point'], oil['clase'] = np.nan, 'materia_prima'
    universo['WTI'] = oil

    return universo


if __name__ == '__main__':
    universo = cargar_universo_diversificado()
    for nombre, d in universo.items():
        vol_anual = d['ret'].std() * np.sqrt(252) * 100
        print(f"{nombre} [{d['clase'].iloc[0] if 'clase' in d else '?'}]: {len(d)} dias, "
              f"{d['dia'].min().date()} -> {d['dia'].max().date()}, vol anualizada={vol_anual:.1f}%")
