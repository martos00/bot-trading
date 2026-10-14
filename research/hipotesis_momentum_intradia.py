"""
FASE 1 -- Identificar la ventaja (NO construir estrategia todavia).

Hipotesis seleccionada de las 3 candidatas (ver README): "Market Intraday
Momentum" (Gao, Han, Xu & Zhou, Journal of Financial Economics-type
hallazgo, 2018) -- el retorno de la PRIMERA media hora de la sesion
regular predice, con el MISMO signo, el retorno de la ULTIMA media hora
de la MISMA sesion. Fundamento: flujo institucional de rebalanceo a
final de dia ("smart money" opera tarde) que continua la direccion ya
marcada por el mercado esa mañana.

ALCANCE DE DATOS (limitacion real, no inventada): solo USTEC y US500 --
XAUUSD se EXCLUYE de esta hipotesis porque no existe una reconstruccion
horaria confiable de su sesion (el metodo robusto de salto de
TickVolume, que SI funciona bien en USTEC/US500, da en XAUUSD solo
43.6% de cobertura confirmada con regimenes inestables -- comprobado
directamente antes de definir esta hipotesis, no asumido). Gold cotiza
casi 24h sin una apertura de caja unica como el NYSE, asi que esto es
coherente con la naturaleza del instrumento, no un fallo de metodo.

PRE-REGISTRO (fijado antes de ejecutar):
 - Sesion: RTH 9:30-16:00 ET, misma reconstruccion horaria ya validada
   (salto semanal de TickVolume), solo dias con offset CONFIRMADO.
 - "Primera media hora": retorno Close[vela 9:45-10:00]/Open[vela
   9:30-9:45] - 1 (las dos primeras velas M15 de la sesion).
 - "Ultima media hora": retorno Close[vela 15:45-16:00]/Open[vela
   15:30-15:45] - 1 (las dos ultimas velas M15 de la sesion).
 - Ambos retornos son del MISMO dia, ya realizados -- no hay entrada ni
   salida que ejecutar todavia (fase de identificacion, no de
   estrategia), por lo que no aplica la convencion de "entrar en el
   Open siguiente": aqui solo se mide la relacion estadistica entre dos
   tramos de precio ya observados.
 - Division en grupos (sin umbral que optimizar): tratamiento = dias
   con retorno de apertura > 0; control = dias con retorno de apertura
   <= 0. Se prueba si el retorno de cierre promedio es mayor en el
   grupo de apertura positiva.
 - Cada dia aporta UNA sola observacion (ret_apertura, ret_cierre) --
   a diferencia del estudio RSI(2), aqui NO hay horizontes solapados
   entre dias distintos.
 - Incertidumbre: bootstrap de bloques de 10 dias consecutivos (misma
   convencion del proyecto) para la diferencia de medias Y para el
   coeficiente de correlacion de Pearson.
"""
import sys
from datetime import timedelta

import numpy as np
import pandas as pd

from orb_backtest import (
    MINUTOS_SESION_REGULAR,
    cargar_y_verificar, clasificar_huecos, detectar_apertura_caja_por_semana,
    construir_regimenes, filtrar_regimenes_confiables,
)

BLOQUE_BOOTSTRAP = 10
REPETICIONES_BOOTSTRAP = 2000
SEED = 20261014


def ejecutar_momentum_intradia(df, categoria_hueco, regimenes_confiables):
    tiempos = df['TimestampServidor']
    idx_por_tiempo = {t: i for i, t in enumerate(tiempos)}
    n = len(df)
    dias = sorted(set(tiempos.dt.normalize()))

    filas = []
    for dia in dias:
        if dia.dayofweek >= 5:
            continue
        reg = regimenes_confiables[(regimenes_confiables['inicio'] <= dia) & (regimenes_confiables['fin'] > dia)]
        if len(reg) == 0:
            continue
        slot = int(reg.iloc[0]['slot_apertura'])
        h, m = slot // 4, (slot % 4) * 15
        t_apertura = dia + timedelta(hours=h, minutes=m)
        t_cierre = t_apertura + timedelta(minutes=MINUTOS_SESION_REGULAR) - timedelta(minutes=15)

        idx_apertura = idx_por_tiempo.get(t_apertura)
        idx_cierre = idx_por_tiempo.get(t_cierre)
        if idx_apertura is None or idx_cierre is None or idx_cierre >= n or idx_cierre - idx_apertura < 2:
            continue
        if (categoria_hueco.iloc[idx_apertura:idx_cierre + 1] != 'intrasesion').any():
            continue

        ret_apertura = df['Close'].iloc[idx_apertura + 1] / df['Open'].iloc[idx_apertura] - 1.0
        ret_cierre = df['Close'].iloc[idx_cierre] / df['Open'].iloc[idx_cierre - 1] - 1.0
        filas.append(dict(dia=dia, anio=dia.year, ret_apertura=ret_apertura, ret_cierre=ret_cierre))

    return pd.DataFrame(filas).sort_values('dia').reset_index(drop=True)


def bootstrap_diferencia_bloques(tabla, col_valor, col_grupo, bloque=BLOQUE_BOOTSTRAP,
                                  repeticiones=REPETICIONES_BOOTSTRAP, seed=SEED):
    valores = tabla[col_valor].to_numpy(dtype=float)
    grupo = tabla[col_grupo].to_numpy(dtype=bool)
    n = len(valores)
    if n < bloque * 2:
        return (np.nan, np.nan, 0)
    rng = np.random.default_rng(seed)
    n_bloques = int(np.ceil(n / bloque))
    max_inicio = n - bloque
    diffs = []
    for _ in range(repeticiones):
        inicios = rng.integers(0, max_inicio + 1, size=n_bloques)
        idx = np.concatenate([np.arange(s, s + bloque) for s in inicios])[:n]
        v, g = valores[idx], grupo[idx]
        if g.sum() == 0 or (~g).sum() == 0:
            continue
        diffs.append(v[g].mean() - v[~g].mean())
    if not diffs:
        return (np.nan, np.nan, 0)
    diffs = np.array(diffs)
    return np.percentile(diffs, 2.5), np.percentile(diffs, 97.5), len(diffs)


def bootstrap_correlacion_bloques(tabla, col_x, col_y, bloque=BLOQUE_BOOTSTRAP,
                                   repeticiones=REPETICIONES_BOOTSTRAP, seed=SEED):
    x = tabla[col_x].to_numpy(dtype=float)
    y = tabla[col_y].to_numpy(dtype=float)
    n = len(x)
    if n < bloque * 2:
        return (np.nan, np.nan)
    rng = np.random.default_rng(seed + 1)
    n_bloques = int(np.ceil(n / bloque))
    max_inicio = n - bloque
    corrs = []
    for _ in range(repeticiones):
        inicios = rng.integers(0, max_inicio + 1, size=n_bloques)
        idx = np.concatenate([np.arange(s, s + bloque) for s in inicios])[:n]
        corrs.append(np.corrcoef(x[idx], y[idx])[0, 1])
    corrs = np.array(corrs)
    return np.percentile(corrs, 2.5), np.percentile(corrs, 97.5)


def analizar(nombre, path):
    print(f"\n\n################ MOMENTUM INTRADIA -- {nombre} ################")
    df = cargar_y_verificar(path, nombre)
    categoria_hueco = clasificar_huecos(df)
    tabla_reg = detectar_apertura_caja_por_semana(df)
    reg = construir_regimenes(tabla_reg)
    reg_conf = filtrar_regimenes_confiables(reg)

    tabla = ejecutar_momentum_intradia(df, categoria_hueco, reg_conf)
    print(f"  Dias con sesion valida y offset confirmado: {len(tabla)}")

    tabla['tratamiento'] = tabla['ret_apertura'] > 0
    trat = tabla[tabla['tratamiento']]
    ctrl = tabla[~tabla['tratamiento']]
    print(f"  Apertura positiva (tratamiento): n={len(trat)}  media cierre={trat['ret_cierre'].mean()*100:+.4f}%  "
          f"mediana={trat['ret_cierre'].median()*100:+.4f}%")
    print(f"  Apertura <=0 (control):          n={len(ctrl)}  media cierre={ctrl['ret_cierre'].mean()*100:+.4f}%  "
          f"mediana={ctrl['ret_cierre'].median()*100:+.4f}%")
    efecto = trat['ret_cierre'].mean() - ctrl['ret_cierre'].mean()
    lo, hi, n_rep = bootstrap_diferencia_bloques(tabla, 'ret_cierre', 'tratamiento')
    sig = not (lo <= 0 <= hi) if not np.isnan(lo) else False
    print(f"  Efecto (tratamiento-control) = {efecto*100:+.4f} pp   "
          f"IC95% diferencia (bloques conjuntos, {n_rep} rep.) = [{lo*100:+.4f} pp, {hi*100:+.4f} pp]  "
          f"{'-> EXCLUYE CERO' if sig else '-> CRUZA CERO (no significativo)'}")

    corr = tabla['ret_apertura'].corr(tabla['ret_cierre'])
    clo, chi = bootstrap_correlacion_bloques(tabla, 'ret_apertura', 'ret_cierre')
    print(f"  Correlacion de Pearson (ret_apertura, ret_cierre) = {corr:+.4f}   "
          f"IC95% bootstrap = [{clo:+.4f}, {chi:+.4f}]")

    print("  Por año:")
    for anio, g in tabla.groupby('anio'):
        t_a = g[g['tratamiento']]['ret_cierre']
        c_a = g[~g['tratamiento']]['ret_cierre']
        aviso = '  [incompleto]' if anio in (2023, 2025) else ''
        print(f"    {anio}: n_trat={len(t_a)} media={t_a.mean()*100:+.4f}%  "
              f"n_ctrl={len(c_a)} media={c_a.mean()*100:+.4f}%  corr={g['ret_apertura'].corr(g['ret_cierre']):+.4f}{aviso}")

    return dict(efecto=efecto, lo=lo, hi=hi, sig=sig, corr=corr, clo=clo, chi=chi, n=len(tabla))


def main(rutas):
    resumen = {}
    for nombre, path in rutas.items():
        resumen[nombre] = analizar(nombre, path)
    print("\n\n################ RESUMEN ################")
    for nombre, r in resumen.items():
        print(f"  {nombre}: efecto={r['efecto']*100:+.4f}pp  IC95%=[{r['lo']*100:+.4f},{r['hi']*100:+.4f}]  "
              f"{'SIGNIFICATIVO' if r['sig'] else 'no significativo'}  corr={r['corr']:+.4f}  n={r['n']}")
    return resumen


if __name__ == '__main__':
    main({'USTEC': sys.argv[1], 'US500': sys.argv[2]})
