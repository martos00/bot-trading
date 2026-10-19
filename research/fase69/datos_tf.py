"""H70 — panel mensual de excesos de rentabilidad de 34 mercados (PREREGISTRO_H70, sección 3).

Uso: python3 datos_tf.py DIR_RAW SALIDA_DIR
  DIR_RAW: y_<simbolo>.json (Yahoo chart API), fred/<ID>.csv, cb/* (bancos centrales).
Salida: panel_excesos.csv (mensual, decimal), clases.csv, auditoria_calidad.txt.
"""
import json, os, sys, io, contextlib
import numpy as np
import pandas as pd

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..'))
import calidad_datos  # noqa: E402

RAW = None
MAX_ANTIGUEDAD_DIAS_HABILES = 5


# ---------- lectores ----------
def yahoo(sim):
    d = json.load(open(os.path.join(RAW, f'y_{sim}.json')))['chart']['result'][0]
    q = d['indicators']['quote'][0]
    df = pd.DataFrame({k: q[k] for k in ['open', 'high', 'low', 'close']},
                      index=pd.to_datetime(d['timestamp'], unit='s').normalize())
    df.columns = ['Open', 'High', 'Low', 'Close']
    df = df[~df.index.duplicated(keep='last')].dropna(subset=['Close'])
    return df[df['Close'] > 0]


def fred(id_):
    s = pd.read_csv(os.path.join(RAW, 'fred', f'{id_}.csv'), index_col=0, parse_dates=True, na_values='.').iloc[:, 0]
    return s.dropna().astype(float)


def bundesbank(fichero):
    lineas = open(os.path.join(RAW, 'cb', fichero), encoding='utf-8-sig').read().splitlines()
    datos = [l.split(',')[:2] for l in lineas if l[:2] in ('19', '20') and len(l) > 10 and l[4] == '-']
    s = pd.Series({pd.Timestamp(a): b for a, b in datos})
    return pd.to_numeric(s, errors='coerce').dropna()


def cb_ca10():
    lineas = open(os.path.join(RAW, 'cb', 'ca10.csv'), encoding='utf-8-sig').read().splitlines()
    i = lineas.index('"OBSERVATIONS"')
    df = pd.read_csv(io.StringIO('\n'.join(lineas[i + 1:])), index_col=0, parse_dates=True)
    return pd.to_numeric(df.iloc[:, 0], errors='coerce').dropna()


def cb_uk10():
    df = pd.read_csv(os.path.join(RAW, 'cb', 'uk10.csv'))
    return pd.Series(df.iloc[:, 1].values, index=pd.to_datetime(df.iloc[:, 0], format='%d %b %Y')).astype(float).dropna()


def cb_jp10():
    df = pd.read_csv(os.path.join(RAW, 'cb', 'jp.csv'), skiprows=1, na_values='-')
    return pd.Series(df['10Y'].values, index=pd.to_datetime(df['Date'], format='%Y/%m/%d')).astype(float).dropna()


def cb_au10():
    h = pd.read_excel(os.path.join(RAW, 'cb', 'au_hist.xls'), header=None, skiprows=11)
    s1 = pd.Series(h[4].values, index=pd.to_datetime(h[0])).astype(float).dropna()
    lineas = open(os.path.join(RAW, 'cb', 'au.csv'), encoding='utf-8-sig').read().splitlines()
    i = next(k for k, l in enumerate(lineas) if l.startswith('Series ID'))
    filas = [l.split(',') for l in lineas[i + 1:] if l.strip()]
    s2 = pd.Series([f[4] if len(f) > 4 else None for f in filas],
                   index=pd.to_datetime([f[0] for f in filas], format='%d-%b-%Y'))
    s2 = pd.to_numeric(s2, errors='coerce').dropna()
    return pd.concat([s1[s1.index < s2.index.min()], s2])


# ---------- utilidades ----------
def cierre_mensual(s):
    """Último dato de cada mes; NaN si tiene más de 5 días hábiles de antigüedad al fin de mes."""
    s = s.sort_index()
    ult = s.groupby(s.index.to_period('M')).tail(1)
    per = ult.index.to_period('M')
    fin = per.to_timestamp(how='end').normalize()
    viejo = np.array([np.busday_count(a.date(), b.date()) for a, b in zip(ult.index, fin)]) > MAX_ANTIGUEDAD_DIAS_HABILES
    out = pd.Series(np.where(viejo, np.nan, ult.values), index=per)
    return out.reindex(pd.period_range(per.min(), per.max(), freq='M'))


def mensual_tipo(s):
    """Tipo corto mensual (% anual) indexado por periodo; se rellena hacia delante como máximo 3 meses."""
    m = s.groupby(s.index.to_period('M')).last()
    return m.reindex(pd.period_range(m.index.min(), '2026-12', freq='M')).ffill(limit=3)


def precio_diario_para_auditoria(s):
    return pd.DataFrame({'dia': s.index, 'Open': s.values, 'High': s.values, 'Low': s.values, 'Close': s.values})


def retorno_bono_par(y_prev, y_act, M):
    """Bono a la par (cupón anual = y_prev) revalorizado al rendimiento y_act con vencimiento M-1/12, más cupón devengado."""
    c, y, n = y_prev / 100, y_act / 100, M - 1 / 12
    precio = np.where(np.abs(y) < 1e-9, c * n + 1, c * (1 - (1 + y) ** -n) / np.where(np.abs(y) < 1e-9, 1, y) + (1 + y) ** -n)
    return precio - 1 + c / 12


def tipos_cortos():
    t = {
        'USD': mensual_tipo(fred('TB3MS')),
        'GBP': mensual_tipo(fred('IR3TIB01GBM156N')),
        'CAD': mensual_tipo(fred('IR3TIB01CAM156N')),
        'AUD': mensual_tipo(fred('IR3TIB01AUM156N')),
        'NZD': mensual_tipo(fred('IR3TIB01NZM156N')),
        'SEK': mensual_tipo(fred('IR3TIB01SEM156N')),
        'NOK': mensual_tipo(fred('IR3TIB01NOM156N')),
    }
    dem, ez = mensual_tipo(fred('IR3TIB01DEM156N')), mensual_tipo(fred('IR3TIB01EZM156N'))
    t['EUR'] = dem.where(dem.index < pd.Period('1999-01', 'M'), ez).combine_first(dem)
    disc, call = mensual_tipo(fred('INTDSRJPM193N')), mensual_tipo(fred('IRSTCI01JPM156N'))
    t['JPY'] = call.combine_first(disc.where(disc.index < pd.Period('1985-07', 'M')))
    chcall, ch3m = mensual_tipo(fred('IRSTCI01CHM156N')), mensual_tipo(fred('IR3TIB01CHM156N'))
    corte = fred('IRSTCI01CHM156N').index.max().to_period('M')
    t['CHF'] = chcall.where(chcall.index <= corte, ch3m).combine_first(ch3m)
    return pd.DataFrame(t)


# ---------- construcción ----------
INDICES = {  # nombre: (símbolo Yahoo, divisa)
    'EQ_SP500': ('%5EGSPC', 'USD'), 'EQ_R2000': ('%5ERUT', 'USD'), 'EQ_N225': ('%5EN225', 'JPY'),
    'EQ_DAX': ('%5EGDAXI', 'EUR'), 'EQ_FTSE': ('%5EFTSE', 'GBP'), 'EQ_TSX': ('%5EGSPTSE', 'CAD'),
    'EQ_ASX': ('%5EAXJO', 'AUD'), 'EQ_CAC': ('%5EFCHI', 'EUR'), 'EQ_AEX': ('%5EAEX', 'EUR'),
    'EQ_IBEX': ('%5EIBEX', 'EUR'), 'EQ_MIB': ('FTSEMIB.MI', 'EUR'),
}
FX = {  # nombre: (serie FRED, ¿USD por unidad extranjera?, divisa)
    'FX_JPY': ('DEXJPUS', False, 'JPY'), 'FX_GBP': ('DEXUSUK', True, 'GBP'), 'FX_CAD': ('DEXCAUS', False, 'CAD'),
    'FX_CHF': ('DEXSZUS', False, 'CHF'), 'FX_AUD': ('DEXUSAL', True, 'AUD'), 'FX_NZD': ('DEXUSNZ', True, 'NZD'),
    'FX_SEK': ('DEXSDUS', False, 'SEK'), 'FX_NOK': ('DEXNOUS', False, 'NOK'),
}


def construir(raw):
    global RAW
    RAW = raw
    tc = tipos_cortos()
    rf = lambda cur: tc[cur].shift(1) / 1200  # tipo conocido al inicio del mes, devengado en el mes
    series_diarias, panel, clases = {}, {}, {}

    for nom, (sim, cur) in INDICES.items():
        p = yahoo(sim)['Close']
        series_diarias[nom] = p
        m = cierre_mensual(p)
        panel[nom], clases[nom] = m / m.shift(1) - 1 - rf(cur), 'EQ'

    bonos = {'BD_US2': (fred('DGS2'), 2, 'USD'), 'BD_US5': (fred('DGS5'), 5, 'USD'), 'BD_US10': (fred('DGS10'), 10, 'USD'),
             'BD_US30': (fred('DGS30'), 30, 'USD'), 'BD_DE10': (bundesbank('de10.csv'), 10, 'EUR'),
             'BD_UK10': (cb_uk10(), 10, 'GBP'), 'BD_JP10': (cb_jp10(), 10, 'JPY'), 'BD_CA10': (cb_ca10(), 10, 'CAD'),
             'BD_AU10': (cb_au10(), 10, 'AUD')}
    for nom, (y, M, cur) in bonos.items():
        series_diarias[nom] = y
        m = cierre_mensual(y)
        r = pd.Series(retorno_bono_par(m.shift(1).values, m.values, M), index=m.index)
        panel[nom], clases[nom] = r - rf(cur), 'BD'

    usd = rf('USD')
    for nom, (id_, directo, cur) in FX.items():
        s = fred(id_)
        s = s if directo else 1 / s
        series_diarias[nom] = s
        m = cierre_mensual(s)
        panel[nom], clases[nom] = m / m.shift(1) - 1 + rf(cur) - usd, 'FX'
    # EUR: DEM (Bundesbank, DEM por USD) hasta 1998, EUR (FRED) desde 1999
    dem = bundesbank('usddem.csv')
    eur_eq = (1.95583 / dem)[dem.index < '1999-01-01']
    eur = pd.concat([eur_eq, fred('DEXUSEU')])
    series_diarias['FX_EUR'] = eur
    m = cierre_mensual(eur)
    panel['FX_EUR'], clases['FX_EUR'] = m / m.shift(1) - 1 + rf('EUR') - usd, 'FX'

    cms = {'CM_WTI': fred('DCOILWTICO'), 'CM_NG': fred('DHHNGSP'), 'CM_GOLD': yahoo('GC%3DF')['Close'],
           'CM_SILVER': yahoo('SI%3DF')['Close'], 'CM_COPPER': yahoo('HG%3DF')['Close']}
    for nom, s in cms.items():
        s = s[s > 0]
        series_diarias[nom] = s
        m = cierre_mensual(s)
        panel[nom], clases[nom] = m / m.shift(1) - 1, 'CM'

    panel = pd.DataFrame(panel)
    panel = panel[panel.index <= pd.Period('2026-09', 'M')]
    # divisas: solo desde la flotación (marzo-1973)
    for c in [c for c in panel if c.startswith('FX_')]:
        panel.loc[panel.index < pd.Period('1973-03', 'M'), c] = np.nan
    return panel, pd.Series(clases), series_diarias


def auditar(series_diarias):
    buf = io.StringIO()
    graves = {}
    with contextlib.redirect_stdout(buf):
        for nom, s in series_diarias.items():
            r = calidad_datos.auditar_historico(precio_diario_para_auditoria(s), nom)
            r.imprimir()
            graves[nom] = r.huecos
    return buf.getvalue(), graves


if __name__ == '__main__':
    raw, out = sys.argv[1:3]
    os.makedirs(out, exist_ok=True)
    panel, clases, diarias = construir(raw)
    texto, huecos = auditar(diarias)
    # meses que contienen un hueco GRAVE de la serie diaria -> NaN (no se rellena nada)
    n_anulados = 0
    for nom, hs in huecos.items():
        for h in hs:
            meses = pd.period_range(h['inicio'].to_period('M'), h['fin'].to_period('M'), freq='M')
            meses = [m for m in meses if m in panel.index]
            n_anulados += int(panel.loc[meses, nom].notna().sum())
            panel.loc[meses, nom] = np.nan
            if meses and meses[-1] + 1 in panel.index:  # el mes siguiente usa un cierre anterior al hueco
                panel.loc[meses[-1] + 1, nom] = np.nan
    open(os.path.join(out, 'auditoria_calidad.txt'), 'w').write(texto + f'\nMeses anulados por huecos GRAVES: {n_anulados}\n')
    panel.index = panel.index.astype(str)
    panel.to_csv(os.path.join(out, 'panel_excesos.csv'), float_format='%.8f')
    clases.to_csv(os.path.join(out, 'clases.csv'), header=['clase'])
    print(texto[-3000:])
    print('Meses anulados por huecos GRAVES:', n_anulados)
    print(panel.notna().sum().to_string())
