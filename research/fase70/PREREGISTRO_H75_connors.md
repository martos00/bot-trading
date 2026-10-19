# Pre-registro H75 — Estrategias de timing del S&P 500 de Connors & Alvarez (2009)

Redactado y enviado a git ANTES de calcular ningún resultado.

## 1. Fuente y fidelidad
Connors & Alvarez, *Short Term Trading Strategies That Work* (2009); backtests del libro con datos
1995-2007. **Fuente leída: un resumen de 61 páginas del libro** (thechartist.com.au) con las reglas
literales del capítulo "Five Strategies To Time The Market" y los capítulos de RSI(2), Double 7's y
salidas. No he podido leer el libro completo, así que no tengo sus tablas de resultados; la
fidelidad se contrasta con una réplica de terceros (StrategyQuant, Double 7's en SPY 1993-2026:
333 operaciones, PF 2,35, Sharpe 0,85, MDD 12,5%).

Diferencia material con la prueba anterior (`hipotesis_rsi2_sma200.py`): aquella midió la señal
RSI(2) sin reglas de salida en CFD 2023-2026; aquí se reproducen las estrategias completas con
datos de SPY desde 1993 y 2008-2026 como período fuera de muestra respecto al libro.

## 2. Reglas (literales; todas en SPY diario, entrada y salida al cierre, 100% del capital, sin stop)
| Id | Estrategia | Entrada | Salida |
|---|---|---|---|
| H75a | VIX Stretches | SPY > SMA200; VIX ≥ 1,05 × SMA10(VIX) durante ≥ 3 días seguidos | RSI2(SPY) > 65 |
| H75b | VIX RSI | SPY > SMA200; RSI2(VIX) > 90; apertura de VIX hoy > cierre de VIX ayer; RSI2(SPY) < 30 | RSI2(SPY) > 65 |
| H75c | Cumulative RSI | SPY > SMA200; RSI2(hoy) + RSI2(ayer) < 45 | RSI2(SPY) > 65 |
| H75d | S&P Short | SPY < SMA200; ≥ 4 cierres alcistas seguidos → corto | cierre < SMA5 |
| H75e | Double 7's | SPY > SMA200; cierre = mínimo de los 7 últimos cierres | cierre = máximo de los 7 últimos cierres |
| H75f | RSI(2) < 5 | SPY > SMA200; RSI2 < 5 | cierre > SMA5 (salida preferida del libro) |
| — | TRIN | **No reproducible**: no hay serie TRIN gratuita; no se sustituye | — |

RSI de Wilder de 2 periodos. Una sola posición por estrategia; si ya hay posición, se ignoran las
nuevas señales. Las condiciones se evalúan con el cierre del día y se ejecutan a ese cierre (en
la práctica, orden al cierre o a las 15:59).

## 3. Datos y costes
SPY y ^VIX diarios de Yahoo (SPY desde 1993; VIX desde 1990). Señales con el cierre sin ajustar por
dividendos (como en el libro); resultados con rentabilidad total (precio ajustado). Auditoría con
`calidad_datos`.

Costes por escenario: (i) ETF: 0,0045 $/acción por lado; (ii) **CFD de prop firm**: spread de
0,5 pt del índice (≈1 pb por ida y vuelta) + financiación diaria en largo de (tipo a 3 meses +
2,5%)/360 y en corto de −(tipo − 2,5%)/360. El CFD no paga el rendimiento total: a los largos se
les abona el dividendo y a los cortos se les carga; equivale a la rentabilidad total menos la
financiación.

## 4. Evaluación
- Períodos: **IS** 1995-2007 (muestra del libro) y **OOS** 2008 → oct-2026.
- Métricas: operaciones, % ganadoras, PF, rentabilidad y Sharpe sobre el capital (incluidos los
  días sin posición), MDD, exposición, rentabilidad por operación.
- Benchmarks: SPY comprar y mantener; la misma exposición con entradas aleatorias en días SPY > SMA200
  y la misma duración (1.000 simulaciones).
- Selección múltiple: N acumulado = 88; DSR sobre el OOS.
- Fondeo: simulador con el P&L diario. **Compatibilidad:** las posiciones duran varios días y
  cruzan fines de semana; solo encajan en cuentas que lo permitan (FTMO Swing, evaluaciones). No
  se modificará la regla para cerrar los viernes en esta prueba.

## 5. Criterio para pasar a candidata
OOS neto de costes de CFD: PF > 1,3, rentabilidad media por operación > 0 con t ≥ 2, y la estrategia
supera al benchmark de entradas aleatorias con p < 0,05.
