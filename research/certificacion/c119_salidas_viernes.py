"""C119 (PREREGISTRO_C119_salidas_viernes.md). Uso: python3 c119_salidas_viernes.py DIR_SCRATCH"""
import sys, numpy as np, pandas as pd
src = open('apex_examen_minuto.py').read(); exec(src[:src.index("otros =")])
def caminos(mins, ini, fin, sig):
    out = {}
    for d, s in mins.items():
        if isinstance(s, pd.DataFrame):
            if s.i.nunique() > 1: continue
            s = pd.Series(s.c.values, index=s.m.values).groupby(level=0).last()
        a = ultimo(s, ini); sg_ = sig.get(d, np.nan)
        if not (a == a and sg_ == sg_): continue
        p = [(s[m] / a - 1) / sg_ for m in range(ini + 1, fin + 1) if m in s.index]
        e = ultimo(s, fin)
        if e == e and len(p) > 5: out[d] = (np.array(p), (e / a - 1) / sg_)
    return out
G = caminos(gmin, 960, 1015, SGd); Sv = caminos(smin, 990, 1017, SSd)
def aplica(p, fin, regla):
    pico = -9
    for v in p:
        if v <= -2: return -2.0
        pico = max(pico, v)
        if regla[0] == 'T' and v >= regla[1]: return regla[1]
        if regla[0] == 'R' and pico >= 1 and v <= pico - regla[1]: return v
    return fin
REG = {'normal': ('N', 0), 'T1': ('T', 1), 'T1.5': ('T', 1.5), 'T2': ('T', 2), 'R1': ('R', 0.5), 'R2': ('R', 0.75), 'R3': ('R', 1.0)}
for nom, D, coste, sig in (('ORO viernes', G, 0.74e-4, SGd), ('PLATA viernes', Sv, 2.3e-4, SSd)):
    df = pd.DataFrame({k: {d: aplica(p, f, r) - coste / sig[d] for d, (p, f) in D.items()} for k, r in REG.items()}).sort_index()
    mfe = pd.Series({d: max(p.max(), 0) for d, (p, f) in D.items()}).sort_index(); fin = pd.Series({d: f for d, (p, f) in D.items()}).sort_index()
    print(f'\n===== {nom}: {len(df)} viernes =====')
    print(f'Descriptivo: pico favorable medio {mfe.mean():.2f} σ (mediana {mfe.median():.2f}) | resultado final medio {fin.mean():+.2f} σ | se devuelve de media {(mfe-fin).mean():.2f} σ | '
          f'acaban por debajo de la mitad de su pico {np.mean(fin < 0.5*mfe)*100:.0f} % | tocan +1 σ en algún momento {np.mean(mfe>=1)*100:.0f} %')
    dentro = df.loc[:'2017']; fuera = df.loc['2018':]
    print('Dentro de muestra (2010-2017), resultado medio por operación en σ: ' + ' | '.join(f'{k} {dentro[k].mean():+.3f}' for k in REG))
    mejor = max([k for k in REG if k != 'normal'], key=lambda k: dentro[k].mean())
    if dentro[mejor].mean() <= dentro['normal'].mean(): print('→ Ninguna regla supera a la salida normal dentro de muestra: NO HAY REGLA'); continue
    dif = fuera[mejor] - fuera['normal']; t = dif.mean() / dif.std() * np.sqrt(len(dif))
    rw = lambda s: s.rolling(10).sum().min()
    print(f'→ Elegida {mejor}. Fuera de muestra (2018-2026, {len(fuera)} viernes): normal {fuera["normal"].mean():+.3f} σ | {mejor} {fuera[mejor].mean():+.3f} σ | diferencia t {t:.2f} | '
          f'peor racha de 10: normal {rw(fuera["normal"]):+.2f} / {mejor} {rw(fuera[mejor]):+.2f} → {"PASA" if t >= 1.65 and rw(fuera[mejor]) >= rw(fuera["normal"]) else "NO PASA"}')
    print('   (informativo, todas fuera de muestra): ' + ' | '.join(f'{k} {fuera[k].mean():+.3f}' for k in REG))
