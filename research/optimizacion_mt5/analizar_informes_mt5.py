"""Analiza informes de prueba simple del Probador de MT5 exportados a Excel (.xlsx, versión en español).
Lee el resumen (calidad del historial, beneficio, PF, DD...) y la tabla de transacciones; reconstruye cada operación
(una entrada 'in' y sus salidas 'out', incluidos cierres parciales) y calcula métricas por año, por dirección y en R.
Uso: python3 analizar_informes_mt5.py RIESGO_PCT SALIDA_CSV NOMBRE=INFORME.xlsx [NOMBRE=INFORME.xlsx ...]"""
import sys
import numpy as np
import pandas as pd


def valor(v, etiqueta, col=3):
    f = v.index[v[0].astype(str).str.strip() == etiqueta]
    return v.iat[f[0], col] if len(f) else None


def valor_en(v, etiqueta):
    for c in (4, 8):
        f = v.index[v[c].astype(str).str.strip().str.startswith(etiqueta)]
        if len(f):
            return v.iat[f[0], c + 3]
    return None


def operaciones(v):
    i = v.index[v[0].astype(str).str.strip() == 'Transacciones'][0]
    t = v.iloc[i + 2:, :13].copy()
    t.columns = ['fecha', 'deal', 'simbolo', 'tipo', 'dir', 'vol', 'precio', 'orden', 'comision', 'swap', 'beneficio', 'balance', 'comentario']
    t = t[t.simbolo.notna() & t.dir.isin(['in', 'out'])]
    ops, actual = [], None
    for _, r in t.iterrows():
        neto = float(r.beneficio) + float(r.comision) + float(r.swap)
        if r.dir == 'in':
            if actual:
                ops.append(actual)
            actual = {'entrada': pd.Timestamp(str(r.fecha).replace('.', '-')), 'lado': 'largo' if r.tipo == 'buy' else 'corto',
                      'balance_antes': float(r.balance) - neto, 'pnl': neto, 'salidas': 0}
        else:
            actual['pnl'] += neto
            actual['salidas'] += 1
            actual['salida'] = pd.Timestamp(str(r.fecha).replace('.', '-'))
            actual['motivo'] = str(r.comentario)
    if actual:
        ops.append(actual)
    return pd.DataFrame(ops)


def pf(x):
    p, n = x[x > 0].sum(), -x[x < 0].sum()
    return p / n if n > 0 else np.inf


def racha_perdidas(x):
    m = c = 0
    for v in x:
        c = c + 1 if v < 0 else 0
        m = max(m, c)
    return m


if __name__ == '__main__':
    riesgo = float(sys.argv[1]) / 100
    filas, todas = [], []
    for arg in sys.argv[3:]:
        nom, f = arg.split('=', 1)
        v = pd.read_excel(f, header=None)
        o = operaciones(v)
        o['R'] = o.pnl / (riesgo * o.balance_antes)
        o['año'] = o.entrada.dt.year
        o.insert(0, 'candidata', nom)
        todas.append(o)
        n = len(o)
        res = {'candidata': nom, 'periodo': valor(v, 'Período:'), 'calidad': valor(v, 'Calidad del historial:'),
               'beneficio': float(valor(v, 'Beneficio Neto:')), 'PF_informe': float(valor(v, 'Factor de Beneficio:')),
               'ops_informe': int(valor(v, 'Total de operaciones ejecutadas:') or n),
               'DD_equidad': valor_en(v, 'Reducción máxima de la equidad'), 'ops': n,
               'aciertos%': round((o.pnl > 0).mean() * 100, 1), 'R_medio': o.R.mean(),
               't_R': o.R.mean() / o.R.std(ddof=1) * np.sqrt(n), 'racha_perd': racha_perdidas(o.pnl)}
        for a, g in o.groupby('año'):
            res[f'{a}_ops'], res[f'{a}_pnl'], res[f'{a}_PF'] = len(g), round(g.pnl.sum()), round(pf(g.pnl), 2)
        for l, g in o.groupby('lado'):
            res[f'{l}_ops'], res[f'{l}_pnl'], res[f'{l}_PF'] = len(g), round(g.pnl.sum()), round(pf(g.pnl), 2)
        # bootstrap de la media en R (10.000 remuestreos): p de media <= 0
        rng = np.random.default_rng(20261020)
        b = rng.choice(o.R.values, (10_000, n)).mean(axis=1)
        res['p_boot'] = (b <= 0).mean()
        filas.append(res)
    r = pd.DataFrame(filas)
    pd.concat(todas).to_csv(sys.argv[2], index=False)
    pd.set_option('display.width', 250); pd.set_option('display.max_columns', 60)
    print(r.T.to_string())
