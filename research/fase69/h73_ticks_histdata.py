"""H73 — comprobación con ticks BID/ASK de HistData (mismo proveedor que las velas M1: NO es una fuente
independiente; sirve para medir el spread y comprobar si el BID del rollover está deprimido respecto al mid).

Uso: python3 h73_ticks_histdata.py AAAA-MM AAAA-MM SALIDA_CSV
Para cada día de Tokio (lunes-viernes, sin festivos de Japón) obtiene BID/ASK del último tick en los 5 minutos
previos a: 17:05 NY (día anterior), 09:55 Tokio y 08:00 Frankfurt. Marca horaria de HistData = hora NY con DST.
"""
import io, re, sys, time, zipfile, urllib.request, urllib.parse, http.cookiejar
import numpy as np
import pandas as pd
import holidays

NY, FRA, TOK = 'America/New_York', 'Europe/Berlin', 'Asia/Tokyo'
B = 'https://www.histdata.com'


def bajar_mes(op, y, m):
    r = f'/download-free-forex-historical-data/?/ascii/tick-data-quotes/usdjpy/{y}/{m}'
    h = op.open(urllib.request.Request(B + r, headers={'User-Agent': 'Mozilla/5.0'}), timeout=60).read().decode('utf8', 'ignore')
    c = {k: re.search(rf'name="{k}" id="{k}" value="([^"]*)"', h).group(1) for k in ('tk', 'date', 'datemonth', 'platform', 'timeframe', 'fxpair')}
    x = op.open(urllib.request.Request(B + '/get.php', data=urllib.parse.urlencode(c).encode(),
                                      headers={'User-Agent': 'Mozilla/5.0', 'Referer': B + r}), timeout=900).read()
    z = zipfile.ZipFile(io.BytesIO(x))
    nombre = [n for n in z.namelist() if n.endswith('.csv')][0]
    t = pd.read_csv(z.open(nombre), header=None, names=['ts', 'bid', 'ask', 'v'], dtype={'ts': str})
    ts = pd.to_datetime(t['ts'], format='%Y%m%d %H%M%S%f').dt.tz_localize(NY, ambiguous='NaT', nonexistent='NaT')
    return pd.DataFrame({'bid': t['bid'].values, 'ask': t['ask'].values}, index=ts).loc[lambda d: d.index.notna()].sort_index()


def cotizacion(tk, T):
    i = tk.index.searchsorted(T, side='left') - 1
    if i < 0 or (T - tk.index[i]) > pd.Timedelta(minutes=5):
        return np.nan, np.nan
    return tk['bid'].iloc[i], tk['ask'].iloc[i]


def main():
    ini, fin, salida = sys.argv[1:4]
    meses = pd.period_range(ini, fin, freq='M')
    fj = set(holidays.Japan(years=range(meses[0].year, meses[-1].year + 1)))
    dias = [d for d in pd.bdate_range(meses[0].start_time, meses[-1].end_time) if d.date() not in fj]
    inst = []
    for d in dias:
        for k, T in (('t1a', pd.Timestamp(f'{(d - pd.Timedelta(days=1)).date()} 17:05', tz=NY)),
                     ('t1b', pd.Timestamp(f'{d.date()} 09:55', tz=TOK).tz_convert(NY)),
                     ('t2b', pd.Timestamp(f'{d.date()} 08:00', tz=FRA).tz_convert(NY))):
            inst.append((d, k, T))
    inst = pd.DataFrame(inst, columns=['dia', 'k', 'T'])
    inst['mes'] = inst['T'].map(lambda x: x.to_period('M'))
    op = urllib.request.build_opener(urllib.request.HTTPCookieProcessor(http.cookiejar.CookieJar()))
    res = []
    for p in sorted(set(inst['mes'])):
        try:
            tk = bajar_mes(op, p.year, p.month)
        except Exception as e:
            print(p, 'ERROR', type(e).__name__, e, flush=True)
            continue
        sub = inst[inst['mes'] == p]
        for _, f in sub.iterrows():
            b, a = cotizacion(tk, f['T'])
            res.append((f['dia'], f['k'], b, a))
        print(p, len(tk), 'ticks', flush=True)
        time.sleep(2)
    r = pd.DataFrame(res, columns=['dia', 'k', 'bid', 'ask']).pivot(index='dia', columns='k', values=['bid', 'ask'])
    r.columns = [f'{a}_{b}' for a, b in r.columns]
    r.to_csv(salida)


if __name__ == '__main__':
    main()
