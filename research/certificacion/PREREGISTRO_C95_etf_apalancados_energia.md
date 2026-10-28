# PREREGISTRO C95 — Rebalanceo de los ETF apalancados de energía en la ventana de liquidación (gas natural y crudo) — 28-oct-2026

Redactado y subido a git ANTES de calcular. Familia nueva (en H69 solo se probó S&P/Nasdaq; en C84 la ventana de liquidación sin condicionar).
Mecanismo (Cheng-Madhavan 2009; Shum et al. 2016): un ETF apalancado ×L debe comprar/vender al cierre una cantidad ∝ L(L−1) × rentabilidad
del día; tanto los largos (×2, ×3) como los inversos (−2, −3: L(L−1) = 6 o 12) compran cuando el día sube y venden cuando baja. En gas
natural (UGAZ/DGAZ ×3 2012-2020; BOIL/KOLD ×2 desde 2011, muy grandes en 2022) y crudo (UCO/SCO ×2; UWT/DWT ×3 2017-2020) ese flujo
se ejecuta contra la liquidación del CME (14:28-14:30 NY). Previsión: continuación en el sentido del día durante la media hora previa.

## Regla (hora de NY)
r = ln(P 14:00 hoy / P 14:30 sesión anterior). Posición en el sentido de r de 14:00 a 14:30 (salida a la liquidación; operable con
órdenes TAS). Precio = cierre del último minuto ≤ la hora (máx. 10 min de antigüedad); días sin datos se descartan.
**2 pruebas: NG y CL.** Controles informativos sin ETF apalancados relevantes: gasóleo HO y gasolina RB. Placebo informativo: 13:30-14:00.
Informativo: dosis-respuesta por terciles de |r|.

## Datos
QuantConnect, futuros a 1 minuto (contrato frontal por interés abierto, ajuste por cociente), 2010-06 → 2026-09, desfase horario 0 en
energía (calibrado en B22). **No hay segunda fuente a 1 minuto para esta franja** (Databento local solo cubre viernes desde las 15:00):
si pasa, queda como candidata pendiente de segunda fuente/forward, no como ventaja confirmada.

## Criterio (Bonferroni unilateral 0,05/2 → t ≥ 2,24)
Descubrimiento 2010-06 → 2017: media > 0. Confirmación 2018 → 2026-09: media > 0 con t (Newey-West) ≥ 2,24, ≥ 60 % de años positivos
y media > coste del futuro (NG 4 pb; CL 1,6 pb). Contador +2.
