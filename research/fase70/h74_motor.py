"""H74 — Noise Area intraday momentum (Zarattini, Aziz & Barbon 2024). Motor PRINCIPAL.
Reglas congeladas en PREREGISTRO_H74_zab_noise_area.md.

Uso: python3 h74_motor.py SPY_1MIN_CSV SALIDA_DIR [comision_por_accion deslizamiento_por_accion]
Entrada: CSV de Interactive Brokers (date en Mountain Time, open, high, low, close, volume, barCount, average).
Salidas: h74_diario.csv (P&L diario, mínimo intradía de equity, exposición) y h74_operaciones.csv.
"""
import os, sys
import numpy as np
import pandas as pd

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..'))
import calidad_datos  # noqa: E402

N_DIAS_SIGMA = 14
VOL_OBJETIVO = 0.02
APALANCAMIENTO_MAX = 4.0
MINUTOS = 390
CAPITAL_INICIAL = 100_000.0
# índices de las velas cuyo CIERRE marca las 10:00, 10:30, ..., 15:30 (vela k empieza a las 9:30 + k min)
DECISIONES = [m - 1 for m in range(30, 361, 30)]


def cargar(fichero):
    d = pd.read_csv(fichero, parse_dates=['date']).drop_duplicates('date').sort_values('date')
    d['t'] = d['date'] + pd.Timedelta(hours=2)      # Mountain -> Eastern (mismas reglas de horario de verano)
    hm = d['t'].dt.hour * 100 + d['t'].dt.minute
    d = d[(hm >= 930) & (hm < 1600)].copy()
    d['dia'] = d['t'].dt.normalize()
    d['k'] = (d['t'].dt.hour - 9) * 60 + d['t'].dt.minute - 30
    return d


def construir_matrices(d):
    dias = []
    O, H, L, C, V, A = [], [], [], [], [], []
    for dia, g in d.groupby('dia'):
        if len(g) < 380:
            continue
        idx = g['k'].to_numpy()
        fila = {}
        for col, lst in (('open', O), ('high', H), ('low', L), ('close', C), ('volume', V), ('average', A)):
            x = np.full(MINUTOS, np.nan)
            x[idx] = g[col].to_numpy()
            lst.append(x)
        dias.append(dia)
    M = {k: np.vstack(v) for k, v in zip('OHLCVA', (O, H, L, C, V, A))}
    # minutos ausentes (< 10 por día): se propaga el último precio; volumen 0 (no se inventa actividad)
    for k in 'OHLCA':
        M[k] = pd.DataFrame(M[k]).T.ffill().bfill().T.to_numpy()
    M['V'] = np.nan_to_num(M['V'])
    return pd.DatetimeIndex(dias), M


def simular(dias, M, comision=0.0035, desliz=0.001):
    O, H, L, C, V, A = (M[k] for k in 'OHLCVA')
    n = len(dias)
    apertura = O[:, 0]
    cierre = C[:, -1]
    move = np.abs(C / apertura[:, None] - 1)                    # n x 390
    ret_diario = np.r_[np.nan, cierre[1:] / cierre[:-1] - 1]
    vwap = np.cumsum(A * V, axis=1) / np.maximum(np.cumsum(V, axis=1), 1e-12)
    aum = CAPITAL_INICIAL
    filas, ops = [], []
    for t in range(N_DIAS_SIGMA + 1, n):
        sigma = move[t - N_DIAS_SIGMA:t].mean(axis=0)
        ref_up = max(apertura[t], cierre[t - 1])
        ref_dn = min(apertura[t], cierre[t - 1])
        ub, lb = ref_up * (1 + sigma), ref_dn * (1 - sigma)
        vol14 = np.std(ret_diario[t - N_DIAS_SIGMA:t], ddof=1)
        acciones = np.floor(aum * min(APALANCAMIENTO_MAX, VOL_OBJETIVO / vol14) / apertura[t])
        pos, entrada, pnl_dia, coste_dia = 0, 0.0, 0.0, 0.0
        min_eq = 0.0
        k_entrada = None
        for k in DECISIONES:
            p = C[t, k]
            nueva = pos
            if pos == 1 and p < max(ub[k], vwap[t, k]):
                nueva = -1 if p < lb[k] else 0
            elif pos == -1 and p > min(lb[k], vwap[t, k]):
                nueva = 1 if p > ub[k] else 0
            elif pos == 0:
                nueva = 1 if p > ub[k] else (-1 if p < lb[k] else 0)
            # flotante mínimo hasta este instante (con lows/highs de las velas)
            if pos != 0:
                tramo = L[t, k_entrada:k + 1] if pos == 1 else H[t, k_entrada:k + 1]
                peor = pnl_dia + pos * acciones * (tramo.min() - entrada if pos == 1 else tramo.max() - entrada) - coste_dia
                min_eq = min(min_eq, peor)
            if nueva != pos:
                ejec = O[t, k + 1]
                if pos != 0:
                    pnl_dia += pos * acciones * (ejec - entrada)
                    coste_dia += acciones * (comision + desliz)
                    ops.append((dias[t], k_entrada, k + 1, pos, entrada, ejec, acciones))
                if nueva != 0:
                    entrada, k_entrada = ejec, k + 1
                    coste_dia += acciones * (comision + desliz)
                pos = nueva
        if pos != 0:
            tramo = L[t, k_entrada:] if pos == 1 else H[t, k_entrada:]
            peor = pnl_dia + pos * acciones * (tramo.min() - entrada if pos == 1 else tramo.max() - entrada) - coste_dia
            min_eq = min(min_eq, peor)
            pnl_dia += pos * acciones * (cierre[t] - entrada)
            coste_dia += acciones * (comision + desliz)
            ops.append((dias[t], k_entrada, MINUTOS, pos, entrada, cierre[t], acciones))
        neto = pnl_dia - coste_dia
        filas.append((dias[t], aum, neto / aum, min(min_eq, neto) / aum, coste_dia / aum, acciones * apertura[t] / aum))
        aum += neto
    diario = pd.DataFrame(filas, columns=['dia', 'aum_inicio', 'ret', 'min_intradia', 'coste', 'apalancamiento']).set_index('dia')
    oper = pd.DataFrame(ops, columns=['dia', 'k_entrada', 'k_salida', 'lado', 'precio_entrada', 'precio_salida', 'acciones'])
    return diario, oper


if __name__ == '__main__':
    fichero, salida = sys.argv[1:3]
    com, desl = (float(sys.argv[3]), float(sys.argv[4])) if len(sys.argv) > 4 else (0.0035, 0.001)
    os.makedirs(salida, exist_ok=True)
    d = cargar(fichero)
    dias, M = construir_matrices(d)
    barras = pd.DataFrame({'dia': dias, 'Open': M['O'][:, 0], 'High': M['H'].max(1), 'Low': M['L'].min(1), 'Close': M['C'][:, -1]})
    calidad_datos.auditar_historico(barras, 'SPY 1min (Kaggle, RTH)').imprimir()
    diario, oper = simular(dias, M, com, desl)
    diario.to_csv(os.path.join(salida, 'h74_diario.csv'))
    oper.to_csv(os.path.join(salida, 'h74_operaciones.csv'), index=False)
    r = diario['ret']
    print(f'días {len(r)}, operaciones {len(oper)} ({len(oper)/len(r):.2f}/día), IRR {((1+r).prod()**(252/len(r))-1)*100:.1f}%, '
          f'vol {r.std()*np.sqrt(252)*100:.1f}%, Sharpe {r.mean()/r.std()*np.sqrt(252):.2f}, '
          f'MDD {(((1+r).cumprod()/(1+r).cumprod().cummax())-1).min()*100:.1f}%, total {((1+r).prod()-1)*100:.0f}%')
