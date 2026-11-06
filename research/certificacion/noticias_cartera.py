import numpy as np, pandas as pd
C=pd.read_csv('componentes_B.csv',index_col=0,parse_dates=True).loc['2018-03-26':]
fomc=pd.to_datetime(pd.read_csv('n/fomc.csv').fomc)
d=C.index; nfp=pd.DatetimeIndex([g.iloc[0] for _,g in pd.Series(d[d.dayofweek==4],index=d[d.dayofweek==4]).groupby([d[d.dayofweek==4].year,d[d.dayofweek==4].month])])
news=d.isin(fomc)|d.isin(nfp)
def volctl(P): pv=P.rolling(60,min_periods=40).std().shift(1); return (P*(P.std()/pv).clip(0.5,2)).dropna()
sh=lambda s: s.mean()/s.std()*np.sqrt(252)
for nombre,cols in (('150K (bot ETF/Tradeify)',['yen','cesta_yen','oro_vie_1655','oro_D-2','plata_visp_1655','plata_viernes','cobre_asia_C102','nikkei_Q+2','nikkei_Q-2']),
                    ('50K',['yen','cesta_yen','oro_vie_1655','oro_D-2','plata_visp_1655','plata_viernes'])):
    X=C[cols]; yrs=(d[-1]-d[0]).days/365.25
    print(f'\n######## Cartera {nombre} — riesgo 0,65 % por operación, cuenta 150.000 $ ########')
    print(f'días de noticias (FOMC + empleo) en el periodo: {news.sum()} ({news.sum()/yrs:.0f}/año)')
    res={}
    for etq,Y in (('OPERA TODO',X),('NO OPERA EN NOTICIAS',X.mul(~news,axis=0))):
        T=volctl(Y.sum(axis=1))*0.65/0.5; e=T.cumsum(); dd=(e-e.cummax()).min(); me=T.resample('ME').sum()
        nops=int((Y!=0).sum().sum()); res[etq]=T
        print(f'\n[{etq}] Sharpe {sh(T):.2f} | rent. anual {T.mean()*252*100:.1f} % (~{T.mean()*252*150000:,.0f} $/año) | caída máx {dd*100:.1f} % | peor mes {me.min()*100:.1f} % | meses negativos {(me<0).mean()*100:.0f} % | operaciones/año {nops/yrs:.0f}')
        print('   por año %:', (T.groupby(T.index.year).sum()*100).round(1).to_dict())
    print('\nLo que hace cada estrategia SOLO en días de noticias (riesgo 0,65 %, sin control de vol.):')
    for c in cols:
        x=X[c]*0.65/0.5; xn=x[news&(x!=0)]; xr=x[~news&(x!=0)]
        if len(xn)==0: print(f'   {c:18s} no opera nunca en días de noticias'); continue
        t=(xn.mean()-xr.mean())/np.sqrt(xn.var()/len(xn)+xr.var()/len(xr))
        print(f'   {c:18s} ops noticias {len(xn):4d} ({len(xn)/yrs:4.1f}/año) | media noticias {xn.mean()*1e4:+.1f} pb de cuenta vs resto {xr.mean()*1e4:+.1f} | total en noticias {xn.sum()*150000:+,.0f} $ en {yrs:.1f} años | dif t {t:+.2f}')
    Tn=res['OPERA TODO']-res['NO OPERA EN NOTICIAS'].reindex(res['OPERA TODO'].index).fillna(0)
