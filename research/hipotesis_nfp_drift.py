"""
Non-Farm Payrolls (NFP) Drift -- familia macro distinta de Pre/Post-
FOMC (ya probada, intradia e indice-only, cerrada) y distinta de
Turno de Mes/Pre-FOMC (ya cerradas). Fundamento: el informe de empleo
de EEUU (primer viernes de cada mes, 8:30 ET) es uno de los eventos
macro de mayor impacto documentado en la literatura de anuncios
macroeconomicos (Andersen, Bollerslev, Diebold & Vega 2003/2007,
"Real-Time Price Discovery in Global Stock, Bond and Foreign Exchange
Markets" -- NFP figura sistematicamente entre los anuncios de mayor
impacto medido en todos esos mercados). Aqui se mide en BARRA DIARIA
(sin reconstruccion de sesion), restringido a XAUUSD/USTEC/US500 (los
3 mercados con histórico ya disponible y suficiente, segun lo pedido
por el usuario).

CALENDARIO: primer viernes de cada mes (regla NFP estandar; excepcion
conocida y declarada -- en meses donde el primer viernes cae en
festivo de Año Nuevo, el informe puede publicarse la semana siguiente;
no se han corregido esas excepciones manualmente -- se declara como
limitacion menor, afecta a <5% de las fechas en el peor caso).

FASE 1 (identificar la ventaja antes de construir señal/SL/TP): mismo
diseño que hipotesis_fomc_drift_multiactivo.py -- retorno Open->Close
del dia de NFP y Open(NFP)->Close(NFP+1), comparado con benchmark de
dias aleatorios no-NFP (1000 repeticiones).
"""
import calendar
from datetime import date

import numpy as np

from datos_multiactivo import cargar_universo
from hipotesis_fomc_drift_multiactivo import medir

MERCADOS_PERMITIDOS = ['XAUUSD', 'USTEC', 'US500']


def primeros_viernes(año_ini, año_fin):
    fechas = []
    for año in range(año_ini, año_fin + 1):
        for mes in range(1, 13):
            cal = calendar.monthcalendar(año, mes)
            for semana in cal:
                if semana[calendar.FRIDAY] != 0:
                    fechas.append(date(año, mes, semana[calendar.FRIDAY]))
                    break
    return fechas


def main():
    fechas_nfp = primeros_viernes(2015, 2026)
    print(f"################ NFP drift -- {len(fechas_nfp)} fechas (primer viernes de cada mes, 2015-2026) ################")
    print("(limitacion declarada: no se han corregido manualmente los pocos meses donde el "
          "informe real se retraso una semana por festivo de Año Nuevo)")
    universo = cargar_universo(MERCADOS_PERMITIDOS)
    print(f"\n{'Activo':<8}{'n':>4}  {'Dia NFP (Open->Close)':>26}  {'NFP->+1d':>20}")
    for nombre, diario in universo.items():
        r = medir(diario, fechas_nfp)
        if r['n'] == 0:
            print(f"{nombre}: sin fechas NFP en el rango de datos")
            continue
        marca_dia = " <-- |z|>2" if abs(r['z_dia']) > 2 else ""
        marca_2d = " <-- |z|>2" if abs(r['z_2d']) > 2 else ""
        print(f"{nombre:<8}{r['n']:>4}  media={r['media_dia_fomc']*100:+.3f}% z={r['z_dia']:+.2f}{marca_dia}"
              f"    media={r['media_fomc_mas1']*100:+.3f}% z={r['z_2d']:+.2f}{marca_2d}")


if __name__ == '__main__':
    main()
