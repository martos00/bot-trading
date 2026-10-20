# Certificación C1 — EURUSD baja de 06:00 a 08:00 ET (mediodía europeo)

Redactado y enviado a git ANTES de descargar los datos de Dukascopy (20-oct-2026). Es el paso 1 del plan acordado con el
usuario: **certificar una ventaja real antes de diseñar ninguna estrategia**. Aquí no se evalúan costes ni reglas de fondeo.

## Origen
- H80 (barrido de franjas, HistData BID): descubrimiento 2010-2017, corto 06:00-08:00 ET, 1,96 pb/día, t = 5,35;
  confirmación 2018-2026, 1,48 pb/día, t = 4,85 (umbral de Bonferroni 2,87), positiva 8 de 9 años.
- Mecanismo publicado: Breedon & Ranaldo, "Intraday patterns in FX returns and order flow" (SNB WP 2011-04;
  J. Money, Credit and Banking 2013): las divisas se deprecian durante su horario local porque los agentes locales son
  compradores netos de divisa extranjera; citan el EURUSD como estrategia operable. Leído solo el resumen.
  Nuestros dos tramos son posteriores a su publicación.

## Datos nuevos (fuente independiente)
Dukascopy, velas M1 BID y ASK, 2018-01-01 → 2026-09-30, marcas en UTC convertidas a Nueva York. Precio = punto medio
(BID+ASK)/2 al cierre del último minuto ≤ hora (tolerancia 5 min). Días lunes-viernes.

## Criterios de certificación (todos)
- **C1** Dukascopy, punto medio, corto 06:00 → 08:00 ET, 2018-2026: media > 0 con t de Newey-West (5 rezagos) ≥ 3,0.
- **C2** Positiva en ≥ 7 de los 9 años (2018-2026).
- **C3** Concordancia de fuentes: correlación diaria con HistData ≥ 0,9 y diferencia de medias ≤ 0,3 pb.
- **C4** No es un artefacto del spread: |media con punto medio − media con BID| ≤ 0,3 pb; se informa del spread medio a las
  06:00 y a las 08:00 ET.
- **C5** Mecanismo: cubierto por la literatura citada.

## Informativo (no decide la certificación; predicciones escritas antes de mirar)
- Si el mecanismo es "divisa local débil en su horario", en la misma franja GBPUSD también debería bajar (libra en su
  horario). Se informa con HistData (dato ya usado en H80, por eso no decide).
- Franjas vecinas (05-07 y 07-09 ET) con Dukascopy: se espera el mismo signo.
- N acumulado no cambia (364): es la confirmación de una franja de H80, no una hipótesis nueva.
