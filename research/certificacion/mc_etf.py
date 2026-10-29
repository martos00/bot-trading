"""Elite Trader Funding Diamond Hands 100K (según terceros, sin verificar): pérdida máx. 3.500 $ arrastrada de fin de día (se fija en el
saldo inicial), pérdida diaria 1.500 $ (se trata como suspenso: supuesto prudente), 397 $/mes mientras dura el examen, objetivo SUPUESTO
+6 % (no consta). Fondeada: mismas reglas; retiro mensual de lo que pase de +3,5 %, 90 %. 24 meses, bootstrap 20 días."""
import numpy as np, pandas as pd
C=pd.read_csv('componentes_B.csv',index_col=0,parse_dates=True).loc['2018-03-26':]; C['bitcoin']*=0.2
def volctl(P): pv=P.rolling(60,min_periods=40).std().shift(1); return (P*(P.std()/pv).clip(0.5,2)).dropna()
base=['yen','cesta_yen','oro_vie_1655','oro_D-2','plata_visp_1655','plata_viernes','cobre_asia_C102','nikkei_Q+2']
carteras={'ETF 100K con bitcoin':volctl(C[base+['bitcoin']].sum(axis=1)),'ETF 100K sin bitcoin':volctl(C[base].sum(axis=1)),
          'Tradeify (referencia, sin cobre ni Nikkei)':volctl(C[['yen','cesta_yen','oro_vie_1655','oro_D-2','plata_visp_1655','plata_viernes']].sum(axis=1))}
rng=np.random.default_rng(9); B=20; T=504; CAP=100000; MES=397; DD=0.035; DLL=0.015; OBJ=0.06
def camino(p): st=rng.integers(0,len(p)-B,T//B+1); return p[(st[:,None]+np.arange(B)).ravel()[:T]]
def simula(p):
    R=camino(p); t=0; pagado=0.0; ret=0.0; perd=0; primero=None; tf=None
    while t<T:
        eq=hwm=0.0; t0=t; ok=False
        while t<T:
            r=R[t]; eq+=r; t+=1; hwm=min(max(hwm,eq),DD)
            if r<=-DLL or eq<=hwm-DD: break
            if eq>=OBJ: ok=True; break
        pagado+=MES*max(1,int(np.ceil((t-t0)/21)))
        if primero is None: primero=ok
        if not ok: continue
        tf=t if tf is None else tf; eq=hwm=0.0; ini=t; vivo=True
        while t<T:
            r=R[t]; eq+=r; t+=1; hwm=min(max(hwm,eq),DD)
            if r<=-DLL or eq<=hwm-DD: vivo=False; perd+=1; break
            if (t-ini)%21==0 and eq>DD: ret+=0.9*(eq-DD)*CAP; eq=DD
        if vivo: break
    return pagado,ret,perd,tf,primero
sh=lambda s: s.mean()/s.std()*np.sqrt(252)
for nom,s in carteras.items():
    for hair in (1.0,0.6):
        x0=s.values; x=x0-x0.mean()*(1-hair); m=x.mean()*252
        print(f'\n=== {nom} | Sharpe {"backtest" if hair==1 else "real al 60 %"} {sh(pd.Series(x)):.2f} ===')
        print('riesgo/op | rent. esperada | peor día histórico | aprueba 1.er examen | meses de cuota pagados (24 m) | pierde la fondeada | retirado 24 m (media) | neto | P(perder dinero)')
        for r_op in (0.15,0.20,0.25,0.30,0.40):
            p=x*(r_op/0.5); S=[simula(p) for _ in range(3000)]
            pg=np.array([q[0] for q in S]); rt=np.array([q[1] for q in S])
            print(f'  {r_op:.2f} % | {p.mean()*252*100:4.1f} % | {p.min()*100:5.2f} % | {np.mean([bool(q[4]) for q in S])*100:3.0f} % | {pg.mean()/MES:4.1f} | {np.mean([q[2]>0 for q in S])*100:3.0f} % | {rt.mean():7,.0f} $ | {(rt-pg).mean():7,.0f} $ | {((rt-pg)<0).mean()*100:3.0f} %')
