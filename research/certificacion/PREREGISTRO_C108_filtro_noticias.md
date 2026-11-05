# PREREGISTRO C108 — ¿Mejora la cartera si las estrategias diarias no operan los días de noticias? — 05-nov-2026

Redactado y subido a git ANTES de calcular. Las estrategias que mantienen posición durante noticias de EE. UU. son las diarias:
C93 (oro, ruptura del día anterior), C99 (oro, rango asiático), C101 (Nikkei, rango asiático), C102 (cobre, rango asiático). Las de
franja (viernes, vísperas, yen, Nikkei de trimestre) no coinciden con noticias importantes; E15 sale a las 10:00 (no se toca).
Días de noticias: decisiones del FOMC (fechas oficiales, `n/fomc.csv`) y empleo de EE. UU. (NFP, primer viernes de cada mes).
Datos: las mismas series que certificaron cada estrategia (2010-06 → 2026-09).

## Regla a evaluar
No operar esas estrategias los días de FOMC y NFP. Se adopta solo si, juntando las 4 estrategias, el resultado medio por operación de
los días de noticias es menor que el del resto con t ≤ −2,0 Y el filtro mejora el Sharpe tanto en 2010-17 como en 2018-26.
Si no se cumple, el bot sigue operando igual. Contador +1.
