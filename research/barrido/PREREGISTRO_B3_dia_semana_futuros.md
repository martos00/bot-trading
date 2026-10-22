# Pre-registro B3 — Barrido de día de la semana en 27 futuros del CME — 22-oct-2026
Redactado y enviado a git ANTES de calcular ninguna rentabilidad por día de la semana con estos datos (salvo el gas natural
del jueves, ya conocido por F1, que sirve de control positivo y no cuenta como hallazgo).
## Motivo
Los flujos con calendario semanal (inventarios EIA, informes del USDA, COT, liquidaciones, vencimientos de opciones semanales)
pueden dejar huella por día de la semana. Nunca se ha barrido de forma sistemática (B1/B2 barrieron horas, no días).
## Datos y regla
- 16 materias primas de C34 (c.0 diario), ZN/ZB/ZF (v.0 diario), y 6A 6B 6E 6J NQ RTY YM (h1 → cierre diario por día UTC) y ES
  (1 min → cierre diario por día UTC). Todas las barras diarias de Databento cierran a las 00:00 UTC; se usa lo mismo para las
  horarias. Sin rentabilidades entre contratos distintos. Días sábado/domingo fuera (el lunes = viernes → lunes).
- Regla k = (mercado, día): estar en el mercado solo ese día de cierre a cierre, con el signo que diga el descubrimiento.
  27 × 5 = 135 reglas.
- Coste por operación: 3 pb materias primas, 1,5 pb futuros financieros.
## Tramos y criterios
Descubrimiento 2010-06 – 2017: se seleccionan las reglas con |t (Newey-West)| ≥ 3,0. Confirmación 2018 – 2026-09, para
cada seleccionada con el signo del descubrimiento: (1) t ≥ umbral de Bonferroni unilateral 0,05/k_sel; (2) ≥ 60 % de años con el
signo; (3) bruto ≥ 3 × coste. Si nada se selecciona, se informa la tabla y no se certifica nada. Contador +135.
