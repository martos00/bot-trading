# PREREGISTRO C100 — Bitcoin: continuación del movimiento del fin de semana (hipótesis salida de C98) con datos no vistos — 28-oct-2026

Redactado y subido a git ANTES de descargar y calcular. Origen: en C98 la regla «cerrar el hueco» perdió −32,5 pb en BTC (t −2,50) y −23,2
en ETH (2017-08 → 2026-09, Binance): la regla contraria (continuación) ganó. Como esa idea salió de mirar los datos, NO se puede validar con
ellos. Prueba con datos no vistos: **BTC en Bitstamp 2012-01 → 2017-07** (antes de Binance; API pública v2/ohlc, 1 h) + forward desde nov-2026.

## Regla (hora de NY con cambio de hora), el espejo exacto de C98
g = ln(P dom 18:00 / P vie 17:00) (apertura de la vela horaria). Posición en el sentido de g del domingo 18:00 al lunes 16:00 NY.
Salida anticipada si el precio vuelve al cierre del viernes (es el stop natural de la regla espejo: el «hueco» se cierra contra nosotros).
Semanas sin datos en alguna de las tres horas se descartan.

## Criterio (1 prueba)
2012-01 → 2017-07 (Bitstamp): media > 0 con t (Newey-West) ≥ 2,0 y ≥ 4 de 6 años positivos. Coste: en 2012-17 no había futuros; se exige
además media > 3 pb (micro MBT). Pasa → candidata para la cartera de futuros (forward obligatorio). Informativo: Bitstamp 2017-08 → 2026-09
(misma muestra que C98, otra fuente). Contador +1.
