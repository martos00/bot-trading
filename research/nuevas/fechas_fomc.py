"""Fechas de anuncio de las reuniones PROGRAMADAS del FOMC (último día de cada reunión), 1994-2026, de las páginas oficiales
federalreserve.gov (fomchistoricalAAAA.htm y fomccalendars.htm). Se excluyen las reuniones no programadas y las llamadas.
Uso: python3 fechas_fomc.py DIR_HTML SALIDA_CSV"""
import html, os, re, sys
import pandas as pd

MESES = {m: i for i, m in enumerate(['January', 'February', 'March', 'April', 'May', 'June', 'July', 'August', 'September',
                                     'October', 'November', 'December'], 1)}
ABR = {'Jan': 1, 'Feb': 2, 'Mar': 3, 'Apr': 4, 'May': 5, 'Jun': 6, 'Jul': 7, 'Aug': 8, 'Sep': 9, 'Oct': 10, 'Nov': 11, 'Dec': 12}


def texto(f):
    t = open(f, encoding='utf8', errors='ignore').read()
    return html.unescape(re.sub(r'\s+', ' ', re.sub(r'<[^>]+>', ' ', t)))


def mes(s):
    s = s.strip()
    return MESES.get(s) or ABR.get(s[:3])


d, salida = sys.argv[1:3]
fechas = set()
for y in range(1994, 2021):
    t = texto(os.path.join(d, f'h{y}.html'))
    for m in re.finditer(r'(\w+)(?:/(\w+))? (\d{1,2})(?:-(\d{1,2}))? Meeting - (\d{4})', t):
        m1, m2, d1, d2, yy = m.groups()
        if int(yy) != y or mes(m1) is None:
            continue
        mm = mes(m2) if m2 else mes(m1)
        fechas.add(pd.Timestamp(y, mm, int(d2 or d1)))
t = texto(os.path.join(d, 'actual.html'))
for y in range(2021, 2027):
    k = t.find(f'{y} FOMC Meetings')
    if k < 0:
        continue
    fin = t.find('FOMC Meetings', k + 20)
    seccion = t[k:fin if fin > 0 else len(t)]
    for m in re.finditer(r'\b(Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)\w*(?:/(\w+))? (\d{1,2})(?:-(\d{1,2}))?\*? (?:Statement|Notation|\(unscheduled\))?', seccion):
        m1, m2, d1, d2 = m.groups()
        frag = seccion[m.start():m.start() + 60]
        if 'unscheduled' in frag or 'notation' in frag.lower():
            continue
        mm = mes(m2) if m2 else mes(m1)
        try:
            fechas.add(pd.Timestamp(y, mm, int(d2 or d1)))
        except ValueError:
            pass
f = sorted(fechas)
# dos fechas a ≤ 2 días: misma reunión mal etiquetada; se conserva la última
f = [x for i, x in enumerate(f) if not (i + 1 < len(f) and (f[i + 1] - x).days <= 2)]
s = pd.Series(f, name='fomc')
s.to_csv(salida, index=False)
print(s.groupby(s.dt.year).size().to_dict())
