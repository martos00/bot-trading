# C112 y C113 — Resultados — 06-nov-2026
Preregistros `PREREGISTRO_C112_momentum_sesiones_oro_plata.md`, `PREREGISTRO_C113_oro_sesion_asiatica_2003_2009.md`. Salidas `c112_resultados.txt`, `c113_resultados.txt`.

## C112 — Momentum entre sesiones (inspirado en Wei 2026; artículo no leído, solo el resumen)
- Oro: pasa los criterios formales (HistData +4,66 pb neto, t 4,32; GC +2,50, t 2,38) PERO la señal no aporta: los días con el día anterior
  negativo dan lo mismo (+4,20). Lo que hay es que **el oro sube en la sesión asiática todos los días** (control +4,42 pb, t 5,39; GC +2,41, t 2,84).
- Plata: no pasa (futuros SI −0,88 pb): lo de HistData en plata es del dato de contado, no del futuro.
No se adopta la señal de momentum. Contador +2.

## C113 — Oro largo 18:00 → 03:00 NY todos los días, fuera de muestra 2003-2009 (Dukascopy, precio medio): PASA
+5,34 pb neto (t 4,12), 7/7 años positivos; por hora Asia +0,68 pb frente a +0,26 el resto del día (no es solo la tendencia del oro).
Plata informativo +22,9 pb: datos de Dukascopy de plata poco fiables (C106) y sin confirmación en futuros: no se usa.
**Fuentes que lo apoyan:** contado 2010-26 (HistData), futuros GC 2010-26 (+2,41 pb, t 2,84; la mitad que en contado), contado 2003-09 (Dukascopy).
**En la cartera de 150K (futuros GC, coste 0,74 pb, peso de diaria 0,2):** Sharpe 2,32 → 2,40 (2018-21 2,01 → 2,03; 2022-26 2,56 → 2,68);
correlación con la cartera −0,02 y con C99 +0,03. Con peso 0,5 o 1 empeora (es una ventaja pequeña por operación: R esperado al 60 % +0,028).
Se añade al bot (`C113_oro_asia`, peso 0,2, ~1 MGC en 150K). Aviso: en futuros es la mitad que en contado; vigilar con `vigilancia.py`.
Contador +1.
