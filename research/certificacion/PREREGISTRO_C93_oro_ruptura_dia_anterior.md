# PREREGISTRO C93 — Oro: ruptura del máximo/mínimo del día anterior (vídeo de TikTok «mgp.quant», estrategia 1 de 3) — 28-oct-2026

Redactado y subido a git ANTES de calcular. Fuente: vídeo enviado por el usuario (transcrito con Whisper y revisado fotograma a fotograma).
Lo que dice el vídeo: XAUUSD; marca el máximo y el mínimo de ayer; si hoy, **entre las 14:00 y las 21:00**, el precio rompe uno de esos
niveles, entra a favor; **stop ajustado a la volatilidad**; **objetivo 3 veces el riesgo**; **cierre automático a las 23:00**. Afirma
(backtest de MetaTrader 2020-2026, riesgo 0,5 %, costes incluidos): 1.254 operaciones, +28,7 %, caída máxima 5,3 %, 7/7 años positivos;
89,1 % se cierran a las 23:00, 10,4 % tocan el stop, 0,6 % el objetivo. Eso equivale a ~+0,046 R por operación (~57 R en total).

El vídeo no dice la zona horaria ni la medida exacta de volatilidad. Fijo ahora, sin ver datos:
- **Día** = sesión de 17:00 NY a 17:00 NY (el día del servidor de MetaTrader, UTC+2/+3). Máximo/mínimo de ayer = de esa sesión.
- **Stop** = 1 × ATR(14) de las sesiones diarias anteriores; objetivo = 3 × ATR(14). Informativo: 0,5 y 2 × ATR.
- **Entrada**: la primera ruptura del día dentro de la ventana (una operación al día como máximo). Precio de entrada = el nivel, o la
  apertura del minuto si ya abre por encima/debajo. Si en el mismo minuto se tocan stop y objetivo, cuenta el stop.
- Dos variantes horarias (2 pruebas):
  - **A (hora de servidor, NY+7)**: ventana 07:00 → 14:00 NY, cierre 16:00 NY.
  - **B (hora de España, NY+6)**: ventana 08:00 → 15:00 NY, cierre 17:00 NY (en futuros, 16:45 por la regla de las firmas).

## Datos
HistData XAUUSD M1 (contado, BID; hora de NY con cambio de hora), 2010-06 → 2026-09. Segunda fuente si pasa: futuro GC 1 min.
2010-2019 queda FUERA de la muestra del vídeo: es la prueba independiente.

## Criterio (Bonferroni unilateral 0,05/2 → t ≥ 2,24), sobre el rendimiento por operación en pb (con signo)
Media > 0 con t (Newey-West) ≥ 2,24; ≥ 60 % de años positivos; media > 0 en 2010-2019 y en 2020-2026; media > 1,5 pb (coste del CFD
de oro en FTMO; en futuros GC 0,74 pb). Informativo: resultado en R, reparto stop/objetivo/cierre (para comparar con el vídeo),
control sin stop ni objetivo. Contador +2.
