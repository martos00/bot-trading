"""
Backtest de Opening Range Breakout (ORB) en USTEC y US500. Reglas FIJAS,
pre-registradas antes de ver resultados -- no se optimiza nada.

DEFINICION (fija):
 - Rango de apertura = la propia vela M15 de 9:30-9:45 ET (High/Low de esa
   vela). Se localiza usando la correspondencia horaria servidor<->ET ya
   reconstruida semana a semana (ver research/overnight_intradia.py) --
   solo se opera en semanas con offset CONFIRMADO (>=20 dias de duracion).
 - Senal: la primera vela POSTERIOR a la de rango cuyo CIERRE supera el
   High (largo) o perfora el Low (corto) del rango. Solo cuenta la
   primera direccion que dispare ese dia (ORB clasico, una operacion/dia).
 - Entrada: Open de la vela SIGUIENTE a la de la señal (sin lookahead).
 - Stop-loss: el lado opuesto del propio rango de apertura.
 - Take-profit: 2x la distancia de riesgo (2R), medido desde la entrada.
 - Si ni SL ni TP se alcanzan, se cierra al Close de la vela de las 16:00
   ET (fin de sesion regular) -- nunca se mantiene overnight.
 - Si una vela toca SL y TP a la vez (ambiguedad de OHLC M15), se asume
   el peor caso (SL) -- convencion conservadora fija, no ajustada.
 - Riesgo: 0.5% de equity por operacion, dimensionado con el riesgo real
   (distancia entrada-SL), redondeo de volumen solo hacia abajo.
 - Costes: variable Spread real de cada vela + escenarios de comision/
   deslizamiento (no se inventa una cifra unica, point 4).
"""
import sys
from datetime import timedelta

import numpy as np
import pandas as pd

MINUTOS_SESION_REGULAR = 6 * 60 + 30
RIESGO_PCT = 0.005
EQUITY_INICIAL = 25000.0
TP_EN_R = 2.0
ESCENARIOS_COSTE = {
    'optimista_solo_spread': dict(comision_por_lote=0.0, slippage_puntos=0.0),
    'moderado': dict(comision_por_lote=3.0, slippage_puntos=1.0),
    'conservador': dict(comision_por_lote=7.0, slippage_puntos=3.0),
}


def cargar_y_verificar(path, nombre):
    df = pd.read_csv(path, sep=';', parse_dates=['TimestampServidor'],
                      date_format='%Y.%m.%d %H:%M:%S')
    df = df.reset_index(drop=True)
    assert df['TimestampServidor'].is_monotonic_increasing
    assert df['TimestampServidor'].duplicated().sum() == 0
    print(f"[OK] {nombre}: {len(df)} filas")
    return df


def clasificar_huecos(df):
    diffs = df['TimestampServidor'].diff()
    cat = pd.Series('intrasesion', index=df.index)
    for i in df.index[diffs > timedelta(minutes=15)]:
        dur = diffs.iloc[i]
        if dur <= timedelta(hours=2):
            cat.iloc[i] = 'cierre_diario'
        elif dur <= timedelta(hours=60):
            cat.iloc[i] = 'fin_de_semana'
        elif dur <= timedelta(hours=24 * 20):
            cat.iloc[i] = 'festivo_extendido'
        else:
            cat.iloc[i] = 'hueco_datos_ausentes'
    return cat


def detectar_apertura_caja_por_semana(df):
    d = df.copy()
    d['semana'] = d['TimestampServidor'].dt.to_period('W')
    d['slot'] = d['TimestampServidor'].dt.hour * 4 + d['TimestampServidor'].dt.minute // 15
    d['dow'] = d['TimestampServidor'].dt.dayofweek
    resultados = []
    for semana, g in d[d['dow'] < 5].groupby('semana'):
        perfil = g.groupby('slot')['TickVolume'].median().reindex(range(96))
        if perfil.isna().sum() > 20:
            continue
        perfil = perfil.ffill().bfill()
        saltos = perfil.diff()
        saltos.iloc[0] = perfil.iloc[0] - perfil.iloc[-1]
        resultados.append(dict(semana=str(semana), slot_apertura=saltos.idxmax()))
    return pd.DataFrame(resultados)


def construir_regimenes(tabla_semanal):
    regimenes = []
    actual_slot, inicio = None, None
    for _, row in tabla_semanal.iterrows():
        semana_inicio = pd.Period(row['semana'].split('/')[0]).start_time
        if row['slot_apertura'] != actual_slot:
            if actual_slot is not None:
                regimenes.append(dict(inicio=inicio, fin=semana_inicio, slot_apertura=actual_slot))
            actual_slot = row['slot_apertura']
            inicio = semana_inicio
    regimenes.append(dict(inicio=inicio, fin=pd.Timestamp('2027-01-01'), slot_apertura=actual_slot))
    return pd.DataFrame(regimenes)


def filtrar_regimenes_confiables(regimenes, dias_minimos=20):
    return pd.DataFrame([r for _, r in regimenes.iterrows() if (r['fin'] - r['inicio']).days >= dias_minimos])


def ejecutar_orb(df, categoria_hueco, regimenes_confiables, digitos, point):
    """Recorre dia a dia (solo con offset confirmado) y simula el ORB."""
    tiempos = df['TimestampServidor']
    idx_por_tiempo = {t: i for i, t in enumerate(tiempos)}
    n = len(df)
    dias = sorted(set(tiempos.dt.normalize()))

    operaciones = []
    descartes = dict(offset_no_confirmado=0, vela_rango_ausente=0, hueco_en_rango=0,
                      sin_senal_en_sesion=0, salida_ausente=0)

    for dia in dias:
        if dia.dayofweek >= 5:
            continue
        reg = regimenes_confiables[(regimenes_confiables['inicio'] <= dia) & (regimenes_confiables['fin'] > dia)]
        if len(reg) == 0:
            descartes['offset_no_confirmado'] += 1
            continue
        slot_apertura = int(reg.iloc[0]['slot_apertura'])
        hora_a, minuto_a = slot_apertura // 4, (slot_apertura % 4) * 15
        t_rango = dia + timedelta(hours=hora_a, minutes=minuto_a)         # vela 9:30-9:45
        t_cierre_sesion = t_rango + timedelta(minutes=MINUTOS_SESION_REGULAR) - timedelta(minutes=15)  # vela 15:45-16:00

        idx_rango = idx_por_tiempo.get(t_rango)
        idx_cierre_sesion = idx_por_tiempo.get(t_cierre_sesion)
        if idx_rango is None or idx_cierre_sesion is None or idx_cierre_sesion >= n:
            descartes['vela_rango_ausente'] += 1
            continue
        if categoria_hueco.iloc[idx_rango] != 'intrasesion' or categoria_hueco.iloc[idx_cierre_sesion] != 'intrasesion':
            descartes['hueco_en_rango'] += 1
            continue

        or_high = df['High'].iloc[idx_rango]
        or_low = df['Low'].iloc[idx_rango]
        rango_puntos = or_high - or_low
        if rango_puntos <= 0:
            descartes['vela_rango_ausente'] += 1
            continue

        # buscar la primera vela (entre idx_rango+1 y idx_cierre_sesion) cuyo CIERRE
        # supera or_high o perfora or_low -- la que ocurra antes, gana; si ninguna, no hay operacion
        idx_senal, direccion = None, None
        for j in range(idx_rango + 1, idx_cierre_sesion + 1):
            if categoria_hueco.iloc[j] != 'intrasesion':
                break  # hueco dentro de la sesion -- se corta la busqueda, no se adivina
            c = df['Close'].iloc[j]
            if c > or_high:
                idx_senal, direccion = j, 'largo'
                break
            if c < or_low:
                idx_senal, direccion = j, 'corto'
                break
        if idx_senal is None:
            descartes['sin_senal_en_sesion'] += 1
            continue

        idx_entrada = idx_senal + 1
        if idx_entrada > idx_cierre_sesion or idx_entrada >= n:
            descartes['salida_ausente'] += 1
            continue
        if categoria_hueco.iloc[idx_entrada] != 'intrasesion':
            descartes['salida_ausente'] += 1
            continue

        precio_entrada = df['Open'].iloc[idx_entrada]
        if direccion == 'largo':
            sl = or_low
            riesgo = precio_entrada - sl
            tp = precio_entrada + TP_EN_R * riesgo
        else:
            sl = or_high
            riesgo = sl - precio_entrada
            tp = precio_entrada - TP_EN_R * riesgo
        if riesgo <= 0:
            descartes['vela_rango_ausente'] += 1
            continue

        spread_entrada = df['Spread'].iloc[idx_entrada] * point

        resultado_precio, motivo_salida, idx_salida = None, None, None
        peor_flotante_r = 0.0  # excursion adversa maxima (equity intra-operacion), en unidades de R
        for k in range(idx_entrada, idx_cierre_sesion + 1):
            if categoria_hueco.iloc[k] != 'intrasesion' and k != idx_entrada:
                break
            hi, lo = df['High'].iloc[k], df['Low'].iloc[k]
            if direccion == 'largo':
                flotante_r_vela = (lo - precio_entrada) / riesgo
                toca_sl = lo <= sl
                toca_tp = hi >= tp
            else:
                flotante_r_vela = (precio_entrada - hi) / riesgo
                toca_sl = hi >= sl
                toca_tp = lo <= tp
            peor_flotante_r = min(peor_flotante_r, flotante_r_vela)
            if toca_sl:  # empate SL+TP en la misma vela -> gana SL (conservador, fijo)
                resultado_precio, motivo_salida, idx_salida = sl, 'SL', k
                break
            if toca_tp:
                resultado_precio, motivo_salida, idx_salida = tp, 'TP', k
                break
        if resultado_precio is None:
            # ni SL ni TP -- cerrar al Close de la vela de las 16:00 ET
            resultado_precio = df['Close'].iloc[idx_cierre_sesion]
            motivo_salida, idx_salida = 'CIERRE_SESION', idx_cierre_sesion

        ret_bruto_puntos = (resultado_precio - precio_entrada) if direccion == 'largo' else (precio_entrada - resultado_precio)

        operaciones.append(dict(
            dia=dia, anio=dia.year, direccion=direccion, or_high=or_high, or_low=or_low,
            rango_puntos=rango_puntos, precio_entrada=precio_entrada, sl=sl, tp=tp,
            resultado_precio=resultado_precio, motivo_salida=motivo_salida,
            ret_bruto_puntos=ret_bruto_puntos, riesgo_puntos=riesgo,
            # spread_entrada ya esta en UNIDADES DE PRECIO (Spread_broker * point),
            # misma unidad que ret_bruto_puntos -- NO volver a dividir por point aqui.
            spread_entrada_precio=spread_entrada,
            peor_flotante_r=peor_flotante_r,
        ))

    return pd.DataFrame(operaciones), descartes


# Auditoria: NO se asume valor de tick/contrato (no confirmado -- "Valor del tick"
# aparecio en 0 en la especificacion, probablemente porque el trading estaba
# desactivado en ese instante, no un cero real). Toda la contabilidad se hace en
# R-multiplos (normaliza el riesgo, sin necesitar saber el valor monetario del
# punto) y en puntos de indice crudos -- nunca convertidos a USD ficticio.
#
# Comision y slippage reales de la cuenta de fondeo NO estan confirmadas. Se
# presentan como ESTRES EXPLICITO en puntos de indice adicionales (no como si
# fueran cifras de bróker reales): 0 (solo spread real), 1 y 3 puntos extra.
EXTRA_PUNTOS_ESTRES = [0.0, 1.0, 3.0]


def calcular_r_multiplos(ops, extra_puntos):
    """R = (retorno bruto - spread real - estres adicional) / riesgo, todo en
    puntos de indice del propio instrumento -- sin conversion a dinero."""
    ops = ops.copy()
    ops['ret_neto_puntos'] = ops['ret_bruto_puntos'] - ops['spread_entrada_precio'] - extra_puntos
    ops['R'] = ops['ret_neto_puntos'] / ops['riesgo_puntos']
    return ops


def metricas_en_r(ops_r):
    if len(ops_r) == 0:
        return dict(n=0)
    r = ops_r['R'].values
    ganadoras = r[r > 0]
    perdedoras = r[r <= 0]
    pf = ganadoras.sum() / abs(perdedoras.sum()) if perdedoras.sum() != 0 else np.nan

    # Drawdown "balance": sobre la curva de R acumulado operacion a operacion (cierres)
    curva_balance = np.concatenate([[0], np.cumsum(r)])
    pico = np.maximum.accumulate(curva_balance)
    dd_balance = (pico - curva_balance)
    max_dd_balance_r = dd_balance.max()

    # Drawdown "equity": la PEOR excursion flotante de cada operacion individual,
    # antes de resolverse -- distinto de que la cuenta global toque ese minimo
    # simultaneamente, pero indica la exposicion real a perdida flotante por operacion.
    peor_flotante_individual = ops_r['peor_flotante_r'].min()
    media_peor_flotante = ops_r['peor_flotante_r'].mean()

    return dict(
        n=len(ops_r), suma_R=r.sum(), media_R=r.mean(), mediana_R=np.median(r),
        profit_factor=pf, pct_acierto=(r > 0).mean() * 100,
        max_drawdown_balance_R=max_dd_balance_r,
        peor_excursion_flotante_individual_R=peor_flotante_individual,
        media_excursion_flotante_R=media_peor_flotante,
    )


def resumen_instrumento(nombre, ops):
    print(f"\n\n######## {nombre} ########")
    print(f"Operaciones totales (todos los años): {len(ops)}")
    if len(ops) == 0:
        print("  SIN OPERACIONES -- no se puede evaluar.")
        return

    for extra in EXTRA_PUNTOS_ESTRES:
        etiqueta = f"spread real + {extra:.0f} puntos extra de estres (comision/slippage NO confirmados)" \
            if extra > 0 else "SOLO spread real (verificado), sin comision ni slippage adicional"
        print(f"\n--- Escenario: {etiqueta} ---")
        ops_r = calcular_r_multiplos(ops, extra)
        m = metricas_en_r(ops_r)
        print(f"  n={m['n']}  Suma R={m['suma_R']:+.2f}  Media R/operacion={m['media_R']:+.4f}  "
              f"Mediana R={m['mediana_R']:+.4f}  Profit Factor={m['profit_factor']:.3f}  "
              f"%Acierto={m['pct_acierto']:.1f}%")
        print(f"  Drawdown balance (cierres, maximo pico-valle en R): {m['max_drawdown_balance_R']:.2f}R")
        print(f"  Excursion flotante (equity intra-operacion): peor caso individual="
              f"{m['peor_excursion_flotante_individual_R']:.2f}R  media={m['media_excursion_flotante_R']:.3f}R")

        print("  Por año:")
        for anio, g in ops_r.groupby('anio'):
            mg = metricas_en_r(g)
            aviso = "  [2025 incompleto]" if anio == 2025 else ""
            print(f"    {anio}: n={mg['n']}  Suma R={mg['suma_R']:+.2f}  Media R={mg['media_R']:+.4f}  "
                  f"PF={mg['profit_factor']:.3f}  %Acierto={mg['pct_acierto']:.1f}%{aviso}")

    print("\n  Distribucion por motivo de salida:")
    print(ops['motivo_salida'].value_counts().to_dict())
    print(f"  Riesgo medio por operacion (puntos de indice): {ops['riesgo_puntos'].mean():.2f}")
    print(f"  Spread medio en el momento de entrada (puntos de indice): {ops['spread_entrada_precio'].mean():.3f}")
    print(f"  Spread medio como fraccion del riesgo (cuanto 'come' el spread de cada 1R): "
          f"{(ops['spread_entrada_precio']/ops['riesgo_puntos']).mean()*100:.1f}%")


def main(rutas):
    resultados = {}
    for nombre, path in rutas.items():
        df = cargar_y_verificar(path, nombre)
        categoria_hueco = clasificar_huecos(df)
        tabla = detectar_apertura_caja_por_semana(df)
        reg = construir_regimenes(tabla)
        reg_conf = filtrar_regimenes_confiables(reg)

        # Digits/point: US500 y USTEC tienen 2 decimales (Dígitos=2) -> point=0.01
        point = 0.01

        ops, descartes = ejecutar_orb(df, categoria_hueco, reg_conf, 2, point)
        print(f"\n[{nombre}] Descartes: {descartes}")
        resumen_instrumento(nombre, ops)
        resultados[nombre] = ops

    return resultados


if __name__ == '__main__':
    main({'USTEC': sys.argv[1], 'US500': sys.argv[2]})
