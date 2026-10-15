"""
Descarga historico XAUUSD de Dukascopy (gratuito) y lo convierte al
formato exacto que usa este proyecto
(TimestampServidor;Open;High;Low;Close;TickVolume;Spread;RealVolume),
para poder ejecutar la estrategia CONGELADA Volatility Expansion
Continuation sin cambiar una linea de research/estrategia_volatilidad_expansion.py.

EJECUTAR EN TU PROPIO ORDENADOR, no en la sandbox de Claude -- el
endpoint de datos de Dukascopy (datafeed.dukascopy.com) bloquea las IPs
de los centros de datos donde corre esta sesion; una conexion domestica
normal deberia funcionar sin problema.

INSTALACION PREVIA (una sola vez):
    pip install duka pandas

USO:
    python3 descargar_dukascopy_xauusd.py 2015-01-01 2022-07-10 ./dukascopy_xauusd

Descarga dia a dia (reanudable: si se interrumpe, se puede volver a
ejecutar con las mismas fechas y salta los meses ya completados),
construye velas M15 EN BID (para ser consistentes con el resto del
proyecto, donde el OHLC de MetaQuotes-Demo tambien es Bid), y calcula
el SPREAD REAL de cada vela como la media de (Ask-Bid) de sus ticks --
una mejora genuina frente a la columna "Spread" autoreportada del
broker que usabamos hasta ahora (ver diferencias documentadas en
README.md tras ejecutar esto).

DIFERENCIA DE ZONA HORARIA A DOCUMENTAR (no es un error, es inherente a
la fuente): los timestamps crudos de Dukascopy estan indexados en UTC;
los de MetaQuotes-Demo usados hasta ahora en este proyecto estan en la
hora de servidor del broker (EET/EEST, ya reconstruida en otras partes
del proyecto). La estrategia Volatility Expansion opera en BARRA DIARIA
agregada por "dia de calendario de los timestamps", asi que el dia
agregado aqui sera un dia UTC, no un dia EET/EEST -- una diferencia
metodologica pequeña pero real entre ambas fuentes, declarada
explicitamente, no corregida con una conversion horaria que podria
introducir sus propios errores.
"""
import csv
import sys
from datetime import date, timedelta
from pathlib import Path

try:
    from duka.core.fetch import fetch_day
    from duka.core.processor import decompress
except ImportError:
    print("Falta instalar 'duka': pip install duka pandas")
    sys.exit(1)

SYMBOL = 'XAUUSD'
POINT = 0.01  # XAUUSD Digits=2, misma convencion que el resto del proyecto
SEGUNDOS_VELA = 15 * 60

CABECERA = ['TimestampServidor', 'Open', 'High', 'Low', 'Close', 'TickVolume', 'Spread', 'RealVolume']


def velas_m15_desde_ticks(ticks):
    """ticks: lista de (datetime_utc, ask, bid, vol_ask, vol_bid) ya decodificados
    por duka para un dia. Devuelve velas M15 en BID con spread real medio."""
    velas = {}
    for ts, ask, bid, vol_ask, vol_bid in ticks:
        bucket = ts.replace(minute=(ts.minute // 15) * 15, second=0, microsecond=0)
        if bucket not in velas:
            velas[bucket] = dict(open=bid, high=bid, low=bid, close=bid,
                                  n_ticks=0, suma_spread=0.0, vol=0.0)
        v = velas[bucket]
        v['high'] = max(v['high'], bid)
        v['low'] = min(v['low'], bid)
        v['close'] = bid
        v['n_ticks'] += 1
        v['suma_spread'] += (ask - bid)
        v['vol'] += (vol_ask + vol_bid)
    return velas


def procesar_mes(simbolo, primer_dia, ultimo_dia, ruta_salida):
    filas = []
    dia = primer_dia
    while dia <= ultimo_dia:
        # No se filtra por dia de la semana -- se intenta siempre y se deja que
        # Dukascopy devuelva vacio en fines de semana/festivos (se maneja abajo
        # sin inventar nada). Mas simple y robusto que adivinar el calendario.
        try:
            buffer = fetch_day(simbolo, dia)
            ticks = decompress(simbolo, dia, buffer)
        except Exception as e:
            print(f"  [AVISO] fallo al descargar {dia}: {e} -- se omite ese dia, no se inventa dato")
            ticks = []
        if ticks:
            velas = velas_m15_desde_ticks(ticks)
            for bucket in sorted(velas.keys()):
                v = velas[bucket]
                spread_medio_precio = v['suma_spread'] / v['n_ticks'] if v['n_ticks'] else 0.0
                spread_puntos = round(spread_medio_precio / POINT)
                filas.append([
                    bucket.strftime('%Y.%m.%d %H:%M:%S'),
                    f"{v['open']:.2f}", f"{v['high']:.2f}", f"{v['low']:.2f}", f"{v['close']:.2f}",
                    v['n_ticks'], spread_puntos, round(v['vol']),
                ])
        print(f"  {dia}: {len(ticks)} ticks" + ("" if ticks else " (sin datos -- fin de semana/festivo esperado)"))
        dia += timedelta(days=1)

    if filas:
        with open(ruta_salida, 'w', newline='') as f:
            w = csv.writer(f, delimiter=';')
            w.writerow(CABECERA)
            w.writerows(filas)
        print(f"  -> guardado {ruta_salida} ({len(filas)} velas M15)")
    else:
        print(f"  -> sin velas en este tramo, no se escribe archivo")


def generar_meses(fecha_inicio, fecha_fin):
    actual = date(fecha_inicio.year, fecha_inicio.month, 1)
    while actual <= fecha_fin:
        if actual.month == 12:
            siguiente = date(actual.year + 1, 1, 1)
        else:
            siguiente = date(actual.year, actual.month + 1, 1)
        fin_mes = min(siguiente - timedelta(days=1), fecha_fin)
        inicio_mes = max(actual, fecha_inicio)
        yield inicio_mes, fin_mes
        actual = siguiente


def main(fecha_inicio_str, fecha_fin_str, carpeta_salida):
    fecha_inicio = date.fromisoformat(fecha_inicio_str)
    fecha_fin = date.fromisoformat(fecha_fin_str)
    carpeta = Path(carpeta_salida)
    carpeta.mkdir(parents=True, exist_ok=True)

    for inicio_mes, fin_mes in generar_meses(fecha_inicio, fecha_fin):
        nombre = carpeta / f"XAUUSD_M15_dukascopy_{inicio_mes.isoformat()}_{fin_mes.isoformat()}.csv"
        if nombre.exists():
            print(f"Ya existe {nombre}, se omite (reanudable) -- borralo si quieres repetirlo")
            continue
        print(f"Procesando {inicio_mes} -> {fin_mes} ...")
        procesar_mes(SYMBOL, inicio_mes, fin_mes, nombre)

    print("\nListo. Sube aqui todos los CSV generados en la carpeta de salida "
          "(uno por mes) y me encargo de unirlos, verificarlos y ejecutar la estrategia.")


if __name__ == '__main__':
    if len(sys.argv) != 4:
        print("Uso: python3 descargar_dukascopy_xauusd.py YYYY-MM-DD YYYY-MM-DD carpeta_salida")
        sys.exit(1)
    main(sys.argv[1], sys.argv[2], sys.argv[3])
