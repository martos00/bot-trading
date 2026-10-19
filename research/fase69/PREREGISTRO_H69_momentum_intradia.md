# Pre-registro H69 — Market Intraday Momentum (reproducción fiel)

Redactado y enviado a git ANTES de calcular ningún resultado con los datos nuevos.
Ninguna regla de este documento se modifica después de ver resultados; cualquier
cambio posterior se añade como apéndice fechado y se cuenta como hipótesis nueva.

## 1. Fuentes que se reproducen

- **Gao, Han, Li & Zhou (2018)**, "Market intraday momentum", *JFE* 129(2):394-414.
  Leído el working paper (versión dic-2015). SPY 1993-2013. La rentabilidad de la
  primera media hora, **medida desde el cierre del día anterior hasta las 10:00 ET**
  (r_ONFH), predice la de la última media hora (15:30-16:00 ET). R² 1,6%. Estrategia de
  timing: 6,67%/año bruto; 4,46%/año tras spread (2001-2013); 6,52% tras spread
  (2005-2013, spread proporcional ≈1,2 pb; salida en la subasta de cierre, sin spread).
- **Baltussen, Da, Lammers & Martens (2021)**, "Hedging demand and market intraday
  momentum", *JFE* 142:377-403. Leído el PDF del autor. >60 futuros 1974-2020.
  Predictor principal: **rentabilidad del resto del día** r_ROD = cierre anterior → 15:30
  ET. Mecanismo: cobertura gamma de creadores de mercado de opciones y ETF apalancados.
  **No modelan costes**; dicen explícitamente que puede no ser explotable salvo a ~1 tick
  de coste en el futuro del S&P 500.

## 2. Por qué NO es una repetición de `hipotesis_momentum_intradia.py` (ya descartada)

| | Prueba anterior | Esta prueba |
|---|---|---|
| Señal | Solo 9:30-10:00 (2 velas M15), **sin el tramo overnight** | r_ONFH incluye el overnight (definición de Gao); r_ROD (Baltussen) |
| Datos | CFD MetaQuotes-Demo M15, hora de apertura inferida por saltos de TickVolume (72-85% de días) | HistData M1, hora fija EST documentada (UTC-5), conversión exacta a ET con calendario NYSE |
| Muestra | 2023-2026 (~700-800 días), con hueco jul-sep 2025 | 2010-2026 (~4.000 días); incluye período post-publicación |
| Fuente independiente | No | Dukascopy (UTC exacto, BID/ASK) para contraste de una submuestra |

## 3. Datos y limpieza (fijados de antemano)

- Primaria: HistData `SPXUSD` (S&P 500) y `NSXUSD` (Nasdaq 100), M1, BID, EST fijo.
  Hora ET = EST + 1 h en los días en que Nueva York está en horario de verano
  (`America/New_York`).
- Calendario: `pandas_market_calendars` NYSE. Se usan solo sesiones regulares completas;
  se **excluyen** los días de cierre anticipado (13:00 ET) y el primer día tras un festivo
  sí se mantiene (su "cierre anterior" es la última sesión NYSE).
- Precio en el instante T = cierre de la última vela M1 con hora de apertura en
  [T-5 min, T-1 min]. Si no existe, el día se excluye (no se rellena nada).
  P(10:00) = cierre de la vela 09:59; P(15:30) = vela 15:29; P(16:00) = vela 15:59.
- Antes de cualquier cálculo: `calidad_datos.auditar_historico()` sobre las barras RTH
  diarias construidas. Huecos ≥3 días hábiles → GRAVE: los días afectados se excluyen y
  se reporta. Además se informa del % de sesiones NYSE con los 4 precios disponibles.

## 4. Hipótesis (exactamente 4 pruebas; se suman al contador de selección múltiple)

| Id | Mercado | Señal | Operación |
|---|---|---|---|
| H69a (principal) | S&P 500 | sign(r_ROD), r_ROD = ln P(15:30)/P(16:00 día anterior) | posición ±1 de 15:30 a 16:00 |
| H69b | S&P 500 | sign(r_ONFH), r_ONFH = ln P(10:00)/P(16:00 día anterior) | igual |
| H69c | Nasdaq 100 | sign(r_ROD) | igual |
| H69d | Nasdaq 100 | sign(r_ONFH) | igual |

Sin filtros, sin umbrales, sin parámetros que optimizar. Si la señal es exactamente 0, no
se opera.

## 5. Estadística y benchmarks

- Regresión predictiva r_LH = a + b·señal, t de Newey-West (5 rezagos).
- Estrategia de timing: rentabilidad diaria = sign(señal)·r_LH.
- Benchmarks: (i) *Always Long* en la última media hora; (ii) signo aleatorio
  (10.000 permutaciones del signo); (iii) la parte "beta" se controla regresando la
  estrategia sobre r_LH.
- Subperíodos fijados: **P1** 2010-2013 (solapa con la muestra de Gao),
  **P2** 2014 → mayo-2020 (fuera de muestra de Gao, dentro de la de Baltussen),
  **P3** junio-2020 → 2026 (posterior a ambas publicaciones = la prueba que importa).
- Selección múltiple: Deflated Sharpe Ratio (Bailey & López de Prado 2014) con
  N = 72 ensayos (68 previos del proyecto + estas 4), varianza de Sharpe entre ensayos
  estimada de los 4 Sharpe de esta familia con un mínimo conservador de 0,5² anual.

## 6. Costes (por operación de ida y vuelta)

- CFD sin comisión: se paga el spread completo (entrada al ask/salida al bid o al revés),
  porque el CFD no tiene subasta de cierre.
- Escenarios: S&P 500 → 0,40 pt (spread US500 registrado en MetaQuotes-Demo) y
  0,40 + 0,25 pt de slippage; Nasdaq 100 → 0,90 pt y 0,90 + 0,50 pt. Además se reporta el
  **coste de equilibrio** (pb por operación que deja la media en cero) y, donde haya
  datos Dukascopy, el spread ASK-BID medido a las 15:30 y 16:00 ET.
- Sin swap (no se mantiene posición overnight). Gaps: no aplican (posición intradía).

## 7. Criterios de decisión (fijados ahora)

Pasa a "candidata" solo si se cumplen TODOS en H69a:
1. P3 (post-publicación): media bruta > 0 con t HAC ≥ 2.
2. Media neta > 0 con el escenario 0,40 + 0,25 pt en el total y en ≥ 2 de los 3
   subperíodos.
3. DSR ≥ 0,95.
4. Contraste con Dukascopy (`USA500IDXUSD`, BID+ASK M1, submuestra fijada: todos los
   días laborables de 2016 y 2023 — el servidor limita a ~3 ficheros/min, la serie
   completa llevaría ~40 h) en los días solapados: coincidencia de signo de la señal
   ≥ 95% y correlación de rentabilidades diarias de la estrategia ≥ 0,9.
5. Dos implementaciones independientes del motor (vectorizada y bucle explícito)
   producen la misma serie de operaciones.

H69b-d se reportan como réplica/robustez; no pueden rescatar a H69a si esta falla.
Si falla, la línea se cierra y se pasa a la siguiente estrategia seleccionada
(trend following diversificado, ver `REVISION_FUENTES.md`).

## Apéndice A (19-oct-2026, antes de calcular ningún resultado de la estrategia) — corrección de huso horario

La documentación de HistData indica "EST sin horario de verano". Verificación empírica
sobre los datos descargados (cociente entre el rango medio de los minutos hh:30-hh:34 y el
de hh:15-hh:28, por año y por estado de horario de verano de Nueva York): el salto de
actividad de la apertura de NY aparece en la marca **09:30** tanto en verano como en
invierno de **todos** los años 2010-2026 (cociente 2,1-4,9), y el cociente en 10:30 es
≈1,0 siempre. Con la regla "EST fijo" las señales de verano quedarían desplazadas una hora.

Decisión: las marcas de HistData para SPXUSD/NSXUSD se interpretan como hora local de
Nueva York (con horario de verano). Es una corrección de la lectura de los datos, tomada
antes de ver ninguna rentabilidad; no cambia ninguna regla de la estrategia.
Aviso para el resto del proyecto: cualquier uso previo de HistData que asumiera EST fijo
(p. ej. XAUUSD 2015-2022) debería verificarse con el mismo test.
