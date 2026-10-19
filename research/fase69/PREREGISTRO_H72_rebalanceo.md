# Pre-registro H72 — Front-running del rebalanceo institucional (Harvey, Mazzoleni & Melone 2025/2026)

Redactado y enviado a git ANTES de construir las series y de calcular ningún resultado.

## 1. Fuente

**Harvey, Mazzoleni & Melone**, "The Unintended Consequences of Rebalancing", NBER WP 33554
(2025); leída la versión del 14-ene-2026 (Fisher College WP 2025-03-001). Muestra
1997-09-10 → 2023-03-17, futuros diarios S&P 500 y T-Note 10 años. Mecanismo: fondos con
mandatos 60/40 (pensiones, TDF, soberanos; ~20 billones USD) rebalancean por calendario o por
umbral; cuando la renta variable está sobreponderada venden acciones y compran bonos, lo que
predice −16/−17 pb en renta variable al día siguiente por desviación típica de la señal. El
efecto es nulo en 1961-1997 (tabla 4 del paper) y aparece a partir de ~2000.

Estrategia del paper (sección 4, tabla 6): R_{t+1} = (R^SP_{t+1} − R^10Y_{t+1}) · w_t, con
w_t = media de (i) −Threshold_t / 1,5% y (ii) Calendar modificado. Resultado bruto: 10,2%
anual, vol 9,2%, Sharpe 1,11, asimetría 5,2 (muy dependiente de 2008-09 y 2020; sin esos
meses Sharpe 0,90); los autores estiman un Sharpe neto "cercano a 1".

## 2. Equivalencia con hipótesis anteriores

"Turno de mes" (`hipotesis_turno_mes.py`) probó un efecto de calendario incondicional en
USTEC/US500 2023-2026. Aquí la dirección depende de la desviación de una cartera 60/40
(puede ser larga o corta), con una segunda pata en bonos y una señal de umbral que actúa
cualquier día. No es equivalente.

## 3. Datos

- S&P 500 Total Return diario (Yahoo `^SP500TR`, desde 1988).
- T-Note 10 años: rentabilidad total diaria a partir del rendimiento DGS10 (FRED) con un
  bono a la par revalorizado cada día (aproximación declarada; el paper usa futuros y
  Gürkaynak-Sack-Wright). Días con ambos datos; sin rellenos.
- La diferencia de rentabilidades totales equivale a la diferencia de rentabilidades de los
  futuros (el tipo sin riesgo se cancela).
- `calidad_datos.auditar_historico()` sobre ambas series antes de calcular.

## 4. Reglas (literalmente las del Apéndice B y la sección 4)

- Cartera 60/40 que deriva con los rendimientos diarios.
- Threshold^δ_t = peso de RV antes de rebalancear − 60%; se rebalancea a 60% si
  |desviación| ≥ δ. Threshold_t = media sobre δ = 0%, 0,1%, …, 2,5% (26 valores).
- Calendar_t = desviación de una cartera que solo rebalancea el último día hábil del mes.
- "week4" = últimos 5 días hábiles del mes.
- Calendar modificado: sign(−Calendar_t) en week4; el primer día hábil del mes siguiente,
  sign(Calendar en el día T−4 del mes anterior) (interpretación declarada de "Calendar
  Signal_{−4}"); 0 el resto de días.
- w_t = ( −Threshold_t/1,5% + Calendar modificado_t ) / 2, aplicado a la rentabilidad del día
  t+1 (S&P menos T-Note).
- Días hábiles = días con dato en ambas series.

## 5. Ensayos (N acumulado = 81)

- **H72a (principal):** estrategia completa del paper (dos patas), costes de futuros.
- H72b: solo la pata de renta variable (R^SP_{t+1} − rf) · w_t, implementable con un CFD
  del S&P 500, costes de CFD.

## 6. Evaluación y costes

- **REP** 1997-09-10 → 2023-03-17 (muestra del paper: comprobar fidelidad, objetivo Sharpe
  ≈ 1,1). **OOS** 2023-03-20 → último dato (la prueba que importa).
- Costes por unidad de rotación del peso (una vía): futuros S&P 0,6 pb, T-Note 1,0 pb.
  CFD S&P: 0,8 pb + recargo de financiación 2,5%/año sobre |w|.
- Métricas: media diaria, t de Newey-West (5), Sharpe, drawdown, asimetría, por año.
- Control: signo aleatorio por día (10.000 simulaciones) en OOS.

## 7. Criterios (H72a)

1. REP: Sharpe bruto ≥ 0,7 (si no, la reproducción no es fiel).
2. OOS: media neta de costes de futuros > 0 con t ≥ 2.
3. DSR ≥ 0,95 en OOS neto con N = 81.
4. Dos implementaciones independientes idénticas.
Aviso de potencia: con ~3,5 años de OOS, t ≥ 2 exige un Sharpe OOS ≥ ~1,05. Si el OOS
es positivo pero no alcanza el umbral, la conclusión será "no confirmada", no "refutada".
