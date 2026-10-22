"""C61: niveles redondos en divisas (rebote R y cruce C). Ver PREREGISTRO_C61."""
import glob
import numpy as np, pandas as pd
from scipy import stats
from c1_certificacion import t_nw
S = '/tmp/claude-0/-home-user-bot-trading/682335b1-28ae-5d18-9355-ce7f0f968722/scratchpad/fxcm/'
PARES = {'EURUSD': 0.01, 'GBPUSD': 0.01, 'AUDUSD': 0.01, 'USDCAD': 0.01, 'USDCHF': 0.01, 'USDJPY': 1.0}
COM = 0.45e-4
def carga(p):
    x = pd.concat([pd.read_csv(f, compression='gzip', usecols=['DateTime', 'BidClose', 'AskClose']) for f in sorted(glob.glob(S + f'{p}/{p}_*.csv.gz'))])
    for c in ('BidClose', 'AskClose'): x[c] = pd.to_numeric(x[c], errors='coerce')
    x = x.dropna(); x = x[(x.BidClose > 0) & (x.AskClose > x.BidClose * 0.99)]
    t = pd.to_datetime(x.DateTime, format='%m/%d/%Y %H:%M:%S.%f').dt.tz_localize('UTC').dt.tz_convert('America/New_York').dt.tz_localize(None)
    x.index = t; x = x[~x.index.duplicated()].sort_index()
    return x[(x.index.weekday < 5)]
EV = {'R': {}, 'C': {}}
for p, paso in PARES.items():
    x = carga(p); pip = paso / 100
    for d, g in x.groupby(x.index.normalize()):
        g = g[(g.index.hour >= 2) & (g.index.hour < 13)]
        if len(g) < 300: continue
        b = g.BidClose.values; a = g.AskClose.values; m = (a + b) / 2; t = g.index
        niv = np.round(m / paso) * paso; dist = (m - niv) / pip
        usados = set()
        for i in range(15, len(m) - 31):
            if t[i].hour >= 12: break
            L = niv[i]
            if L in usados or abs(dist[i]) > 0.5: continue
            lado = np.sign(m[i - 15] - L)
            if abs(m[i - 15] - L) / pip < 5 or lado == 0: continue
            usados.add(L); avance = -lado                        # +1 si venía de abajo (sube hacia L)
            if (t[i + 30] - t[i]) > pd.Timedelta(minutes=40): continue
            # R: en contra del avance
            br = -avance * np.log(m[i + 30] / m[i])
            ne = (np.log(b[i + 30] / a[i]) if -avance > 0 else np.log(b[i] / a[i + 30])) - COM
            EV['R'].setdefault(d, []).append((br, ne))
            # C: cruce de 3 pips en el sentido del avance dentro de los 60 min siguientes
            for j in range(i + 1, min(i + 61, len(m) - 31)):
                if avance * (m[j] - L) / pip >= 3:
                    if (t[j + 30] - t[j]) > pd.Timedelta(minutes=40): break
                    bc = avance * np.log(m[j + 30] / m[j])
                    nc = (np.log(b[j + 30] / a[j]) if avance > 0 else np.log(b[j] / a[j + 30])) - COM
                    EV['C'].setdefault(d, []).append((bc, nc)); break
    print(p, 'hecho', flush=True)
ps, filas = {}, {}
for k in ('R', 'C'):
    X = pd.DataFrame({d: np.mean(v, axis=0) for d, v in EV[k].items()}, index=['bruto', 'neto']).T.sort_index()
    dsc, c = X.loc['2012':'2018'], X.loc['2019':'2026']; t = t_nw(c.neto.values); ps[k] = 1 - stats.norm.cdf(t); filas[k] = (dsc, c, t)
orden = sorted(ps, key=ps.get); seguir = True
for j, k in enumerate(orden):
    seguir = seguir and ps[k] <= 0.05 / (2 - j); dsc, c, t = filas[k]; an = c.neto.groupby(c.index.year).sum(); coste = (c.bruto - c.neto).mean()
    ok = seguir and (an > 0).mean() >= 0.6 and c.bruto.mean() >= 3 * coste
    print(f'{k}: 2012-18 n {len(dsc)} bruto {dsc.bruto.mean()*1e4:.2f} neto {dsc.neto.mean()*1e4:.2f} pb (t {t_nw(dsc.neto.values):.2f}) | 2019-26 n {len(c)} bruto {c.bruto.mean()*1e4:.2f} '
          f'(t {t_nw(c.bruto.values):.2f}) neto {c.neto.mean()*1e4:.2f} pb (t {t:.2f}) coste {coste*1e4:.2f} años+ {(an>0).sum()}/{len(an)} | Holm {seguir} → {"CERTIFICADA" if ok else "no"}')
