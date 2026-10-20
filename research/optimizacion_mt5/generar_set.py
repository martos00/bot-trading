"""Genera archivos .set (UTF-16, formato del Probador de MT5) para validar las candidatas con riesgo uniforme del 0,5%.
Los parámetros de señal salen tal cual de las pasadas de los informes; el resto, de los valores por defecto del EA del repo.
Uso: python3 generar_set.py OPT.CSV [riesgo prefijo]
Con riesgo 1.5 y prefijo REPRO genera los archivos de reproducción de 2025-2026."""
import re, sys
import pandas as pd

EA = '../../MQL5/Experts/XAUUSD_SupplyDemand_RSI_EA.mq5'
P = ['InpMaxSweepDistanceATRMult', 'InpImportanciaMinimaZona', 'InpSetupMaxBarras', 'InpFVGMinSizeATRMult',
     'InpFVGEntryPercent', 'InpSLBufferATRMult', 'InpModoTP', 'InpMinimumRR']
ENTEROS = {'InpImportanciaMinimaZona', 'InpSetupMaxBarras', 'InpModoTP'}
H4, SES, FVG = 'InpUsarFiltroRegimen', 'InpUsarFiltroSesion', 'InpUsarFiltroFVGMinimo'
CAND = [  # nombre, informe, pasada, filtros desactivados (verificados por el nombre del informe; FVG también con los datos)
    ('CAND1', 'SIN_REGIMEN_H4_SOLAMENTE', 1400, [H4]),
    ('CAND2', 'SIN_REGIMEN_H4_Y_SIN_SOLO_BUSCAR_SEEPS_NUEVOS_EN_LA_FRANJA_DE_MAYOR_LIQUIDEZ', 2815, [H4, SES]),
    ('CAND3', 'SIN_REGIMEN_H4_Y_SIN_IGNORAR_FVG_PEQUE_OS_RESPECTO_AL_ATR', 1374, [H4, FVG]),
    ('CAND4', 'SIN_NADA', 1310, [H4, SES, FVG]),
    ('CAND5', 'SIN_REGIMEN_H4_Y_SIN_SOLO_BUSCAR_SEEPS_NUEVOS_EN_LA_FRANJA_DE_MAYOR_LIQUIDEZ', 2709, [H4, SES]),
    ('CAND6', 'SIN_NADA', 1381, [H4, SES, FVG]),
]
src = open(EA, encoding='utf-8', errors='ignore').read()
MAPA = {'PERIOD_M15': '15', 'PERIOD_H4': '16388', 'PERIOD_H1': '16385', 'MODO_TP_FIJO_RR': '0', 'MODO_TP_SIGUIENTE_LIQUIDEZ': '1'}
defecto = [(n, MAPA.get(v.strip(), v.strip().strip('"').lower() if t == 'bool' else v.strip().strip('"')))
           for t, n, v in re.findall(r'^input\s+(\w+)\s+(\w+)\s*=\s*([^;]+);', src, re.M)]
d = pd.read_csv(sys.argv[1])
RIESGO = sys.argv[2] if len(sys.argv) > 2 else '0.5'
PREFIJO = sys.argv[3] if len(sys.argv) > 3 else ''
for nom, inf, ps, off in CAND:
    r = d[(d.informe == inf) & (d.Pass == ps)].iloc[0]
    over = {f: 'false' for f in off}
    over |= {c: (str(int(r[c])) if c in ENTEROS else f'{r[c]:g}') for c in P}
    over['InpRiskPercent'] = RIESGO                     # 0,5 en la validación; 1,5 (supuesto) en la reproducción
    over['InpFixedRR'] = '2'                            # PROVISIONAL: acotado a [2,00; 2,25) por los informes; confirmar en MT5
    cab = [f'; {nom}: informe {inf}, pasada {ps}. riesgo {RIESGO}%.',
           '; InpFixedRR=2 es PROVISIONAL (los informes solo lo acotan entre 2,00 y 2,25); solo afecta si InpModoTP=0.']
    fn = f'{PREFIJO + "_" if PREFIJO else ""}{nom}_{inf[:20]}_p{ps}.set'
    open(fn, 'w', encoding='utf-16').write('\r\n'.join(cab + [f'{n}={over.get(n, v)}' for n, v in defecto]) + '\r\n')
    print(fn, {k: over[k] for k in P + off + ['InpRiskPercent']})
