# Pre-registro C7 — Cambio de mes y víspera de festivo en el S&P 500 (21-oct-2026)

Redactado y enviado a git ANTES de descargar los datos y de calcular ningún resultado.

## Fuentes y mecanismo
- **Cambio de mes:** Ariel (1987); Lakonishok y Smidt (1988), Dow Jones 1897-1986; McConnell y Xu (2008). La subida media
  del índice se concentra en el último día del mes y los primeros días del siguiente. Mecanismo propuesto: entradas de
  dinero periódicas (nóminas, aportaciones a planes de pensiones y fondos) que se invierten a principio de mes.
- **Víspera de festivo:** Ariel (1990); Lakonishok y Smidt (1988): la rentabilidad del día anterior a un festivo bursátil
  es varias veces la de un día normal. Mecanismo propuesto: cierre de posiciones cortas y optimismo antes del festivo.
- Ya probado en el proyecto: cambio de mes en USTEC/US500/XAUUSD **solo con 2023-2026** (44 episodios, sin potencia;
  descartado por "evidencia débil"). Aquí se repite con la misma ventana y 36 años. Contaminación declarada: esos
  44 meses caen dentro del tramo de confirmación.

## Datos
Yahoo, cierres diarios: **S&P 500 (^GSPC)** (prueba principal) y **Nasdaq 100 (^NDX)** (informativo), 1990-01 → 2026-09.
Rentabilidad = cierre a cierre (convención de los estudios). Días de sesión = días con dato.

## Reglas (sin parámetros que ajustar)
- **R1 Cambio de mes (ventana de Lakonishok y Smidt, la misma que la prueba anterior):** comprado del cierre de la sesión
  −2 al cierre de la sesión +3, siendo −1 la última sesión del mes y +1..+3 las tres primeras del mes siguiente
  (4 sesiones de rentabilidad).
- **R2 Víspera de festivo:** comprado del cierre de la sesión anterior al cierre de la víspera; víspera = sesión cuyo
  siguiente día laborable (lunes-viernes) no tiene sesión. Se excluyen los cierres no programados: 11-14 sep 2001,
  29-30 oct 2012, 11 jun 2004, 2 ene 2007, 5 dic 2018, 9 ene 2025 (y la sesión anterior a cada uno no cuenta como víspera).
  Si una sesión es a la vez víspera y parte de la ventana de cambio de mes, cuenta en las dos reglas (se informa).

## Costes de CFD de fondeo (por operación)
Spread 0,5 pb (ida y vuelta) + financiación de la posición larga 2,0 pb por noche natural mantenida (como en N1-N3).
R1 ≈ 7 noches naturales por operación; R2 ≈ 1-3.

## Tramos y criterios (para cada regla; 2 pruebas → umbral de Bonferroni t ≥ 2,24)
- **Descubrimiento 1990-2007:** media diaria en la ventana mayor que en el resto de sesiones, t de la diferencia ≥ 2,0.
- **Confirmación 2008-2026-09 (las cuatro):**
  1. Media neta por operación > 0 con t ≥ 2,24.
  2. Diferencia de medias diarias ventana − resto > 0 con t ≥ 1,645 (que no sea solo la subida general de la bolsa).
  3. Neto positivo en ≥ 60% de los años.
  4. Media bruta por operación ≥ 3 × coste.
- Informativo: Nasdaq 100 con las mismas reglas; correlación con E1; peor operación y caída máxima con un riesgo del 0,5%.
Contador: +2 (N acumulado ≈ 1.158). Si una regla falla, se descarta sin cambiar ventana ni días.
