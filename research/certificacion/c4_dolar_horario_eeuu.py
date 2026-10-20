"""C4 — factor "dólar débil en horario de EE. UU." con HistData 2003-2011 (PREREGISTRO_C4_dolar_horario_eeuu.md).
Uso: python3 c4_dolar_horario_eeuu.py DIR_HISTDATA (con subcarpetas EURUSD, GBPUSD, USDCHF y opcionalmente USDJPY)"""
import glob, os, sys
import numpy as np
import pandas as pd
from c1_certificacion import t_nw
from c3_breedon_ranaldo import precio, instantes

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..'))
import calidad_datos  # noqa: E402

NY = 'America/New_York'
PARES = {'EURUSD': +1, 'GBPUSD': +1, 'USDCHF': -1}
INFORMATIVOS = {'USDJPY': -1}


def cargar(d, par):
    fs = [f for f in sorted(glob.glob(os.path.join(d, par, f'DAT_ASCII_{par}_M1_*.csv')))
          if 2003 <= int(os.path.basename(f).split('_')[-1][:4]) <= 2011]
    x = pd.concat([pd.read_csv(f, sep=';', header=None, names=['ts', 'o', 'h', 'l', 'c', 'v']) for f in fs])
    x['t'] = pd.to_datetime(x.ts, format='%Y%m%d %H%M%S').dt.tz_localize(NY, ambiguous='NaT', nonexistent='NaT')
    x = x.dropna(subset=['t']).drop_duplicates('t').sort_values('t')
    dd = x.assign(dia=x.t.dt.tz_localize(None).dt.normalize()).groupby('dia').agg(
        Open=('o', 'first'), High=('h', 'max'), Low=('l', 'min'), Close=('c', 'last')).reset_index()
    aud = calidad_datos.auditar_historico(dd[dd.dia.dt.weekday < 5], f'{par} HistData M1 2003-2011')
    aud.imprimir()
    m = ((x.t.dt.tz_convert('UTC').dt.tz_localize(None) - pd.Timestamp('1970-01-01')) // pd.Timedelta(minutes=1)).to_numpy(np.int64)
    return m, x.c.to_numpy(float), aud


if __name__ == '__main__':
    d = sys.argv[1]
    dias = pd.bdate_range('2003-01-02', '2011-12-30')
    T0, T1 = instantes(dias, 'NY', 8), instantes(dias, 'NY', 16)
    series = {}
    for par, signo in {**PARES, **INFORMATIVOS}.items():
        if not os.path.isdir(os.path.join(d, par)):
            continue
        m, v, aud = cargar(d, par)
        r = pd.Series(np.log(precio(m, v, T1) / precio(m, v, T0)), index=dias) * signo
        hueco = np.zeros(len(r), bool)
        for g in aud.huecos:
            hueco |= (r.index >= g['inicio'] - pd.Timedelta(days=1)) & (r.index <= g['fin'] + pd.Timedelta(days=1))
        r[hueco] = np.nan
        series[par] = r
    s = pd.DataFrame(series)
    print('\nPor par (sentido previsto, pb/día):')
    for par in s.columns:
        for nom, sl in (('2003-2007', slice('2003', '2007')), ('2008-2011', slice('2008', '2011'))):
            x = s.loc[sl, par].dropna()
            print(f'  {par} {nom}: n {len(x)}, media {x.mean() * 1e4:+.2f}, t {t_nw(x.values):.2f}{"  (informativo)" if par in INFORMATIVOS else ""}')
    f = s[list(PARES)].dropna().mean(axis=1)
    p = f.loc['2008':'2011']
    tp = t_nw(p.values)
    print(f'\nPRINCIPAL factor 2008-2011: n {len(p)}, media {p.mean() * 1e4:+.2f} pb, t {tp:.2f} →', 'CUMPLE' if p.mean() > 0 and tp >= 1.645 else 'NO CUMPLE', '(t ≥ 1,645)')
    tt = t_nw(f.values)
    a = f.groupby(f.index.year).mean() * 1e4
    print(f'SECUNDARIO factor 2003-2011: media {f.mean() * 1e4:+.2f} pb, t {tt:.2f}, años + {(a > 0).sum()}/9 →',
          'CUMPLE' if tt >= 2 and (a > 0).sum() >= 6 else 'NO CUMPLE', '(t ≥ 2 y ≥ 6/9)')
    print('Factor por año (pb):', a.round(2).to_dict())
    print(f'Sharpe bruto del factor 2003-2011: {f.mean() / f.std() * np.sqrt(252):.2f}')
