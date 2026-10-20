"""Selecciona candidatas de los informes del optimizador de MT5 por ROBUSTEZ (meseta de vecinas), no por el máximo.
Regla (fijada antes de cualquier validación): en cada informe, combinaciones con >= 60 operaciones y >= 4 vecinas
evaluadas (vecina = misma combinación salvo un parámetro movido un paso de su rejilla); se ordena por la
MEDIANA del profit factor de las vecinas y se toma la primera. El riesgo no cuenta como parámetro de señal.
Uso: python3 seleccionar_candidatas.py OPT.CSV"""
import sys
import numpy as np
import pandas as pd

P = ['InpMaxSweepDistanceATRMult', 'InpImportanciaMinimaZona', 'InpSetupMaxBarras', 'InpFVGMinSizeATRMult',
     'InpFVGEntryPercent', 'InpSLBufferATRMult', 'InpModoTP', 'InpMinimumRR']
CORTOS = {'SIN_FILTRO_REGIMEN_H4': 'A_sinH4(riesgo optimizado)', 'SIN_REGIMEN_H4_SOLAMENTE': 'F_sinH4',
          'SIN_REGIMEN_H4_Y_SIN_SOLO_BUSCAR_SEEPS_NUEVOS_EN_LA_FRANJA_DE_MAYOR_LIQUIDEZ': 'B_sinH4_sinSesion',
          'SIN_REGIMEN_H4_Y_SIN_IGNORAR_FVG_PEQUE_OS_RESPECTO_AL_ATR': 'E_sinH4_sinFVGmin',
          'SIN_NADA': 'D_sinNingunFiltro', 'COMPLETO': 'C_todosLosFiltros(riesgo optimizado)'}

d = pd.read_csv(sys.argv[1])
d['inf'] = d.informe.map(CORTOS)
rej = {c: np.array(sorted(d[c].unique())) for c in P}
filas = []
for inf, g in d.groupby('inf'):
    g = g.sort_values('Profit Factor', ascending=False).drop_duplicates(P)   # una fila por señal (mejor riesgo si se optimizó)
    idx = {tuple(r): pf for r, pf in zip(g[P].itertuples(index=False), g['Profit Factor'])}
    for _, r in g[g.Trades >= 60].iterrows():
        vec = []
        for i, c in enumerate(P):
            pos = np.searchsorted(rej[c], r[c])
            for p2 in (pos - 1, pos + 1):
                if 0 <= p2 < len(rej[c]):
                    k = list(r[P]); k[i] = rej[c][p2]
                    if tuple(k) in idx:
                        vec.append(idx[tuple(k)])
        if len(vec) >= 4:
            filas.append({'informe': inf, 'pass': int(r.Pass), 'PF': r['Profit Factor'], 'ops': int(r.Trades),
                          'DD%': r['Equity DD %'], 'beneficio': r.Profit, 'riesgo%': r.InpRiskPercent,
                          'n_vecinas': len(vec), 'PF_vecinas_mediana': np.median(vec), 'PF_vecinas_min': min(vec),
                          **{c.replace('Inp', ''): r[c] for c in P}})
f = pd.DataFrame(filas).sort_values('PF_vecinas_mediana', ascending=False)
sel = f.groupby('informe').head(1)
pd.set_option('display.width', 300); pd.set_option('display.max_columns', 40)
print(sel.round(2).to_string(index=False))
sel.to_csv('candidatas_seleccionadas.csv', index=False)
