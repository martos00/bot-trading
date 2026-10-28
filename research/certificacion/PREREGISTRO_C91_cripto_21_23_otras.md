# PREREGISTRO C91 — Cripto largo 21:00 → 23:00 UTC (C2) en otras criptomonedas con futuros en el CME (SOL, XRP) — 28-oct-2026

Redactado y subido a git ANTES de calcular. C2 certificó BTC 21-23 UTC tras su publicación (Quantpedia, 2022-02) y lo replicó en ETH.
Si el mecanismo es del mercado cripto en general, debería aparecer en otras monedas. El CME lista futuros de SOL y XRP (desde 2025),
operables en cuentas de fondeo de futuros que admitan cripto y mantener posiciones hasta las 19:00 NY (en invierno 16-18 NY).

## Datos
Binance spot, velas de 1 h (data.binance.vision): SOLUSDT (se descarga ahora), XRPUSDT (ya en disco). Informativo: LTCUSDT, ADAUSDT,
BNBUSDT (sin futuros en el CME). Periodo de prueba: **2022-02-04 → 2026-09-30** (posterior a la publicación). Regla idéntica a C2:
largo de la apertura de la vela de las 21:00 UTC a la de las 23:00 UTC, todos los días.

## Criterio (2 pruebas: SOL y XRP)
Media > 0 con t (Newey-West) ≥ 2,24 (Bonferroni unilateral 0,05/2); ≥ 60 % de años positivos; media > 5 pb (coste estimado de los
micro futuros de SOL/XRP del CME, a medir). Informativo: 2018-2022 (antes de la publicación) y las tres monedas sin futuros.
Pasa → candidata para la cartera de futuros (requiere firma con cripto y horario compatible). Contador +2.
