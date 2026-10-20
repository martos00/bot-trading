"""C5 — inversión en Asia: venta USD/JPY 08-15 Tokio y compra AUD/USD 10-16 Sídney, HistData 2003-2011 (PREREGISTRO_C5).
Uso: python3 c5_asia_invertida.py DIR_HISTDATA"""
import sys
import numpy as np
import pandas as pd
from c1_certificacion import t_nw
from c3_breedon_ranaldo import precio, instantes
from c4_dolar_horario_eeuu import cargar

SESIONES = {'USDJPY': ('TOK', 8, 15, -1), 'AUDUSD': ('SYD', 10, 16, +1)}   # signo "invertido"

if __name__ == '__main__':
    dias = pd.bdate_range('2003-01-02', '2011-12-30')
    s = {}
    for par, (z, h0, h1, signo) in SESIONES.items():
        m, v, aud = cargar(sys.argv[1], par)
        r = pd.Series(np.log(precio(m, v, instantes(dias, z, h1)) / precio(m, v, instantes(dias, z, h0))), index=dias) * signo
        for g in aud.huecos:
            r[(r.index >= g['inicio'] - pd.Timedelta(days=1)) & (r.index <= g['fin'] + pd.Timedelta(days=1))] = np.nan
        s[par] = r
    s = pd.DataFrame(s)
    print('\nPor par (sentido invertido, pb/día):')
    for par in s:
        for nom, sl in (('2003-2007 (informativo)', slice('2003', '2007')), ('2008-2011', slice('2008', '2011'))):
            x = s.loc[sl, par].dropna()
            print(f'  {par} {nom}: n {len(x)}, media {x.mean() * 1e4:+.2f}, t {t_nw(x.values):.2f}')
    f = s.dropna().mean(axis=1)
    p = f.loc['2008':'2011']
    tp = t_nw(p.values)
    a = p.groupby(p.index.year).mean() * 1e4
    signos = all(s.loc['2008':'2011', par].mean() > 0 for par in s)
    print(f'\nFactor 2008-2011: n {len(p)}, media {p.mean() * 1e4:+.2f} pb, t {tp:.2f} →', 'CUMPLE' if p.mean() > 0 and tp >= 1.645 else 'NO CUMPLE', '(t ≥ 1,645)')
    print('Ambos pares con signo invertido 2008-2011:', 'CUMPLE' if signos else 'NO CUMPLE')
    print('Factor por año 2008-2011 (pb):', a.round(2).to_dict(), '→', 'CUMPLE' if (a > 0).sum() >= 3 else 'NO CUMPLE', '(≥ 3/4)')
    q = f.loc['2003':'2007']
    print(f'Informativo 2003-2007: media {q.mean() * 1e4:+.2f} pb, t {t_nw(q.values):.2f}; por año',
          (q.groupby(q.index.year).mean() * 1e4).round(2).to_dict())
    print('VEREDICTO:', 'CERTIFICADA' if p.mean() > 0 and tp >= 1.645 and signos and (a > 0).sum() >= 3 else 'NO CERTIFICADA')
