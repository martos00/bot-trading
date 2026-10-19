"""H69 — Market Intraday Momentum (Gao et al. 2018; Baltussen et al. 2021).

Motor PRINCIPAL (pandas, vectorizado). Reglas congeladas en
PREREGISTRO_H69_momentum_intradia.md — este script no tiene parámetros ajustables.

Uso: python3 h69_motor.py DIR_HISTDATA SIMBOLO SALIDA_CSV
     (DIR_HISTDATA contiene los DAT_ASCII_<SIM>_M1_*.csv de HistData)

Salida: una fila por sesión NYSE completa con los 4 precios clave, las dos señales
(r_ROD, r_ONFH) y la rentabilidad de la última media hora (r_LH).
"""
import glob, os, sys
import numpy as np
import pandas as pd
import pandas_market_calendars as mcal

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..'))
import calidad_datos  # noqa: E402

NY = 'America/New_York'
INSTANTES = {'p1000': '10:00', 'p1530': '15:30', 'p1600': '16:00'}
TOLERANCIA_MIN = 5  # se acepta la última vela con apertura en [T-5min, T-1min]


def cargar_histdata(directorio, sim):
    ficheros = sorted(glob.glob(os.path.join(directorio, f'DAT_ASCII_{sim}_M1_*.csv')))
    m1 = pd.concat([pd.read_csv(f, sep=';', header=None, names=['ts', 'Open', 'High', 'Low', 'Close', 'Vol'])
                    for f in ficheros], ignore_index=True)
    # HistData: hora de APERTURA de la vela. Su documentación dice "EST sin horario de verano",
    # pero para SPXUSD/NSXUSD la verificación empírica (apéndice A del pre-registro) muestra que
    # la apertura de NY cae a las 09:30 de la marca original en verano e invierno de todos los
    # años: la marca es hora local de Nueva York CON horario de verano.
    t = pd.to_datetime(m1['ts'], format='%Y%m%d %H%M%S')
    m1['t_ny'] = t.dt.tz_localize(NY, ambiguous='NaT', nonexistent='NaT')
    m1 = m1.dropna(subset=['t_ny']).drop(columns=['ts', 'Vol'])
    n_dup = m1['t_ny'].duplicated().sum()
    m1 = m1.drop_duplicates('t_ny').sort_values('t_ny').reset_index(drop=True)
    return m1, n_dup, ficheros


def sesiones_completas(ini, fin):
    cal = mcal.get_calendar('NYSE')
    sch = cal.schedule(ini, fin)
    tempranas = cal.early_closes(sch).index
    sch = sch[~sch.index.isin(tempranas)]
    return pd.DatetimeIndex(sch.index), len(tempranas)


def precio_en(m1_idx, dias, hhmm):
    """Cierre de la última vela con apertura en [T-5min, T-1min] para cada día (NaN si no hay)."""
    objetivo = pd.DatetimeIndex([pd.Timestamp(f'{d.date()} {hhmm}', tz=NY) for d in dias])
    pos = m1_idx.index.searchsorted(objetivo, side='left') - 1  # última vela con apertura < T
    pos_ok = pos >= 0
    t_vela = m1_idx.index[np.clip(pos, 0, None)]
    valido = pos_ok & ((objetivo - t_vela) <= pd.Timedelta(minutes=TOLERANCIA_MIN))
    vals = m1_idx['Close'].to_numpy()[np.clip(pos, 0, None)]
    return np.where(valido, vals, np.nan)


def barras_rth(m1):
    """Barra diaria de sesión regular (09:30-16:00 ET) para la auditoría de calidad."""
    t = m1['t_ny']
    hm = t.dt.hour * 100 + t.dt.minute
    rth = m1[(hm >= 930) & (hm < 1600)].copy()
    rth['dia'] = rth['t_ny'].dt.tz_localize(None).dt.normalize()
    d = rth.groupby('dia').agg(Open=('Open', 'first'), High=('High', 'max'),
                               Low=('Low', 'min'), Close=('Close', 'last')).reset_index()
    return d


def construir(directorio, sim):
    m1, n_dup, ficheros = cargar_histdata(directorio, sim)
    diario = barras_rth(m1)
    auditoria = calidad_datos.auditar_historico(diario, f'{sim} (HistData, barras RTH)')

    dias, n_tempranas = sesiones_completas(diario['dia'].min(), diario['dia'].max())
    m1_idx = m1.set_index('t_ny')
    df = pd.DataFrame(index=dias)
    for col, hhmm in INSTANTES.items():
        df[col] = precio_en(m1_idx, dias, hhmm)
    # cierre del día anterior = P(16:00) de la sesión NYSE anterior (completa o no)
    cal_todas = mcal.get_calendar('NYSE').schedule(dias.min() - pd.Timedelta(days=10), dias.max())
    idx_todas = pd.DatetimeIndex(cal_todas.index)
    previa = idx_todas[idx_todas.searchsorted(dias) - 1]
    cierre_prev = pd.Series(precio_en(m1_idx, previa, '16:00'), index=dias)
    # en un día de cierre anticipado el "cierre" es a las 13:00
    tempranas = mcal.get_calendar('NYSE').early_closes(cal_todas).index
    es_temprana = previa.isin(tempranas)
    if es_temprana.any():
        cierre_prev[es_temprana] = precio_en(m1_idx, previa[es_temprana], '13:00')
    df['p_prev'] = cierre_prev.to_numpy()

    # días dentro de huecos GRAVES detectados por la auditoría: se excluyen
    en_hueco = np.zeros(len(df), bool)
    for h in auditoria.huecos:
        en_hueco |= (df.index > h['inicio']) & (df.index <= h['fin'])
    df['excluido_hueco'] = en_hueco

    df['r_ROD'] = np.log(df['p1530'] / df['p_prev'])
    df['r_ONFH'] = np.log(df['p1000'] / df['p_prev'])
    df['r_LH'] = np.log(df['p1600'] / df['p1530'])
    df['completo'] = df[['p_prev', 'p1000', 'p1530', 'p1600']].notna().all(axis=1) & ~df['excluido_hueco']
    info = dict(sim=sim, n_ficheros=len(ficheros), velas_m1=len(m1), duplicadas=n_dup,
                sesiones_nyse_completas=len(dias), cierres_anticipados_excluidos=n_tempranas,
                sesiones_utilizables=int(df['completo'].sum()))
    return df, auditoria, info


if __name__ == '__main__':
    directorio, sim, salida = sys.argv[1:4]
    df, aud, info = construir(directorio, sim)
    aud.imprimir()
    print(info)
    df.index.name = 'dia'
    df.to_csv(salida)
