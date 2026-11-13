"""Apex 150K: examen EOD frente a Intraday, minuto a minuto en los viernes (oro y plata, datos de 1 min, stop 2 σ por pata).
EOD: pérdida máx. 4.000 $ arrastrada con el saldo de cierre; límite diario 2.000 $ (cierra el día al tocarlo).
Intraday: SIN límite diario; pérdida máx. 4.000 $ arrastrada con el máximo EN TIEMPO REAL (incluye ganancias abiertas) de los viernes; en el
resto de días solo se conoce el cierre (aproximación favorable al Intraday). Objetivo 9.000 $ comprobado al cierre del día; 21 hábiles.
Cartera manual sin rupturas (con C113). Uso: python3 apex_eod_vs_intraday.py DIR_SCRATCH"""
import sys
src = open('apex_examen_minuto.py').read()
src = src[:src.index("def serie_dia(")]
exec(src)
def camino_viernes(d, r, hair):
    if d not in gmin or d not in smin: return None
    s = gmin[d]; g = smin[d]
    if g.i.nunique() > 1: return None
    sv = pd.Series(g.c.values, index=g.m.values).groupby(level=0).last()
    a = ultimo(s, 960); b = ultimo(sv, 990); g_ = SGd.get(d, np.nan); s_ = SSd.get(d, np.nan)
    if not (a == a and b == b and g_ == g_ and s_ == s_): return None
    eg = min(r / g_, 6) * CAP; es = min(r / s_, 6) * CAP; adj_g = mu_g * (1 - hair); adj_s = mu_s * (1 - hair)
    pg_open = True; ps_open = False; ps_done = False; pnl_g = pnl_s = 0.0; path = []
    for m in range(961, 1018):
        if pg_open and m <= 1015 and m in s.index:
            rg_ = s[m] / a - 1 - adj_g * (m - 960) / 55; pnl_g = eg * rg_
            if rg_ <= -2 * g_: pnl_g = -eg * 2 * g_; pg_open = False
        if m == 1015 and pg_open: pg_open = False
        if m == 991 and not ps_done: ps_open = True
        if ps_open and m in sv.index:
            rs_ = sv[m] / b - 1 - adj_s * (m - 990) / 27; pnl_s = es * rs_
            if rs_ <= -2 * s_: pnl_s = -es * 2 * s_; ps_open = False; ps_done = True
        if m == 1017 and ps_open: ps_open = False; ps_done = True
        path.append(pnl_g + pnl_s)
    path[-1] -= eg * 0.74e-4 + es * 2.3e-4
    return np.array(path)
def dias(r, hair):
    o = Cd[otros].sum(axis=1) * CAP * r / 0.005; o = o - Cd[otros].sum(axis=1).mean() * CAP * r / 0.005 * (1 - hair)
    fv = Cd['oro_vie_1655'] + Cd['plata_viernes']; fvd = (fv - fv.mean() * (1 - hair)) * CAP * r / 0.005
    out = []
    for d in Cd.index:
        p = None
        if d.dayofweek == 4 and fv[d] != 0:
            p = camino_viernes(d, r, hair)
            if p is None: p = np.array([fvd[d]])
        out.append((o[d], p))
    return out
def ex_eod(D):
    eq = hwm = 0.0
    for o, p in D:
        x = o
        if p is not None:
            hit = np.any(p <= -2000); x += -2000 if hit else p[-1]
        x = max(x, -2000); eq += x; hwm = max(hwm, eq); piso = 9000 if hwm >= 13000 else hwm - 4000
        if eq <= piso: return 0
        if eq >= 9000: return 1
    return 0
def ex_intra(D):
    eq = hwm = 0.0
    for o, p in D:
        base = eq + o                       # el resto del día (solo cierre)
        hwm = max(hwm, base)
        if p is not None:
            for v in p:
                hwm = max(hwm, base + v); piso = 9000 if hwm >= 13000 else hwm - 4000
                if base + v <= piso: return 0
            eq = base + p[-1]
        else: eq = base
        hwm = max(hwm, eq); piso = 9000 if hwm >= 13000 else hwm - 4000
        if eq <= piso: return 0
        if eq >= 9000: return 1
    return 0
for hair, et in ((0.6, 'PRUDENTE'), (1.0, 'BACKTEST')):
    for rpct in (1.0, 2.0, 3.0):
        D = dias(rpct / 100, hair)
        pe = np.mean([ex_eod(D[i:i + 21]) for i in range(len(D) - 21)]); pi = np.mean([ex_intra(D[i:i + 21]) for i in range(len(D) - 21)])
        print(f'{et:8s} riesgo examen {rpct:.0f} | aprueba en 30 días: EOD {pe*100:3.0f} % | Intraday {pi*100:3.0f} %', flush=True)
