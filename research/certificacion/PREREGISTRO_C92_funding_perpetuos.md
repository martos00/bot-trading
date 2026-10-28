# PREREGISTRO C92 — Presión de precio antes del pago de financiación (funding) de los perpetuos de Binance — 28-oct-2026

Redactado y subido a git ANTES de descargar el histórico completo y de calcular. Familia nueva: flujo obligado que cambia de signo según
el posicionamiento. Mecanismo: con funding positivo los largos pagan a los cortos cada 8 h (00:00, 08:00, 16:00 UTC); los largos
apalancados que no quieren pagar cierran antes del cobro y los arbitrajistas venden el perpetuo/compran contado → presión bajista antes
de la hora de pago (y al revés con funding negativo). Operable con los futuros de BTC/ETH del CME (las tres horas caen en sesión).

## Datos
Binance USDⓈ-M: tasas de funding históricas de BTCUSDT y ETHUSDT (data.binance.vision, 2019-09/2019-11 → 2026-09). Precio: Binance
contado 1 h (apertura de la vela). Para no usar información futura, la señal usa la tasa del periodo ANTERIOR (cobrada 8 h antes).

## Regla
En cada hora de pago T ∈ {00:00, 08:00, 16:00 UTC}: f = tasa cobrada en T − 8 h.
- f > 0,0001 (por encima del valor por defecto 0,01 %): **corto** de T − 1 h a T.
- f < 0: **largo** de T − 1 h a T.
- 0 ≤ f ≤ 0,0001: sin operación.
6 pruebas (2 monedas × 3 horas). Informativo: la hora siguiente (T → T + 1 h).

## Criterio (Bonferroni unilateral 0,05/6 → t ≥ 2,39)
Descubrimiento 2019-09 → 2022-12: media > 0. Confirmación 2023-01 → 2026-09: media > 0 con t (Newey-West) ≥ 2,39, ≥ 60 % de años
positivos y media > 3 pb (coste del micro futuro del CME). Contador +6.
