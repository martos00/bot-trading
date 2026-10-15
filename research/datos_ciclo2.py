"""
Carga de datos compartida para el nuevo ciclo de investigacion (ver
README, "Metodologia mejorada con regimenes"). Centraliza aqui las
rutas y la construccion de barra diaria + regimen, para que las ~7
hipotesis de este ciclo reutilicen EXACTAMENTE la misma preparacion de
datos (nada de recalcular ATR/SMA/regimen de formas distintas por
script).

POLITICA DE USO DE DATOS DE ESTE CICLO (fijada antes de programar
ninguna hipotesis):
 - XAUUSD: historico COMPLETO 2015-2026 (HistData 2015-2022 + MetaQuotes-
   Demo 2023-2026, concatenados). 2015-2022 YA SE USO UNA VEZ para
   validar (y descartar) Volatility Expansion Continuation -- no se
   trata como holdout virgen para las estrategias NUEVAS de este ciclo,
   pero tampoco esta "quemado": una sola validacion de una familia de
   reglas distinta no es lo mismo que haber minado patrones en el, as
   que se usa con normalidad para desarrollo + se exige consistencia
   AMBOS lados (2015-2022 y 2023-2026) antes de llamar a nada
   "prometedora", precisamente para no depender de un tramo ya tocado.
 - USTEC / US500: solo 2023-2026 disponible (sin historico pre-2023,
   no se compra ni se busca otra fuente sin consultar). Este tramo ya
   se ha usado intensivamente en el desarrollo de ~14 candidatas
   anteriores -- cualquier resultado aqui se trata como EXPLORATORIO,
   nunca como validacion independiente (misma convencion ya aplicada a
   RSI(2) en 2023-2026).

DIFERENCIA DE ZONA HORARIA EN LA SERIE XAUUSD CONCATENADA (declarada,
no corregida -- igual criterio que con Dukascopy): las barras antes de
2023-01-03 agregan por dia de calendario EST sin DST (convencion de
HistData); desde 2023-01-03 agregan por dia de calendario de servidor
EET/EEST (convencion MetaQuotes-Demo). Esto crea UNA discontinuidad en
el punto de union (no un sesgo recurrente) -- irrelevante para ATR/SMA
de periodo <=200 pasado un año desde la union, pero se declara.
"""
from pathlib import Path

import pandas as pd

from hipotesis_rsi2_sma200 import cargar_m15
from estrategia_gap_fade import agregar_diario_con_spread
from regimenes_mercado import clasificar_regimenes

RUTA_XAUUSD_2015_2022 = '/tmp/claude-0/-home-user-bot-trading/0b8bbddf-7bd5-59ce-baf0-0685f40ca055/scratchpad/XAUUSD_M15_histdata_2015_2022.csv'
RUTA_XAUUSD_2023_2026 = '/root/.claude/uploads/0b8bbddf-7bd5-59ce-baf0-0685f40ca055/20c75528-XAUUSD_M15_Export.csv'
RUTA_USTEC_2023_2026 = '/root/.claude/uploads/0b8bbddf-7bd5-59ce-baf0-0685f40ca055/3b9869d6-USTEC_M15_Export.csv'
RUTA_US500_2023_2026 = '/root/.claude/uploads/0b8bbddf-7bd5-59ce-baf0-0685f40ca055/1eac00f2-US500_M15_Export.csv'


def _diario_con_regimen(df_m15):
    diario = agregar_diario_con_spread(df_m15)
    return clasificar_regimenes(diario)


def cargar_xauusd_completo():
    a = cargar_m15(RUTA_XAUUSD_2015_2022)
    b = cargar_m15(RUTA_XAUUSD_2023_2026)
    df = pd.concat([a, b], ignore_index=True).sort_values('TimestampServidor').reset_index(drop=True)
    assert df['TimestampServidor'].is_monotonic_increasing
    assert df['TimestampServidor'].duplicated().sum() == 0
    return _diario_con_regimen(df)


def cargar_ustec_2023_2026():
    return _diario_con_regimen(cargar_m15(RUTA_USTEC_2023_2026))


def cargar_us500_2023_2026():
    return _diario_con_regimen(cargar_m15(RUTA_US500_2023_2026))


MERCADOS = {
    'XAUUSD': dict(cargar=cargar_xauusd_completo, point=0.01, tramo='2015-2026 (XAUUSD 2015-2022 no es holdout virgen -- ver docstring)'),
    # point=0.01 para los 3 mercados: Digits=2 en los tres (ver comentario en orb_backtest.py main()).
    'USTEC': dict(cargar=cargar_ustec_2023_2026, point=0.01, tramo='2023-2026 (exploratorio, tramo muy usado)'),
    'US500': dict(cargar=cargar_us500_2023_2026, point=0.01, tramo='2023-2026 (exploratorio, tramo muy usado)'),
}


if __name__ == '__main__':
    for nombre, cfg in MERCADOS.items():
        d = cfg['cargar']()
        n_con_regimen = d['regimen'].notna().sum()
        print(f"{nombre} [{cfg['tramo']}]: {len(d)} barras diarias, {d['dia'].min().date()} -> {d['dia'].max().date()}, "
              f"{n_con_regimen} con regimen clasificado ({n_con_regimen/len(d)*100:.0f}%)")
        print("  ", d['regimen'].value_counts(dropna=True).to_dict())
