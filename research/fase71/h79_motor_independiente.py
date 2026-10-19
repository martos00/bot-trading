"""H79 — motor INDEPENDIENTE (Python puro: csv + datetime, sin pandas ni numpy). Mismas reglas del pre-registro.
Uso: python3 h79_motor_independiente.py DIR_HISTDATA_NSX SALIDA_CSV desliz comision"""
import csv, datetime as dt, glob, os, sys
from collections import defaultdict
from zoneinfo import ZoneInfo
import pandas_market_calendars as mcal   # solo para el calendario de sesiones completas

NY = ZoneInfo('America/New_York')
d_in, out, DESL, COM = sys.argv[1], sys.argv[2], float(sys.argv[3]), float(sys.argv[4])

velas = defaultdict(dict)
for f in sorted(glob.glob(os.path.join(d_in, 'DAT_ASCII_NSXUSD_M1_*.csv'))):
    for ts, o, h, l, c, _ in csv.reader(open(f), delimiter=';'):
        t = dt.datetime.strptime(ts, '%Y%m%d %H%M%S')
        k = (t.hour - 9) * 60 + t.minute - 30
        if 0 <= k <= 375 and t.date() not in velas or 0 <= k <= 375:
            velas[t.date()].setdefault(k, (float(o), float(h), float(l), float(c)))

cal = mcal.get_calendar('NYSE')
s = cal.schedule('2010-01-01', '2026-12-31')
completas = {x.date() for x in s.index.difference(cal.early_closes(s).index)}

w = csv.writer(open(out, 'w', newline=''))
w.writerow(['dia', 'lado', 'contratos', 'pnl'])
for dia in sorted(velas):
    v = velas[dia]
    if dia not in completas or len(v) < 370 or any(k not in v for k in range(15)):
        continue
    # relleno hacia delante de velas que faltan (precio plano = último cierre)
    barras, ult = [], None
    for k in range(375):
        if k in v:
            ult = v[k]; barras.append(v[k])
        else:
            barras.append((ult[3],) * 4)
    cierre = v[375][0] if 375 in v else barras[374][3]
    hi = max(b[1] for b in barras[:15]); lo = min(b[2] for b in barras[:15])
    sl = (hi - lo) / 2
    if sl <= 0:
        continue
    compra, venta = hi + 2, lo - 2
    entrada = None
    for k in range(15, 375):
        o, h, l, c = barras[k]
        if h >= compra or l <= venta:
            if h >= compra and l <= venta:
                lado = 1 if abs(o - compra) <= abs(o - venta) else -1
            else:
                lado = 1 if h >= compra else -1
            entrada = (k, lado, max(o, compra) if lado == 1 else min(o, venta))
            break
    if entrada is None:
        w.writerow([dia, 0, 0, 0.0]); continue
    k0, lado, base = entrada
    n = max(1, int(250 / (sl * 2)))
    stop, obj, px_ent = base - lado * sl, base + lado * 2 * sl, base + lado * DESL
    salida = None
    for k in range(k0, 375):
        o, h, l, c = barras[k]
        if lado == 1:
            if l <= stop:
                salida = (stop if k == k0 else min(o, stop)) - DESL; break
            if h >= obj and (k > k0 or c >= obj):
                salida = obj if k == k0 else max(o, obj); break
        else:
            if h >= stop:
                salida = (stop if k == k0 else max(o, stop)) + DESL; break
            if l <= obj and (k > k0 or c <= obj):
                salida = obj if k == k0 else min(o, obj); break
    if salida is None:
        salida = cierre - lado * DESL
    w.writerow([dia, lado, n, n * ((salida - px_ent) * lado * 2 - COM)])
