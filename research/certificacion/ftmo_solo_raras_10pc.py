# FTMO: solo E10 (plata víspera), E13 y E16 (Nikkei) a riesgo alto; P(+10 % en 4 meses antes de -10 %). Modelo de dos puntos por operación (aproximado, infravalora las pérdidas grandes). Informativo.
import numpy as np
rng=np.random.default_rng(3)
# (operaciones/año, % aciertos, ratio, R medio) ; dos puntos ajustados a la media
OPS={'E10':(8,.59,2.35,.38),'E13':(4,.55,1.8,.39),'E16':(4,.72,.58,.13)}
def pts(p,ratio,m): L=m/(p*ratio-(1-p)); return p, ratio*L, L
for hair,coste,et in ((0.6,0.0,'PRUDENTE sin coste plata'),(0.6,0.15,'PRUDENTE con coste plata CFD')):
  for R in (1,2,3,4,5,6,8):
    ok=lost=0; N=20000
    for _ in range(N):
      tr=[]
      for k,(n,p,ra,m) in OPS.items():
        pp,W,L=pts(p,ra,m)
        c=coste if k=='E10' else 0
        for _ in range(rng.poisson(n/3)):
          x=(W if rng.random()<pp else -L)
          x=x-(1-hair)*m  # prudente: 60 % del beneficio medio
          tr.append(x-c)
      rng.shuffle(tr); eq=0
      for x in tr:
        eq+=x*R/100
        if eq<=-0.10: lost+=1; break
        if eq>=0.10: ok+=1; break
    print(f'{et:30s} riesgo {R}%/op: +10 % en 4 meses {ok/N:5.1%} | pierde la cuenta {lost/N:5.1%}')
