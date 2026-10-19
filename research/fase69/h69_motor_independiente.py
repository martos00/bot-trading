"""H69 — implementación INDEPENDIENTE del cálculo de precios/señales (contraste del motor
principal h69_motor.py). Python puro: csv + datetime + zoneinfo, sin pandas ni numpy y sin
importar nada de h69_motor. Lo único compartido es la lista de sesiones NYSE (completas y de
cierre anticipado), que se lee de un fichero generado aparte.

Uso: python3 h69_motor_independiente.py DIR_HISTDATA SIMBOLO SESIONES_CSV SALIDA_CSV
     SESIONES_CSV: columnas dia,tipo  (tipo = completa | temprana), todas las sesiones NYSE.
"""
import csv, glob, math, os, sys
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo

NY = ZoneInfo('America/New_York')
UTC = ZoneInfo('UTC')


def leer_minutos(directorio, sim):
    """dict: minuto UTC (epoch//60) de APERTURA de la vela -> cierre. Primera aparición gana."""
    precios = {}
    for f in sorted(glob.glob(os.path.join(directorio, f'DAT_ASCII_{sim}_M1_*.csv'))):
        with open(f) as fh:
            for fila in csv.reader(fh, delimiter=';'):
                local = datetime.strptime(fila[0], '%Y%m%d %H%M%S')
                # hora local NY con DST; se descartan las horas ambiguas/inexistentes del cambio de hora
                a = local.replace(tzinfo=NY, fold=0)
                b = local.replace(tzinfo=NY, fold=1)
                if a.utcoffset() != b.utcoffset():
                    continue
                if a.astimezone(UTC).astimezone(NY).replace(tzinfo=None) != local:
                    continue
                clave = int(a.timestamp()) // 60
                if clave not in precios:
                    precios[clave] = float(fila[4])
    return precios


def precio(precios, dia, hh, mm):
    """Cierre de la última vela con apertura en [T-5, T-1] minutos."""
    t = datetime(dia.year, dia.month, dia.day, hh, mm, tzinfo=NY)
    base = int(t.timestamp()) // 60
    for k in range(1, 6):
        if base - k in precios:
            return precios[base - k]
    return None


def main():
    directorio, sim, f_ses, salida = sys.argv[1:5]
    precios = leer_minutos(directorio, sim)
    with open(f_ses) as fh:
        sesiones = [(datetime.strptime(r['dia'], '%Y-%m-%d'), r['tipo']) for r in csv.DictReader(fh)]
    minutos = sorted(precios)
    primero = datetime.fromtimestamp(minutos[0] * 60, NY).replace(tzinfo=None)
    ultimo = datetime.fromtimestamp(minutos[-1] * 60, NY).replace(tzinfo=None)
    filas = []
    for i in range(1, len(sesiones)):
        dia, tipo = sesiones[i]
        if tipo != 'completa' or dia < primero - timedelta(days=1) or dia > ultimo:
            continue
        previo, tipo_prev = sesiones[i - 1]
        p_prev = precio(precios, previo, 13, 0) if tipo_prev == 'temprana' else precio(precios, previo, 16, 0)
        p10, p1530, p16 = precio(precios, dia, 10, 0), precio(precios, dia, 15, 30), precio(precios, dia, 16, 0)
        if None in (p_prev, p10, p1530, p16):
            filas.append([dia.date(), '', '', ''])
            continue
        filas.append([dia.date(), math.log(p1530 / p_prev), math.log(p10 / p_prev), math.log(p16 / p1530)])
    with open(salida, 'w', newline='') as fh:
        w = csv.writer(fh)
        w.writerow(['dia', 'r_ROD', 'r_ONFH', 'r_LH'])
        w.writerows(filas)


if __name__ == '__main__':
    main()
