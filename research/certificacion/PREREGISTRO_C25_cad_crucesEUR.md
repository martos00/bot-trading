# Pre-registro C25 — Efectos de sesión independientes del "dólar fuerte en la mañana europea" (21-oct-2026)

Redactado y enviado a git ANTES de descargar USDCAD, EURGBP y EURCHF de FXCM y de calcular nada.
Objetivo: ventajas del mismo mecanismo (flujos de empresas en su horario) pero poco correlacionadas con E1, para subir el
Sharpe de la cartera. Datos con BID y ASK reales (lección de C23/C24: nada de conclusiones con datos solo BID).

## Pruebas (3, bilaterales; Holm)
- **USDCAD**, horario norteamericano 08:00 → 16:00 NY (Toronto y Nueva York a la vez; signo sin predicción clara).
- **EURGBP**, sesión europea 07:00 Londres → 08:00 NY (ambas divisas locales; sin predicción clara).
- **EURCHF**, sesión europea 07:00 Londres → 08:00 NY (ídem).

## Datos, tramos y criterios
FXCM M1 BID/ASK, 2012-01 → 2026-09; rentabilidad sobre el precio medio; coste ejecutable = medio spread real a la entrada y a
la salida + 0,45 pb de comisión + 0,2 pb de deslizamiento. Descubrimiento 2012-2018: fija el signo. Confirmación
2019 → 2026-09: mismo signo con t de Newey-West ≥ 2,39 (Holm, 3), ≥ 60% de años, media neta ejecutable > 0 y bruta ≥ 3 × coste.
Informativo: correlación con E1. Contador +3 (N ≈ 1.192).
