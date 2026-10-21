# Pre-registro C15 — Gas natural el día del informe EIA y ciclo de semanas pares del FOMC (21-oct-2026)

Redactado y enviado a git ANTES de descargar los datos del gas y de calcular ningún resultado.

## N — Día del informe de almacenamiento de gas (Prokopczuk, Wese Simen y Wichmann, Energy Journal 2021; leído el resumen)
Más de la mitad de la rentabilidad anual del futuro de gas natural se produce los días del informe semanal de la EIA
(jueves 10:30 ET), sin que lo explique la sorpresa del dato. Mecanismo propuesto: prima por riesgo de anuncio.
- **Regla:** largo del futuro de gas (Yahoo `NG=F`, continuo) del cierre del miércoles al cierre del jueves. Aproximación
  declarada: se usan todos los jueves con dato (las semanas con festivo el informe se mueve; no se corrige). Días de cambio
  de contrato (|r| > 5 desviaciones típicas de 60 días) anulados.
- Coste: futuro NG, 1 tick (10 $) + 4 $ sobre ≈ 30.000 $ ≈ 5 pb; estrés CFD 15 pb.

## F — Ciclo del FOMC (Cieslak, Morse y Vissing-Jorgensen, JF 2019; leído el resumen)
Desde 1994 la prima de la bolsa de EE. UU. se gana en las semanas pares (0, 2, 4, 6) del ciclo del FOMC; la semana 0 empieza
el día antes del anuncio. Mecanismo propuesto: flujo de información de la Fed.
- **Regla:** días del ciclo k = sesiones desde el anuncio (anuncio = 0); semana 0 = días −1…+3, semana 1 = +4…+8, etc.
  (semanas de 5 sesiones). Largo del S&P 500 (^GSPC) en semanas pares, fuera en impares. Fechas de `fechas_fomc.py`.
- Coste: futuro ES, 0,6 pb por entrada y salida.

## Tramos y criterios (2 pruebas → t ≥ 2,24)
- N: descubrimiento 2001-2016 (≈ muestra del estudio) media > 0; **confirmación 2017 → 2026-09**: (1) media neta > 0 con
  t ≥ 2,24; (2) bruta ≥ 3 × coste; (3) neta positiva en ≥ 60% de los años; informativo: jueves frente al resto de días.
- F: descubrimiento 1994-2016 (muestra del estudio) diferencia pares − impares > 0; **confirmación 2017 → 2026-09**:
  (1) diferencia de medias diarias pares − impares > 0 con t ≥ 2,24; (2) estrategia neta > 0; (3) pares > impares en ≥ 60% de años.
Contador +2 (N ≈ 1.170). Lo que falle se descarta sin cambiar días ni ventanas.
