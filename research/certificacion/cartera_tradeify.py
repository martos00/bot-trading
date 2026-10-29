import numpy as np, pandas as pd
C=pd.read_csv('componentes_B.csv',index_col=0,parse_dates=True).loc['2018-03-26':]
cols=['yen','cesta_yen','oro_vie_1655','oro_D-2','plata_visp_1655','plata_viernes']
P=C[cols].sum(axis=1); pv=P.rolling(60,min_periods=40).std().shift(1); T=(P*(P.std()/pv).clip(0.5,2)).dropna()
pd.DataFrame({'T':T}).to_csv('cartera_tradeify.csv')
sh=lambda s: s.mean()/s.std()*np.sqrt(252)
print(f'Sharpe {sh(T):.2f} | rent. anual a riesgo base 0,5 % {T.mean()*252*100:.1f} % | vol {T.std()*np.sqrt(252)*100:.1f} %')
ops={c:int((C[c]!=0).sum()) for c in cols}; yrs=(C.index[-1]-C.index[0]).days/365.25
print('operaciones/año:', {k: round(v/yrs,1) for k,v in ops.items()}, 'total', round(sum(ops.values())/yrs), '| días con posición/año', round((T!=0).sum()/yrs))
for c in cols:
    x=C[c]; print(f'  {c}: aporta {x.sum()/P.sum()*100:.0f} % del beneficio')
for obj in (0.10,0.15,0.25):
    k=obj/(T.mean()*252); q=T*k; e=q.cumsum(); dd=(e-e.cummax()).min()
    an=q.groupby(q.index.year).sum()*100; me=q.resample('ME').sum()
    # racha: días seguidos bajo máximos
    uw=(e<e.cummax()); best=cur=0
    for v in uw: cur=cur+1 if v else 0; best=max(best,cur)
    print(f'\n=== objetivo {obj*100:.0f} %: riesgo base {0.5*k:.2f} % por operación ===')
    print(f'  caída máx. {dd*100:.1f} % | peor mes {me.min()*100:.1f} % | meses negativos {(me<0).mean()*100:.0f} % | racha más larga bajo máximos {best} días hábiles (~{best/21:.0f} meses) | peor día {q.min()*100:.2f} %')
    print('  por año:', an.round(1).to_dict())
