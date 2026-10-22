# Pre-registro B6 — Barrido día × hora en 13 pares de divisas con BID/ASK reales (FXCM) — 22-oct-2026
Redactado y enviado a git ANTES de calcular.
## Datos y regla
FXCM M1 BID/ASK 2012-2026: EURUSD GBPUSD USDJPY USDCHF AUDUSD USDCAD EURGBP EURCHF EURJPY GBPJPY EURAUD EURNZD GBPCAD.
Precio en cada hora en punto (hora de NY) = cierre del minuto hh:59 anterior (mid). Franjas de 1 h, por día de la semana (lun-vie),
inicio 0-22 (sin 16-18 NY por el cambio de día/rollover, donde el spread se dispara). Rentabilidad con el signo del descubrimiento.
Coste por operación = medio spread real a la entrada + medio a la salida (media del tramo) + comisión 0,45 pb.
## Criterios (como B4)
Descubrimiento 2012-2018: |t (NW)| ≥ 3,5 y n ≥ 200. Confirmación 2019 – 2026-09 con su signo: (1) t ≥ Bonferroni unilateral 0,05/k_sel;
(2) ≥ 60 % de años con el signo; (3) bruto ≥ 3 × coste medio. Ya conocida (control, no cuenta): EURUSD/GBPUSD 06-08 NY (E1/C3).
Lo que pase necesita una segunda fuente (Dukascopy o HistData) antes de operar. Contador + nº de reglas.
