import numpy as np, pandas as pd, glob, os, io, zipfile, holidays
from c45_oro_viernes import carga, tramo
from c83_oro_d2_nikkei_q2 import ultimos
from c84_ventana_liquidacion import cargar
J=pd.read_csv('/tmp/claude-0/-home-user-bot-trading/682335b1-28ae-5d18-9355-ce7f0f968722/scratchpad/serie_ftmo.csv',index_col=0,parse_dates=True).loc['2018-03-26':]
def sh(s): return s.mean()/s.std()*np.sqrt(252)
def add(s, r, cost):
    r=r.loc['2018-03-26':]; pnl=0.005*(r-cost)/r.std(); o=pd.Series(0.0,index=s.index); ix=o.index.intersection(pnl.index); o.loc[ix]=pnl.reindex(ix); return s+o
def ajusta(col, dc_pb, sig_pb):
    x=J[col].copy(); x[x!=0]-= 0.005*dc_pb/sig_pb; return x
gc={}
for f in sorted(glob.glob('/tmp/claude-0/-home-user-bot-trading/682335b1-28ae-5d18-9355-ce7f0f968722/scratchpad/gc_vie/*.csv')):
    x=pd.read_csv(f)
    if len(x)<30 or x.instrument_id.nunique()>1: continue
    x.index=pd.to_datetime(x.ts_event,utc=True).dt.tz_convert('America/New_York'); mm=x.index.hour*60+x.index.minute
    def px(m):
        y=x.close[(mm<m)&(mm>=m-10)]; return y.iloc[-1] if len(y) else np.nan
    gc[pd.Timestamp(os.path.basename(f)[:10])]=(px(960),px(1005),px(1015))
g=pd.DataFrame(gc,index=['a','b','c']).T; oro45=np.log(g.b/g.a).dropna(); oro55=np.log(g.c/g.a).dropna()
jp=carga('/tmp/claude-0/-home-user-bot-trading/682335b1-28ae-5d18-9355-ce7f0f968722/scratchpad/hd_new/JPXJPY'); r=tramo(jp,15,0,15,59); dd=r.index
nik=r.reindex([grp.sort_values().iloc[1] for (y,m),grp in pd.Series(dd,index=dd).groupby([dd.year,dd.month]) if m in (1,4,7,10) and len(grp)>1]).dropna()
xau=carga('/tmp/claude-0/-home-user-bot-trading/682335b1-28ae-5d18-9355-ce7f0f968722/scratchpad/hd2/XAUUSD'); dx=pd.DatetimeIndex(sorted(set(xau.index.tz_localize(None).normalize()))); dx=dx[dx.weekday<5]
od2=(-tramo(xau,9,30,9,59)).reindex(ultimos(dx,2)).dropna()
dj=pd.DatetimeIndex(sorted(set(jp.index.tz_localize(None).normalize()))); dj=dj[dj.weekday<5]
nq2=(-tramo(jp,20,0,20,59)).reindex(ultimos(dj,1,(3,6,9,12))).dropna()
# plata SI futuro 1m
x=cargar(sorted(glob.glob('/tmp/claude-0/-home-user-bot-trading/682335b1-28ae-5d18-9355-ce7f0f968722/scratchpad/m1/SI_*.csv')))
df=pd.DataFrame({'c':x.close.values,'i':x.instrument_id.values,'dia':x.index.normalize(),'m':x.index.hour*60+x.index.minute})
def px(m): return df[(df.m<m)&(df.m>=m-10)].groupby('dia').last()
P={k:px(m) for k,m in (('1600',960),('1630',990),('1645',1005),('1655',1015),('1700',1020))}
def ret(a,b):
    j=P[a].join(P[b],lsuffix='a',rsuffix='b',how='inner'); j=j[j.ia==j.ib]; return np.log(j.cb/j.ca)
fest=holidays.financial_holidays('NYSE',years=range(2010,2027))
def esvis(d):
    if d.weekday()>=5 or d.date() in fest: return False
    n=d+pd.Timedelta(days=1)
    while n.weekday()>=5: n+=pd.Timedelta(days=1)
    return n.date() in fest
s45=ret('1600','1645'); s45=s45[[esvis(d) for d in s45.index]]
s55=ret('1600','1655'); s55=s55[[esvis(d) for d in s55.index]]
svie=ret('1630','1700'); svie=svie[svie.index.dayofweek==4]
# bitcoin 21-23 UTC (dias laborables)
rows=[]
for f in sorted(glob.glob('/tmp/claude-0/-home-user-bot-trading/682335b1-28ae-5d18-9355-ce7f0f968722/scratchpad/bn/1h/BTCUSDT-1h-*.zip')):
    with zipfile.ZipFile(f) as z: rows.append(pd.read_csv(io.BytesIO(z.read(z.namelist()[0])),header=None,usecols=[0,1]))
b=pd.concat(rows); t=b[0].astype('int64'); t=np.where(t>1e14,t//1000,t); o=pd.Series(b[1].astype(float).values,index=pd.to_datetime(t,unit='ms')); o=o[~o.index.duplicated()]
o21=o[o.index.hour==21]; o23=o[o.index.hour==23]; o21.index=o21.index.normalize(); o23.index=o23.index.normalize()
btc=np.log(o23/o21).dropna(); btc=btc[btc.index.dayofweek<5]
fu=ajusta('e1',0.21,13)+ajusta('yen',0.44,12)+J['ej']/3
fu=add(fu,oro45,0.74e-4); fu=add(fu,nik,2.5e-4); fu=add(fu,od2,0.74e-4); fu=add(fu,nq2,2.5e-4)
print(f'A Futuros, firma con cierre 16:45 (base): Sharpe {sh(fu):.2f}  rent {fu.mean()*252*100:.1f} %')
fa=add(fu,s45,2.3e-4); print(f'B  + plata vispera 16:45 (E10b): Sharpe {sh(fa):.2f}  rent {fa.mean()*252*100:.1f} %')
fo=ajusta('e1',0.21,13)+ajusta('yen',0.44,12)+J['ej']/3+J['fest']
fo=add(fo,oro55,0.74e-4); fo=add(fo,nik,2.5e-4); fo=add(fo,od2,0.74e-4); fo=add(fo,nq2,2.5e-4); fo=add(fo,s55,2.3e-4)
print(f'C Firma que permite mantener (oro hasta 16:55, plata vispera 16:55, materias primas festivos): Sharpe {sh(fo):.2f}  rent {fo.mean()*252*100:.1f} %')
fv=add(fo,svie,2.3e-4); print(f'D  + plata viernes 16:30-17:00: Sharpe {sh(fv):.2f}  rent {fv.mean()*252*100:.1f} %')
fb=add(fv,btc,3e-4); print(f'E  + bitcoin 21-23 UTC (MBT 3 pb): Sharpe {sh(fb):.2f}  rent {fb.mean()*252*100:.1f} %')


e1=ajusta('e1',0.21,13)
for nom,q in (('E completa',fb),('E sin euro',fb-e1)):
    eq=q.cumsum(); print(f'{nom}: Sharpe {sh(q):.2f}, rent {q.mean()*252*100:.1f} %/año, DD max {(eq-eq.cummax()).min()*100:.1f} %, años', (q.groupby(q.index.year).sum()*100).round(1).to_dict())
    k=-5/((eq-eq.cummax()).min()*100); print(f'   escalado a DD 5 %: rent {q.mean()*252*100*k:.1f} %/año')
print('E1 sola Sharpe', round(sh(e1),2))

import sys as _s; _s.argv=['x','/tmp/claude-0/-home-user-bot-trading/682335b1-28ae-5d18-9355-ce7f0f968722/scratchpad']
import c93_oro_ruptura_dia_anterior as m93, c93b_controles_y_gc as m93b, c99_ruptura_rango_asiatico as m99, c101_ruptura_asiatica_otros as m101, c102_ruptura_asiatica_asia as m102
gg,ex=m93b.carga_gc('/tmp/claude-0/-home-user-bot-trading/682335b1-28ae-5d18-9355-ce7f0f968722/scratchpad/m1'); gg=gg.loc['2010-06-01':'2026-09-30']
c93=m93.simula(gg,480,900,1005,1.0,excluir=ex).r; c93.index=pd.DatetimeIndex(c93.index)
c99=m99.simula(gg,ex)/1e4
_,nk,_=m101.uno('NKD'); nk=nk/1e4
_,hg,_=m102.uno('HG'); hg=hg/1e4
_,pa,_=m102.uno('PA'); pa=pa/1e4
ng=pd.read_csv('/tmp/claude-0/-home-user-bot-trading/682335b1-28ae-5d18-9355-ce7f0f968722/scratchpad/ng_c95_diaria.csv',index_col=0,parse_dates=True).iloc[:,0]/1e4
W=0.2
def pn(r,c): r=r.loc['2018-03-26':]; return W*(0.005*(r-c)/r.std())
conf={'c93':(c93,0.74e-4),'c99':(c99,0.74e-4),'nkd':(nk,1.5e-4),'hg':(hg,2e-4)}
cand={'ng':(ng,4e-4),'pa':(pa,6e-4)}
A=fa-e1; B=fb-e1
def suma(base,d):
    q=base.copy()
    for k,(r,c) in d.items(): q=add(q,0*r,0) if False else q.add(pn(r,c).reindex(q.index).fillna(0),fill_value=0)
    return q
out={'A_conf':suma(A,conf),'A_cand':suma(A,{**conf,**cand}),'B_conf':suma(B,conf),'B_cand':suma(B,{**conf,**cand})}
out['A_base']=A; out['B_base']=B
for k,v in out.items(): print(k, round(sh(v),2))
pd.DataFrame(out).to_csv('/tmp/claude-0/-home-user-bot-trading/682335b1-28ae-5d18-9355-ce7f0f968722/scratchpad/carteras_v3.csv')
