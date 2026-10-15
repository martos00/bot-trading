"""
CPI Release Drift -- familia macro distinta de FOMC/NFP (ya probadas),
con fundamento academico real: el IPC de EEUU es, junto a NFP y FOMC,
uno de los anuncios macro de mayor impacto medido en la literatura de
anuncios en tiempo real (Andersen/Bollerslev/Diebold/Vega) -- y
especialmente relevante para el oro, que es sensible a expectativas de
inflacion.

CALENDARIO: fechas de publicacion REALES, verificadas una a una contra
las paginas de calendario oficiales del BLS (bls.gov/schedule/<año>/home.htm),
NO calculadas por una regla generica (el IPC no sigue un patron fijo
como "primer viernes" de NFP). Incluye la alteracion real del
calendario por el cierre de la Administracion de 2025 (sin IPC de
referencia octubre-2025; el de referencia septiembre-2025 se publico
el 24-oct en vez de mediados de mes) -- declarada, no omitida.
"""
from datetime import date

from datos_multiactivo import cargar_universo
from hipotesis_fomc_drift_multiactivo import medir

MERCADOS_PERMITIDOS = ['XAUUSD', 'USTEC', 'US500']

FECHAS_CPI = [
    date(2023, 1, 12), date(2023, 2, 14), date(2023, 3, 14), date(2023, 4, 12),
    date(2023, 5, 10), date(2023, 6, 13), date(2023, 7, 12), date(2023, 8, 10),
    date(2023, 9, 13), date(2023, 10, 12), date(2023, 11, 14), date(2023, 12, 12),
    date(2024, 1, 11), date(2024, 2, 13), date(2024, 3, 12), date(2024, 4, 10),
    date(2024, 5, 15), date(2024, 6, 12), date(2024, 7, 11), date(2024, 8, 14),
    date(2024, 9, 11), date(2024, 10, 10), date(2024, 11, 13), date(2024, 12, 11),
    date(2025, 1, 15), date(2025, 2, 12), date(2025, 3, 12), date(2025, 4, 10),
    date(2025, 5, 13), date(2025, 6, 11), date(2025, 7, 15), date(2025, 8, 12),
    date(2025, 9, 11), date(2025, 10, 24), date(2025, 12, 18),
    # (sin IPC de referencia octubre-2025 -- cancelado por el cierre de la
    # Administracion; el de referencia noviembre-2025 se publico 18-dic)
    date(2026, 1, 13), date(2026, 2, 13), date(2026, 3, 11), date(2026, 4, 10),
    date(2026, 5, 12), date(2026, 6, 10), date(2026, 7, 14), date(2026, 8, 12),
    date(2026, 9, 11),
    # (el de referencia septiembre-2026, 14-oct-2026, cae fuera del rango
    # de datos disponible -- 9-oct-2026 -- se omite, no se inventa)
]


def main():
    print(f"################ CPI drift -- {len(FECHAS_CPI)} fechas verificadas (BLS, 2023-2026) ################")
    universo = cargar_universo(MERCADOS_PERMITIDOS)
    print(f"{'Activo':<8}{'n':>4}  {'Dia CPI (Open->Close)':>24}  {'CPI->+1d':>20}")
    for nombre, diario in universo.items():
        r = medir(diario, FECHAS_CPI)
        if r['n'] == 0:
            print(f"{nombre}: sin fechas CPI en el rango de datos")
            continue
        marca_dia = " <-- |z|>2" if abs(r['z_dia']) > 2 else ""
        marca_2d = " <-- |z|>2" if abs(r['z_2d']) > 2 else ""
        print(f"{nombre:<8}{r['n']:>4}  media={r['media_dia_fomc']*100:+.3f}% z={r['z_dia']:+.2f}{marca_dia}"
              f"    media={r['media_fomc_mas1']*100:+.3f}% z={r['z_2d']:+.2f}{marca_2d}")


if __name__ == '__main__':
    main()
