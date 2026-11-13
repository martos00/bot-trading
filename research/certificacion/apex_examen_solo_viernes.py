"""SOLO oro y plata del viernes. Apex 150K EOD: examen (30 días) y fondeada con el límite de pérdida diaria aplicado MINUTO A MINUTO en los viernes (oro 16:00→16:55
y plata 16:30→16:57, datos de 1 min de GC y SI), con stop a 2 σ en cada pata. Resto de estrategias (sin rupturas, con C113): resultado
diario recortado al límite. Tamaño como en la hoja manual: exposición = riesgo / σ de los últimos 52 viernes (sin control de volatilidad de cartera).
Costes de futuros. Ventanas reales de 21 hábiles (2018-11 → 2026-09). Uso: python3 apex_examen_minuto.py DIR_SCRATCH"""
import sys, glob, os, numpy as np, pandas as pd
sys.path.insert(0, '.')
exec(open('plan_reinversion_etf.py').read().split('CAP, OBJ')[0])
from c84_ventana_liquidacion import cargar
CAP = 150000
# --- minutos de oro (viernes) y plata ---
gmin = {}
for f in sorted(glob.glob(f'{SP}/gc_vie/*.csv')):
    x = pd.read_csv(f)
    if len(x) < 30 or x.instrument_id.nunique() > 1: continue
    x.index = pd.to_datetime(x.ts_event, utc=True).dt.tz_convert('America/New_York'); mm = x.index.hour * 60 + x.index.minute
    s = pd.Series(x.close.values, index=mm).groupby(level=0).last()
    gmin[pd.Timestamp(os.path.basename(f)[:10])] = s
si = cargar(sorted(glob.glob(f'{SP}/m1/SI_*.csv')))
sdf = pd.DataFrame({'c': si.close.values, 'i': si.instrument_id.values, 'dia': si.index.normalize().tz_localize(None) if si.index.tz is not None else si.index.normalize(), 'm': si.index.hour * 60 + si.index.minute})
smin = {d: g for d, g in sdf[sdf.dia.dt.dayofweek == 4].groupby('dia')}
def ultimo(s, m):   # cierre de la última vela que empieza en [m-10, m)
    y = s[(s.index < m) & (s.index >= m - 10)]; return y.iloc[-1] if len(y) else np.nan
rg, rs = {}, {}
for d, s in gmin.items():
    a, b = ultimo(s, 960), ultimo(s, 1015)
    if a == a and b == b: rg[d] = np.log(b / a)
for d, g in smin.items():
    if g.i.nunique() > 1: continue
    s = pd.Series(g.c.values, index=g.m.values).groupby(level=0).last(); a, b = ultimo(s, 990), ultimo(s, 1017)
    if a == a and b == b: rs[d] = np.log(b / a)
RG = pd.Series(rg).sort_index(); RS = pd.Series(rs).sort_index()
SGd = RG.rolling(52, min_periods=30).std().shift(1); SSd = RS.rolling(52, min_periods=30).std().shift(1)
sg = RG.loc['2010':].std(); ss = RS.loc['2010':].std()
print(f'σ oro viernes {sg*1e4:.1f} pb | σ plata viernes {ss*1e4:.1f} pb | viernes con datos de los dos: {len(set(gmin)&set(smin))}')
def viernes(d, r, dll, hair, mu_g, mu_s):
    """resultado en $ del bloque oro+plata del viernes d con riesgo r (fracción), límite diario dll, stops 2σ"""
    if d not in gmin or d not in smin: return None
    s = gmin[d]; g = smin[d]
    if g.i.nunique() > 1: return None
    sv = pd.Series(g.c.values, index=g.m.values).groupby(level=0).last()
    a = ultimo(s, 960); b = ultimo(sv, 990)
    if not (a == a and b == b): return None
    g_ = SGd.get(d, np.nan); s_ = SSd.get(d, np.nan)
    if not (g_ == g_ and s_ == s_): return None
    eg = min(r / g_, TOPE) * CAP; es = min(r / s_, TOPE) * CAP; adj_g = mu_g * (1 - hair); adj_s = mu_s * (1 - hair)
    pg_open = True; ps_open = False; ps_done = False; pnl_g = pnl_s = 0.0
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
        if pnl_g + pnl_s <= -dll: return -dll, True
    cost = eg * 0.74e-4 + es * 2.3e-4
    return pnl_g + pnl_s - cost, False
otros = ['yen']   # se anula abajo: solo viernes
Cd = C.loc['2018-11-05':]
mu_g = pd.Series(rg).loc['2018-11-05':].mean(); mu_s = pd.Series(rs).loc['2018-11-05':].mean()
def serie_dia(r, dll, hair, minuto=True):
    o = Cd['yen'] * 0.0
    fv = Cd['oro_vie_1655'] + Cd['plata_viernes']; fvd = (fv - fv.mean() * (1 - hair)) * CAP * r / 0.005
    out = []; toques = 0; nv = 0
    for d in Cd.index:
        x = o[d]
        if d.dayofweek == 4 and fv[d] != 0:
            res = viernes(d, r, dll, hair, mu_g, mu_s) if minuto else None
            if res is None: x += max(fvd[d], -dll)
            else: x += res[0]; toques += res[1]; nv += 1
        out.append(max(x, -dll))
    return np.array(out), toques, nv
def examen(x):
    eq = hwm = 0.0
    for t, v in enumerate(x):
        eq += v; hwm = max(hwm, eq); piso = 9000 if hwm >= 13000 else hwm - 4000
        if eq <= piso: return 0
        if eq >= 9000: return 1
    return 0
for hair, et in ((0.6, 'PRUDENTE'), (1.0, 'BACKTEST')):
    TOPE = 6
    for rpct in (1.0, 2.0, 3.0):
        r = rpct / 100
        xm, toq, nv = serie_dia(r, 2000, hair, True); xd, _, _ = serie_dia(r, 2000, hair, False)
        pm = np.mean([examen(xm[i:i + 21]) for i in range(len(xm) - 21)]); pd_ = np.mean([examen(xd[i:i + 21]) for i in range(len(xd) - 21)])
        print(f'{et:8s} riesgo examen {rpct:.2f} | aprueba en 30 días: minuto a minuto {pm*100:3.0f} % (antes, al cierre: {pd_*100:3.0f} %) | viernes que tocan el límite de 2.000 $ {toq/max(nv,1)*100:3.0f} % de {nv}', flush=True)
