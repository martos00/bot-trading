# Pre-registro C17 — Deriva antes de datos macro de las 10:00 (Kurov, Sancetta, Strasser y Wolfe, JFQA 2019) — 21-oct-2026

Redactado y enviado a git ANTES de calcular ningún resultado.

## Fuente (versión de trabajo de 2015 leída; tabla 5)
E-mini S&P 500 y futuro del bono a 10 años, ene-2008 → mar-2014: en varias publicaciones el precio empieza a moverse en la
dirección "correcta" unos 30 minutos antes y esa deriva es, de media, la mitad del ajuste total. Con deriva significativa:
ISM no manufacturero, producción industrial, ventas pendientes de viviendas, PIB preliminar, ventas de viviendas usadas,
ISM manufacturero y confianza del consumidor del Conference Board. Causas propuestas: filtraciones y previsiones con datos
privados. Aviso: varios emisores privados cerraron sus accesos anticipados hacia 2013-2014.

## Implementación (la dirección del dato no se conoce: se sigue la deriva)
- Eventos con calendario fijo y gratuito (aproximación declarada: no se corrigen los meses con fechas atípicas):
  ISM manufacturero = 1.er día hábil del mes; ISM no manufacturero = 3.er día hábil; confianza del Conference Board = último
  martes del mes. Todos a las 10:00 NY.
- Regla: a las 09:55 se toma posición en el sentido del movimiento 09:30 → 09:55 y se cierra a las 10:30.
- Datos: HistData SPXUSD M1 (hora NY). Coste 1,0 pb ida y vuelta. Informativo: Nasdaq 100; acierto del signo.

## Tramos y criterios (una prueba conjunta de los tres eventos)
- Descubrimiento nov-2010 → mar-2014 (dentro del estudio): media bruta > 0.
- Confirmación abr-2014 → sep-2026 (todos): (1) media neta > 0 con t ≥ 2,0; (2) bruta ≥ 3 × coste; (3) neta positiva en
  ≥ 60% de los años. Contador +1 (N ≈ 1.172). Si falla, se descarta sin cambiar ventanas ni eventos.
