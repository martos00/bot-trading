import numpy as np, pandas as pd
U = pd.read_csv(__import__('sys').argv[1], index_col=0)['U'].dropna().values
print(f'U: {U.mean()*252:.1%}/año, vol diaria {U.std():.2%}')
rng = np.random.default_rng(5); B=20; T=252*6
def sim(x, ini):
    st = rng.integers(0, len(x)-B, T//B+1); R = x[(st[:,None]+np.arange(B)).ravel()[:T]]
    t=0; anual=np.zeros(6); examen=True; cap=ini; n_ex=0; pierde=0; t_ap=None
    while t<T:
        if examen: n_ex+=1; cap=ini
        eq=0.0; perdida=False
        while t<T:
            r=R[t]; t+=1
            if r<=-0.03: r=-0.03
            eq+=r
            if eq<=-0.06: perdida=True; break
            if eq>=0.10:
                if not examen: anual[min(t//252,5)]+=0.8*0.10*cap; cap=min(cap*2,4_000_000)
                elif t_ap is None: t_ap=t
                examen=False; eq=0.0
        if perdida: examen=True; pierde+=1
    return anual, n_ex, t_ap
for hair,et in ((0.6,'PRUDENTE'),(1.0,'BACKTEST')):
    for r in (0.5,0.65,0.8):
        x=(U-U.mean()*(1-hair))*r/0.5
        res=[sim(x,200_000) for _ in range(2000)]
        A=np.array([a for a,_,_ in res]); ne=np.array([n for _,n,_ in res]); ta=np.array([t if t else np.nan for _,_,t in res])
        print(f'{et} riesgo {r}: al MES de media ' + ' | '.join(f'año {i+1} {A[:,i].mean()/12:7,.0f} (med {np.median(A[:,i])/12:6,.0f})' for i in range(4)) + f' | exámenes en 6 años (mediana) {np.median(ne):.0f} | 1.er aprobado mediana {np.nanmedian(ta)/21:.1f} meses')
