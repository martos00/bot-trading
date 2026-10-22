"""C65: oro del viernes y plata de víspera según régimen de VIX. Ver PREREGISTRO_C65."""
import glob, os, io, contextlib, sys
import numpy as np, pandas as pd
from scipy import stats
from c1_certificacion import t_nw
S = '/tmp/claude-0/-home-user-bot-trading/682335b1-28ae-5d18-9355-ce7f0f968722/scratchpad/'
v = pd.read_csv(S + 'n/VIX_History.csv'); v.columns = [c.strip().upper() for c in v.columns]
vix = pd.Series(v.CLOSE.values, index=pd.to_datetime(v.DATE)).sort_index()
alto = (vix > vix.rolling(252).median()).shift(1)                       # régimen conocido al cierre del día anterior
F = {}
for f in sorted(glob.glob(S + 'gc_vie/*.csv')):
    x = pd.read_csv(f)
    if len(x) < 30 or x.instrument_id.nunique() > 1: continue
    x.index = pd.to_datetime(x.ts_event, utc=True).dt.tz_convert('America/New_York'); mm = x.index.hour * 60 + x.index.minute
    a = x.close[(mm < 960) & (mm >= 950)]; b = x.close[(mm < 1015) & (mm >= 1005)]
    if len(a) and len(b): F[pd.Timestamp(os.path.basename(f)[:10])] = np.log(b.iloc[-1] / a.iloc[-1])
oro = pd.Series(F)
sys.argv = ['x', S + 'databento/h1']
with contextlib.redirect_stdout(io.StringIO()):
    exec(open('c50_metales_duracion_cierre.py').read().split("for s in ('GC', 'SI'):")[0])
plata = R.SI[cat == 3]
for nom, r, principal in (('Oro viernes 16:00-16:55', oro, True), ('Plata víspera 16-17 (inf.)', plata, False)):
    reg = alto.reindex(r.index); hi, lo = r[reg == True], r[reg == False]
    t = stats.ttest_ind(hi, lo, equal_var=False)
    print(f'{nom}: VIX alto n {len(hi)} {hi.mean()*1e4:.2f} pb (media/desv {hi.mean()/hi.std():.3f}) | VIX bajo n {len(lo)} {lo.mean()*1e4:.2f} pb (media/desv {lo.mean()/lo.std():.3f}) '
          f'| diferencia {(hi.mean()-lo.mean())*1e4:.2f} pb (t Welch {t.statistic:.2f})' + (f' → {"PASA" if t.statistic >= 1.65 else "NO PASA"}' if principal else ''))
