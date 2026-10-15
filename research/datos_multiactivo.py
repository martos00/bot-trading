"""
Pipeline de datos diario para la fase "Opcion B" (TSMOM, momentum
transversal, pairs trading) -- universo de 9 activos, mismo broker
MetaQuotes-Demo, mismo formato M15 que el resto del proyecto. Reutiliza
exactamente cargar_m15/agregar_diario_con_spread ya validados -- no se
reimplementa la aggregacion diaria.

POINT/DIGITS verificados leyendo los propios datos (no asumidos de
memoria): EURUSD/GBPUSD/USDCAD/USDCHF/USDSEK tienen 5 decimales
(point=0.00001); USDJPY tiene 3 decimales (point=0.001); XAUUSD/USTEC/
US500 tienen 2 decimales (point=0.01, ya usado en todo el proyecto).

LIMITACION DECLARADA: salvo XAUUSD (2015-2026), todo el universo es
2023-2026 (~3.75 anios) -- muy por debajo de las decadas de historia de
los estudios academicos citados en el README. Los 6 pares Forex NUNCA
se han usado en este proyecto (datos frescos); XAUUSD/USTEC/US500 si
se han usado en ciclos anteriores con OTRAS hipotesis (intradia,
diaria de corto plazo) -- no se ha probado TSMOM/momentum transversal
sobre ellos antes.
"""
import pandas as pd

from hipotesis_rsi2_sma200 import cargar_m15
from estrategia_gap_fade import agregar_diario_con_spread

RUTA_XAUUSD_2015_2022 = '/tmp/claude-0/-home-user-bot-trading/0b8bbddf-7bd5-59ce-baf0-0685f40ca055/scratchpad/XAUUSD_M15_histdata_2015_2022.csv'

_UPLOADS = '/root/.claude/uploads/0b8bbddf-7bd5-59ce-baf0-0685f40ca055'

UNIVERSO = {
    'XAUUSD': dict(rutas=[RUTA_XAUUSD_2015_2022, f'{_UPLOADS}/20c75528-XAUUSD_M15_Export.csv'],
                   point=0.01, clase='metal', tramo='2015-2026'),
    'USTEC':  dict(rutas=[f'{_UPLOADS}/3b9869d6-USTEC_M15_Export.csv'], point=0.01, clase='indice', tramo='2023-2026'),
    'US500':  dict(rutas=[f'{_UPLOADS}/1eac00f2-US500_M15_Export.csv'], point=0.01, clase='indice', tramo='2023-2026'),
    'EURUSD': dict(rutas=[f'{_UPLOADS}/5ec4d09c-EURUSD_M15_Export.csv'], point=0.00001, clase='fx', tramo='2023-2026'),
    'GBPUSD': dict(rutas=[f'{_UPLOADS}/1dfbe904-GBPUSD_M15_Export.csv'], point=0.00001, clase='fx', tramo='2023-2026'),
    'USDJPY': dict(rutas=[f'{_UPLOADS}/28cd3ffd-USDJPY_M15_Export.csv'], point=0.001, clase='fx', tramo='2023-2026'),
    'USDCAD': dict(rutas=[f'{_UPLOADS}/40a93081-USDCAD_M15_Export.csv'], point=0.00001, clase='fx', tramo='2023-2026'),
    'USDCHF': dict(rutas=[f'{_UPLOADS}/f08582d5-USDCHF_M15_Export.csv'], point=0.00001, clase='fx', tramo='2023-2026'),
    'USDSEK': dict(rutas=[f'{_UPLOADS}/adb478b9-USDSEK_M15_Export.csv'], point=0.00001, clase='fx', tramo='2023-2026'),
}


def fusionar_domingo_en_lunes(diario):
    """Correccion de un artefacto REAL de la union HistData/MetaQuotes-Demo
    en XAUUSD (encontrado al comprobar, a peticion del usuario, que la
    diferencia de proveedores no genera señales artificiales): HistData
    (EST sin DST, 2015-2022) agrega por dia de calendario EST, lo que
    produce una vela "domingo" propia cada semana (solo la breve
    reapertura del domingo por la tarde, rango medio ~8,9 frente a
    ~17-20 de un dia completo) que NO existe en MetaQuotes-Demo
    (EET/EEST, 2023-2026), donde esa misma sesion de reapertura queda
    dentro de la vela del lunes. Sin corregir esto, el tramo 2015-2022
    tiene 6 "dias" por semana (5 completos + 1 parcial) y el tramo
    2023-2026 tiene 5 completos -- un sesgo estructural que arrastra el
    ATR14 hacia abajo de forma distinta en cada tramo (la vela domingo,
    de rango bajo, entra en la media movil de las otras). Se corrige
    fusionando cada vela domingo (si existe) dentro de la vela lunes
    SIGUIENTE (Open=domingo, High/Low=combinado, Close=lunes), igual
    convencion que usaria MetaQuotes-Demo -- no se inventa nada, se
    iguala el criterio de agregacion entre ambas fuentes."""
    d = diario.sort_values('dia').reset_index(drop=True)
    dow = d['dia'].dt.dayofweek
    idx_domingo = d.index[dow == 6].to_numpy()
    if len(idx_domingo) == 0:
        return d
    filas_a_borrar = []
    for i in idx_domingo:
        if i + 1 >= len(d) or dow.iloc[i + 1] != 0:
            continue  # sin lunes siguiente contiguo -- no se fusiona a ciegas
        d.loc[i + 1, 'Open'] = d.loc[i, 'Open']
        d.loc[i + 1, 'High'] = max(d.loc[i, 'High'], d.loc[i + 1, 'High'])
        d.loc[i + 1, 'Low'] = min(d.loc[i, 'Low'], d.loc[i + 1, 'Low'])
        filas_a_borrar.append(i)
    return d.drop(index=filas_a_borrar).reset_index(drop=True)


def cargar_diario(nombre):
    cfg = UNIVERSO[nombre]
    piezas = [cargar_m15(r) for r in cfg['rutas']]
    df = pd.concat(piezas, ignore_index=True).sort_values('TimestampServidor').reset_index(drop=True) \
        if len(piezas) > 1 else piezas[0]
    diario = agregar_diario_con_spread(df)
    diario = fusionar_domingo_en_lunes(diario)
    diario['activo'] = nombre
    diario['point'] = cfg['point']
    diario['clase'] = cfg['clase']
    return diario


def cargar_universo(nombres=None):
    nombres = nombres or list(UNIVERSO.keys())
    return {n: cargar_diario(n) for n in nombres}


if __name__ == '__main__':
    for nombre, diario in cargar_universo().items():
        cfg = UNIVERSO[nombre]
        print(f"{nombre} [{cfg['clase']}, {cfg['tramo']}]: {len(diario)} barras diarias, "
              f"{diario['dia'].min().date()} -> {diario['dia'].max().date()}, "
              f"spread medio={diario['Spread'].mean()*cfg['point']:.6f} (precio), "
              f"Close medio={diario['Close'].mean():.4f}")
