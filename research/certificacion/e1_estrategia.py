"""E1 — estrategia sobre la ventaja certificada C1 (PREREGISTRO_E1_estrategia_eurusd.md): backtest y simulación de fondeo.
Uso: python3 e1_estrategia.py e1_franjas.csv"""
import os, sys
import numpy as np
import pandas as pd
from c1_certificacion import t_nw

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'fondeo'))
import simulador_fondeo as SF  # noqa: E402

COSTES = {'bajo 0,44 pb': 0.44, 'medio 0,53 pb': 0.53, 'alto 0,79 pb': 0.79}
OBJETIVOS = {'riesgo 0,5%': 0.005, 'riesgo 1,0%': 0.010}
FIRMAS = ['FTMO_2step', 'FundedNext_2step', 'FundingPips_2step']


def construir(x, objetivo, coste_pb):
    r = -np.log(x.mid8 / x.mid6)
    sd = r.rolling(60).std().shift(1)
    w = (objetivo / sd).clip(upper=10)
    adverso = x.ask_max / x.mid6 - 1
    stop = adverso >= 4 * sd
    bruto = np.where(stop, -(4 * sd + 0.5e-4), r)
    c = coste_pb / 1e4
    ret = w * (bruto - c)
    peor = w * (-np.minimum(adverso.fillna(0), 4 * sd + 0.5e-4) - c)
    d = pd.DataFrame({'ret': ret, 'peor': np.minimum(peor, ret), 'stop': stop, 'w': w}).dropna()
    return d


def resumen(d):
    eq = d.ret.cumsum()
    anual = d.ret.groupby(d.index.year).sum()
    return {'rent_anual%': round(d.ret.mean() * 252 * 100, 1), 'Sharpe': round(d.ret.mean() / d.ret.std() * np.sqrt(252), 2),
            't': round(t_nw(d.ret.values), 2), 'DD_max%': round((eq - eq.cummax()).min() * 100, 1),
            'peor_dia%': round(d.ret.min() * 100, 2), 'peor_intradia%': round(d.peor.min() * 100, 2),
            'años+': f'{(anual > 0).sum()}/{len(anual)}', 'stops': int(d.stop.sum()), 'expos_media': round(d.w.mean(), 1)}


if __name__ == '__main__':
    x = pd.read_csv(sys.argv[1], index_col=0, parse_dates=True)
    pd.set_option('display.width', 250); pd.set_option('display.max_columns', 30)
    filas, sims = [], []
    for nr, obj in OBJETIVOS.items():
        for nc, c in COSTES.items():
            d = construir(x, obj, c)
            filas.append({'riesgo': nr, 'coste': nc, 'dias': len(d), **resumen(d)})
            for fz in FIRMAS:
                o = SF.montecarlo(d.ret.values, d.peor.values, SF.REGLAS[fz], n_sim=5000)
                o0 = SF.montecarlo(d.ret.values - d.ret.mean(), d.peor.values - d.ret.mean(), SF.REGLAS[fz], n_sim=5000,
                                   incertidumbre_media=False)
                sims.append({'riesgo': nr, 'coste': nc, 'firma': fz, 'supera': round(o['supera'], 3),
                             'sin_ventaja': round(o0['supera'], 3), 'incumple_diaria': round(o['incumple_diaria'], 3),
                             'incumple_maxima': round(o['incumple_maxima'], 3), 'sin_resolver': round(o['sin_resolver'], 3),
                             'dias_mediana': o['dias_mediana_superar'],
                             'sobrevive_financiada_1año': round(o['p_sobrevive_financiada_dado_supera'], 3)})
    print('=== Backtest 2018-2026 (rentabilidades sobre el capital, sin capitalizar) ===')
    print(pd.DataFrame(filas).to_string(index=False))
    print('\n=== Simulación de fondeo (5.000 simulaciones; "sin_ventaja" = misma estrategia con media 0) ===')
    print(pd.DataFrame(sims).to_string(index=False))
