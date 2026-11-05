"""C109 — tono de los comunicados de la Fed (PREREGISTRO_C109). Uso: python3 -I c109_tono_fed.py DIR_COMUNICADOS DIR_SCRATCH"""
import sys, os, re, glob, html
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import numpy as np, pandas as pd
from c1_certificacion import t_nw
import c94_ruptura_otros_futuros as c94
DURAS = ["raise the target range", "increase the target range", "firming", "tighten", "tightening", "strong", "strengthened", "solid",
         "robust", "elevated", "upside risk", "further increases", "additional increases", "reduce its holdings", "reducing its holdings",
         "balance sheet reduction"]
BLANDAS = ["lower the target range", "reduce the target range", "decrease the target range", "accommodative", "accommodation", "easing",
           "weak", "weakened", "slowed", "moderated", "downside risk", "patient", "increase its holdings", "purchases of",
           "exceptionally low", "slack", "subdued", "soft"]
def texto(f):
    h = open(f, encoding='utf-8', errors='ignore').read()
    m = re.search(r'id="article"(.*?)(Voting for|For media inquiries|Implementation Note)', h, re.S)
    t = m.group(1) if m else h
    t = html.unescape(re.sub(r'<[^>]+>', ' ', t)).lower(); return re.sub(r'\s+', ' ', t)
def cuenta(t, lista): return sum(len(re.findall(r'\b' + re.escape(w), t)) for w in lista)
if __name__ == '__main__':
    D, SP = sys.argv[1], sys.argv[2]; c94.SP = SP
    filas = []
    for f in sorted(glob.glob(os.path.join(D, 'monetary*a.htm'))):
        t = texto(f); d = cuenta(t, DURAS); b = cuenta(t, BLANDAS)
        filas.append((pd.Timestamp(os.path.basename(f)[8:16]), d, b, (d - b) / (d + b) if d + b else 0.0, len(t.split())))
    T = pd.DataFrame(filas, columns=['dia', 'duras', 'blandas', 'tono', 'palabras']).set_index('dia').sort_index()
    T['senal'] = T.tono.diff()
    print(T.describe().round(2).to_string()); T.to_csv('c109_tono_por_comunicado.csv')
    R = {}
    for fut in ('ZN', '6E', 'GC'):
        h, ex = c94.carga_h1(fut); n = h.index.tz_localize(None)
        c = pd.Series(h.c.values, index=n)[(n.hour == 15)]; c.index = c.index.normalize(); c = c[~c.index.duplicated()]
        lr = np.log(c); R[fut] = (lr, c.index)
    out = []
    for d, s in T.senal.dropna().items():
        if s == 0: continue
        for fut, (lr, idx) in R.items():
            if d not in lr.index: continue
            i = lr.index.get_loc(d)
            for k in (1, 5):
                if i + k < len(lr): out.append((d, fut, k, -np.sign(s) * (lr.iloc[i + k] - lr.iloc[i]) * 1e4))
    O = pd.DataFrame(out, columns=['dia', 'fut', 'h', 'r'])
    O['z'] = O.groupby(['fut', 'h']).r.transform(lambda x: x / x.std())
    print()
    for k in (1, 5):
        g = O[O.h == k].groupby('dia').z.mean()
        a, b = g.loc[:'2017'], g.loc['2018':]
        ok = a.mean() > 0 and b.mean() > 0 and t_nw(b.values) >= 2.24
        print(f'PRINCIPAL h{k} (3 activos juntos): n {len(g)} | 2010-17 {a.mean():+.3f} (t {t_nw(a.values):.2f}) | 2018-26 {b.mean():+.3f} (t {t_nw(b.values):.2f}) → ' + ('PASA' if ok else 'NO PASA'))
        for fut in ('ZN', '6E', 'GC'):
            x = O[(O.h == k) & (O.fut == fut)].set_index('dia').r
            print(f'   {fut} h{k}: {x.mean():+.2f} pb (t {t_nw(x.values):.2f}) | 2010-17 {x.loc[:"2017"].mean():+.2f} | 2018-26 {x.loc["2018":].mean():+.2f}')
