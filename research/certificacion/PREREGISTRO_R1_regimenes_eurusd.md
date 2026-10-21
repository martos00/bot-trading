# Pre-registro R1 — ¿Depende la ventaja certificada C1 (EUR/USD corto 06→08 NY) del régimen de mercado?

Redactado y enviado a git ANTES de calcular nada (21-oct-2026). Origen: propuesta del usuario a partir de un vídeo
(@tradingstraty) sobre estrategias por régimen. Se aplica a una ventaja ya certificada, no para crear una nueva.

## Regímenes (dos variables, fijadas aquí, solo con información anterior al día de la operación)
- **Volatilidad**: σ = desviación típica de la rentabilidad de la franja en los 60 días anteriores (la misma que usa el
  tamaño de E1). Alta si σ > mediana expandida de σ hasta el día anterior (mínimo 250 días de historia); baja si no.
- **Tendencia**: cierre diario del EUR/USD del día anterior frente a su media de 200 días: por encima = alcista,
  por debajo = bajista (cierre = último minuto del día de Nueva York, HistData).

## Datos
- Descubrimiento 2010-2017: serie de H80 (HistData, `h06_d2`, la que descubrió la franja).
- Confirmación 2018-2026: serie certificada de C1 (FXCM + Dukascopy, punto medio).

## Criterio para adoptar un filtro (todos; si no, la estrategia queda SIN filtro)
1. En el descubrimiento, la diferencia de medias entre los dos regímenes de una variable tiene |t| ≥ 2,5 (Bonferroni para 2
   variables, bilateral, con margen).
2. En la confirmación, la diferencia va en el mismo sentido con t unilateral ≥ 2,0.
3. En la confirmación, la estrategia filtrada (operar solo en el régimen bueno), neta del coste medio (0,53 pb), tiene un
   Sharpe mayor que la estrategia sin filtro.
Se informan las medias de los 4 regímenes combinados (volatilidad × tendencia) solo como información; no se elige ninguna
combinación con ellos. N acumulado del proyecto: +2.
