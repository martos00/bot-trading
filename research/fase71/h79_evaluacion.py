"""H79 — evaluación según el pre-registro. Uso: python3 h79_evaluacion.py DIR_HISTDATA_NSX DIR_SALIDA"""
import os, sys
import numpy as np
import pandas as pd
import h79_motor as M

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'fondeo'))
import simulador_fondeo as SF  # noqa: E402

HUECO = (pd.Timestamp('2017-02-16'), pd.Timestamp('2017-02-28'))   # hueco de la auditoría ± 1 día


def t_nw(x, L=5):
    x = np.asarray(x, float); n = len(x); e = x - x.mean()
    g = [e[k:] @ e[:n - k] / n for k in range(L + 1)]
    return x.mean() / np.sqrt((g[0] + 2 * sum((1 - k / (L + 1)) * g[k] for k in range(1, L + 1))) / n)


def resumen(df, nombre):
    x = df[df.lado != 0]
    gan, per = x.pnl[x.pnl > 0].sum(), -x.pnl[x.pnl < 0].sum()
    eq = M.CUENTA + df.pnl.cumsum()
    print(f'{nombre:<26} ops={len(x):5d} pnl={df.pnl.sum():>10,.0f} $  media/día={df.pnl.mean():7.1f} $  t_NW={t_nw(df.pnl):6.2f}  '
          f'PF={gan / per:5.2f}  aciertos={(x.pnl > 0).mean() * 100:4.1f}%  DDmax={(eq - eq.cummax()).min():>9,.0f} $  '
          f'contratos med={x.contratos.median():.0f}')


if __name__ == '__main__':
    hd, out = sys.argv[1:3]
    m1, _ = M.cargar(hd)
    m1 = m1[(m1.dia < HUECO[0]) | (m1.dia > HUECO[1])]
    res = {}
    for nom, desl, com in (('bruto (sin costes)', 0.0, 0.0), ('neto base 1 tick + 1,50 $', 0.25, 1.50), ('neto estrés 2 ticks + 2,50 $', 0.50, 2.50)):
        res[nom] = M.simular(m1, desl, com)
        resumen(res[nom], nom)
    b = res['neto base 1 tick + 1,50 $']
    b.to_csv(os.path.join(out, 'h79_neto_base.csv'))
    print('\nneto base por año ($):', b.pnl.groupby(b.index.year).sum().round(0).astype(int).to_dict())
    print('años positivos:', (b.pnl.groupby(b.index.year).sum() > 0).sum(), 'de', b.index.year.nunique())
    for nom, sl in (('2010-2015', slice('2010', '2015')), ('2016-2020', slice('2016', '2020')), ('2021-2026', slice('2021', '2026'))):
        resumen(b.loc[sl], f'neto base {nom}')
    x = b[b.lado != 0]
    print(f'\nPuntos netos medios por operación =  {x.pts.mean():.2f}; largos {x[x.lado == 1].pts.mean():.2f}, cortos {x[x.lado == -1].pts.mean():.2f}')
    # control de dirección aleatoria: P&L de cada día con lado +1 y con lado −1 (determinista), mezcla aleatoria
    pl = {}
    for s in (1, -1):
        filas = []
        validos = M.dias_validos(m1.dia.min(), m1.dia.max())
        for dia, g in m1.groupby('dia'):
            if dia not in validos or len(g) < 370:
                continue
            g = g.set_index('k').reindex(range(M.K_CIERRE + 1))
            if g.loc[0:M.K_RANGO, ['h', 'l']].isna().any().any():
                continue
            o_ult = g.at[M.K_CIERRE, 'o']; g = g.ffill()
            o, h, l, c = (g[k].to_numpy() for k in 'ohlc'); o = o.copy(); o[M.K_CIERRE] = o_ult
            r = M.operar(o, h, l, c, 0.25, 1.50, s)
            filas.append((dia, r[3] if r else 0.0))
        pl[s] = pd.Series(dict(filas))
    P = np.vstack([pl[1].reindex(b.index).values, pl[-1].reindex(b.index).values])
    rng = np.random.default_rng(79)
    sims = np.array([P[rng.integers(0, 2, P.shape[1]), np.arange(P.shape[1])].mean() for _ in range(1000)])
    print(f'\nControl dirección aleatoria (neto base): media/día regla {b.pnl.mean():.1f} $; simulada {sims.mean():.1f} $ '
          f'(p95 {np.percentile(sims, 95):.1f}); p(sim >= regla) = {(sims >= b.pnl.mean()).mean():.3f}')
    print(f'Siempre largo tras la ruptura: {pl[1].mean():.1f} $/día; siempre corto: {pl[-1].mean():.1f} $/día')
    # fondeo (neto base, toda la historia, con incertidumbre de la media)
    print('\nFondeo (Monte Carlo, bloques de 5 días, incertidumbre de la ventaja):')
    r_, m_ = b.ret.values, b.min_intradia.values
    for k in ('Topstep_50K', 'FTMO_2step'):
        o = SF.montecarlo(r_, m_, SF.REGLAS[k], n_sim=5000)
        o0 = SF.montecarlo(r_ - r_.mean(), m_ - r_.mean(), SF.REGLAS[k], n_sim=5000, incertidumbre_media=False)
        print(f'  {k}: supera {o["supera"]:.3f}  (con ventaja 0: {o0["supera"]:.3f})  incumple diaria {o["incumple_diaria"]:.3f}  '
              f'incumple máxima {o["incumple_maxima"]:.3f}  días mediana {o["dias_mediana_superar"]}  '
              f'sobrevive financiada {o["p_sobrevive_financiada_dado_supera"]:.3f}')
    print(f'\nP&L diario (neto base): vol {b.ret.std() * 100:.2f}% del capital; percentil 1 {np.percentile(b.ret, 1) * 100:.2f}%; '
          f'peor día {b.ret.min() * 100:.2f}%; peor flotante {b.min_intradia.min() * 100:.2f}%; '
          f'racha perdedora máx {max(len(s) for s in "".join("p" if v < 0 else "g" for v in x.pnl).split("g"))} ops')
