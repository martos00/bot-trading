# PREREGISTRO C98 y C99 — Dos estrategias populares sin probar: «el hueco del CME en bitcoin se cierra» y la ruptura del rango asiático — 28-oct-2026

Redactado y subido a git ANTES de calcular.

## C98 — Hueco de fin de semana del futuro de bitcoin del CME
Creencia popular: el precio vuelve a cerrar el hueco entre el cierre del CME del viernes (17:00 NY) y la reapertura del domingo (18:00 NY).
Equivale a apostar por la reversión del movimiento del fin de semana.
- Datos: Binance BTCUSDT y ETHUSDT 1 h (precio = apertura de la vela), 2017-08 → 2026-09 (ETH desde 2017-08). Hora de NY con cambio de hora.
- Regla: g = ln(P dom 18:00 / P vie 17:00). Si |g| > 0: posición contraria a g del domingo 18:00 al lunes 16:00 NY (dentro del horario de
  las firmas de futuros); si el precio toca el cierre del viernes antes, se sale ahí (hueco cerrado). Sin stop.
- 2 pruebas (BTC, ETH). Criterio: media > 0 con t (Newey-West) ≥ 2,24; ≥ 60 % de años positivos; media > coste del micro (BTC 3 pb,
  ETH 4 pb); > 0 en 2017-21 y 2022-26. Informativo: % de huecos cerrados antes del lunes 16:00 y antes del viernes.

## C99 — Ruptura del rango asiático («London breakout»)
- Rango = máximo/mínimo de 19:00 NY (día anterior) a 03:00 NY. Ventana de ruptura 03:00 → 11:00 NY; primera ruptura; entrada al nivel
  (o a la apertura del minuto si abre más allá); stop = el otro extremo del rango; objetivo = 1 × la anchura del rango; cierre 16:45 NY.
  Si en el mismo minuto se tocan stop y objetivo, cuenta el stop. Días laborables.
- 4 pruebas: oro (XAUUSD), EURUSD, GBPUSD, USDJPY. Principal HistData M1 2010-06 → 2026-09; confirmación Databento 1 h (GC, 6E, 6B, 6J;
  misma regla en barras horarias, contratos que cambian excluidos).
- Criterio (Bonferroni unilateral 0,05/4 → t ≥ 2,50): HistData media > 0 con t ≥ 2,50, ≥ 60 % de años positivos, > 0 en 2010-19 y en
  2020-26, media > coste del futuro (GC 0,74; 6E 0,6; 6B 0,8; 6J 0,8 pb); y Databento media > coste con t ≥ 2,0.
Contador +6.
