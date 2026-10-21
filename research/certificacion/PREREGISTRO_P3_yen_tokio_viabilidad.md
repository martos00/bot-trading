# Pre-registro P3 — Yen en horario de Tokio: ¿es operable con costes reales? (21-oct-2026)

Redactado y enviado a git ANTES de calcular los costes ejecutables.

## Situación
C3/C5: el yen se aprecia de 08:00 a 15:00 de Tokio en los tres períodos vistos (USD/JPY: 2003-07 +1,28 pb t 1,95;
2008-11 +3,06 pb t 2,57; 2012-26 FXCM punto medio +1,43 pb t 3,17). Es un hallazgo **a posteriori**: no quedan datos
históricos sin usar, así que **esta prueba no puede certificar la ventaja**; solo decide si merece un forward test en demo.
Riesgo conocido (H73): las 08:00 de Tokio son las 23:00 UTC, 1-2 h después del rollover de las 17:00 NY, cuando el spread
aún puede estar alto. Con datos BID ya nos engañó una vez; aquí se usan BID y ASK reales de FXCM.

## Regla (fija)
Cada día laborable de Tokio: VENTA de USD/JPY al BID del cierre del minuto que termina a las 08:00 Tokio; RECOMPRA al ASK
del cierre del minuto que termina a las 15:00 Tokio (tolerancia 5 min). Coste añadido: comisión 0,45 pb (FTMO) + 0,1 pb de
deslizamiento por lado. Sin filtros. Datos: FXCM M1 BID/ASK 2012-01 → 2026-09.

## Criterios para pasar a forward test (todos)
1. Media ejecutable neta > 0 con t de Newey-West (5) ≥ 2,0.
2. Media en punto medio ≥ 3 × coste medio (spread ejecutado + comisión + deslizamiento).
3. Neto positivo en ≥ 60% de los años.
Informativo: spread mediano y p90 a las 08:00 y 15:00 Tokio; correlación diaria con E1 (EUR/USD 06-08 NY).
Si falla cualquiera, se cierra. Si pasa, se escribe un pre-registro de forward test (demo, ≥ 6 meses) antes de operar.
Contador: +1 (N ≈ 1.156).
