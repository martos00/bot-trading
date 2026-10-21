# Pre-registro C33 — Ruptura del rango del día anterior y reversión después de noticias (EUR/USD, GBP/USD) — 21-oct-2026

Redactado y enviado a git ANTES de calcular. G1 (reversión asiática con filtro) ya se probó y no se repite.

## R — Ruptura del rango del día anterior
Día FX de 17:00 a 17:00 NY. Máximo H y mínimo L del día anterior (precio medio M1). Entre las 03:00 y las 12:00 NY, orden stop
en H (compra) y en L (venta); la primera que salte. Stop en el punto medio del rango del día anterior; objetivo 1 rango (H−L)
desde la entrada; salida a las 16:55 NY si no salta nada. Una operación al día.
## N — Reversión después de noticias (sin calendario: se detecta el impacto)
Días en que |rentabilidad 08:29→08:45 NY| > 3 × mediana de |esa misma ventana| en los 60 días hábiles anteriores (datos de
EE. UU. de las 08:30). A las 08:45 se opera en contra del movimiento y se cierra a las 10:00 NY (stop: el extremo del
movimiento 08:29-08:45 ± 0, se supone que el spread ya se ha normalizado a las 08:45).

## Datos, costes, tramos y criterios (2 pruebas, Holm)
FXCM M1 BID/ASK 2012-2026; ejecución al ASK/BID reales + 0,45 pb de comisión + 0,1 pb de deslizamiento por lado (en R, el stop
y el objetivo se ejecutan al precio de la orden más medio spread). Media de los dos pares por día.
Descubrimiento 2012-2018; confirmación 2019-2026-09: media neta > 0 con t que supere Holm (2), ≥ 60% de años, bruto ≥ 3 × coste.
Contador +2 (N ≈ 1.802).
