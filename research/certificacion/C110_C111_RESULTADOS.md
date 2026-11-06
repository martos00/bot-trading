# C110 y C111 — Resultados — 06-nov-2026
Preregistros: `PREREGISTRO_C110_configuracion_150k.md`, `PREREGISTRO_C111_yen_festivos_japon.md`. Salidas `c110_resultados.txt`, `c111_resultados.txt`.

## C110 — Configuración de la cartera de 150K (2018-11 → 2026-09)
| Variante | Sharpe | 2018-21 | 2022-26 | Caída (desv. diarias) | Decisión |
|---|---|---|---|---|---|
| V0 actual | 2,38 | 2,11 | 2,56 | −17,1 | referencia |
| V1 sin control de volatilidad | 2,11 | 2,34 | 1,98 | −35,8 | no |
| V2 paridad de riesgo por componente | 1,85 | 1,90 | 1,86 | −10,6 | no |
| V3 + cobre C102 | 2,45 | 2,46 | 2,45 | −17,1 | no (2022-26 por debajo de V0) |
| V4 + cobre con paridad | 1,93 | 2,23 | 1,80 | −9,8 | no |
**Se queda V0.** El cobre sube el Sharpe total (2,38 → 2,45) y el de 2018-21, pero no el de 2022-26: según la regla no se adopta como
mejora; es opcional (diversifica) si la firma ofrece MHG. La paridad de riesgo baja la caída pero también el Sharpe. Contador +4.

## C111 — USDJPY antes de los festivos de Japón: NO PASA
Sin días gotobi: HistData n 59, +0,44 pb (t 0,29); FXCM +0,83 (t 0,52); control +0,80. El efecto del festivo no existe por sí solo.
Informativo con gotobi: +3,70 pb (t 2,37), es el efecto gotobi (C10), no del festivo. Contador +1.
