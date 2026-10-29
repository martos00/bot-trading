"""Cuenta 150K pegada por el usuario: objetivo 9.000 $ (6 %), pérdida máx. 5.000 $ (3,33 %) arrastrada EN VIVO (incluye beneficio abierto;
con datos diarios se aproxima con el cierre del día → optimista), sin límite diario, cuota 30 días (34,70 $ con descuento; también 347 $),
activación única 247 $, retiro máx. 2.250 $ por pago (mensual, 90 %), arrastre que se fija en el saldo inicial (supuesto)."""
import numpy as np, pandas as pd
C=pd.read_csv('componentes_B.csv',index_col=0,parse_dates=True).loc['2018-03-26':]
def volctl(P): pv=P.rolling(60,min_periods=40).std().shift(1); return (P*(P.std()/pv).clip(0.5,2)).dropna()
cols=['yen','cesta_yen','oro_vie_1655','oro_D-2','plata_visp_1655','plata_viernes','cobre_asia_C102','nikkei_Q+2']
S=volctl(C[cols].sum(axis=1)); sh=lambda s: s.mean()/s.std()*np.sqrt(252)
rng=np.random.default_rng(13); B=20; T=504; CAP=150000; DD=5000/CAP; OBJ=9000/CAP; ACT=247; TOPE=2250
def camino(p): st=rng.integers(0,len(p)-B,T//B+1); return p[(st[:,None]+np.arange(B)).ravel()[:T]]
def simula(p, mes):
    R=camino(p); t=0; pag=0.0; ret=0.0; perd=0; primero=None
    while t<T:
        eq=hwm=0.0; t0=t; ok=False
        while t<T:
            eq+=R[t]; t+=1; hwm=min(max(hwm,eq),DD)
            if eq<=hwm-DD: break
            if eq>=OBJ: ok=True; break
        pag+=mes*max(1,int(np.ceil((t-t0)/21)))
        if primero is None: primero=ok
        if not ok: continue
        pag+=ACT; eq=hwm=0.0; ini=t; vivo=True
        while t<T:
            eq+=R[t]; t+=1; hwm=min(max(hwm,eq),DD)
            if eq<=hwm-DD: vivo=False; perd+=1; break
            if (t-ini)%21==0 and (t-ini)>=21*1 and eq>DD:
                q=min((eq-DD)*CAP,TOPE); ret+=0.9*q; eq-=q/CAP
        if vivo: break
    return pag,ret,perd,primero
for hair in (1.0,0.6):
    x=S.values-S.values.mean()*(1-hair)
    for mes in (34.70,347):
        print(f'\n=== 150K | Sharpe {sh(pd.Series(x)):.2f} ({"backtest" if hair==1 else "real al 60 %"}) | cuota {mes} $/30 días ===')
        print('riesgo/op | rent. esperada | peor día | aprueba 1.º | cuotas pagadas | pierde la fondeada (24 m) | retirado 24 m | neto | P(perder dinero)')
        for r_op in (0.15,0.20,0.25,0.30,0.40):
            p=x*(r_op/0.5); R_=[simula(p,mes) for _ in range(3000)]
            pg=np.array([q[0] for q in R_]); rt=np.array([q[1] for q in R_])
            print(f'  {r_op:.2f} % | {p.mean()*252*100:4.1f} % | {p.min()*100:5.2f} % | {np.mean([bool(q[3]) for q in R_])*100:3.0f} % | {pg.mean():6,.0f} $ | {np.mean([q[2]>0 for q in R_])*100:3.0f} % | {rt.mean():7,.0f} $ | {(rt-pg).mean():7,.0f} $ | {((rt-pg)<0).mean()*100:3.0f} %')
