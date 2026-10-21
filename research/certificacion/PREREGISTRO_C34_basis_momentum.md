# Pre-registro C34 — Basis-momentum en materias primas (Boons y Prado, Journal of Finance 2019) — 21-oct-2026

Redactado y enviado a git ANTES de descargar los datos de primer y segundo vencimiento y de calcular nada.
## Fuente (resumen; no texto completo)
Basis-momentum = momentum (12 meses) del futuro del primer vencimiento menos el del segundo. Predice rentabilidades de
materias primas en sección cruzada mejor que el carry y el momentum; su muestra termina en 2014. Mecanismo propuesto:
desequilibrio entre la demanda de cobertura y la capacidad de los especuladores (prima de riesgo de cobertura).
## Regla
Universo: 16 futuros del CME (CL, HO, RB, NG, GC, SI, HG, PL, ZC, ZS, ZW, ZL, ZM, KE, LE, HE). Datos Databento diarios,
contratos continuos por calendario c.0 (primer vencimiento) y c.1 (segundo), sin rentabilidades entre contratos distintos.
Fin de cada mes: BM_i = rentabilidad acumulada de 12 meses de c.0 − la de c.1. Largo del tercio con BM más alto y corto del
tercio más bajo (igual peso), mantenido un mes en el segundo vencimiento (c.1, menos afectado por la entrega). Coste 3 pb por
lado y cambio de posición. Informativo: carry (pendiente c.1/c.0) y momentum de 12 meses con la misma construcción.
## Tramos y criterios
Réplica 2011-2014 (dentro de su muestra): media > 0 (comprobación). **Confirmación 2015-2026-09**: media mensual neta > 0 con
t ≥ 2,0 y ≥ 60% de años positivos; Sharpe anual informativo; correlación con E1. Contador +1 (N ≈ 1.803).
Aviso de aplicabilidad: mantiene posiciones semanas → no sirve en firmas que obligan a cerrar cada día; sí en cuenta propia.
