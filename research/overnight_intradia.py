"""
Analisis overnight vs intradia de US500 y USTEC. NO es un EA, NO define
SL/TP/entradas operativas todavia -- solo comprobacion descriptiva de si
existe la anomalia, y una primera estimacion neta de costes.

Metodologia de reconstruccion horaria (punto 3): en vez de asumir el
offset actual del servidor, se detecta semana a semana el instante de
servidor en que el TickVolume da el salto caracteristico de apertura de
caja de EEUU (9:30 ET) -- la sesion de efectivo de EEUU concentra tanto
volumen que ese salto es, con mucho, el mayor de todo el dia para un
indice de EEUU. Se repite cada semana de 2023 a 2026, lo que permite ver
los cambios de +/-60 min (DST) directamente en los datos, sin asumir que
el offset de hoy valga para 2023.
"""
import sys
from datetime import timedelta

import numpy as np
import pandas as pd

MINUTOS_SESION_REGULAR = 6 * 60 + 30  # 9:30 -> 16:00 ET = 6h30
SEED = 42
REPETICIONES_BOOTSTRAP = 1500


def cargar_y_verificar(path, nombre):
    df = pd.read_csv(path, sep=';', parse_dates=['TimestampServidor'],
                      date_format='%Y.%m.%d %H:%M:%S')
    df = df.reset_index(drop=True)
    assert df['TimestampServidor'].is_monotonic_increasing
    assert df['TimestampServidor'].duplicated().sum() == 0
    assert (df['High'] >= df[['Open', 'Close']].max(axis=1)).all()
    assert (df['Low'] <= df[['Open', 'Close']].min(axis=1)).all()
    print(f"[OK] {nombre}: {len(df)} filas, {df['TimestampServidor'].iloc[0]} -> {df['TimestampServidor'].iloc[-1]}")
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
            cat.iloc[i] = 'hueco_datos_ausentes'  # el tramo de 55 dias de 2025, tratado aparte
    return cat


def detectar_apertura_caja_por_semana(df):
    """Punto 3: detecta, semana a semana, el time-of-day de servidor donde
    el TickVolume medio da el mayor salto -- proxy de la apertura de caja
    de EEUU (9:30 ET), sin asumir ningun offset de antemano."""
    d = df.copy()
    d['semana'] = d['TimestampServidor'].dt.to_period('W')
    d['slot'] = d['TimestampServidor'].dt.hour * 4 + d['TimestampServidor'].dt.minute // 15
    d['dow'] = d['TimestampServidor'].dt.dayofweek

    resultados = []
    for semana, g in d[d['dow'] < 5].groupby('semana'):  # solo lunes-viernes
        perfil = g.groupby('slot')['TickVolume'].median()
        perfil = perfil.reindex(range(96))
        if perfil.isna().sum() > 20:  # semana con demasiados huecos (ej. la de 55 dias), se omite
            continue
        perfil = perfil.ffill().bfill()
        saltos = perfil.diff()
        saltos.iloc[0] = perfil.iloc[0] - perfil.iloc[-1]  # circular (medianoche)
        slot_apertura = saltos.idxmax()
        # salto de cierre: mayor caida, buscada en una ventana posterior razonable (no circular
        # para evitar confundir con la propia apertura)
        resultados.append(dict(semana=str(semana), slot_apertura=slot_apertura,
                                hora_apertura=f"{slot_apertura//4:02d}:{(slot_apertura%4)*15:02d}",
                                magnitud_salto=saltos.max()))
    return pd.DataFrame(resultados)


def construir_regimenes(tabla_semanal):
    """Agrupa semanas consecutivas con el mismo slot de apertura en
    regimenes [fecha_inicio, fecha_fin) -- cambios de regimen = DST."""
    regimenes = []
    actual_slot = None
    inicio = None
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
    """Solo se confia en un regimen si dura al menos `dias_minimos` --
    los tramos cortos/ruidosos (deteccion inestable) se marcan como NO
    confirmados y se excluyen del analisis en vez de adivinar."""
    confiables = []
    for _, r in regimenes.iterrows():
        dur = (r['fin'] - r['inicio']).days
        if dur >= dias_minimos:
            confiables.append(r)
    return pd.DataFrame(confiables)


def construir_sesiones(df, categoria_hueco, regimenes_confiables):
    """Para cada dia habil cubierto por un regimen CONFIRMADO, localiza
    las velas de apertura (9:30 ET) y cierre (16:00 ET) de caja via el
    slot de apertura de ese regimen, y construye devoluciones overnight/
    intradia SOLO cuando todas las velas necesarias existen de verdad
    (sin rellenar) y ninguna cae dentro de un hueco catalogado."""
    tiempos = df['TimestampServidor']
    idx_por_tiempo = {t: i for i, t in enumerate(tiempos)}
    n = len(df)

    filas = []
    dias = sorted(set(tiempos.dt.normalize()))

    for dia in dias:
        dow = dia.dayofweek
        if dow >= 5:
            continue
        reg = regimenes_confiables[(regimenes_confiables['inicio'] <= dia) &
                                    (regimenes_confiables['fin'] > dia)]
        if len(reg) == 0:
            continue  # offset no confirmado para esta fecha -- se excluye, no se adivina
        slot_apertura = int(reg.iloc[0]['slot_apertura'])
        minuto_apertura = (slot_apertura % 4) * 15
        hora_apertura = slot_apertura // 4
        t_apertura = dia + timedelta(hours=hora_apertura, minutes=minuto_apertura)
        t_cierre = t_apertura + timedelta(minutes=MINUTOS_SESION_REGULAR)

        idx_apertura = idx_por_tiempo.get(t_apertura)
        idx_cierre = idx_por_tiempo.get(t_cierre)
        if idx_apertura is None or idx_cierre is None:
            continue  # vela ausente en ese instante exacto -- no se interpola, se descarta el dia

        if categoria_hueco.iloc[idx_apertura] != 'intrasesion' or categoria_hueco.iloc[idx_cierre] != 'intrasesion':
            continue  # cae justo en un hueco catalogado -- fuera

        filas.append(dict(dia=dia, dow=dow, idx_apertura=idx_apertura, idx_cierre=idx_cierre,
                           open_0930=df['Open'].iloc[idx_apertura], close_1600=df['Close'].iloc[idx_cierre],
                           anio=dia.year))
    return pd.DataFrame(filas)


def calcular_retornos(sesiones):
    """Intradia = Close(16:00) / Open(9:30) del mismo dia (sin lookahead,
    ambos precios ya estaban determinados en su propio instante).
    Overnight = Open(9:30) del SIGUIENTE dia habil / Close(16:00) de hoy
    -- separado explicitamente fin de semana (viernes->lunes) del resto."""
    sesiones = sesiones.sort_values('dia').reset_index(drop=True)
    filas = []
    for i in range(len(sesiones) - 1):
        hoy = sesiones.iloc[i]
        manana = sesiones.iloc[i + 1]
        dias_entre = (manana['dia'] - hoy['dia']).days
        if dias_entre > 4:
            continue  # salto mayor que un fin de semana normal -- posible festivo/hueco, se excluye
        tipo_noche = 'finde' if hoy['dow'] == 4 else 'entre_semana'
        ret_intradia = np.log(hoy['close_1600'] / hoy['open_0930'])
        ret_overnight = np.log(manana['open_0930'] / hoy['close_1600'])
        filas.append(dict(dia=hoy['dia'], anio=hoy['anio'], tipo_noche=tipo_noche,
                           ret_intradia=ret_intradia, ret_overnight=ret_overnight))
    return pd.DataFrame(filas)


def bootstrap_bloques_ic(valores, bloque=10, repeticiones=REPETICIONES_BOOTSTRAP, seed=SEED):
    valores = np.asarray(valores, dtype=float)
    valores = valores[~np.isnan(valores)]
    n = len(valores)
    if n < bloque * 2:
        return (np.nan, np.nan)
    rng = np.random.default_rng(seed)
    n_bloques = int(np.ceil(n / bloque))
    max_inicio = n - bloque
    medias = np.empty(repeticiones)
    for b in range(repeticiones):
        inicios = rng.integers(0, max_inicio + 1, size=n_bloques)
        medias[b] = np.concatenate([valores[s:s + bloque] for s in inicios])[:n].mean()
    return np.percentile(medias, 2.5), np.percentile(medias, 97.5)


def resumen_retornos(ret, nombre_instrumento):
    print(f"\n######## {nombre_instrumento} ########")
    for anio, g in ret.groupby('anio'):
        n_total = len(g)
        print(f"\n--- Año {anio} (n sesiones={n_total}) ---")
        if anio == 2025:
            print("  AVISO: 2025 NO es un año completo (hueco de 55 dias jul-sep ya excluido).")
        for etiqueta, sub in [('TODAS', g), ('entre semana (lun-jue noche)', g[g['tipo_noche']=='entre_semana']),
                               ('fin de semana (vie->lun)', g[g['tipo_noche']=='finde'])]:
            if len(sub) < 5:
                print(f"  {etiqueta}: n insuficiente ({len(sub)})")
                continue
            m_o, med_o = sub['ret_overnight'].mean(), sub['ret_overnight'].median()
            m_i, med_i = sub['ret_intradia'].mean(), sub['ret_intradia'].median()
            ic_o = bootstrap_bloques_ic(sub['ret_overnight'].values)
            ic_i = bootstrap_bloques_ic(sub['ret_intradia'].values)
            print(f"  {etiqueta} (n={len(sub)}):")
            print(f"    overnight: media={m_o:+.5f} mediana={med_o:+.5f} IC95%={[round(x,5) for x in ic_o]}")
            print(f"    intradia : media={m_i:+.5f} mediana={med_i:+.5f} IC95%={[round(x,5) for x in ic_i]}")


def main(rutas):
    datos = {}
    categorias = {}
    for nombre, path in rutas.items():
        df = cargar_y_verificar(path, nombre)
        datos[nombre] = df
        categorias[nombre] = clasificar_huecos(df)

    print("\n### Punto 1: tramos de datos ausentes (no se interpolan, no se cruzan en retornos) ###")
    for nombre, cat in categorias.items():
        n_ausentes = (cat == 'hueco_datos_ausentes').sum()
        print(f"  {nombre}: {n_ausentes} hueco(s) de 'datos ausentes' (>20 dias) catalogado(s)")

    print("\n### Punto 3: deteccion semanal del instante de apertura de caja (TickVolume) ###")
    regimenes = {}
    regimenes_confiables = {}
    for nombre, df in datos.items():
        tabla = detectar_apertura_caja_por_semana(df)
        reg = construir_regimenes(tabla)
        regimenes[nombre] = reg
        reg_conf = filtrar_regimenes_confiables(reg)
        regimenes_confiables[nombre] = reg_conf
        print(f"\n  {nombre}: {len(reg)} regimenes brutos, {len(reg_conf)} CONFIRMADOS (>=20 dias de duracion)")
        print(f"  Cobertura temporal confirmada: {reg_conf['inicio'].min()} -> {reg_conf['fin'].max()}" if len(reg_conf) else "  SIN regimenes confiables")
        dias_cubiertos = sum((r['fin'] - r['inicio']).days for _, r in reg_conf.iterrows())
        dias_totales = (df['TimestampServidor'].max() - df['TimestampServidor'].min()).days
        print(f"  {dias_cubiertos} de {dias_totales} dias del rango total quedan con offset confirmado "
              f"({dias_cubiertos/dias_totales*100:.1f}%)")

    print("\n\n################ INFORME: OVERNIGHT vs INTRADIA ################")
    print("Definicion (punto 4): intradia = Close(vela que termina a 16:00 ET)/Open(vela que empieza "
          "a 9:30 ET); overnight = Open(9:30 ET dia siguiente)/Close(16:00 ET dia actual). Ambos precios "
          "ya estaban fijados en su propio instante -- sin lookahead. Analisis BRUTO primero (punto 6).")

    todas_sesiones = {}
    todos_retornos = {}
    for nombre, df in datos.items():
        sesiones = construir_sesiones(df, categorias[nombre], regimenes_confiables[nombre])
        ret = calcular_retornos(sesiones)
        todas_sesiones[nombre] = sesiones
        todos_retornos[nombre] = ret
        resumen_retornos(ret, nombre)

    return datos, categorias, regimenes, regimenes_confiables, todos_retornos


if __name__ == '__main__':
    rutas = {'US500': sys.argv[1], 'USTEC': sys.argv[2]}
    main(rutas)
