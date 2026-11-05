"""Aplica las reglas de research/REGLAS_VIGILANCIA.md al registro del bot.
Uso: python3 vigilancia.py CarteraFuturos_log.csv"""
import sys
import numpy as np, pandas as pd

ESPERADO = {'E8_oro_viernes': 0.128, 'plata_viernes': 0.099, 'E10_plata_vispera': 0.215, 'E9_yen_fin_mes': 0.159,
            'E11_yen_fin_trim': 0.208, 'E15_oro_Dmenos2': 0.108, 'E13_nikkei_Qmas2': 0.243, 'E16_nikkei_Qmenos2': 0.120,
            'C102_cobre_rango_asia': 0.023, 'C93_oro_dia_anterior': 0.022, 'C99_oro_rango_asia': 0.015, 'C101_nikkei_rango_asia': 0.012}
CALENDARIO = {'E10_plata_vispera', 'E9_yen_fin_mes', 'E11_yen_fin_trim', 'E15_oro_Dmenos2', 'E13_nikkei_Qmas2', 'E16_nikkei_Qmenos2'}
COSTE_PB = {'MGC': 0.74, 'GC': 0.74, 'SIL': 2.3, 'SI': 2.3, 'MJY': 0.8, '6J': 0.8, 'NKD': 1.5, 'MHG': 2.0, 'HG': 2.0}

def operaciones(log):
    """Empareja entradas y salidas de cada estrategia → R = rentabilidad (pb) / sigma (pb)."""
    out, abiertas = [], {}
    for _, f in log.iterrows():
        e, ev = f.estrategia, str(f.evento)
        if ev.startswith(('compra', 'venta')) and f.contratos > 0 and e not in ('cartera', 'ejecucion'):
            abiertas[e] = (f.hora_NY, 1 if ev.startswith('compra') else -1, float(f.precio), float(f.sigma_pb))
        elif ev.startswith('cierre') and e in abiertas:
            t0, sg, p0, sig = abiertas.pop(e)
            r_pb = sg * np.log(float(f.precio) / p0) * 1e4
            out.append((f.hora_NY, e, r_pb, r_pb / sig if sig > 0 else np.nan))
    return pd.DataFrame(out, columns=['hora', 'estrategia', 'r_pb', 'R']).dropna()

def z(x): return x.mean() / (x.std(ddof=1) / np.sqrt(len(x))) if len(x) > 2 and x.std() > 0 else np.nan

if __name__ == '__main__':
    log = pd.read_csv(sys.argv[1])
    ops = operaciones(log)
    print(f'Operaciones cerradas: {len(ops)}\n')
    print('1) EJECUCIÓN — coste medio de las últimas 20 ejecuciones por contrato (deslizamiento):')
    ej = log[log.estrategia == 'ejecucion'].copy()
    if len(ej):
        ej['pb'] = ej.evento.str.extract(r'_ticks_([-\d.]+)_pb')[0].astype(float)
        ej['raiz'] = ej.contrato.str.split(' ').str[0]
        for raiz, g in ej.groupby('raiz'):
            m = g.pb.tail(20).mean(); sup = COSTE_PB.get(raiz, np.nan)
            alerta = '  ← SUPERA 1,5× el supuesto: mitad de tamaño y revisar' if sup == sup and m > 1.5 * sup / 2 else ''
            print(f'   {raiz}: deslizamiento medio por ejecución {m:+.2f} pb (supuesto ~{sup/2:.2f} por lado){alerta}')
    print('\n2) ESTRATEGIAS:')
    grupos = {**{e: e for e in ops.estrategia.unique() if e not in CALENDARIO}, **{e: 'grupo_calendario' for e in CALENDARIO}}
    ops['grupo'] = ops.estrategia.map(lambda e: grupos.get(e, e))
    for g, d in ops.groupby('grupo'):
        R = d.R; n = len(R); zz = z(R)
        exp = np.mean([ESPERADO.get(e, 0) for e in d.estrategia]) if g == 'grupo_calendario' else ESPERADO.get(g, 0)
        acc = 'ok'
        if n >= 50 and zz <= -2.0: acc = 'FUERA (z ≤ −2)'
        elif n >= 50 and R.mean() < 0 and zz <= -1.5: acc = 'MITAD de tamaño (z ≤ −1,5)'
        elif n < 50: acc = f'aún pocas operaciones ({n}/50)'
        print(f'   {g:24s} n {n:4d} | media R {R.mean():+.3f} (esperado {exp:+.3f}) | z {zz:+.2f} | acumulado R {R.sum():+.1f} → {acc}')
        if g in ('E8_oro_viernes', 'plata_viernes') and n >= 104:
            u = R.tail(104); print(f'      últimas 104: media {u.mean():+.3f} z {z(u):+.2f}'
                                   + ('  → MITAD (regla de régimen)' if (g == 'E8_oro_viernes' and u.mean() <= 0) or z(u) <= -2 else ''))
    print('\n3) CARTERA:')
    if len(ops):
        R = ops.sort_values('hora').R
        print(f'   acumulado R {R.sum():+.1f} | media {R.mean():+.3f} | z {z(R):+.2f}')
        print('   Escalar solo si: ≥ 6 meses reales, sin fallos técnicos y acumulado R ≥ 0.')
