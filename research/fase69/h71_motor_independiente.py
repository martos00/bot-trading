"""H71 — implementación INDEPENDIENTE (Python puro: csv + datetime + zoneinfo; sin pandas y sin
importar h71_motor). Solo comparte las listas de festivos (paquete holidays).

Uso: python3 h71_motor_independiente.py DIR_HISTDATA PAR SALIDA_CSV
"""
import csv, glob, math, os, sys
from datetime import datetime, date, timedelta
from zoneinfo import ZoneInfo
import holidays

NY, FRA, LON, TOK = (ZoneInfo(z) for z in ('America/New_York', 'Europe/Berlin', 'Europe/London', 'Asia/Tokyo'))


def leer(directorio, par):
    p = {}
    for f in sorted(glob.glob(os.path.join(directorio, f'DAT_ASCII_{par}_M1_*.csv'))):
        for fila in csv.reader(open(f), delimiter=';'):
            loc = datetime.strptime(fila[0], '%Y%m%d %H%M%S')
            a, b = loc.replace(tzinfo=NY, fold=0), loc.replace(tzinfo=NY, fold=1)
            if a.utcoffset() != b.utcoffset() or a.astimezone(ZoneInfo('UTC')).astimezone(NY).replace(tzinfo=None) != loc:
                continue
            k = int(a.timestamp()) // 60
            p.setdefault(k, float(fila[4]))
    return p


def px(p, d, hh, mm, tz):
    base = int(datetime(d.year, d.month, d.day, hh, mm, tzinfo=tz).timestamp()) // 60
    for j in range(1, 6):
        if base - j in p:
            return p[base - j]
    return None


def main():
    directorio, par, salida = sys.argv[1:4]
    p = leer(directorio, par)
    ks = sorted(p)
    d0 = datetime.fromtimestamp(ks[0] * 60, NY).date() + timedelta(days=1)
    d1 = datetime.fromtimestamp(ks[-1] * 60, NY).date() - timedelta(days=1)
    s = 1.0 if par.startswith('USD') else -1.0
    fe = set(holidays.financial_holidays('XECB', years=range(d0.year, d1.year + 1)))
    fj = set(holidays.Japan(years=range(d0.year, d1.year + 1)))
    out = []
    d = d0
    while d <= d1:
        if d.weekday() < 5:
            if d not in fe:
                v = [px(p, d, 8, 0, FRA), px(p, d, 14, 15, FRA), px(p, d, 16, 0, LON), px(p, d, 16, 55, NY)]
                if None not in v:
                    out.append([d, 'EUROPA', s * math.log(v[1] / v[0]) - s * math.log(v[3] / v[2])])
            if d not in fj:
                v = [px(p, d - timedelta(days=1), 17, 5, NY), px(p, d, 9, 55, TOK), px(p, d, 9, 55, TOK), px(p, d, 8, 0, FRA)]
                if None not in v:
                    out.append([d, 'TOKIO', s * math.log(v[1] / v[0]) - s * math.log(v[3] / v[2])])
        d += timedelta(days=1)
    w = csv.writer(open(salida, 'w', newline=''))
    w.writerow(['dia', 'estrategia', 'r'])
    w.writerows(out)


if __name__ == '__main__':
    main()
