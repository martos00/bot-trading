"""
Ejecuta la validacion independiente de Volatility Expansion Continuation
(XAUUSD) sobre el historico 2015-2022 de HistData.com (gratuito, mismo
periodo pre-2023 que no se ha usado nunca en el desarrollo de esta
estrategia -- ver research/convertir_histdata_m1_a_m15.py para el origen
y limitaciones de los datos).

NO reimplementa ni modifica la señal/SL/TP/cierre forzoso de la
estrategia congelada -- reutiliza exactamente
validacion_independiente_volexp.ejecutar_congelada_realista,
calcular_equity_simultanea, control_direccion_aleatoria y
control_dia_aleatorio. La UNICA adaptacion (permitida explicitamente por
el usuario: "Adaptar unicamente la lectura de datos y los costes
necesarios") es el tratamiento de costes, porque este dataset no tiene
spread real (ver docstring de convertir_histdata_m1_a_m15.py):

 - "CERO COSTE" (extra=0$): limite OPTIMISTA, no es "solo spread real"
   como en el tramo 2023-2026 -- aqui no hay spread real disponible.
 - Estres explicito en dolares por operacion (1$, 3$, 5$): mismo
   concepto que EXTRA_PUNTOS_ESTRES del resto del proyecto pero
   reportado aparte porque aqui sustituye por completo al spread real
   (no se añade encima de el, se añade sobre un coste base de 0).
   Ninguno de estos valores es una cifra de broker real -- son estres
   etiquetado para ver cuanto margen tiene el resultado antes de
   desaparecer.
"""
import sys

import numpy as np

from orb_backtest import calcular_r_multiplos, metricas_en_r
from hipotesis_rsi2_sma200 import cargar_m15
from estrategia_gap_fade import agregar_diario_con_spread
from validacion_independiente_volexp import (
    ejecutar_congelada_realista, calcular_equity_simultanea,
    control_direccion_aleatoria, control_dia_aleatorio, SEED, REPETICIONES_CONTROL,
)

ESTRES_DOLARES_SIN_SPREAD_REAL = [0.0, 1.0, 3.0, 5.0]


def main(path, nombre='XAUUSD_HISTDATA_2015_2022'):
    print(f"\n\n################ VALIDACION INDEPENDIENTE -- {nombre} ################")
    df = cargar_m15(path)
    diario = agregar_diario_con_spread(df)
    print(f"Barras diarias construidas: {len(diario)} ({diario['dia'].min().date()} .. {diario['dia'].max().date()})")
    ops, d = ejecutar_congelada_realista(diario, point=0.01)

    print(f"\nOperaciones totales (señal+SL+TP+cierre forzoso IDENTICOS a la estrategia congelada): {len(ops)}")
    if len(ops) == 0:
        print("  SIN OPERACIONES -- no se puede validar en este historico.")
        return
    print(f"  Direccion: {ops['direccion'].value_counts().to_dict()}")
    print("  Motivo de salida:", ops['motivo_salida'].value_counts().to_dict())

    for extra in ESTRES_DOLARES_SIN_SPREAD_REAL:
        etiqueta = "CERO COSTE (sin spread real disponible -- limite optimista)" if extra == 0.0 \
            else f"estres etiquetado de {extra:.0f}$/operacion (NO es spread real del broker)"
        ops_r = calcular_r_multiplos(ops, extra)
        m = metricas_en_r(ops_r)
        print(f"\n--- {etiqueta} ---")
        print(f"  n={m['n']}  Suma R={m['suma_R']:+.2f}  Media R={m['media_R']:+.4f}  "
              f"PF={m['profit_factor']:.3f}  %Acierto={m['pct_acierto']:.1f}%  "
              f"Drawdown balance={m['max_drawdown_balance_R']:.2f}R")
        for anio, g in ops_r.groupby('anio'):
            mg = metricas_en_r(g)
            print(f"    {anio}: n={mg['n']}  Suma R={mg['suma_R']:+.2f}  Media R={mg['media_R']:+.4f}  PF={mg['profit_factor']:.3f}")

    eq = calcular_equity_simultanea(ops, d)
    print(f"\n--- Riesgo agregado y drawdown de equity (posiciones simultaneas, sin impedir solapamiento) ---")
    print(f"  Maximo de posiciones simultaneas abiertas: {eq['max_posiciones_simultaneas']}")
    print(f"  Drawdown de EQUITY (marcado a mercado): {eq['max_drawdown_equity_R']:.2f}R "
          f"(el {eq['dia_max_drawdown'].date()})")

    rng = np.random.default_rng(SEED)
    media_real, media_ctrl_a, std_ctrl_a, z_a = control_direccion_aleatoria(ops, rng)
    print(f"\n--- Control A: misma fecha/riesgo, DIRECCION aleatoria ({REPETICIONES_CONTROL} rep.) ---")
    print(f"  Media real={media_real:+.4f}  Media aleatoria={media_ctrl_a:+.4f} (std={std_ctrl_a:.4f})  z={z_a:+.2f}")

    medias_ctrl_b = control_dia_aleatorio(diario, 0.01, len(ops), rng)
    z_b = (media_real - medias_ctrl_b.mean()) / medias_ctrl_b.std() if medias_ctrl_b.std() > 0 else np.nan
    print(f"\n--- Control B: DIAS DE ENTRADA aleatorios (no necesariamente expansion), mismo mecanismo "
          f"de riesgo ({REPETICIONES_CONTROL} rep.) ---")
    print(f"  Media real={media_real:+.4f}  Media aleatoria={medias_ctrl_b.mean():+.4f} "
          f"(std={medias_ctrl_b.std():.4f})  z={z_b:+.2f}")


if __name__ == '__main__':
    main(sys.argv[1], sys.argv[2] if len(sys.argv) > 2 else 'XAUUSD_HISTDATA_2015_2022')
