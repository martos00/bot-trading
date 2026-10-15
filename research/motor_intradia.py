"""
Informe compartido para las 6 hipotesis intradia de este ciclo --
centraliza el reporte (coste, por año, por regimen diario, drawdown de
equity, control de direccion aleatoria) para no repetir el mismo
bloque de impresion en cada hipotesis. Reutiliza exactamente los mismos
helpers ya validados del resto del proyecto (orb_backtest,
validacion_independiente_volexp) -- no se reimplementa nada de la
contabilidad en R, drawdown o bootstrap.

Las 6 hipotesis producen un DataFrame `ops` con el mismo esquema
estandar ya usado en todo el proyecto (dia, anio, direccion,
idx_entrada, idx_salida, precio_entrada, riesgo_puntos,
ret_bruto_puntos, spread_entrada_precio, motivo_salida,
peor_flotante_r), mas una columna `regimen` (regimen DIARIO -- tendencia
x volatilidad -- del dia de entrada, uniendo con el regimen ya
clasificado por regimenes_mercado.py: señal intradia, pero el contexto
de regimen se evalua igual que en el ciclo anterior para comparar
peras con peras).

ESCENARIOS DE COSTE (distintos de los del ciclo diario -- aqui se pide
explicitamente modelar slippage ademas de spread, ver instruccion del
usuario): 'spread real', 'spread + 1pt slippage', 'spread + 3pt
slippage' -- en puntos de indice (point=0.01, Digits=2, igual que el
resto del proyecto).
"""
import numpy as np

from orb_backtest import calcular_r_multiplos, metricas_en_r
from validacion_independiente_volexp import calcular_equity_simultanea, control_direccion_aleatoria
from regimenes_mercado import resumen_por_regimen

ESTRES_COSTE = [0.0, 1.0, 3.0]
SEED = 20261015


def etiquetar_regimen(ops, diario_regimen):
    if len(ops) == 0:
        ops['regimen'] = []
        return ops
    mapa = diario_regimen.set_index('dia')['regimen']
    ops = ops.copy()
    ops['regimen'] = ops['dia'].map(mapa)
    return ops


def analizar(nombre_hipotesis, mercado, ops, d_m15):
    print(f"\n\n######## {nombre_hipotesis} -- {mercado} ########")
    print(f"Operaciones: {len(ops)}")
    if len(ops) == 0:
        print("  SIN OPERACIONES -- no se puede evaluar (revisar viabilidad).")
        return None
    print(f"  Direccion: {ops['direccion'].value_counts().to_dict()}")
    print("  Motivo salida:", ops['motivo_salida'].value_counts().to_dict())

    resultados = {}
    for extra in ESTRES_COSTE:
        etiqueta = "solo spread real" if extra == 0.0 else f"spread real + {extra:.0f}pt estres (slippage/comision)"
        ops_r = calcular_r_multiplos(ops, extra)
        m = metricas_en_r(ops_r)
        resultados[extra] = m
        print(f"\n--- {etiqueta} ---")
        print(f"  n={m['n']}  Media R={m['media_R']:+.4f}  PF={m['profit_factor']:.3f}  "
              f"%Acierto={m['pct_acierto']:.1f}%  Drawdown balance={m['max_drawdown_balance_R']:.2f}R")
        for anio, g in ops_r.groupby('anio'):
            mg = metricas_en_r(g)
            print(f"    {anio}: n={mg['n']}  Media R={mg['media_R']:+.4f}  PF={mg['profit_factor']:.3f}")
        if extra == 0.0 and 'regimen' in ops_r.columns and ops_r['regimen'].notna().any():
            resumen_por_regimen(ops_r)

    max_por_dia = ops.groupby('dia').size().max()
    eq = None
    if max_por_dia == 1:
        # Maximo 1 operacion por dia por construccion (primera señal del dia,
        # cerrada el mismo dia, nunca overnight) -- verificado, no asumido.
        # Sin solapamiento posible, el drawdown de equity (mark-to-market)
        # coincide exactamente con el de balance (cierres secuenciales).
        m0 = resultados[0.0]
        print(f"\n  Max operaciones simultaneas: 1 (verificado -- a lo sumo 1 señal/dia, sin overnight) "
              f"-> Drawdown equity = Drawdown balance = {m0['max_drawdown_balance_R']:.2f}R")
    else:
        eq = calcular_equity_simultanea(ops, d_m15)
        print(f"\n  Max posiciones simultaneas: {eq['max_posiciones_simultaneas']}  "
              f"Drawdown equity: {eq['max_drawdown_equity_R']:.2f}R ({eq['dia_max_drawdown'].date()})")

    rng = np.random.default_rng(SEED)
    media_real, media_ctrl, std_ctrl, z = control_direccion_aleatoria(ops, rng)
    print(f"  Control direccion aleatoria: media real={media_real:+.4f}  media aleatoria={media_ctrl:+.4f}  z={z:+.2f}")

    drawdown_equity = resultados[0.0]['max_drawdown_balance_R'] if eq is None else eq['max_drawdown_equity_R']
    return dict(n=len(ops), resultados=resultados, drawdown_equity=drawdown_equity, z_control=z)
