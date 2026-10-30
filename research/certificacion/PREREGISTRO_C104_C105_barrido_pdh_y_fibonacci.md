# PREREGISTRO C104 y C105 — Dos vídeos de TikTok: barrido del máximo/mínimo de ayer y retrocesos de Fibonacci — 30-oct-2026

Redactado y subido a git ANTES de calcular. Fuente: dos vídeos enviados por el usuario (transcritos con Whisper y revisados).

## C104 — Barrido del máximo/mínimo de ayer (PDH/PDL) con vela de confirmación
Lo que dice el vídeo: si una vela perfora el máximo de ayer y su cuerpo vuelve abajo (solo deja mecha) es un barrido; esperar una
vela bajista que cierre por debajo de la vela del barrido y vender al cierre; stop encima de la mecha; objetivo el mínimo de ayer;
si antes una vela cierra con cuerpo por encima del máximo de ayer, no hay operación. Simétrico en el mínimo de ayer (compra).
El vídeo no dice la temporalidad: se fija **velas de 15 min** (la habitual en estos contenidos).
- Día = sesión 17:00 → 17:00 NY; PDH/PDL = máximo/mínimo de la sesión anterior (como C93).
- Ventana de búsqueda 03:00 → 15:00 NY; una operación al día (la primera señal); si no toca stop ni objetivo, cierre 16:45 NY.
- Vela de barrido (venta): máximo > PDH y cierre < PDH. Disparo: vela posterior bajista (cierre < apertura) con cierre < mínimo de la
  vela de barrido; entrada al cierre del disparo; stop = máximo de la vela de barrido; objetivo = PDL. Anula: cualquier vela que cierre
  > PDH antes del disparo. Si el objetivo ya está más cerca que 0,5 × la distancia al stop, se opera igual (regla del vídeo).
- Mercados (5 pruebas): oro (XAUUSD), EURUSD, USDJPY, GBPUSD (HistData M1 → 15 min, 2010-06 → 2026-09) y S&P 500 (ES, Databento 1 min).
- Confirmación (si pasa): oro con el futuro GC 1 min (Databento). Costes: oro 0,74 pb, EUR 0,6, JPY 0,8, GBP 0,8, ES 0,73.
- Criterio (Bonferroni unilateral 0,05/5 → t ≥ 2,58): media > coste con t ≥ 2,58, ≥ 60 % de años positivos, > 0 en 2010-17 y 2018-26.
  Informativo: % de aciertos (el vídeo vende acierto) y resultado en R.

## C105 — Retrocesos de Fibonacci
Lo que dice el vídeo: tras una subida, el precio rebota en el 38,2 / 50 / 61,8 % porque ahí se acumulan órdenes; no comprar solo por
tocar la línea: esperar que frene y salga una vela verde con volumen. Regla mecánica fijada ahora (velas diarias):
- Tramo: en cada día t, máximo (H) y mínimo (L) de los 20 días anteriores, con el máximo posterior al mínimo y H/L ≥ 1 + 2 × ATR(20)/precio.
- Para cada nivel k: precio P_k = H − k × (H − L). Toque = primer día después del máximo en que el mínimo diario ≤ P_k (sin haber hecho
  antes un máximo nuevo). Confirmación (versión del vídeo): ese día o el siguiente cierra en verde (cierre > apertura) y por encima de
  P_k → compra al cierre; stop = mínimo del día de toque − 0,5 ATR; objetivo = H; máximo 10 días.
- Prueba central (¿son especiales los niveles de Fibonacci?): resultado medio en los niveles de Fibonacci (38,2, 50, 61,8 %) frente a
  niveles de control no Fibonacci (30, 45, 55, 70 %). Diferencia > 0 con t ≥ 2,0 → los niveles sí importan.
- Prueba de estrategia: resultado medio de las compras en 38,2/50/61,8 con confirmación > coste con t ≥ 2,24 (Bonferroni 2) y > 0 en
  2010-17 y 2018-26. Simétrico a la baja (ventas tras caídas) incluido.
- Mercados (cesta, igual peso): oro, plata, EURUSD, GBPUSD, USDJPY, AUDUSD (HistData) + S&P 500 (ES Databento) + crudo, gas, bonos
  10 años (Databento diarios), 2010-06 → 2026-09. Coste 1,5 pb por operación (media aproximada de futuros).
Contador +7.
