# Pre-registro B2 — Barrido de franjas horarias con futuros del CME (Databento) — 21-oct-2026

Redactado y enviado a git ANTES de descargar los datos horarios que faltan y de calcular nada. Repite la idea de B1 con datos
limpios (precio de negociación real, sin artefactos de BID; sin rentabilidades entre contratos distintos).

## Universo (15 futuros, contrato continuo por volumen, barras de 1 h)
Índices ES, NQ; bonos ZN, ZB; energía CL, NG; metales GC, SI, HG; grano ZS, ZC; divisas 6E, 6J, 6B, 6A.
(NG, HG, ZS, CL, GC y ZN ya estaban descargados por horas para otras pruebas; ES se agrega desde M1.)

## Reglas
Para cada mercado: ventanas que empiezan en cada hora en punto (hora de NY) y duran 1 o 2 horas, sin tocar la pausa de
17:00-18:00 NY → 44 reglas por mercado, 660 en total. Rentabilidad del cierre de la barra inicial al de la final (mismo contrato).
Dirección = signo en el descubrimiento.

## Tramos y criterios
- Descubrimiento 2010-06 → 2017: |t de Newey-West| ≥ 3,0.
- Confirmación 2018 → 2026-09, para las seleccionadas (k): mismo signo con t unilateral ≥ umbral de Bonferroni (0,05/k);
  ≥ 60% de años con ese signo; neta de 1 tick de ida y vuelta > 0 y bruta ≥ 3 × ese coste.
- Comprobación de control (no cuenta como hallazgo): la franja 06:00-08:00 NY en 6E debería aparecer con signo negativo (E1).
Contador +660 (N ≈ 1.864). Lo que no pase, se descarta; no se prueban variantes de las franjas.
