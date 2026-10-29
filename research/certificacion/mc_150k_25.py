import numpy as np, pandas as pd
C=pd.read_csv('componentes_B.csv',index_col=0,parse_dates=True).loc['2018-03-26':]
def volctl(P): pv=P.rolling(60,min_periods=40).std().shift(1); return (P*(P.std()/pv).clip(0.5,2)).dropna()
cols=['yen','cesta_yen','oro_vie_1655','oro_D-2','plata_visp_1655','plata_viernes','cobre_asia_C102','nikkei_Q+2']
S=volctl(C[cols].sum(axis=1))
rng=np.random.default_rng(21); B=20; T=504; CAP=150000; DD=5000/CAP; OBJ=9000/CAP; ACT=247; TOPE=2250; RESET=47
def camino(p): st=rng.integers(0,len(p)-B,T//B+1); return p[(st[:,None]+np.arange(B)).ravel()[:T]]
def simula(p, mes):
    R=camino(p); t=0; pag=mes; ret=0.0; perd=0; intentos=0; tf=None; dur=None; ret12=0.0; meses_pagados=1; t_ult_cuota=0
    while t<T:
        intentos+=1
        if intentos>1: pag+=RESET
        eq=hwm=0.0; ok=False
        while t<T:
            eq+=R[t]; t+=1; hwm=min(max(hwm,eq),DD)
            if t-t_ult_cuota>=21: pag+=mes; t_ult_cuota=t
            if eq<=hwm-DD: break
            if eq>=OBJ: ok=True; break
        if not ok: continue
        if tf is None: tf=t
        pag+=ACT; eq=hwm=0.0; ini=t; vivo=True
        while t<T:
            eq+=R[t]; t+=1; hwm=min(max(hwm,eq),DD)
            if eq<=hwm-DD: vivo=False; perd+=1; break
            if (t-ini)%21==0 and eq>DD:
                q=min((eq-DD)*CAP,TOPE); ret+=0.9*q; eq-=q/CAP
                if t<=252: ret12+=0.9*q
        if dur is None: dur=(t-ini) if not vivo else 10**6
        if vivo: break
        t_ult_cuota=t; pag+=mes
    return dict(pag=pag,ret=ret,perd=perd,intentos=intentos,tf=tf,dur=dur,ret12=ret12)
sh=lambda s: s.mean()/s.std()*np.sqrt(252)
for hair,et in ((1.0,'backtest'),(0.6,'Sharpe real al 60 %')):
    x=S.values-S.values.mean()*(1-hair); m=x.mean()*252
    for mes in (34.70,347):
        r_op=0.5*0.25/m; p=x*0.25/m
        R_=[simula(p,mes) for _ in range(4000)]
        pg=np.array([q['pag'] for q in R_]); rt=np.array([q['ret'] for q in R_]); tf=np.array([q['tf'] if q['tf'] else np.nan for q in R_])
        it=np.array([q['intentos'] for q in R_]); du=np.array([q['dur'] if q['dur'] is not None else np.nan for q in R_])
        e=pd.Series(p).cumsum(); 
        print(f'\n=== 150K, objetivo 25 %/año | {et} (Sharpe {sh(pd.Series(x)):.2f}) | cuota {mes} $ ===')
        print(f'  riesgo por operación {r_op:.2f} % | peor día histórico {p.min()*100:.2f} % ({p.min()*CAP:,.0f} $) | caída máx. histórica {(e-e.cummax()).min()*100:.1f} % ({(e-e.cummax()).min()*CAP:,.0f} $; límite 5.000 $)')
        print(f'  aprueba al 1.er intento {np.mean([q["intentos"]==1 and q["tf"] is not None for q in R_])*100:.0f} % | llega a fondeada en 24 m {np.mean(~np.isnan(tf))*100:.0f} % | meses hasta fondeada (mediana) {np.nanmedian(tf)/21:.1f} | intentos (media) {it.mean():.1f}')
        f=~np.isnan(du)
        print(f'  fondeada: la pierde en < 3 meses {np.mean(du[f]<63)*100:.0f} % | en < 6 m {np.mean(du[f]<126)*100:.0f} % | en < 12 m {np.mean(du[f]<252)*100:.0f} % | la pierde en 24 m (alguna) {np.mean([q["perd"]>0 for q in R_])*100:.0f} %')
        print(f'  dinero 24 m: pagado {pg.mean():,.0f} $ | retirado media {rt.mean():,.0f} $ / mediana {np.median(rt):,.0f} $ / 10 % peor {np.percentile(rt,10):,.0f} $ | neto media {(rt-pg).mean():,.0f} $ | P(acabar perdiendo dinero) {((rt-pg)<0).mean()*100:.0f} % | P(neto > 10.000 $) {((rt-pg)>10000).mean()*100:.0f} %')
        print(f'  máximo retirable por el tope: 2.250 $ × 90 % ≈ 2.025 $/mes ≈ 24.300 $/año (16 % de 150K)')
