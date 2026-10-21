# Pre-registro C35 — Base de los futuros del VIX (Simon y Campasano, Journal of Derivatives 2014) — 21-oct-2026

Redactado y enviado a git ANTES de descargar los futuros del VIX y de calcular nada.
## Fuente (resumen conocido; no texto completo)
La base (futuro − VIX al contado) no predice cambios del VIX de contado, sino del futuro: el futuro converge al contado.
Regla del estudio: rodamiento diario = (VX1 − VIX) / días hábiles hasta el vencimiento; si > 0,10 → corto en VX1; si < −0,10 →
largo; solo con ≥ 10 días hábiles hasta el vencimiento (si no, se usa el segundo vencimiento). Muestra del estudio 2006-2011.
## Datos
Futuros del VIX del CBOE (liquidación diaria por contrato, cdn.cboe.com, gratuitos); VIX al contado (VIX_History del CBOE).
## Regla (idéntica a la del estudio)
Cada día t con la señal del cierre de t, posición en el futuro elegido hasta el cierre de t+1. Resultado en puntos de VIX por
contrato (1 punto = 1.000 $). Coste: 0,05 puntos por ida y vuelta (1 tick) cada vez que cambia la posición o el contrato.
## Tramos y criterios
Descubrimiento 2013-2014; **confirmación 2015-2026-09** (después de la publicación): media diaria neta > 0 con t ≥ 2,0 y
≥ 60% de años positivos. Informativo: peor día y caída máxima en puntos (riesgo de cola, p. ej. feb-2018 y mar-2020).
Contador +1 (N ≈ 1.804). Aviso: el riesgo de cola de vender volatilidad puede romper cualquier límite de pérdida diaria.
