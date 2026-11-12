# PREREGISTRO C116 — Mejoras de la cartera CFD (Upcomers)

Redactado y subido a git ANTES de calcular (12-nov-2026). Objetivo: subir el Sharpe de la cartera CFD sin reglas nuevas
elegidas mirando datos. Solo se prueban reglas ya fijadas antes (certificadas o preregistradas) con los costes CFD medidos.

## Base
Cartera CFD Upcomers de `cartera_cfd_upcomers.py` (con diarias C93, C99, C101), 2018-03-26 → final de los datos,
control de volatilidad (60 días, 0,5-2). Misma unidad: 0,005 × (r − coste) / sigma por operación, sigma = desviación de toda la muestra
de la propia franja (como en las demás componentes).

## Candidatas (4 pruebas → Bonferroni, t ≥ 2,24 unilateral al 5 % / 4)
| | Regla (ya fijada) | Serie | Coste CFD ida y vuelta | Peso |
|---|---|---|---|---|
| K1 | Bitcoin largo 21→23 UTC laborables (C2) | Binance BTCUSDT 1 h | 1,2 pb (spread 0,36 + comisión 0,04 % por lado) | 0,2 |
| K2 | Euro E2: EURUSD corto 06→08 NY laborables salvo festivos TARGET e Inglaterra (sin la lista del BCE: no disponible) | `c1_precios.csv` punto medio | **0,95 pb** (spread 0,09 + 5 $/lote por lado ≈ 0,86); informativo 0,52 si los 5 $ son ida y vuelta | 1 |
| K3 | C113 oro largo 18:00→03:00 NY dom-jue | GC 1 h (como `c113_cartera.py`) | 1,36 pb (spread 1,11 a las 18:01 + comisión 0,25) | 0,2 |
| K4 | E8 con la salida original 16:55 en vez de 16:45 (Upcomers cotiza hasta 16:59) | `componentes_B` oro_vie_1655 | coste de 16:45 + 0,10 pb (spread de salida más ancho medido) | 1 |

## Criterio (cada candidata por separado, añadida a la base)
1. Sharpe de la cartera con control de volatilidad sube ≥ 0,05 en todo el periodo **y** sube en 2018-21 **y** en 2022-26.
2. K1-K3: media neta por operación de la candidata > 0 con t ≥ 2,24 en 2018-2026. K4 (regla original preregistrada): el tramo
   16:45→16:55 neto del coste extra tiene media > 0 (sin exigir t).
Pasa = 1 y 2. Las que pasen se activan en el EA; las que no, quedan desactivadas (K1 bitcoin incluido, aunque ya esté en el EA).
Después se informa la cartera con todas las que pasan (sin más selección).

## No se hace
- No se prueban otros pesos, horas ni costes para «rescatar» una candidata.
- Reparto del riesgo por volatilidad: aplazado (con estas estrategias sobrepondera las trimestrales; requiere diseño propio).
- Órdenes limitadas: se prueban en demo, no en este backtest.
