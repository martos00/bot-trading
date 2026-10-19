# Pre-registro H79 — ORB de 15 minutos en MNQ (bot enviado por el usuario, 19-oct-2026)

Redactado y enviado a git ANTES de ejecutar ningún cálculo con esta regla.

## Fuente
Código Python enviado por el usuario (origen no indicado; no es una estrategia publicada con resultados).
Es de la familia ORB, ya probada en H76 (ORB de 5 min de Zarattini-Aziz: post-publicación sin significación).
Se trata como **hipótesis nueva**: exige t ≥ 3.

## Reglas tal como están en el código
- Rango: máximo y mínimo de las velas de 1 min entre 09:30 y 09:45 ET.
- Órdenes stop OCO: compra en máximo + 2 puntos, venta en mínimo − 2 puntos. Una sola operación al día
  (`posicion_abierta` no se reinicia hasta el cierre).
- Stop a (rango / 2) puntos de la entrada; objetivo a 2 × esa distancia (1:2).
- Contratos = int(0,005 × 50.000 $ / (stop_pts × 2 $)), mínimo 1. Saldo fijo de 50.000 $ (no compone).
- Cierre forzoso a las 15:45 ET.

## Ambigüedades del código y cómo se resuelven (fijado antes de ver resultados)
1. `between_time('09:30','09:45')` incluye la vela de las 09:45, pero el rango se calcula a las 09:45, cuando esa
   vela aún no existe. **Se usan las velas 09:30-09:44** (15 minutos completos, como dice el comentario).
2. La sección 2 del código entra con `close > high` (sin los 2 puntos), y la sección 1 envía stops a ±2 puntos.
   **Se ejecuta lo que se envía al bróker: stops a ±2 puntos**, activados por el máximo/mínimo de la vela.
3. "SL en la mitad de la caja": la distancia es rango/2 **medida desde el precio de entrada**, como en el código.
4. Las órdenes se colocan a las 09:45 y pueden ejecutarse hasta las 15:45; si ninguna se ejecuta, no hay operación.
5. Vela ambigua: si una misma vela toca stop y objetivo, se asume el stop. Si toca las dos órdenes de entrada,
   se toma la más cercana a la apertura de la vela y luego se comprueba su stop en esa misma vela. En la vela
   de entrada, el objetivo solo cuenta si la vela cierra más allá de él (supuesto conservador).
6. Si la vela de las 09:45 abre más allá de una orden stop, se llena a la apertura (gap).

## Datos
HistData NSXUSD M1 (índice Nasdaq-100, zona horaria de Nueva York con horario de verano, verificada en H69) de
2010-01 a 2026-09; sesiones NYSE completas (sin medias sesiones); `calidad_datos` sobre barras diarias. El índice
y el futuro NQ tienen el mismo movimiento intradía salvo la base (constante en el día); se declara como
aproximación. Puntos de NQ = puntos del índice.

## Costes (MNQ, 2 $/punto)
Comisión + tasas 1,50 $ por contrato ida y vuelta. Deslizamiento de 1 tick (0,25 pt) en la entrada stop y en la
salida por stop o cierre; 0 en el objetivo (orden límite). Estrés: 2 ticks y 2,50 $.

## Criterios
Candidata si, neta del caso base, en 2010-2026: media diaria > 0 con **t ≥ 3** (Newey-West), positiva en ≥ 2/3
de los años, positiva en el tramo reciente 2021-2026, y mejor que la misma regla con dirección aleatoria
(p < 0,05, 1.000 réplicas). Dos motores (vectorizado y bucle en Python puro). Simulación de fondeo con
Topstep 50K y FTMO 2-Step aunque no sea candidata (como referencia frente a la tasa base). N acumulado = 94.
