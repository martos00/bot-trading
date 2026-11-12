# PREREGISTRO C118 — Bitcoin: ventana del fixing de los ETF y reversión día/noche (estudios 2026)

Redactado y subido a git ANTES de calcular (12-nov-2026). Fuentes (solo resúmenes; los artículos completos devolvieron 403 y NO se han leído):
- Schmidt y Kraft, «Trading to the fixing…», Finance Research Letters 2026: desde los ETF de contado (11-ene-2024) el volumen de BTC se
  concentra en la ventana del índice de referencia 15:00-16:00 NY (las creaciones/reembolsos se compran o venden en esa hora).
  Kaiko 2024: esa hora pasó del 4,5 % al 6,7 % del volumen. Fabus et al. (SSRN 2026): la rentabilidad de las 24 h previas predice los
  flujos del día.
- MDPI JRFM 19(9) 692 (2026), Kraken 2016-2025, sesiones de 12 h: óptimo de la muestra BTC «reversión/reversión» con el día empezando a
  las 08:00 UTC; ETH «largo de noche / reversión de día» empezando a las 05:00 UTC. (Óptimo elegido entre 25 combinaciones × horas:
  muy expuesto a minería de datos → solo vale el periodo POSTERIOR a su muestra.)

## Pruebas (3 → Bonferroni: t ≥ 2,13 unilateral al 5 % / 3). Datos: Binance 1 h (BTCUSDT, ETHUSDT). Coste CFD Upcomers: BTC 1,2 pb, ETH 1,5 pb por operación.
| | Regla | Periodo |
|---|---|---|
| F1 | Laborables de NY: posición en BTC de 15:00 a 16:00 NY = signo de la rentabilidad de BTC de 16:00 NY del día hábil anterior a 15:00 NY (flujos de los ETF siguen a la rentabilidad previa y se ejecutan en la ventana) | 2024-01-11 → final |
| R1 | BTC: de 08:00 a 20:00 UTC posición = −signo(20:00→08:00 previo); de 20:00 a 08:00 posición = −signo(08:00→20:00 previo) | 2025-10-01 → final (fuera de su muestra) |
| R2 | ETH: de 05:00 a 17:00 UTC posición = −signo(17:00→05:00 previo); de 17:00 a 05:00 largo | 2025-10-01 → final |

Criterio de cada una: media neta por operación > 0 con t ≥ 2,13 en su periodo. Informativo (no decide): F1 en 2021-2023 (antes de los
ETF, debería ser ~0 si el mecanismo es el de los ETF); R1/R2 en 2017-2025 (dentro de la muestra del artículo).
Si alguna pasa: después se mide su efecto en la cartera CFD (C116) con el mismo criterio de C116 antes de activarla.
Límite declarado: R1/R2 fuera de muestra tienen ~1 año de datos (poca potencia).
