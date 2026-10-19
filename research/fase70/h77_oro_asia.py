"""H77 — oro largo en la sesión de Tokio (09:00 → 15:00 hora de Tokio). PREREGISTRO_H77_oro_asia.md.

Uso:
  python3 h77_oro_asia.py m1 DIR_HISTDATA SALIDA_CSV          (rentabilidad bruta con BID M1, regla y control)
  python3 h77_oro_asia.py ticks AAAA-MM AAAA-MM SALIDA_CSV     (BID/ASK de HistData en los instantes, OOS)
"""
import glob, io, os, re, sys, time, zipfile, urllib.request, urllib.parse, http.cookiejar
import numpy as np
import pandas as pd
import holidays

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..'))
import calidad_datos  # noqa: E402

NY, TOK = 'America/New_York', 'Asia/Tokyo'
TOL = pd.Timedelta(minutes=5)


def dias_tokio(ini, fin):
    fj = set(holidays.Japan(years=range(ini.year, fin.year + 1)))
    return [d for d in pd.bdate_range(ini, fin) if d.date() not in fj]


def instantes(dias, desfase_h=0):
    """(entrada, salida) en hora de Tokio; desfase_h=12 da la ventana de control 21:00 → 03:00."""
    ent = pd.DatetimeIndex([pd.Timestamp(f'{d.date()} 09:00', tz=TOK) for d in dias]) + pd.Timedelta(hours=desfase_h)
    return ent, ent + pd.Timedelta(hours=6)


def precio_en(idx, valores, T):
    pos = idx.searchsorted(T.tz_convert(NY), side='left') - 1
    pc = np.clip(pos, 0, None)
    ok = (pos >= 0) & ((T.tz_convert(NY) - idx[pc]) <= TOL)
    return np.where(ok, valores[pc], np.nan)


def modo_m1(directorio, salida):
    fs = sorted(glob.glob(os.path.join(directorio, 'DAT_ASCII_XAUUSD_M1_*.csv')))
    m = pd.concat([pd.read_csv(f, sep=';', header=None, names=['ts', 'o', 'h', 'l', 'c', 'v']) for f in fs])
    t = pd.to_datetime(m.ts, format='%Y%m%d %H%M%S').dt.tz_localize(NY, ambiguous='NaT', nonexistent='NaT')
    m = m.assign(t=t).dropna(subset=['t']).drop_duplicates('t').sort_values('t')
    d = m.assign(dia=m.t.dt.tz_localize(None).dt.normalize()).groupby('dia').agg(
        Open=('o', 'first'), High=('h', 'max'), Low=('l', 'min'), Close=('c', 'last')).reset_index()
    d = d[d.dia.dt.weekday < 5]
    aud = calidad_datos.auditar_historico(d, 'XAUUSD HistData M1')
    aud.imprimir()
    idx, c = pd.DatetimeIndex(m.t), m.c.to_numpy()
    dias = dias_tokio(m.t.min().tz_convert(TOK).tz_localize(None).normalize() + pd.Timedelta(days=1),
                      m.t.max().tz_convert(TOK).tz_localize(None).normalize() - pd.Timedelta(days=1))
    out = pd.DataFrame(index=pd.DatetimeIndex(dias))
    for nom, desf in (('regla', 0), ('control', 12)):
        e, s = instantes(dias, desf)
        pe, ps = precio_en(idx, c, e), precio_en(idx, c, s)
        out[f'{nom}_pe'], out[f'{nom}_ps'] = pe, ps
        out[f'{nom}_r'] = np.log(ps / pe)
    en_hueco = np.zeros(len(out), bool)
    for h in aud.huecos:
        en_hueco |= (out.index >= h['inicio']) & (out.index <= h['fin'] + pd.Timedelta(days=1))
    out.loc[en_hueco, ['regla_r', 'control_r']] = np.nan
    out.index.name = 'dia_tokio'
    out.to_csv(salida)
    print('días con regla:', out.regla_r.notna().sum())


def bajar_mes(op, y, mes):
    r = f'/download-free-forex-historical-data/?/ascii/tick-data-quotes/xauusd/{y}/{mes}'
    B = 'https://www.histdata.com'
    h = op.open(urllib.request.Request(B + r, headers={'User-Agent': 'Mozilla/5.0'}), timeout=60).read().decode('utf8', 'ignore')
    c = {k: re.search(rf'name="{k}" id="{k}" value="([^"]*)"', h).group(1) for k in ('tk', 'date', 'datemonth', 'platform', 'timeframe', 'fxpair')}
    x = op.open(urllib.request.Request(B + '/get.php', data=urllib.parse.urlencode(c).encode(),
                                      headers={'User-Agent': 'Mozilla/5.0', 'Referer': B + r}), timeout=900).read()
    z = zipfile.ZipFile(io.BytesIO(x))
    t = pd.read_csv(z.open([n for n in z.namelist() if n.endswith('.csv')][0]), header=None, names=['ts', 'bid', 'ask', 'v'], dtype={'ts': str})
    ts = pd.to_datetime(t.ts, format='%Y%m%d %H%M%S%f').dt.tz_localize(NY, ambiguous='NaT', nonexistent='NaT')
    return pd.DataFrame({'bid': t.bid.values, 'ask': t.ask.values}, index=ts).loc[lambda d: d.index.notna()].sort_index()


def modo_ticks(ini, fin, salida):
    meses = pd.period_range(ini, fin, freq='M')
    dias = dias_tokio(meses[0].start_time, meses[-1].end_time)
    ins = []
    for nom, desf in (('regla', 0), ('control', 12)):
        e, s = instantes(dias, desf)
        ins += [(d, f'{nom}_e', x) for d, x in zip(dias, e)] + [(d, f'{nom}_s', x) for d, x in zip(dias, s)]
    ins = pd.DataFrame(ins, columns=['dia', 'k', 'T'])
    ins['mes'] = ins['T'].map(lambda x: x.tz_convert(NY).to_period('M'))
    op = urllib.request.build_opener(urllib.request.HTTPCookieProcessor(http.cookiejar.CookieJar()))
    res = []
    for p in sorted(set(ins.mes)):
        try:
            tk = bajar_mes(op, p.year, p.month)
        except Exception as e:
            print(p, 'ERROR', e, flush=True)
            continue
        idx = tk.index
        sub = ins[ins.mes == p]
        b = precio_en(idx, tk.bid.to_numpy(), pd.DatetimeIndex(sub['T']))
        a = precio_en(idx, tk.ask.to_numpy(), pd.DatetimeIndex(sub['T']))
        res += list(zip(sub.dia, sub.k, b, a))
        print(p, len(tk), flush=True)
        time.sleep(2)
    r = pd.DataFrame(res, columns=['dia', 'k', 'bid', 'ask']).pivot_table(index='dia', columns='k', values=['bid', 'ask'])
    r.columns = [f'{a}_{b}' for a, b in r.columns]
    r.to_csv(salida)


if __name__ == '__main__':
    if sys.argv[1] == 'm1':
        modo_m1(*sys.argv[2:4])
    else:
        modo_ticks(*sys.argv[2:5])
