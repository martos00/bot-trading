# Pre-registro H78 — Estacionalidad intradía de Bitcoin (Quantpedia): largo 21:00 → 23:00 UTC

Redactado y enviado a git ANTES de descargar los datos y de calcular ningún resultado.

## Fuente (leída, 19-oct-2026)
Padyšák & Vojtko (Quantpedia), "Are There Seasonal Intraday or Overnight Anomalies in Bitcoin?",
18-feb-2022 (Gemini, horario, 9-oct-2015 → 3-feb-2022): **comprar a las 21:00 UTC y vender a las 23:00 UTC**,
cada día; 33% anual, vol 20,9%, DD máx −22,5%; **costes no indicados** (bruto). Actualización
"The Seasonality of Bitcoin" (13-sep-2023, datos hasta 30-jun-2023): 40,6% anual, "mala racha en 2022-2023".
Nivel de evidencia: bajo-medio (blog de investigación, sin revisión por pares, sin costes, sin estadísticos).
Ningún precedente en este proyecto (primera prueba en cripto).

## Regla (única y congelada)
Todos los días naturales (también fines de semana, como en la fuente, que usa todas las horas de Gemini):
largo BTC a la apertura de la vela de las 21:00 UTC, cierre a la apertura de la vela de las 23:00 UTC.
Sin stop, objetivo ni filtros. Las variantes de la actualización (día de la semana, tendencia, volatilidad)
**no se evalúan** como candidatas.

## Datos
Binance BTCUSDT spot (data.binance.vision), velas de 1 hora desde 2017-08 (motor principal) y de 1 minuto
en el OOS (motor independiente: precios a las 21:00:00 y 23:00:00 desde el minuto). Bolsa distinta a la de
la fuente (Gemini): es una prueba de robustez, no una copia exacta; se declara. Auditoría de huecos: días
sin la vela de las 21:00 o de las 22:00 se excluyen.

## Tramos
- **Réplica** (período de la fuente con nuestros datos): 2017-08-17 → 2022-02-03.
- **OOS posterior a la publicación**: 2022-02-04 → 2026-09-30 (≈ 4,7 años).

## Costes (CFD en FTMO; fuente de terceros, Propvator)
Comisión de 0,0325% por lado (6,5 pb ida y vuelta) más spread. El spread de BTCUSD en FTMO no es público:
caso base 0,02% (2 pb) por ida y vuelta, estrés 0,10%. Se informa además del **coste de equilibrio**.

## Criterios (reproducción de estrategia publicada)
Candidata si en el OOS, neta del caso base: media > 0 con t ≥ 2 (Newey-West), positiva en ≥ 3 de 5 años
(2022-2026) y mejor que el control (p < 0,05): misma duración de 2 h con hora de inicio aleatoria en los mismos
días (10.000 réplicas). Además, coste de equilibrio ≥ 3× el coste base (puerta de APRENDIZAJE_METODOLOGIA.md).
Si cumple: simulación de fondeo con `research/fondeo/simulador_fondeo.py`. N acumulado = 93.
