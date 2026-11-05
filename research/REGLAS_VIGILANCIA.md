# Reglas de vigilancia del bot en real (fijadas el 05-nov-2026, ANTES de operar)

Objetivo: cortar a tiempo lo que deje de funcionar sin tocar lo que va bien y sin cambiar reglas a la vista de los resultados.
Se revisan **una vez al mes** con `certificacion/vigilancia.py` sobre `CarteraFuturos_log.csv`. Ninguna regla se cambia después:
para cambiar algo hace falta un preregistro nuevo.

Unidad: resultado de cada operación en **desviaciones** (R = rentabilidad de la operación / sigma usada por el bot al entrar).
Lo esperado en real (60 % del backtest) por operación: oro viernes +0,13 · plata viernes +0,10 · plata víspera +0,21 · yen fin de mes
+0,16 · cesta yen +0,21 · oro D-2 +0,11 · Nikkei Q+2 +0,24 · Nikkei Q-2 +0,12 · cobre/oro/Nikkei rango asia y oro C93 +0,01-0,02.

**Aviso importante (honesto):** la ventaja por operación es pequeña frente al ruido. Distinguir «funciona» de «no funciona» en una
estrategia concreta lleva ~250 operaciones en el oro del viernes (~5 años) y ~400 en la plata; la cartera entera, ~3 años. Por eso
las reglas solo detectan rápido los fallos grandes (ejecución, costes, errores); un desgaste lento se verá tarde.

## 1. Ejecución (rápidas, cada semana)
- **Fallo técnico** (no entró en una ventana que tocaba sin motivo registrado, salió tarde, posición olvidada): se para la cuenta
  afectada hasta corregirlo. Cero tolerancia.
- **Coste:** si el deslizamiento + comisión medio de las últimas 20 operaciones de una estrategia supera **1,5 veces** el supuesto
  (oro 0,74 pb, plata 2,3, yen 0,8, Nikkei 1,5), esa estrategia se pone a la mitad de tamaño hasta revisarlo.

## 2. Estrategias (lentas, cada mes)
- **Mitad de tamaño:** con ≥ 50 operaciones reales, si la media en R está por debajo de cero con z ≤ −1,5.
- **Fuera:** con ≥ 50 operaciones reales, si z ≤ −2,0 (claramente negativa). Solo vuelve con un preregistro nuevo.
- Las de pocas operaciones al año (yen, oro D-2, Nikkei Q±2, vísperas) se evalúan juntas como grupo «calendario».
- **Oro del viernes (riesgo de régimen, C106):** si la media de los **últimos 104 viernes** (2 años) es ≤ 0 → mitad de tamaño
  (en 2018-2026 nunca ocurrió). Si además z ≤ −2 → fuera.
- **Plata del viernes:** mitad si la media de los últimos 104 viernes tiene z ≤ −2 (en 2018-2026 nunca ocurrió; con 52 viernes
  saldrían falsas alarmas el 25 % del tiempo, por eso no se usa la ventana corta).

## 3. Cartera y cuentas
- **Caída:** si la caída de una cuenta supera el **percentil 99** de la simulada a 12 meses para su riesgo, se baja el riesgo a la
  mitad en todas las cuentas hasta recuperar la mitad de esa caída.
- **Escalar (comprar más cuentas):** solo si tras 6 meses reales no hay fallos técnicos y el resultado acumulado en R es ≥ 0.
- **Dejar de escalar:** si tras 12 meses reales el Sharpe de la cartera en real es < 0 (con ≥ 150 operaciones): se mantienen 1-2
  cuentas y se revisa todo.
