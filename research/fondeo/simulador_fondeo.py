"""Simulador de evaluaciones y cuentas financiadas de prop firms (Monte Carlo).

Entrada: una serie DIARIA de resultados de una estrategia, expresados como fracción del capital
con el que se dimensionó (riesgo de referencia), y opcionalmente el peor valor intradía de la equity
de cada día (mínimo del P&L flotante + realizado, también como fracción). Con eso se comprueban:

- objetivo de beneficio por fase, días mínimos y días máximos;
- pérdida diaria medida sobre la EQUITY (no solo sobre lo cerrado), con base en el saldo inicial
  o en el saldo al inicio del día, según la empresa;
- pérdida máxima estática, trailing de cierre de día o trailing intradía (con tope en el saldo inicial
  si la empresa lo aplica);
- regla de consistencia (mejor día ≤ X% del beneficio total): si no se cumple, se sigue operando;
- límites internos del bot más estrictos que los oficiales (pérdida diaria interna y colchón sobre la
  pérdida máxima), modelados como cierre forzoso con un deslizamiento adicional.

Monte Carlo: remuestreo por bloques estacionario de los días de la serie (conserva rachas y clusters
de volatilidad) y, opcionalmente, incertidumbre de la ventaja: en cada simulación se desplaza la media
diaria con un valor extraído de N(0, error estándar de la media). Así la probabilidad estimada no
asume que la ventaja histórica es exacta.

IMPORTANTE: la probabilidad simulada NO es la probabilidad real de cobrar. Supone que el futuro se
parece a la muestra, que la ejecución real coincide con el backtest y que la empresa aplica sus
reglas tal como están configuradas.
"""
from dataclasses import dataclass, field
import numpy as np


@dataclass
class Reglas:
    nombre: str
    objetivos: list                      # objetivo por fase (fracción); [] = cuenta financiada sin objetivo
    perdida_diaria: float                # fracción
    base_perdida_diaria: str = 'inicial'  # 'inicial' | 'saldo_dia'
    perdida_maxima: float = 0.10
    tipo_maxima: str = 'estatica'        # 'estatica' | 'trailing_cierre' | 'trailing_intradia'
    trailing_tope_inicial: bool = True   # el trailing deja de subir al llegar al saldo inicial
    dias_minimos: int = 0
    dias_maximos: int = 0                # 0 = sin límite
    consistencia: float = 0.0            # mejor día ≤ consistencia × beneficio total (0 = sin regla)


@dataclass
class LimitesInternos:
    perdida_diaria: float = 0.0          # 0 = desactivado; si la equity del día cae a −x se cierra todo
    colchon_maxima: float = 0.0          # se deja de operar si la distancia a la pérdida máxima es < colchón
    deslizamiento_cierre: float = 0.0    # pérdida extra al forzar un cierre (gaps, spread)


def _bloques(n, largo_medio, rng, n_out):
    """Índices de un remuestreo por bloques estacionario (Politis-Romano)."""
    idx = np.empty(n_out, int)
    i = rng.integers(n)
    for k in range(n_out):
        idx[k] = i
        i = rng.integers(n) if rng.random() < 1 / largo_medio else (i + 1) % n
    return idx


def simular_fase(r, m, objetivo, reglas, lim, max_dias):
    """Simula una fase sobre secuencias r (resultado del día) y m (mínimo intradía). Devuelve (estado, días)."""
    saldo, pico_cierre, pico_intra = 1.0, 1.0, 1.0
    beneficios_dia = []
    dias_operados = 0
    for d in range(min(len(r), max_dias)):
        # importe del límite diario: % del capital inicial (FTMO, FundedNext) o % del saldo al inicio del día
        base_dia = 1.0 if reglas.base_perdida_diaria == 'inicial' else saldo
        if reglas.tipo_maxima == 'estatica':
            suelo = 1.0 - reglas.perdida_maxima
        else:
            pico = pico_cierre if reglas.tipo_maxima == 'trailing_cierre' else pico_intra
            suelo = (min(pico, 1.0) if reglas.trailing_tope_inicial else pico) - reglas.perdida_maxima
        if lim.colchon_maxima and saldo - suelo < lim.colchon_maxima:
            return 'parado_por_colchon', d
        rd, md = r[d], m[d]
        # límite interno diario: si el mínimo intradía lo alcanza, se cierra en ese nivel con deslizamiento
        if lim.perdida_diaria and md * saldo <= -lim.perdida_diaria * base_dia:
            rd = md = -lim.perdida_diaria * base_dia / saldo - lim.deslizamiento_cierre
        eq_min = saldo + md * saldo
        if eq_min <= saldo - reglas.perdida_diaria * base_dia:
            return 'incumple_diaria', d + 1
        if eq_min <= suelo:
            return 'incumple_maxima', d + 1
        pnl = rd * saldo
        saldo += pnl
        pico_intra = max(pico_intra, saldo)  # aproximación: el máximo intradía se toma al cierre
        pico_cierre = max(pico_cierre, saldo)
        dias_operados += 1
        beneficios_dia.append(pnl)
        if objetivo is not None and saldo - 1.0 >= objetivo and dias_operados >= reglas.dias_minimos:
            total = saldo - 1.0
            if reglas.consistencia and max(beneficios_dia) > reglas.consistencia * total:
                continue
            return 'supera', d + 1
    return ('sin_resolver' if objetivo is not None else 'sobrevive'), min(len(r), max_dias)


def montecarlo(r_hist, m_hist, reglas, lim=None, escala=1.0, n_sim=5000, largo_bloque=5,
               incertidumbre_media=True, dias_financiada=250, semilla=20261019):
    """Probabilidades de superar todas las fases y de sobrevivir `dias_financiada` en la cuenta financiada."""
    lim = lim or LimitesInternos()
    rng = np.random.default_rng(semilla)
    r_hist = np.asarray(r_hist, float) * escala
    m_hist = np.minimum(np.asarray(m_hist, float) * escala, np.minimum(r_hist, 0))
    n = len(r_hist)
    se = r_hist.std(ddof=1) / np.sqrt(n)
    max_dias = reglas.dias_maximos or 2000
    res = {'supera': 0, 'incumple_diaria': 0, 'incumple_maxima': 0, 'sin_resolver': 0, 'parado_por_colchon': 0}
    dias_superar, sobrevive_fin, n_fin = [], 0, 0
    for _ in range(n_sim):
        delta = rng.normal(0, se) if incertidumbre_media else 0.0
        estado, total_dias = 'supera', 0
        for obj in reglas.objetivos:
            idx = _bloques(n, largo_bloque, rng, max_dias)
            estado, dd = simular_fase(r_hist[idx] + delta, m_hist[idx] + delta, obj, reglas, lim, max_dias)
            total_dias += dd
            if estado != 'supera':
                break
        res[estado] += 1
        if estado == 'supera':
            dias_superar.append(total_dias)
            n_fin += 1
            idx = _bloques(n, largo_bloque, rng, dias_financiada)
            e2, _ = simular_fase(r_hist[idx] + delta, m_hist[idx] + delta, None, reglas, lim, dias_financiada)
            sobrevive_fin += e2 == 'sobrevive'
    out = {k: v / n_sim for k, v in res.items()}
    out['dias_mediana_superar'] = float(np.median(dias_superar)) if dias_superar else np.nan
    out['p_sobrevive_financiada_dado_supera'] = sobrevive_fin / n_fin if n_fin else np.nan
    # error de Monte Carlo (binomial) de la probabilidad de superar
    p = out['supera']
    out['ic95_supera'] = (max(0, p - 1.96 * np.sqrt(p * (1 - p) / n_sim)), min(1, p + 1.96 * np.sqrt(p * (1 - p) / n_sim)))
    return out


REGLAS = {
    'FTMO_2step': Reglas('FTMO 2-Step', [0.10, 0.05], 0.05, 'inicial', 0.10, 'estatica', dias_minimos=4, consistencia=0.50),
    'FTMO_1step': Reglas('FTMO 1-Step', [0.10], 0.03, 'inicial', 0.10, 'trailing_cierre', dias_minimos=0, consistencia=0.50),
    'FundedNext_2step': Reglas('FundedNext Stellar 2-Step', [0.08, 0.05], 0.05, 'inicial', 0.10, 'estatica', dias_minimos=5),
    # Topstep 50K: MLL 2.000 $ (4%) trailing de cierre con tope en el inicial; objetivo 3.000 $ (6%); consistencia 50% (fuentes discrepan: 50-55%)
    'Topstep_50K': Reglas('Topstep 50K', [0.06], 1.0, 'inicial', 0.04, 'trailing_cierre', True, consistencia=0.50),
}
# FTMO y FundedNext: suelo diario = saldo al inicio del día − X% del capital INICIAL ('inicial').
# Simplificación declarada: el "día" del simulador es el día de la estrategia; FTMO lo corta a las 00:00 CE(S)T.


if __name__ == '__main__':
    # autocomprobación con datos sintéticos: estrategia con Sharpe ~1,5 y 0,8% de vol diaria
    rng = np.random.default_rng(1)
    r = rng.normal(0.0008, 0.008, 2000)
    m = np.minimum(r, 0) - np.abs(rng.normal(0, 0.003, 2000))
    for k, reg in REGLAS.items():
        o = montecarlo(r, m, reg, n_sim=2000)
        print(k, {a: (round(b, 3) if isinstance(b, float) else b) for a, b in o.items()})
