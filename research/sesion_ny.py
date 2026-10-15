"""
Reconstruccion de la sesion regular de Nueva York (9:30-16:00 ET) para
USTEC/US500 -- NO es una estrategia, es la misma infraestructura de
localizacion horaria ya usada y confirmada en orb_backtest.py
(deteccion del slot de apertura por salto de TickVolume, semana a
semana, con filtro de regimenes >=20 dias). Se reutiliza AQUI tal cual
(sin reimplementarla) para que las 6 hipotesis intradia de este ciclo
comparen el mismo anclaje horario fiable -- lo que cambia entre
hipotesis son las REGLAS de señal/riesgo, nunca la localizacion de la
sesion.

XAUUSD queda fuera de este modulo (ver instruccion del usuario): no
tiene cobertura confirmada de offset semanal (43,6% en el analisis
original), asi que no se reconstruye su sesion aqui.

Da, por cada dia de sesion con offset CONFIRMADO: idx_apertura (vela
9:30-9:45 ET), idx_cierre_sesion (vela 15:45-16:00 ET, ultima de sesion
regular) e idx_fin_primera_hora/idx_inicio_mediodia/etc. derivados por
desplazamiento de 15 minutos desde idx_apertura -- todos indices
enteros sobre el DataFrame M15 original, listos para que cada
hipotesis indexe directamente con .iloc.
"""
from datetime import timedelta

import pandas as pd

from orb_backtest import (
    clasificar_huecos, detectar_apertura_caja_por_semana, construir_regimenes,
    filtrar_regimenes_confiables, MINUTOS_SESION_REGULAR,
)

BARRAS_SESION_REGULAR = MINUTOS_SESION_REGULAR // 15  # 26 barras M15 de 9:30 a 16:00 ET


def construir_tabla_sesiones(df):
    """df: M15 crudo (TimestampServidor;Open;High;Low;Close;Spread;...).
    Devuelve (tabla_sesiones, categoria_hueco). tabla_sesiones tiene una
    fila por cada dia de semana (lunes-viernes) en el rango de df, con
    columnas: dia, confirmado (bool), idx_apertura, idx_cierre_sesion
    (NaN si no confirmado o hueco en esas velas concretas)."""
    categoria_hueco = clasificar_huecos(df)
    tabla_semanal = detectar_apertura_caja_por_semana(df)
    regimenes = construir_regimenes(tabla_semanal)
    regimenes_confiables = filtrar_regimenes_confiables(regimenes)

    tiempos = df['TimestampServidor']
    idx_por_tiempo = {t: i for i, t in enumerate(tiempos)}
    n = len(df)
    dias = sorted(set(tiempos.dt.normalize()))

    filas = []
    for dia in dias:
        if dia.dayofweek >= 5:
            continue
        reg = regimenes_confiables[(regimenes_confiables['inicio'] <= dia) & (regimenes_confiables['fin'] > dia)]
        if len(reg) == 0:
            filas.append(dict(dia=dia, confirmado=False, idx_apertura=None, idx_cierre_sesion=None))
            continue
        slot = int(reg.iloc[0]['slot_apertura'])
        hora_a, minuto_a = slot // 4, (slot % 4) * 15
        t_apertura = dia + timedelta(hours=hora_a, minutes=minuto_a)
        t_cierre = t_apertura + timedelta(minutes=MINUTOS_SESION_REGULAR) - timedelta(minutes=15)

        idx_a = idx_por_tiempo.get(t_apertura)
        idx_c = idx_por_tiempo.get(t_cierre)
        confirmado = idx_a is not None and idx_c is not None and idx_c < n
        if confirmado:
            confirmado = (categoria_hueco.iloc[idx_a] == 'intrasesion' and categoria_hueco.iloc[idx_c] == 'intrasesion')
        filas.append(dict(dia=dia, confirmado=confirmado,
                           idx_apertura=idx_a if confirmado else None,
                           idx_cierre_sesion=idx_c if confirmado else None))
    return pd.DataFrame(filas), categoria_hueco


def sin_huecos_en_tramo(categoria_hueco, idx_inicio, idx_fin):
    """True si todas las velas [idx_inicio, idx_fin] son 'intrasesion'
    (salvo la propia idx_inicio, que puede ser el cierre_diario previo)."""
    return (categoria_hueco.iloc[idx_inicio + 1:idx_fin + 1] == 'intrasesion').all()
