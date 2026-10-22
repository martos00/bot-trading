# Pre-registro E6 — ¿E1 sigue el reloj de Europa o el de Nueva York en las semanas de desfase horario? — 22-oct-2026
Redactado y enviado a git ANTES de calcular nada para estas semanas por separado.
## Pregunta
E1 = corto EURUSD 06:00→08:00 NY, que normalmente es 12:00→14:00 Frankfurt. En las semanas en que EE. UU. ya ha cambiado de hora
y Europa no (2.º domingo de marzo → último domingo de marzo; último domingo de octubre → 1.er domingo de noviembre) la diferencia es
de 5 h: 06:00-08:00 NY = 11:00-13:00 Frankfurt. Si el flujo es europeo, en esas semanas la ventana buena sería 07:00-09:00 NY.
## Regla
Días laborables de desfase 2010-2026 (fuente: FXCM M1, mid; 2010-2011 con HistData si falta FXCM). Se compara la rentabilidad del
corto en el tramo exclusivo de cada reloj: A = 06:00→07:00 NY (solo reloj NY) frente a B = 08:00→09:00 NY (solo reloj de
Frankfurt); el tramo común 07:00→08:00 se informa. Diferencia D = (corto en B) − (corto en A) por día.
## Decisión (fijada ahora)
Si D > 0 con t ≥ 1,65 (unilateral 5 %): el EA usará el reloj de Frankfurt (12:00-14:00 CET) todo el año. Si D < 0 con t ≤ −1,65:
reloj de NY (como ahora). En otro caso se mantiene el reloj de NY (sin evidencia, no se cambia). Informativo: lo mismo en los
días normales (sin desfase), donde A y B no deberían diferir de la misma forma. Contador +1.
