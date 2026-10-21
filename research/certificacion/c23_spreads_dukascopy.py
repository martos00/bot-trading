"""Verificación del artefacto del BID de C20/C22/C23: spread real (Dukascopy BID/ASK) de USDPLN y USDHUF a las 07:00 Londres,
08:00 NY y 16:00 NY. Artefacto esperado en una rentabilidad medida con BID = (spread_inicio − spread_fin)/2.
Uso: python3 c23_spreads_dukascopy.py DIR_MUESTRA"""
import glob, os, sys
from datetime import datetime
from zoneinfo import ZoneInfo
import numpy as np, pandas as pd
from c1_certificacion import velas, en
LON, NY = ZoneInfo('Europe/London'), ZoneInfo('America/New_York')
d = sys.argv[1]
for sim in ('USDPLN', 'USDHUF'):
    filas = []
    for fb in sorted(glob.glob(os.path.join(d, sim, f'{sim}_BID_*.bi5'))):
        fa = fb.replace('_BID_', '_ASK_')
        if not os.path.exists(fa): continue
        b, a = velas(fb), velas(fa)
        dia = datetime.strptime(fb[-14:-4], '%Y-%m-%d')
        fila = {'dia': dia.date()}
        for nom, T in (('07L', datetime(dia.year, dia.month, dia.day, 7, tzinfo=LON)), ('08NY', datetime(dia.year, dia.month, dia.day, 8, tzinfo=NY)),
                       ('16NY', datetime(dia.year, dia.month, dia.day, 16, tzinfo=NY))):
            pb, pa = en(b, T), en(a, T)
            fila[nom] = (pa - pb) / ((pa + pb) / 2) * 1e4
        filas.append(fila)
    t = pd.DataFrame(filas).set_index('dia')
    print(f'\n== {sim}: {len(t)} días ==')
    print(t.round(2).to_string())
    print(f'medias (pb): 07:00 Londres {t["07L"].mean():.2f} | 08:00 NY {t["08NY"].mean():.2f} | 16:00 NY {t["16NY"].mean():.2f}')
    print(f'artefacto esperado mañana (07L→08NY) = {(t["07L"]-t["08NY"]).mean()/2:.2f} pb a favor de USD/xxx ; '
          f'tarde (08NY→16NY) = {-(t["08NY"]-t["16NY"]).mean()/2:.2f} pb (negativo = a favor de la "vuelta")')
