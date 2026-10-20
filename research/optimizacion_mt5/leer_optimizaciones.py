"""Lee informes XML (SpreadsheetML) del optimizador de MT5 y los une en un CSV.
Uso: python3 leer_optimizaciones.py SALIDA_CSV FICHERO.xml [FICHERO.xml ...]"""
import re, sys, xml.etree.ElementTree as ET
import pandas as pd

NS = {'ss': 'urn:schemas-microsoft-com:office:spreadsheet', 'o': 'urn:schemas-microsoft-com:office:office'}
tablas = []
for f in sys.argv[2:]:
    r = ET.parse(f).getroot()
    titulo = r.find('o:DocumentProperties/o:Title', NS).text
    filas = [[c.find('ss:Data', NS).text if c.find('ss:Data', NS) is not None else None for c in row.findall('ss:Cell', NS)]
             for row in r.iter('{urn:schemas-microsoft-com:office:spreadsheet}Row')]
    df = pd.DataFrame(filas[1:], columns=filas[0])
    for c in df.columns:
        n = pd.to_numeric(df[c], errors='coerce')
        if n.notna().all():
            df[c] = n
    nombre = re.sub(r'^.*ReportOptimizer|-\d+\.xml$', '', f).strip('_-') or 'COMPLETO'
    df.insert(0, 'informe', nombre)
    print(f'{nombre}: {titulo} | pasadas {len(df)} | columnas {list(df.columns[11:])}')
    tablas.append(df)
pd.concat(tablas, ignore_index=True).to_csv(sys.argv[1], index=False)
