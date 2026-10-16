"""
Turtle System 2 (reglas CONGELADAS, sin tocar ningun parametro) sobre
el historico AMPLIADO descubierto en la fase de validacion del EA:
XAUUSD desde 2012-01-03, USTEC desde 2022-07-06, US500 desde
2012-08-06 (export crudo D1 directo del broker,
research/datos_raw_mt5/*_D1_Comparacion.csv).

DISCIPLINA: mismas reglas que research/estrategia_turtle_trading.py
(SISTEMAS['S2'], sin piramidacion) -- NINGUN parametro se ha tocado
tras ver estos resultados. El unico tratamiento de datos aplicado es
el ya documentado en el README ("Auditoria de calidad del historico
ampliado"): se excluye la unica vela degenerada de US500 (sabado
2018-04-07, 1 tick fantasma) y se marca explicitamente
INTEGRIDAD_DATOS_COMPROMETIDA en toda operacion cuyo periodo de
tenencia solape el hueco de datos 2025-07-16/2025-09-09 en USTEC/US500
-- no se descarta esa operacion, se reporta aparte.

SEPARACION DE PERIODOS (pedida explicitamente): "periodo ya usado"
es el que ya participo en la seleccion/evaluacion de esta estrategia
(XAUUSD >= 2015-01-01, USTEC/US500 >= 2023-01-03, igual que
datos_multiactivo.py). "Periodo nuevo" es el resto, anterior a esas
fechas -- evidencia que NO se uso para elegir ni para congelar las
reglas.
"""
import numpy as np
import pandas as pd

from datos_multiactivo import cargar_universo, UNIVERSO
from estrategia_turtle_trading import ejecutar_sistema
from orb_backtest import calcular_r_multiplos, metricas_en_r

FECHA_INICIO_YA_USADO = {'XAUUSD': '2015-01-01', 'USTEC': '2023-01-03', 'US500': '2023-01-03'}

# Fechas de entrada EXACTAS de las operaciones que ya aparecen en el backtest
# PUBLICADO (dataset mixto de datos_multiactivo.py) -- se usan para clasificar
# "ya_usado" vs "nuevo" por PRESENCIA REAL, no por un simple corte de fecha.
# Esto importa porque el backtest original tiene menos historial previo (menor
# "burn-in" del EMA/canales) que el export crudo del broker: una operación
# puede caer DESPUÉS de la fecha de corte nominal y aun así ser territorio
# "nuevo" si el backtest original, por falta de histórico previo suficiente,
# nunca pudo detectarla (ver README, "Auditoría de calidad del histórico
# ampliado" -- caso encontrado en USTEC 2023-02-02).
def fechas_ya_publicadas(sim):
    d = cargar_universo([sim])[sim].reset_index(drop=True)
    ops = ejecutar_sistema(d, 55, 20, UNIVERSO[sim]['point'], False)
    return set(pd.to_datetime(ops['dia']).dt.date)
HUECO_INICIO = pd.Timestamp('2025-07-16')
HUECO_FIN = pd.Timestamp('2025-09-09')
SEED = 20261016
REPETICIONES = 5000


def cargar_mt5_crudo(sim):
    d = pd.read_csv(f'datos_raw_mt5/{sim}_D1_Comparacion.csv', sep=';')
    d['dia'] = pd.to_datetime(d['Fecha'], format='%Y.%m.%d')
    d = d[['dia', 'Open', 'High', 'Low', 'Close', 'Spread']].sort_values('dia').reset_index(drop=True)
    if sim == 'US500':
        # vela degenerada: sabado 2018-04-07, 1 tick fantasma, O=H=L=C=cierre del viernes anterior
        antes = len(d)
        d = d[d['dia'] != pd.Timestamp('2018-04-07')].reset_index(drop=True)
        assert len(d) == antes - 1, "no se encontro la vela degenerada esperada"
    return d


def ejecutar_y_marcar(sim):
    d = cargar_mt5_crudo(sim)
    point = UNIVERSO[sim]['point']
    ops = ejecutar_sistema(d, 55, 20, point, False)
    ops['dia'] = pd.to_datetime(ops['dia'])
    ops['fecha_salida'] = pd.to_datetime(d['dia'].iloc[ops['idx_salida'].to_numpy()].to_numpy())
    ops['mercado'] = sim
    ops['integridad_comprometida'] = (ops['dia'] <= HUECO_FIN) & (ops['fecha_salida'] >= HUECO_INICIO)
    publicadas = fechas_ya_publicadas(sim)
    ops['periodo'] = np.where(ops['dia'].dt.date.isin(publicadas), 'ya_usado', 'nuevo')
    return ops


def imprimir_metricas(etiqueta, ops_r):
    m = metricas_en_r(ops_r)
    if m['n'] == 0:
        print(f"  {etiqueta}: sin operaciones")
        return m
    print(f"  {etiqueta}: n={m['n']}  Media R={m['media_R']:+.4f}  Suma R={m['suma_R']:+.2f}  "
          f"PF={m['profit_factor']:.3f}  %Acierto={m['pct_acierto']:.1f}%  "
          f"MaxDD(balance)={m['max_drawdown_balance_R']:.2f}R")
    return m


def cluster_bootstrap_anio(pool_r, rng, reps=REPETICIONES):
    anios = sorted(pool_r['anio'].unique())
    por_anio = {a: pool_r[pool_r['anio'] == a]['R'].to_numpy() for a in anios}
    medias = np.empty(reps)
    for b in range(reps):
        anios_resampleados = rng.choice(anios, size=len(anios), replace=True)
        valores = np.concatenate([por_anio[a] for a in anios_resampleados])
        medias[b] = valores.mean()
    return medias, len(anios)


def main():
    simbolos = ['XAUUSD', 'USTEC', 'US500']
    todas_ops = {sim: ejecutar_y_marcar(sim) for sim in simbolos}

    print("=" * 78)
    print("1. OPERACIONES TOTALES (histórico ampliado completo, reglas congeladas)")
    print("=" * 78)
    for sim in simbolos:
        ops = todas_ops[sim]
        print(f"\n{sim}: {len(ops)} operaciones totales "
              f"({ops['dia'].min().date()} -> {ops['dia'].max().date()})")
        print(f"  Periodo YA USADO (>= {FECHA_INICIO_YA_USADO[sim]}): {(ops['periodo']=='ya_usado').sum()} operaciones")
        print(f"  Periodo NUEVO (antes de {FECHA_INICIO_YA_USADO[sim]}): {(ops['periodo']=='nuevo').sum()} operaciones")
        n_comprometidas = ops['integridad_comprometida'].sum()
        if n_comprometidas:
            print(f"  >>> {n_comprometidas} operación(es) con INTEGRIDAD_DATOS_COMPROMETIDA (hueco 2025-07-16/2025-09-09)")

    print("\n" + "=" * 78)
    print("2. MÉTRICAS POR SÍMBOLO -- PERÍODO NUEVO (evidencia que NO se usó para elegir la estrategia)")
    print("=" * 78)
    r_nuevo = {}
    for sim in simbolos:
        ops = todas_ops[sim]
        nuevo = ops[ops['periodo'] == 'nuevo']
        nuevo_limpio = nuevo[~nuevo['integridad_comprometida']]
        print(f"\n{sim} (nuevo, {len(nuevo)} operaciones brutas, "
              f"{nuevo['integridad_comprometida'].sum()} comprometidas excluidas de las métricas):")
        ops_r = calcular_r_multiplos(nuevo_limpio, 0.0)
        r_nuevo[sim] = ops_r
        imprimir_metricas('[solo spread real]', ops_r)
        for extra in [1.0, 3.0]:
            ops_r_estres = calcular_r_multiplos(nuevo_limpio, extra)
            imprimir_metricas(f'[spread + {extra:.0f} estrés]', ops_r_estres)

        print("  Por año:")
        for anio, g in ops_r.groupby('anio'):
            m = metricas_en_r(g)
            print(f"    {anio}: n={m['n']}  Media R={m['media_R']:+.4f}  PF={m['profit_factor']:.3f}")

        print("  Largo vs Corto:")
        for direccion, g in ops_r.groupby('direccion'):
            m = metricas_en_r(g)
            print(f"    {direccion}: n={m['n']}  Media R={m['media_R']:+.4f}  PF={m['profit_factor']:.3f}  "
                  f"%Acierto={m['pct_acierto']:.1f}%")

        if len(ops_r) >= 3:
            orden = ops_r.sort_values('R', ascending=False)
            print("  Sensibilidad a valores extremos:")
            imprimir_metricas('    todas', ops_r)
            imprimir_metricas('    excl. mejor trade', orden.iloc[1:])
            if len(orden) >= 3:
                imprimir_metricas('    excl. 3 mejores', orden.iloc[3:])

        rng = np.random.default_rng(SEED)
        if ops_r['R'].to_numpy().size and nuevo_limpio['direccion'].notna().any():
            # control direccion aleatoria simple, reutilizando spread/riesgo ya calculados
            riesgos = nuevo_limpio['riesgo_puntos'].to_numpy()
            ret_con_signo = nuevo_limpio['ret_bruto_puntos'].to_numpy() * np.where(nuevo_limpio['direccion'] == 'largo', 1, -1)
            spreads = nuevo_limpio['spread_entrada_precio'].to_numpy()
            medias_ctrl = []
            for _ in range(2000):
                dir_rnd = rng.choice([1, -1], size=len(nuevo_limpio))
                ret_sim = ret_con_signo * dir_rnd - spreads
                medias_ctrl.append((ret_sim / riesgos).mean())
            medias_ctrl = np.array(medias_ctrl)
            media_real = ops_r['R'].mean()
            z = (media_real - medias_ctrl.mean()) / medias_ctrl.std() if medias_ctrl.std() > 0 else np.nan
            print(f"  Control dirección aleatoria: media real={media_real:+.4f}  media aleatoria={medias_ctrl.mean():+.4f}  z={z:+.2f}")

        # benchmark simple: comprar y mantener sobre el mismo periodo nuevo (no ajustado por volatilidad,
        # solo contexto -- el motor Turtle no usa vol-targeting, se declara esta limitación)
        d = cargar_mt5_crudo(sim)
        d_nuevo = d[d['dia'] < pd.Timestamp(FECHA_INICIO_YA_USADO[sim])]
        if len(d_nuevo) > 1:
            ret_bh = d_nuevo['Close'].iloc[-1] / d_nuevo['Close'].iloc[0] - 1.0
            anios_bh = (d_nuevo['dia'].iloc[-1] - d_nuevo['dia'].iloc[0]).days / 365.25
            ret_anual_bh = (1 + ret_bh) ** (1 / anios_bh) - 1 if anios_bh > 0 else np.nan
            print(f"  Referencia comprar-y-mantener (mismo periodo nuevo, SIN ajuste de riesgo): "
                  f"ret. acumulado={ret_bh*100:+.1f}%  ret. anualizado={ret_anual_bh*100:+.2f}%")

    print("\n" + "=" * 78)
    print("3. POOLED (3 mercados) -- PERÍODO NUEVO, excluyendo operaciones con integridad comprometida")
    print("=" * 78)
    pool_nuevo = pd.concat([r_nuevo[s] for s in simbolos], ignore_index=True)
    imprimir_metricas('Pooled nuevo (solo spread real)', pool_nuevo)
    print("  Por año (pooled):")
    for anio, g in pool_nuevo.groupby('anio'):
        m = metricas_en_r(g)
        print(f"    {anio}: n={m['n']}  Media R={m['media_R']:+.4f}  PF={m['profit_factor']:.3f}")

    rng = np.random.default_rng(SEED)
    medias_cluster, n_clusters = cluster_bootstrap_anio(pool_nuevo, rng)
    lo, hi = np.percentile(medias_cluster, 2.5), np.percentile(medias_cluster, 97.5)
    print(f"\n  Cluster-bootstrap por año (n_clusters={n_clusters}): IC95%=[{lo:+.4f}, {hi:+.4f}]  "
          f"P(media<=0)={(medias_cluster<=0).mean()*100:.1f}%")

    # Independencia entre mercados en el periodo NUEVO: fechas de entrada USTEC vs US500
    ustec_fechas = set(r_nuevo['USTEC']['dia'].dt.date) if 'USTEC' in r_nuevo else set()
    us500_fechas = set(r_nuevo['US500']['dia'].dt.date)
    coincidencias = ustec_fechas & us500_fechas
    print(f"\n  Fechas de entrada EXACTAMENTE coincidentes USTEC/US500 en el periodo nuevo: {len(coincidencias)} "
          f"de {len(ustec_fechas)}/{len(us500_fechas)} respectivamente")

    print("\n" + "=" * 78)
    print("4. COMBINADO (período ya usado + período nuevo), por símbolo -- la muestra TOTAL disponible hoy")
    print("=" * 78)
    for sim in simbolos:
        ops = todas_ops[sim]
        limpio = ops[~ops['integridad_comprometida']]
        ops_r = calcular_r_multiplos(limpio, 0.0)
        imprimir_metricas(f'{sim} combinado (ex. comprometidas)', ops_r)

    print("\n" + "=" * 78)
    print("5. Operaciones con INTEGRIDAD_DATOS_COMPROMETIDA (reportadas aparte, no mezcladas)")
    print("=" * 78)
    for sim in simbolos:
        ops = todas_ops[sim]
        comp = ops[ops['integridad_comprometida']]
        if len(comp):
            ops_r_comp = calcular_r_multiplos(comp, 0.0)
            print(f"\n{sim}:")
            print(ops_r_comp[['dia', 'direccion', 'precio_entrada', 'fecha_salida', 'motivo_salida', 'R']].to_string(index=False))


if __name__ == '__main__':
    main()
