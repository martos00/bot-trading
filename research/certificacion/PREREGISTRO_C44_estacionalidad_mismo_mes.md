# Pre-registro C44 — Estacionalidad del mismo mes en materias primas (Keloharju, Linnainmaa y Nyberg, JF 2016) — 22-oct-2026
Redactado y enviado a git ANTES de calcular nada.
## Fuente (de memoria; no texto completo verificado)
KLN 2016 ("Return seasonalities"): los activos con rentabilidad alta en un mes del calendario en años anteriores tienden a rendir
más en ese mismo mes; lo documentan en acciones, índices de países y materias primas. Mecanismo propuesto: primas de riesgo
estacionales. Aviso: un trabajo de arXiv (2026, 2609.12227) concluye que la estacionalidad de materias primas es inestable fuera de muestra.
## Regla
16 futuros de C34 (c.0 diario, sin cambios de contrato). Al final de cada mes t−1, señal de cada mercado para el mes t = media de
sus rentabilidades en ese mismo mes del calendario en todos los años anteriores disponibles (mínimo 5). Largo del tercio con señal
más alta y corto del tercio más baja (igual peso), un mes. Coste 3 pb por lado y cambio de posición.
## Tramos y criterios
Todo lo calculable es posterior a la publicación: **evaluación 2016-01 – 2026-09**: media mensual neta > 0 con t (NW, 3) ≥ 2,0 y
≥ 60 % de años positivos. Contador +1.
