# Nasdaq de madrugada (NQ largo 01:00 → 03:00 NY): exploración y prueba hacia delante (21-oct-2026)

Salió de B2 (barrido) como la franja nueva más prometedora sin llegar al umbral (2018-2026 +1,34 pb, t 2,55). Exploración
(no certifica; `nq_madrugada_exploracion.txt`): positiva en 15 de 17 años; 2010-2017 +1,9 pb (t 4,81), 2018-2020 +2,2 pb,
**2021-2026 +0,9 pb (t 1,67)**: se ha debilitado, como dicen los autores del "overnight drift" (Boyarchenko, Larsen y
Whelan), pero sigue positiva. El efecto está repartido entre las 00:00 y las 04:00 (apertura de Europa).
Coste: futuro NQ ≈ 0,3 pb (1 tick); un CFD de Nasdaq de madrugada suele tener 0,5-1 pb o más → solo tiene sentido con futuros.

## Pre-registro F2 — prueba hacia delante (reglas congeladas desde hoy)
Largo del futuro NQ de 01:00 a 03:00 NY cada día laborable. Medición con Databento o el registro de la demo.
Por etapas (mismo esquema que F1): cada 250 días, descartar si la t acumulada hacia delante ≤ −1; certificar con t ≥ 2.
Mientras tanto, como mucho riesgo pequeño (≤ 1/4 del de E1) y solo con coste de futuros.
