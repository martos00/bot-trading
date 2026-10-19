"""H72 — implementación INDEPENDIENTE de las señales y de la estrategia (contraste de h72_motor).
Lleva el valor en dólares de cada pata (no recursión de pesos), detecta fin de mes con datetime y
calcula todo en bucles explícitos. Lee las rentabilidades diarias producidas por h72_motor (r_sp, r_10y,
rf), que son datos, no lógica de la estrategia.

Uso: python3 h72_motor_independiente.py H72_CSV SALIDA_CSV
"""
import csv, sys
from datetime import date


def main():
    filas = list(csv.DictReader(open(sys.argv[1])))
    dias = [date.fromisoformat(f['dia'][:10]) for f in filas]
    rs = [float(f['r_sp']) for f in filas]
    rb = [float(f['r_10y']) for f in filas]
    rf = [float(f['rf']) if f['rf'] else float('nan') for f in filas]
    n = len(dias)
    ultimo = [i == n - 1 or (dias[i + 1].year, dias[i + 1].month) != (dias[i].year, dias[i].month) for i in range(n)]

    def dev_serie(regla):
        acc, bon, out = 60.0, 40.0, []
        for t in range(n):
            acc *= 1 + rs[t]
            bon *= 1 + rb[t]
            dv = acc / (acc + bon) - 0.60
            out.append(dv)
            if regla(t, dv):
                tot = acc + bon
                acc, bon = 0.60 * tot, 0.40 * tot
        return out

    deltas = [k / 1000 for k in range(26)]
    series_th = [dev_serie(lambda t, dv, d=d: abs(dv) >= d - 1e-15) for d in deltas]
    th = [sum(s[t] for s in series_th) / len(deltas) for t in range(n)]
    cal = dev_serie(lambda t, dv: ultimo[t])
    # días hasta fin de mes
    hasta_fin = [0] * n
    for t in range(n - 1, -1, -1):
        hasta_fin[t] = 0 if ultimo[t] else hasta_fin[t + 1] + 1
    sg = lambda x: (x > 0) - (x < 0)
    cm = [0.0] * n
    t4_prev = None
    for t in range(n):
        if t > 0 and (dias[t].year, dias[t].month) != (dias[t - 1].year, dias[t - 1].month):
            cm[t] = sg(t4_prev) if t4_prev is not None else 0.0
            t4_prev = None
        if hasta_fin[t] < 5:
            cm[t] = sg(-cal[t])
        if hasta_fin[t] == 4:
            t4_prev = cal[t]
    w = [(-th[t] / 0.015 + cm[t]) / 2 for t in range(n)]
    out = csv.writer(open(sys.argv[2], 'w', newline=''))
    out.writerow(['dia', 'w', 'estr', 'estr_rv'])
    for t in range(n):
        e = w[t - 1] * (rs[t] - rb[t]) if t else ''
        e2 = w[t - 1] * (rs[t] - rf[t]) if t else ''
        out.writerow([dias[t], w[t], e, e2])


if __name__ == '__main__':
    main()
