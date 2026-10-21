"""Ranking de firmas de fondeo para la estrategia E1 (EUR/USD corto 06→08 NY, riesgo 0,5%) con el coste y las reglas de cada una.
Coste por operación = comisión ida y vuelta por lote / nocional + spread medido (0,16 pb) + deslizamiento 0,1 pb.
Datos de las firmas: investigación del 21-oct-2026 (fuentes oficiales salvo donde se indica; ver RANKING_FIRMAS_EURUSD.md).
Uso: python3 ranking_firmas_eurusd.py ../certificacion/e1_franjas.csv"""
import os, sys
import numpy as np
import pandas as pd

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'certificacion'))
import simulador_fondeo as SF  # noqa: E402
import e1_estrategia as E  # noqa: E402

NOC = 114_000          # $ por lote EUR/USD
SPREAD, DESL = 0.16, 0.10

# nombre, comisión i/v por lote ($), Reglas del simulador, precio $100k, reparto, devolución (True si se devuelve), notas
R = SF.Reglas
FIRMAS = [
    ('FTMO 2-Step (2,50 $/lado = 5 $ i/v, oficial)', 5.0, SF.REGLAS['FTMO_2step'], 585, 0.80, True, 'EA permitido; el más permisivo'),
    ('FundingPips 2-Step (5 $/lote i/v [3])', 5.0, SF.REGLAS['FundingPips_2step'], 522, 0.80, False, 'EA propio con prueba; SIN VPS'),
    ('FundingPips 2-Step (5 $/lote por lado)', 10.0, SF.REGLAS['FundingPips_2step'], 522, 0.80, False, ''),
    ('The5ers High Stakes (4 $ i/v, oficial)', 4.0, R('The5ers HS', [0.08, 0.05], 0.04, 'saldo_dia', 0.08, 'estatica', dias_minimos=3), 455, 0.80, False, 'EA con código propio; FAQ contradictoria; tope 4.000 $/pago'),
    ('FXIFY 2-Phase Pro (RAW 6 $/lote, i/v supuesto)', 6.0, R('FXIFY Pro', [0.04, 0.08], 0.04, 'saldo_dia', 0.08, 'estatica', dias_minimos=3), 599, 0.80, False, 'EA con aprobación previa'),
    ('FXIFY Two Phase Standard (RAW 6 $/lote)', 6.0, R('FXIFY Std', [0.10, 0.05], 0.04, 'saldo_dia', 0.10, 'trailing_cierre', True), 549, 0.80, True, 'EA con aprobación; máx. trailing [3]'),
    ('Blue Guardian 2-Step (5 $/lote i/v)', 5.0, R('Blue Guardian', [0.08, 0.04], 0.04, 'inicial', 0.08, 'estatica', dias_minimos=3), 463, 0.85, True, 'EA propio; ¿5 $ por lado?'),
    ('Blue Guardian 2-Step (5 $/lote por lado)', 10.0, R('Blue Guardian', [0.08, 0.04], 0.04, 'inicial', 0.08, 'estatica', dias_minimos=3), 463, 0.85, True, ''),
    ('Funded Trading Plus 2-Step (7 $/lote i/v [3])', 7.0, R('FT+', [0.07, 0.07], 0.04, 'saldo_dia', 0.08, 'estatica', consistencia=0.35), 549, 0.80, False, 'límite 3% por símbolo'),
    ('Goat Funded Trader 2-Step (5 $/lote i/v)', 5.0, R('GFT', [0.10, 0.05], 0.05, 'saldo_dia', 0.10, 'estatica', dias_minimos=3), 628, 0.80, True, 'EA propio, sin VPS'),
    ('Audacity Ability (3 $/lote i/v [3])', 3.0, R('Audacity', [0.10, 0.05], 0.05, 'saldo_dia', 0.10, 'estatica', dias_minimos=4), 549, 0.75, True, 'Fase 1: 7,5%/15%; EA propio'),
    ('Topstep 50K, futuro 6E (4,22 $ + 1 tick)', None, SF.REGLAS['Topstep_50K'], 345, 0.90, False, 'futuros; sin VPS; precio aprox. (cuota mensual)'),
]


def coste_pb(com):
    if com is None:                                    # futuro 6E: 1 tick (6,25 $) + 4,22 $ por 125.000 EUR
        return (6.25 + 4.22) / (125_000 * NOC / 100_000) * 1e4 + DESL
    return com / NOC * 1e4 + SPREAD + DESL


if __name__ == '__main__':
    x = pd.read_csv(sys.argv[1], index_col=0, parse_dates=True)
    filas = []
    for nom, com, reg, precio, split, dev, nota in FIRMAS:
        c = coste_pb(com)
        d = E.construir(x, 0.005, c)
        o = SF.montecarlo(d.ret.values, d.peor.values, reg, n_sim=3000)
        anual = d.ret.mean() * 252
        # valor esperado del primer año: P(superar) × [beneficio anual × reparto × P(sobrevivir) + devolución] − precio
        capital = 50_000 if nom.startswith('Topstep') else 100_000
        ev = o['supera'] * (max(anual, 0) * capital * split * o['p_sobrevive_financiada_dado_supera'] + (precio if dev else 0)) - precio
        filas.append({'firma': nom, 'coste_pb': round(c, 2), 'neto_anual%': round(anual * 100, 1), 'supera': round(o['supera'], 2),
                      'dias_med': o['dias_mediana_superar'], 'sobrevive': round(o['p_sobrevive_financiada_dado_supera'], 2),
                      'precio$': precio, 'valor_esperado_1er_año$': round(ev), 'notas': nota})
    pd.set_option('display.width', 250); pd.set_option('display.max_columns', 20)
    print(pd.DataFrame(filas).sort_values('valor_esperado_1er_año$', ascending=False).to_string(index=False))
