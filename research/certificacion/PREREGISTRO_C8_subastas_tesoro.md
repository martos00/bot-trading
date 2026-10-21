# Pre-registro C8 — Ciclo de subastas del Tesoro de EE. UU. en futuros de bonos (Lou, Yan y Zhang 2013) — 21-oct-2026

Redactado y enviado a git ANTES de descargar las fechas de subasta y de calcular ningún resultado (las series de
rendimientos de FRED se descargaron, sin calcular nada con ellas).

## Fuente (texto completo leído: FMG Discussion Paper 684 / RFS 26(8), 2013)
Muestra 1980 → jun-2008, notas on-the-run (CRSP, precio medio). Los precios caen en los días previos a cada subasta y
se recuperan después. Notas a 5 años: el rendimiento sube 2,67 pb en los 5 días previos y baja 2,73 pb en los 5
posteriores; la rentabilidad de 5 días antes es 22,54 pb (t 3,67) menor que la de 5 días después. 2 años: 2,53 / 2,32 pb.
10 años: 1,57 / 2,00 pb (diferencia 23,84 pb, t 1,78). Su estrategia (largo-corto con cobertura de duración) da un Sharpe
de 1,08 (1,44 en 1998-2008). Mecanismo: los dealers primarios tienen capacidad limitada de asumir riesgo y los inversores
finales no mueven el capital al instante, así que el precio se abarata para absorber cada emisión.

## Operación (implementable con el futuro ZF, nota a 5 años del CME)
Para cada subasta de la nota a 5 años (sin TIPS ni bonos flotantes), día 0 = fecha de la subasta:
- **Corto** del cierre del día −5 al cierre del día 0; **largo** del cierre del día 0 al cierre del día +5
  (días = sesiones con dato en FRED).
- Rentabilidad de precio aproximada con el rendimiento a plazo constante DGS5 (FRED) y un bono a la par a 5 años
  revalorizado cada día (como en H72); el paper usa el precio on-the-run de CRSP (aproximación declarada).
- Fechas de subasta: API pública de Fiscal Data del Tesoro (`auctions_query`).
- Si dos subastas a 5 años quedan a menos de 11 sesiones, se usa solo la primera.

## Costes (futuros, por ciclo completo)
Entrada corta, cambio a larga y salida = dos idas y vueltas: 2 × (1 tick de 7,8125 $ + 4 $ de comisión) sobre el nominal
del ZF (≈ 100.000 $ × precio/100) ≈ 2,2 pb por ciclo.

## Tramos y criterios
- **Réplica 1990 → jun-2008** (dentro del paper): diferencia (corto antes + largo después) > 0. Si no, la reproducción
  no es fiel y se investiga antes de concluir.
- **Confirmación jul-2008 → sep-2026** (posterior a su muestra y a la publicación), todos:
  1. Media neta por ciclo > 0 con t ≥ 2,0.
  2. Media bruta ≥ 3 × coste.
  3. Neto positivo en ≥ 60% de los años.
- Informativo (no decide): lo mismo con la nota a 2 años (DGS2, futuro ZT) y a 10 años (DGS10, futuro ZN, incluidas
  reaperturas); cada pata por separado; correlación con E1; peor ciclo.
Contador: +1 prueba principal (N acumulado ≈ 1.159). Si falla, se descarta sin cambiar ventana ni plazo.
