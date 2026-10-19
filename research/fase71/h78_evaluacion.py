"""H78 — evaluación según el pre-registro. Uso: python3 h78_evaluacion.py H78_1H.CSV [H78_1M.CSV]"""
import sys
import numpy as np
import pandas as pd

BASE, ESTRES = 0.00065 + 0.0002, 0.00065 + 0.0010
REPL, OOS = slice('2017-08-17', '2022-02-03'), slice('2022-02-04', '2026-09-30')


def t_nw(x, L=5):
    x = np.asarray(x) - np.mean(x); n = len(x)
    g = [x[k:] @ x[:n - k] / n for k in range(L + 1)]
    return (np.sqrt(g[0] + 2 * sum((1 - k / (L + 1)) * g[k] for k in range(1, L + 1))) / np.sqrt(n))


def resumen(r, nombre):
    r = r.dropna()
    se = t_nw(r.values)
    eq = (1 + r).cumprod()
    print(f'{nombre:<22} n={len(r):5d} media={r.mean()*1e4:7.2f} pb  t_NW={r.mean()/se:6.2f}  '
          f'anual(compuesto)={(eq.iloc[-1]**(365/len(r))-1)*100:7.1f}%  DDmax={(eq/eq.cummax()-1).min()*100:6.1f}%  aciertos={(r>0).mean()*100:.1f}%')


if __name__ == '__main__':
    d = pd.read_csv(sys.argv[1], index_col=0, parse_dates=True)
    d.index = d.index.tz_localize(None) if d.index.tz is not None else d.index
    horas = [c for c in d.columns if c.startswith('h')]
    print('Días sin dato excluidos (de calendario):', len(pd.date_range(d.index.min(), d.index.max())) - len(d))
    for nom, sl in (('RÉPLICA', REPL), ('OOS', OOS)):
        x = d.loc[sl]
        print(f'\n== {nom} {x.index.min().date()} → {x.index.max().date()}')
        resumen(x.regla, 'bruto')
        resumen(x.regla - BASE, 'neto base (8,5 pb)')
        resumen(x.regla - ESTRES, 'neto estrés (16,5 pb)')
        print(f'coste de equilibrio = {x.regla.mean()*1e4:.2f} pb ida y vuelta (puerta: ≥ {3*BASE*1e4:.1f} pb)')
        print('media bruta por año (pb):', (x.regla.groupby(x.index.year).mean() * 1e4).round(2).to_dict())
        print('neta base por año (pb):', ((x.regla - BASE).groupby(x.index.year).mean() * 1e4).round(2).to_dict())
        print('media por hora de inicio (pb):', (x[horas].mean() * 1e4).round(1).to_dict())
        # control: hora de inicio aleatoria por día, mismos días
        rng = np.random.default_rng(78)
        M = x[horas].to_numpy()
        ok = ~np.isnan(M)
        sims = np.empty(10_000)
        for i in range(10_000):
            h = rng.integers(0, 24, len(M))
            v = M[np.arange(len(M)), h]
            sims[i] = np.nanmean(v)
        print(f'control hora aleatoria: p(sim >= regla) = {(sims >= x.regla.mean()).mean():.4f}  (media sim {sims.mean()*1e4:.2f} pb)')
        print('fin de semana vs laborable (bruto pb):',
              (x.regla.groupby(x.index.weekday >= 5).mean() * 1e4).round(2).rename({False: 'L-V', True: 'S-D'}).to_dict())
    if len(sys.argv) > 2:
        m = pd.read_csv(sys.argv[2], index_col=0, parse_dates=True)['regla_1m']
        m.index = m.index.tz_localize(None) if m.index.tz is not None else m.index
        c = pd.concat([d.loc[OOS, 'regla'], m], axis=1, join='inner').dropna()
        print(f'\nMotor independiente (1 min) en OOS: n={len(c)}  máx|dif|={np.abs(c.regla-c.regla_1m).max():.2e}  '
              f'media 1h {c.regla.mean()*1e4:.3f} pb vs 1m {c.regla_1m.mean()*1e4:.3f} pb')
