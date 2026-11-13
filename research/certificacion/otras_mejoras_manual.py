"""Otras ideas de la tabla (operación manual): (1) no operar en días anómalos: festivos de EE. UU. entre semana y sesiones con cierre
anticipado (víspera de Navidad/Año Nuevo, día después de Acción de Gracias, 3-jul) — efecto en las estrategias que caen en esos días;
(2) no abrir el yen E9 (USDJPY largo 07-08 NY, antepenúltimo laborable) si el spread de FXCM a la entrada es > 2× su mediana de 60
días. Informativo (no cambia reglas sin preregistro). Uso: python3 otras_mejoras_manual.py DIR_SCRATCH"""
import sys, glob, numpy as np, pandas as pd, holidays
from datetime import datetime
from zoneinfo import ZoneInfo
sys.path.insert(0, '.')
from c1_certificacion import fxcm, en, t_nw
SP = sys.argv[1]; NY = ZoneInfo('America/New_York')
C = pd.read_csv(f'{SP}/componentes_B.csv', index_col=0, parse_dates=True).loc['2018-03-26':]
fest = holidays.financial_holidays('NYSE', years=range(2018, 2027))
anom = set(pd.Timestamp(d) for d in fest)
for y in range(2018, 2027):
    for d in (pd.Timestamp(y, 12, 24), pd.Timestamp(y, 12, 31), pd.Timestamp(y, 7, 3)):
        if d.weekday() < 5: anom.add(d)
    tg = [pd.Timestamp(d) for d, n in holidays.US(years=y).items() if 'Thanksgiving' in n][0]; anom.add(tg + pd.Timedelta(days=1))
cols = ['yen', 'cesta_yen', 'oro_vie_1655', 'oro_D-2', 'plata_visp_1655', 'plata_viernes', 'nikkei_Q+2', 'nikkei_Q-2']
print('(1) Días anómalos (festivo o cierre anticipado en EE. UU.)')
for c in cols:
    s = C[c]; s = s[s != 0]; a = s[s.index.isin(anom)]; n = s[~s.index.isin(anom)]
    if len(a): print(f'   {c:16s}: operaciones en días anómalos {len(a):3d} de {len(s):4d} | media en anómalos {a.mean()*1e4/50:+.2f} R·100 frente a normal {n.mean()*1e4/50:+.2f}')
tot = C[cols].sum(axis=1); aa = tot[tot.index.isin(anom) & (tot != 0)]
print(f'   cartera: {len(aa)} días anómalos con operación, suman {aa.sum()/tot.sum()*100:+.1f} % del beneficio total')
# (2) spread del yen E9
b, a = {}, {}
for f in sorted(glob.glob(f'{SP}/fxcm/USDJPY/USDJPY_*.csv.gz')):
    bb, aa_ = fxcm(f); b.update(bb); a.update(aa_)
rows = []
for d in pd.bdate_range('2012-01-02', '2026-09-30'):
    t0 = datetime(d.year, d.month, d.day, 7, tzinfo=NY); t1 = datetime(d.year, d.month, d.day, 8, tzinfo=NY)
    v = [en(b, t0), en(a, t0), en(b, t1), en(a, t1)]
    if not np.isnan(v).any(): rows.append((d, (v[1] - v[0]) / ((v[0] + v[1]) / 2) * 1e4, np.log((v[2] + v[3]) / (v[0] + v[1])) * 1e4, (v[2] - v[3] + 0) / 1, v))
df = pd.DataFrame([(r[0], r[1], r[2]) for r in rows], columns=['dia', 'spread', 'mid']).set_index('dia')
df['med'] = df.spread.rolling(60, min_periods=20).median().shift(1)
dias = df.index; s_ = pd.Series(range(len(dias)), index=dias); fin = s_.groupby(s_.index.to_period('M')).cumcount(ascending=False) + 1
e9 = df[(fin.values == 3)].copy()
e9['neto'] = e9.mid - e9.spread       # largo: compra al ask, vende al bid (aprox. spread de entrada + salida ≈ 2 × medio)
ancho = e9.spread > 2 * e9.med
print(f'\n(2) Yen E9 (FXCM 2012-2026, {len(e9)} operaciones): spread mediano a la entrada {e9.spread.median():.2f} pb')
print(f'   días con spread > 2× su mediana: {ancho.sum()} | neto medio esos días {e9.neto[ancho].mean():+.2f} pb frente a {e9.neto[~ancho].mean():+.2f} pb el resto')
print(f'   saltándolos: neto total {e9.neto[~ancho].sum():+.0f} pb frente a {e9.neto.sum():+.0f} pb operando todos; t {t_nw(e9.neto[~ancho].values):.2f} frente a {t_nw(e9.neto.values):.2f}')
