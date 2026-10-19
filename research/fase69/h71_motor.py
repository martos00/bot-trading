"""H71 — reversiones en torno a los fixings FX (Krohn, Mueller & Whelan 2024). Motor PRINCIPAL (pandas).
Reglas congeladas en PREREGISTRO_H71_fixings_fx.md.

Uso: python3 h71_motor.py DIR_HISTDATA PAR SALIDA_CSV
Salida: una fila por día y estrategia ('EUROPA', 'TOKIO') con los 4 precios de los dos tramos y la
rentabilidad bruta (log) de cada tramo en la dirección de la estrategia.
"""
import glob, os, sys
import numpy as np
import pandas as pd
import holidays

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..'))
import calidad_datos  # noqa: E402

NY, FRA, LON, TOK = 'America/New_York', 'Europe/Berlin', 'Europe/London', 'Asia/Tokyo'
TOLERANCIA_MIN = 5


def cargar(directorio, par):
    fs = sorted(glob.glob(os.path.join(directorio, f'DAT_ASCII_{par}_M1_*.csv')))
    m1 = pd.concat([pd.read_csv(f, sep=';', header=None, names=['ts', 'Open', 'High', 'Low', 'Close', 'Vol']) for f in fs],
                   ignore_index=True)
    t = pd.to_datetime(m1['ts'], format='%Y%m%d %H%M%S')
    m1['t'] = t.dt.tz_localize(NY, ambiguous='NaT', nonexistent='NaT')  # hora local NY con DST (verificado)
    m1 = m1.dropna(subset=['t']).drop_duplicates('t').sort_values('t')
    return m1.set_index('t')


def precios(m1, instantes):
    idx = m1.index
    obj = pd.DatetimeIndex(instantes).tz_convert(NY)
    pos = idx.searchsorted(obj, side='left') - 1
    ok = pos >= 0
    pc = np.clip(pos, 0, None)
    valido = ok & ((obj - idx[pc]) <= pd.Timedelta(minutes=TOLERANCIA_MIN))
    return np.where(valido, m1['Close'].to_numpy()[pc], np.nan)


def instante(dias, hhmm, tz, desfase_dias=0):
    return pd.DatetimeIndex([pd.Timestamp(f'{(d + pd.Timedelta(days=desfase_dias)).date()} {hhmm}', tz=tz) for d in dias])


def diario_auditoria(m1):
    d = m1.copy()
    d['dia'] = d.index.tz_localize(None).normalize()
    d = d[d.index.weekday < 5]
    return d.groupby('dia').agg(Open=('Open', 'first'), High=('High', 'max'), Low=('Low', 'min'), Close=('Close', 'last')).reset_index()


def construir(directorio, par):
    m1 = cargar(directorio, par)
    aud = calidad_datos.auditar_historico(diario_auditoria(m1), f'{par} (HistData M1)')
    ini, fin = m1.index.min().tz_localize(None).normalize(), m1.index.max().tz_localize(None).normalize()
    dias = pd.bdate_range(ini + pd.Timedelta(days=1), fin - pd.Timedelta(days=1))
    signo_usd = 1.0 if par.startswith('USD') else -1.0   # +log(P1/P0) es largo USD si el par es USDxxx
    anios = range(dias.min().year, dias.max().year + 1)
    fest_ecb = set(holidays.financial_holidays('XECB', years=anios))
    fest_jp = set(holidays.Japan(years=anios))
    filas = []
    # EUROPA: tramo 1 largo USD 08:00->14:15 Frankfurt; tramo 2 corto USD 16:00 Londres -> 16:55 NY
    e = dias[[d.date() not in fest_ecb for d in dias]]
    pe = pd.DataFrame({'p1a': precios(m1, instante(e, '08:00', FRA)), 'p1b': precios(m1, instante(e, '14:15', FRA)),
                       'p2a': precios(m1, instante(e, '16:00', LON)), 'p2b': precios(m1, instante(e, '16:55', NY))}, index=e)
    pe['r1'] = signo_usd * np.log(pe.p1b / pe.p1a)
    pe['r2'] = -signo_usd * np.log(pe.p2b / pe.p2a)
    pe['estrategia'] = 'EUROPA'
    pe['t1a'] = instante(e, '08:00', FRA).tz_convert(NY).strftime('%H:%M')
    pe['t2a'] = instante(e, '16:00', LON).tz_convert(NY).strftime('%H:%M')
    filas.append(pe)
    # TOKIO (día = fecha de Tokio): tramo 1 largo USD 17:05 NY del día anterior -> 09:55 Tokio;
    # tramo 2 corto USD 09:55 Tokio -> 08:00 Frankfurt
    k = dias[[d.date() not in fest_jp for d in dias]]
    pt = pd.DataFrame({'p1a': precios(m1, instante(k, '17:05', NY, -1)), 'p1b': precios(m1, instante(k, '09:55', TOK)),
                       'p2a': precios(m1, instante(k, '09:55', TOK)), 'p2b': precios(m1, instante(k, '08:00', FRA))}, index=k)
    pt['r1'] = signo_usd * np.log(pt.p1b / pt.p1a)
    pt['r2'] = -signo_usd * np.log(pt.p2b / pt.p2a)
    pt['estrategia'] = 'TOKIO'
    pt['t1a'] = '17:05'
    pt['t2a'] = instante(k, '09:55', TOK).tz_convert(NY).strftime('%H:%M')
    filas.append(pt)
    df = pd.concat(filas)
    en_hueco = np.zeros(len(df), bool)
    for h in aud.huecos:
        en_hueco |= (df.index > h['inicio']) & (df.index <= h['fin'] + pd.Timedelta(days=1))
    df['completo'] = df[['p1a', 'p1b', 'p2a', 'p2b']].notna().all(axis=1) & ~en_hueco
    df['r'] = df['r1'] + df['r2']
    return df, aud


if __name__ == '__main__':
    directorio, par, salida = sys.argv[1:4]
    df, aud = construir(directorio, par)
    aud.imprimir()
    print(par, df.groupby('estrategia').completo.agg(['size', 'sum']).to_string())
    df.index.name = 'dia'
    df.to_csv(salida)
