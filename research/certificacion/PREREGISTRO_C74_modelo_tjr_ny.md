# PREREGISTRO C74 — Modelo "TJR" de sesión de NY (barrida de Asia/Londres → cambio de estructura → FVG) — 26-oct-2026

Petición del usuario: probar el setup que enseña el youtuber TJR (escuela ICT/SMC). No tengo acceso a su material de
pago; las reglas siguientes son la versión pública que suele describir (marcar máximos/mínimos de Asia y Londres,
esperar a que la apertura de Nueva York barra uno, confirmar con un cambio de estructura en 5 minutos y entrar en el
retroceso al fair value gap, stop tras la barrida, objetivo 2R). Cada elección discrecional se fija aquí, ANTES de
ejecutar nada, y no se cambiará después de ver resultados. Pruebas previas de la misma familia (H2, Liquidity
Sweep PDH/PDL, Sweep→MSS→FVG en XAUUSD M15) fueron negativas; esta es una variante distinta (niveles de sesión,
ventana de NY, 5 minutos) y cuenta como 3 pruebas nuevas en el contador.

## Datos (ya en disco, nada se compra)
- ES (S&P 500 futuro): Databento 1 minuto, UTC → America/New_York. Se descarta el día si el contrato
  (`instrument_id`) cambia entre las 19:00 NY del día anterior y las 12:00 NY del día.
- EURUSD y XAUUSD: HistData M1 (hora EST fija, UTC−5) → America/New_York.
- Velas de 5 minutos construidas desde M1 (etiqueta = inicio). Una vela de 5 min necesita ≥1 minuto con datos.
- Periodo: 2011-01-01 a 2026-09-30. Descubrimiento 2011-2018, confirmación 2019-2026.
- Solo días laborables (lunes a viernes) con datos en las tres ventanas.

## Reglas (hora de Nueva York)
1. **Niveles**: Asia = máx/mín de 19:00 (día anterior) a 00:00; Londres = máx/mín de 02:00 a 05:00.
   Cuatro niveles: AsiaH, AsiaL, LonH, LonL. Un nivel deja de ser válido si se supera entre su cierre y las 09:30
   (ya "tomado" antes de NY).
2. **Ventana de barrida**: velas de 5 min con inicio entre 09:30 y 10:55. Barrida alcista = el máximo de una vela
   supera un nivel alto válido (AsiaH o LonH); bajista = el mínimo perfora un nivel bajo válido. Se toma la PRIMERA
   vela que barre. Si la misma vela barre un nivel alto y uno bajo, se descarta el día.
3. **Dirección**: barrida de máximo → buscar CORTO; de mínimo → LARGO.
4. **Extremo de la barrida**: para el corto, el máximo más alto desde la vela de barrida hasta la vela del cambio
   de estructura (incluidas); simétrico para el largo.
5. **Cambio de estructura (MSS)**: punto de referencia = el último mínimo de swing (fractal de 3 velas de 5 min:
   mínimo menor que el de la vela anterior y el de la siguiente) con vela central entre 09:00 y la vela de barrida
   (sin incluirla). Si no hay ninguno, el mínimo de las velas de 09:00 hasta la anterior a la barrida.
   MSS = primera vela posterior a la barrida, con inicio ≤ 10:55, que CIERRA por debajo de ese punto. Si antes del
   MSS el precio sigue subiendo, la barrida no se invalida: el extremo se actualiza (regla 4). Si no hay MSS en la ventana, no hay operación ese día. Largo: simétrico (cierre por encima del último máximo
   de swing).
6. **FVG**: entre la vela de barrida y la del MSS (incluidas), el ÚLTIMO hueco bajista de 3 velas
   (mínimo de la vela i−2 > máximo de la vela i, con la vela i entre barrida y MSS). Si no existe, no hay operación.
   Largo: máximo de i−2 < mínimo de i.
7. **Entrada**: orden limitada en el borde cercano del FVG (corto: máximo de la vela i; largo: mínimo de la vela i),
   activa desde la vela siguiente al MSS hasta la vela de inicio 11:25. Se cancela si antes de llenarse el precio
   toca el stop o el objetivo.
8. **Stop**: extremo de la barrida (regla 4). **Objetivo**: 2R (R = |entrada − stop|). Si R < 1 pb del precio,
   no se opera (riesgo degenerado).
9. **Salida**: stop, objetivo, o cierre de la vela que empieza a las 11:55 (salida a mercado a las 12:00).
   Vela que toca stop y objetivo a la vez → stop. En la vela de llenado, si toca el stop → stop (peor caso);
   el objetivo en la vela de llenado no se cuenta.
10. Una operación por día como máximo.

## Costes (ida y vuelta, en puntos básicos del precio, restados a cada operación y convertidos a R)
EURUSD 0,54 pb (medido en FTMO) · XAUUSD 1,5 pb · ES 1,0 pb (orientativo para un CFD de índice). Se informa también
el resultado bruto. Las órdenes limitadas se llenan al precio exacto (supuesto optimista, a favor de la estrategia).

## Criterio de éxito (por instrumento, 3 instrumentos → Bonferroni)
- Muestra completa: media neta en R > 0 con t ≥ 2,39 (unilateral 0,025/3), t sobre operaciones (1 por día).
- Y media neta > 0 en descubrimiento (2011-2018) Y en confirmación (2019-2026).
- Pasa → "candidata", que requeriría segunda fuente antes de certificar. Falla → se cierra, sin variantes.
- Se informan nº de operaciones, % aciertos, media R bruta/neta, t, y resultado por año.
