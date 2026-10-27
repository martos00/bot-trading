# PREREGISTRO C79 — El dólar tras las subastas de deuda del Tesoro de EE. UU. — 27-oct-2026

Redactado y subido a git ANTES de calcular. Idea del usuario (vía ChatGPT: "prima macroeconómica después de subastas del Tesoro",
estudio de 2025 que NO he podido leer ni verificar). Antecedente propio: C8 (ciclo de subastas en bonos, Lou-Yan-Zhang) existe en
bonos pero no es operable; FTMO no ofrece CFD de bonos. Aquí se prueba si el dólar tiene un movimiento sistemático tras las subastas.

## Datos
- Calendario: TreasuryDirect (`c8_subastas.json`): subastas de notas y bonos nominales de 2, 3, 5, 7, 10, 20 y 30 años (sin TIPS
  ni FRN). Un día cuenta como "día de subasta" si hay al menos una; resultado publicado a las 13:00 NY.
- Precios: FXCM M1 (punto medio BID/ASK), EURUSD, USDJPY y GBPUSD, 2012-2026-09.
- Dólar = media de (−EURUSD, +USDJPY, −GBPUSD) en rentabilidad logarítmica (positivo = dólar sube).

## Pruebas (2), sin signo previsto (bilateral)
- W1: 13:00 → 14:00 NY del día de subasta (reacción a la subasta).
- W2: 13:00 del día de subasta → 13:00 del siguiente día hábil (la "prima" del día siguiente).
Precio = cierre del último minuto anterior a cada hora (hasta 10 minutos atrás).

## Criterio
Descubrimiento 2012-2018: |t (NW)| ≥ 2,0 fija el signo (si no, la prueba se cierra). Confirmación 2019-2026-09 con ese signo:
t ≥ 2,24 (Bonferroni unilateral 0,025/2... se usa 0,05/2 → 1,96; se exige 2,24 por prudencia, como Holm con 2 pruebas al 0,025),
≥ 60 % de años con el signo, y media > coste (0,6 pb, coste FTMO medio de los tres pares). Informativo: días sin subasta a la
misma hora. Lo que pase necesita otra fuente (HistData). Contador +2.
