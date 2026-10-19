"""H74 — implementación INDEPENDIENTE (contraste de h74_motor.py). Python puro con csv y bucles
explícitos sobre filas minuto a minuto; no importa h74_motor ni usa pandas/numpy.

Uso: python3 h74_motor_independiente.py SPY_1MIN_CSV SALIDA_CSV [coste_por_accion_y_lado]
"""
import csv, math, sys
from datetime import datetime, timedelta
from collections import OrderedDict


def main():
    f, out = sys.argv[1], sys.argv[2]
    coste = float(sys.argv[3]) if len(sys.argv) > 3 else 0.0045
    vistos, dias = set(), OrderedDict()
    for r in csv.DictReader(open(f)):
        if r['date'] in vistos:
            continue
        vistos.add(r['date'])
        t = datetime.strptime(r['date'], '%Y-%m-%d %H:%M:%S') + timedelta(hours=2)
        k = (t.hour - 9) * 60 + t.minute - 30
        if not 0 <= k < 390:
            continue
        dias.setdefault(t.date(), {})[k] = tuple(float(r[c]) for c in ('open', 'high', 'low', 'close', 'volume', 'average'))
    validos = []
    for d, b in dias.items():
        if len(b) < 380:
            continue
        ult = None
        filas = []
        for k in range(390):   # relleno de minutos ausentes con el último precio y volumen 0
            if k in b:
                ult = b[k]
                filas.append(b[k])
            elif ult is not None:
                filas.append((ult[3], ult[3], ult[3], ult[3], 0.0, ult[3]))
            else:
                filas.append(None)
        if filas[0] is None:
            primero = next(x for x in filas if x is not None)
            filas = [x if x is not None else (primero[0],) * 4 + (0.0, primero[0]) for x in filas]
        validos.append((d, filas))
    aum = 100000.0
    res = []
    for t in range(15, len(validos)):
        d, B = validos[t]
        abre = B[0][0]
        cierre_prev = validos[t - 1][1][389][3]
        hist = [validos[t - i][1] for i in range(1, 15)]
        rets = [validos[t - i][1][389][3] / validos[t - i - 1][1][389][3] - 1 for i in range(1, 15)]
        mu = sum(rets) / 14
        vol = math.sqrt(sum((x - mu) ** 2 for x in rets) / 13)
        acc = math.floor(aum * min(4.0, 0.02 / vol) / abre)
        pv = vv = 0.0
        pos, ent, pnl = 0, 0.0, 0.0
        for k in range(390):
            pv += B[k][5] * B[k][4]
            vv += B[k][4]
            if k + 1 in range(30, 361, 30):
                sig = sum(abs(h[k][3] / h[0][0] - 1) for h in hist) / 14
                ub = max(abre, cierre_prev) * (1 + sig)
                lb = min(abre, cierre_prev) * (1 - sig)
                vw = pv / vv if vv > 0 else B[k][3]
                p = B[k][3]
                nueva = pos
                if pos == 1 and p < max(ub, vw):
                    nueva = -1 if p < lb else 0
                elif pos == -1 and p > min(lb, vw):
                    nueva = 1 if p > ub else 0
                elif pos == 0:
                    nueva = 1 if p > ub else (-1 if p < lb else 0)
                if nueva != pos:
                    x = B[k + 1][0]
                    if pos:
                        pnl += pos * acc * (x - ent) - acc * coste
                    if nueva:
                        ent = x
                        pnl -= acc * coste
                    pos = nueva
        if pos:
            pnl += pos * acc * (B[389][3] - ent) - acc * coste
        res.append((d, pnl / aum))
        aum += pnl
    w = csv.writer(open(out, 'w', newline=''))
    w.writerow(['dia', 'ret'])
    w.writerows(res)


if __name__ == '__main__':
    main()
