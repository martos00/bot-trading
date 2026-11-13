"""Apex 150K EOD: aprobar el examen en 30 días (21 hábiles). Ventanas REALES de 2018-2026 (cada día de inicio posible, sin remuestreo),
para ver el efecto del riesgo, de las rupturas y de la fecha de inicio (ventanas que contienen el cambio de trimestre: Nikkei Q-2, yen Q0,
Nikkei Q+2, más el D-2 del mes). Reglas: objetivo 9.000 $, pérdida 4.000 $ EOD arrastrada (fija en +9.000 al llegar a +13.000), límite
diario 2.000 $ (recorta el día). Uso: python3 apex_examen_30dias.py DIR_SCRATCH"""
import sys, numpy as np, pandas as pd
exec(open('plan_reinversion_etf.py').read().split('CAP, OBJ')[0])
base = ['yen', 'cesta_yen', 'oro_vie_1655', 'oro_D-2', 'plata_visp_1655', 'plata_viernes', 'nikkei_Q+2', 'nikkei_Q-2', 'c113']
def examen(r):
    eq = hwm = 0.0
    for t, x in enumerate(r):
        x = max(x, -2000); eq += x; hwm = max(hwm, eq); piso = 9000 if hwm >= 13000 else hwm - 4000
        if eq <= piso: return 0, t + 1
        if eq >= 9000: return 1, t + 1
    return 0, len(r)
for nom, cols in (('sin rupturas', base), ('+ C93', base + ['oro_video_C93']), ('+ C93 + C99', base + ['oro_video_C93', 'oro_asia_C99'])):
    P = C[cols].sum(axis=1); pv = P.rolling(60, min_periods=40).std().shift(1); s = (P * (P.std() / pv).clip(0.5, 2)).dropna().loc['2018-11-05':]
    idx = s.index; q = ((idx.month % 3 == 0) & (idx.day >= 20)) | ((idx.month % 3 == 1) & (idx.day <= 5))   # días de cambio de trimestre
    for hair, et in ((0.6, 'PRUDENTE'), (1.0, 'BACKTEST')):
        for rk in (1.0, 1.25, 1.5, 2.0):
            x = ((s - s.mean() * (1 - hair)) * rk / 0.5 * 150000).values; res = []; trim = []
            for i in range(len(x) - 21):
                ok, t = examen(x[i:i + 21]); res.append(ok); trim.append(q[i:i + 21].any() and q[i:i + 21].sum() >= 5)
            res = np.array(res); trim = np.array(trim)
            print(f'{nom:13s} {et:8s} riesgo {rk:4.2f} | aprueba: empezando cualquier día {res.mean()*100:3.0f} % | si el mes incluye el cambio de trimestre {res[trim].mean()*100:3.0f} % | si no {res[~trim].mean()*100:3.0f} %', flush=True)
