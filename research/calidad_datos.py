"""
Control de calidad de datos y de resultados de backtest -- construido
tras encontrar (sin que ningún backtest anterior lo detectara) un
hueco de 38 días hábiles sin ninguna vela en USTEC/US500
(16-jul a 9-sep-2025), que afectaba directamente a las dos operaciones
más grandes del resultado ya publicado de Turtle System 2.

PRINCIPIO RECTOR (pedido explícitamente): un problema de integridad
GRAVE debe marcar el resultado como NO VÁLIDO -- nunca debe continuar
en silencio como si los datos fueran completos y fiables.

Este módulo NO decide automáticamente qué hacer con un resultado
inválido (excluir, re-ejecutar, pedir más datos) -- eso depende del
contexto de cada investigación. Solo DETECTA y REPORTA, de forma
explícita y verificable, para que la decisión se tome con conocimiento
de causa.
"""
import numpy as np
import pandas as pd

UMBRAL_HUECO_DIAS_HABILES = 3
UMBRAL_VELA_ARTIFICIAL_FRACCION_RANGO = 0.35   # rango High-Low < 35% de la mediana => sospechosa
UMBRAL_RETORNO_DIARIO_EXTREMO = 0.15           # |retorno log diario| > 15% => revisar manualmente
UMBRAL_RIESGO_MINIMO_FRACCION_PRECIO = 0.0001  # riesgo_puntos / precio_entrada por debajo de esto => denominador degenerado


class ResultadoAuditoria:
    """Acumula hallazgos de una auditoría. es_valido() es False en
    cuanto hay al menos un problema GRAVE -- los avisos (leves) no
    invalidan el resultado por sí solos, pero se reportan igualmente."""

    def __init__(self, nombre):
        self.nombre = nombre
        self.problemas_graves = []   # lista de strings
        self.avisos = []             # lista de strings
        self.huecos = []             # lista de dict(inicio, fin, dias_habiles_saltados)
        self.operaciones_comprometidas = None  # Series booleana, si se auditó un backtest

    def grave(self, msg):
        self.problemas_graves.append(msg)

    def aviso(self, msg):
        self.avisos.append(msg)

    def es_valido(self):
        return len(self.problemas_graves) == 0

    def imprimir(self):
        estado = "VÁLIDO" if self.es_valido() else "NO VÁLIDO -- revisar antes de usar este resultado"
        print(f"\n[AUDITORÍA DE CALIDAD -- {self.nombre}] Estado: {estado}")
        if self.problemas_graves:
            print("  PROBLEMAS GRAVES:")
            for p in self.problemas_graves:
                print(f"    - {p}")
        if self.avisos:
            print("  Avisos (no invalidan el resultado, pero conviene revisarlos):")
            for a in self.avisos:
                print(f"    - {a}")
        if not self.problemas_graves and not self.avisos:
            print("  Sin hallazgos.")


# ======================================================================
# CHEQUEOS A NIVEL DE HISTÓRICO (no requieren operaciones de backtest)
# ======================================================================

def detectar_duplicados_y_desorden(diario, col_fecha='dia'):
    """(5) Datos duplicados o desordenados."""
    problemas = []
    fechas = diario[col_fecha]
    n_dup = fechas.duplicated().sum()
    if n_dup > 0:
        problemas.append(f"{n_dup} fecha(s) duplicada(s)")
    if not fechas.is_monotonic_increasing:
        problemas.append("las fechas no están en orden estrictamente creciente")
    return problemas


def detectar_velas_invalidas_y_precios_anomalos(diario):
    """(3) Precios anómalos: OHLC inconsistente, precios <= 0, retornos diarios extremos."""
    problemas = []
    invalidas = (diario['High'] < diario['Low']) | (diario['High'] < diario['Open']) | \
                (diario['High'] < diario['Close']) | (diario['Low'] > diario['Open']) | \
                (diario['Low'] > diario['Close'])
    if invalidas.sum() > 0:
        problemas.append(f"{invalidas.sum()} vela(s) con High/Low inconsistente con Open/Close")
    no_positivos = (diario[['Open', 'High', 'Low', 'Close']] <= 0).any(axis=1)
    if no_positivos.sum() > 0:
        problemas.append(f"{no_positivos.sum()} vela(s) con precio <= 0")

    ret_log = np.log(diario['Close'] / diario['Close'].shift(1))
    extremos = ret_log.abs() > UMBRAL_RETORNO_DIARIO_EXTREMO
    n_extremos = extremos.sum()
    return problemas, n_extremos, invalidas, no_positivos


def detectar_huecos(diario, col_fecha='dia', umbral_dias_habiles=UMBRAL_HUECO_DIAS_HABILES):
    """(1) Huecos inesperados de cotización: días hábiles consecutivos sin ninguna vela."""
    fechas = diario[col_fecha].sort_values().reset_index(drop=True)
    huecos = []
    for i in range(1, len(fechas)):
        rango_habil = pd.bdate_range(fechas[i - 1], fechas[i])
        saltados = len(rango_habil) - 2
        if saltados >= umbral_dias_habiles:
            huecos.append(dict(inicio=fechas[i - 1], fin=fechas[i], dias_habiles_saltados=saltados))
    return huecos


def detectar_velas_artificiales(diario):
    """(2) Velas de domingo/festivo con rango anormalmente estrecho (artefacto ya
    documentado de huso horario HistData/MetaQuotes-Demo) -- compara el rango
    High-Low de cada vela contra la MEDIANA del resto, no la media (más robusta
    a los propios outliers que se buscan)."""
    rango = diario['High'] - diario['Low']
    mediana_rango = rango.median()
    if mediana_rango <= 0:
        return pd.Series(False, index=diario.index)
    sospechosas = rango < (UMBRAL_VELA_ARTIFICIAL_FRACCION_RANGO * mediana_rango)
    return sospechosas


def auditar_historico(diario, nombre='activo', col_fecha='dia'):
    """Corre todos los chequeos a nivel de histórico y devuelve un
    ResultadoAuditoria. Los huecos >= umbral y las velas inválidas son
    GRAVES; las velas artificiales y los retornos extremos son avisos
    (pueden ser legítimos -- un movimiento real de mercado también
    puede superar el umbral -- se reportan para revisión manual, no se
    asume automáticamente que son un error)."""
    r = ResultadoAuditoria(nombre)

    dup = detectar_duplicados_y_desorden(diario, col_fecha)
    for p in dup:
        r.grave(p)

    problemas_ohlc, n_extremos, invalidas, no_positivos = detectar_velas_invalidas_y_precios_anomalos(diario)
    for p in problemas_ohlc:
        r.grave(p)
    if n_extremos > 0:
        fechas_extremas = diario.loc[np.log(diario['Close'] / diario['Close'].shift(1)).abs() > UMBRAL_RETORNO_DIARIO_EXTREMO, col_fecha]
        r.aviso(f"{n_extremos} día(s) con |retorno log diario| > {UMBRAL_RETORNO_DIARIO_EXTREMO*100:.0f}%: "
                f"{', '.join(str(f.date()) for f in fechas_extremas)}")

    huecos = detectar_huecos(diario, col_fecha)
    r.huecos = huecos
    for h in huecos:
        r.grave(f"hueco de {h['dias_habiles_saltados']} días hábiles sin ninguna vela, "
                f"de {h['inicio'].date()} a {h['fin'].date()}")

    artificiales = detectar_velas_artificiales(diario)
    n_artificiales = artificiales.sum()
    if n_artificiales > 0:
        r.aviso(f"{n_artificiales} vela(s) con rango sospechosamente estrecho "
                f"(< {UMBRAL_VELA_ARTIFICIAL_FRACCION_RANGO*100:.0f}% de la mediana) -- "
                f"revisar si son artefactos de domingo/festivo antes de usarlas sin más")

    return r


# ======================================================================
# CHEQUEOS A NIVEL DE OPERACIONES DE BACKTEST
# ======================================================================

def marcar_operaciones_con_huecos(ops, huecos, col_entrada='dia', col_salida='fecha_salida'):
    """(6) y (8): para cada operación, True si su periodo de tenencia
    [entrada, salida] SOLAPA algún hueco detectado -- el stop/la salida
    no se pudieron verificar con datos reales durante ese solape."""
    if len(huecos) == 0:
        return pd.Series(False, index=ops.index)
    comprometida = pd.Series(False, index=ops.index)
    for h in huecos:
        solapa = (ops[col_entrada] <= h['fin']) & (ops[col_salida] >= h['inicio'])
        comprometida = comprometida | solapa
    return comprometida


def verificar_denominadores_r(ops, col_riesgo='riesgo_puntos', col_precio='precio_entrada'):
    """(7): riesgo_puntos <= 0, o riesgo_puntos/precio_entrada anormalmente
    pequeño -- un denominador así de pequeño dispara un R-múltiplo enorme
    por un problema de cálculo, no por una operación genuinamente buena."""
    problemas = []
    riesgo_no_positivo = ops[col_riesgo] <= 0
    if riesgo_no_positivo.sum() > 0:
        problemas.append(f"{riesgo_no_positivo.sum()} operación(es) con riesgo_puntos <= 0 (R indefinido/infinito)")

    fraccion = ops[col_riesgo] / ops[col_precio]
    degenerado = (fraccion > 0) & (fraccion < UMBRAL_RIESGO_MINIMO_FRACCION_PRECIO)
    if degenerado.sum() > 0:
        problemas.append(f"{degenerado.sum()} operación(es) con riesgo/precio < {UMBRAL_RIESGO_MINIMO_FRACCION_PRECIO*100:.3f}% "
                          f"(denominador sospechosamente pequeño -- revisar antes de confiar en su R)")
    return problemas, (riesgo_no_positivo | degenerado)


def auditar_backtest(diario, ops, nombre='activo', col_fecha='dia', col_entrada='dia',
                      col_salida='fecha_salida', col_riesgo='riesgo_puntos', col_precio='precio_entrada'):
    """Auditoría completa: histórico + operaciones. Devuelve
    (ResultadoAuditoria, ops con columna 'integridad_comprometida' añadida).
    Un hueco detectado en el histórico que NO solapa ninguna operación
    real es un aviso (no invalida el backtest); un hueco que SÍ solapa
    al menos una operación es GRAVE (esa operación concreta no se puede
    verificar) -- y el resultado agregado del backtest se marca no
    válido mientras esas operaciones sigan mezcladas sin excluir."""
    r = auditar_historico(diario, nombre, col_fecha)

    ops = ops.copy()
    ops['integridad_comprometida'] = marcar_operaciones_con_huecos(ops, r.huecos, col_entrada, col_salida)
    n_comprometidas = ops['integridad_comprometida'].sum()
    if n_comprometidas > 0:
        r.grave(f"{n_comprometidas} operación(es) de backtest cuyo periodo de tenencia solapa un hueco de datos "
                f"-- su stop/salida NO se puede verificar; deben excluirse o reportarse aparte, nunca mezclarse sin aviso")
        r.operaciones_comprometidas = ops['integridad_comprometida']

    problemas_r, degeneradas = verificar_denominadores_r(ops, col_riesgo, col_precio)
    for p in problemas_r:
        r.grave(p)

    return r, ops


if __name__ == '__main__':
    # Autocomprobación: reproduce los hallazgos ya documentados del
    # README para USTEC/US500 (hueco de 38 días) y XAUUSD (sin huecos).
    from datos_multiactivo import cargar_universo

    for sim in ['XAUUSD', 'USTEC', 'US500']:
        d = cargar_universo([sim])[sim].reset_index(drop=True)
        d['dia'] = pd.to_datetime(d['dia'])
        r = auditar_historico(d, sim)
        r.imprimir()
