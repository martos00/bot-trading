# PREREGISTRO C110 — Mejor configuración de la cartera para cuentas de 150K — 06-nov-2026

Redactado y subido a git ANTES de calcular. Pregunta: ¿alguna configuración sin parámetros ajustados sube el Sharpe de la cartera de 150K
frente a la actual de forma estable? Serie: `componentes_B.csv` (2018-03 → 2026-09, a riesgo base 0,5 %), mismas reglas de entrada/salida.

## Variantes (fijadas ahora; ninguna se ajusta con los datos)
- V0 actual: 8 componentes de 150K (yen, cesta_yen, oro viernes, oro D-2, plata víspera, plata viernes, Nikkei Q+2, Q-2), mismo riesgo
  por operación, control de volatilidad (escala = σ larga / σ 60 d, 0,5-2).
- V1 sin control de volatilidad.
- V2 paridad de riesgo por componente: cada componente escalado a la misma volatilidad anual (con su σ de los 252 días anteriores, sin mirar
  el futuro), luego control de volatilidad de la cartera.
- V3 V0 + cobre C102 (peso 0,2, como en el bot) — solo si la firma ofrece MHG.
- V4 V0 + cobre con paridad de riesgo (V2 + C102).

## Criterio
Se adopta una variante solo si mejora el Sharpe de V0 en los DOS periodos 2018-03→2021-12 y 2022-01→2026-09 y en el total, y la caída máxima
al mismo riesgo anual no empeora más de un 10 %. Si varias cumplen, la más sencilla. Si ninguna, se queda V0. Contador +4.
