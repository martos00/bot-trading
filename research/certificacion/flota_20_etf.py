"""20 cuentas ETF 150K ya montadas (todas empiezan como fondeadas recién activadas), 24 meses, mismas operaciones en todas.
Compara cobrar lo que haya frente a cobrar solo 2.250 $ completos. Uso: python3 flota_20_etf.py DIR_SCRATCH"""
import sys, numpy as np, pandas as pd
exec(open('plan_reinversion_etf.py').read().split('rng = np.random')[0])
rng = np.random.default_rng(17); N = 20
def flota(x, solo_max):
    st = rng.integers(0, len(x) - B, T // B + 1); R = x[(st[:, None] + np.arange(B)).ravel()[:T]]
    A = [dict(f='fond', eq=0.0, hwm=0.0, ini=0, tc=0) for _ in range(N)]; mes = np.zeros(T // 21 + 1); coste = np.zeros_like(mes); perd = 0
    for t in range(T):
        m = t // 21
        for a in A:
            a['eq'] += R[t]; a['hwm'] = min(max(a['hwm'], a['eq']), DD)
            if a['f'] == 'eval' and t - a['tc'] >= 21: coste[m] += CUOTA; a['tc'] = t
            if a['eq'] <= a['hwm'] - DD:
                perd += a['f'] == 'fond'; coste[m] += RESET if a['f'] == 'eval' else CUOTA; a.update(f='eval', eq=0.0, hwm=0.0, tc=t); continue
            if a['f'] == 'eval' and a['eq'] >= OBJ: coste[m] += ACT; a.update(f='fond', eq=0.0, hwm=0.0, ini=t); continue
            if a['f'] == 'fond' and (t - a['ini']) % 10 == 0 and a['eq'] > DD and (not solo_max or (a['eq'] - DD) * CAP >= TOPE):
                q = min((a['eq'] - DD) * CAP, TOPE); a['eq'] -= q / CAP; mes[m] += 0.9 * q
    neto = (mes * 0.7 - coste)[:24]   # 30 % de cada cobro apartado para impuestos
    return neto, perd, np.mean([a['f'] == 'fond' for a in A])
for hair, et in ((1.0, 'BACKTEST'), (0.6, 'REAL AL 60 %')):
    x = SER - SER.mean() * (1 - hair); print(f'\n######## {et} — 20 cuentas ETF 150K, riesgo 0,65 %, dinero ya descontado el 30 % de impuestos y los costes')
    for sm in (False, True):
        res = [flota(x, sm) for _ in range(1000)]; M = np.array([r[0] for r in res]); tot = M.sum(axis=1)
        print(f'{"Cobra lo que haya (hasta 2.250 $)" if sm is False else "Solo cobra 2.250 $ completos":34s} | al mes: media {M.mean():,.0f} $ / mediana {np.median(M):,.0f} $ | meses con menos de 0 $ {(M<0).mean()*100:.0f} % | '
              f'meses > 20.000 $ {(M>20000).mean()*100:.0f} % | 24 m: media {tot.mean():,.0f} $ (10 % peor {np.percentile(tot,10):,.0f}) | fondeadas perdidas al año {np.mean([r[1] for r in res])/2:.1f} de 20 | '
              f'peor racha de 6 meses {np.percentile([min(np.convolve(m, np.ones(6), "valid")) for m in M], 50):,.0f} $ (mediana)')
