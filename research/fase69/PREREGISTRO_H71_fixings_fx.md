# Pre-registro H71 — Reversiones intradía en torno a los fixings de divisas (Krohn, Mueller & Whelan 2024)

Redactado y enviado a git ANTES de construir las series y de calcular ningún resultado.

## 1. Fuente

**Krohn, Mueller & Whelan (2024)**, "Foreign Exchange Fixings and Returns around the Clock",
*Journal of Finance* 79(1):541-578. Leído el working paper del Banco de Canadá (SWP 2021-48).
Datos: G9 frente a USD, 1999-2019, mid-quotes de alta frecuencia. Hecho principal: el USD
se aprecia antes de los fixings (Tokio 9:55 hora de Tokio; BCE 14:15 Frankfurt; WM/R
16:00 Londres) y se deprecia después (t entre 4,5 y 11,7). Mecanismo: los dealers cubren
por adelantado una demanda incondicional de USD en el fixing (inventario/intermediación
con restricciones).

Estrategias del paper (sección V): **Europa** = largo USD de 2:00 a 8:15 ET (hasta el
fixing del BCE) + corto USD de 11:00 a 17:00 ET (tras el fixing de Londres); **Tokio** =
largo USD de 17:00 a 20:55 ET + corto USD de 20:55 a 2:00 ET. Bruto, Europa: EUR 15,6%,
GBP 12,4% anual, vol < 8%. Con el 100% del spread indicativo: negativas; con el 50%:
EUR 8,64% pre-BCE y 5,46% post-Londres. Tokio con el 50% del spread: negativa desde 2013
en EUR/GBP, plana en JPY. Los autores concluyen que "no es obvio que pueda explotarlo el
operador medio".

## 2. Equivalencia con hipótesis anteriores del proyecto

Ninguna. Las pruebas intradía anteriores fueron de índices (ORB, VWAP, momentum intradía,
H1-H6) u oro; las de divisas fueron mensuales (TSMOM, carry, valor, COT). Es un mecanismo
nuevo para el proyecto (inventario de dealers en torno a un evento diario fijo).

## 3. Datos

- HistData M1 BID, EURUSD, GBPUSD, USDJPY, 2003-2026. Marca horaria = hora local de Nueva
  York con horario de verano (verificado: el salto de actividad de las 08:30 ET aparece en
  la marca 08:30 en verano e invierno, todos los años; mismo hallazgo que en SPXUSD).
- Las horas de los fixings se aplican en su hora local real y se convierten a ET cada día
  (Tokio no tiene horario de verano; Frankfurt/Londres cambian en fechas distintas a NY).
- Precio en T = cierre de la última vela M1 con apertura en [T-5 min, T-1 min]; sin
  rellenos. Antes de calcular: `calidad_datos.auditar_historico()` sobre barras diarias;
  días en huecos GRAVES excluidos.
- Spreads: Dukascopy BID/ASK M1, muestra fijada = primer día laborable de cada mes,
  2019-01 a 2026-09, EURUSD y GBPUSD (USDJPY: se usará el spread de EURUSD en pips × 1,5 como
  aproximación declarada si no da tiempo a descargarlo).

## 4. Reglas (adaptación minorista declarada: no operar en el minuto del rollover)

Rentabilidad = log de la variación del precio del USD frente a la divisa extranjera.

| Estrategia | Tramo 1 (largo USD) | Tramo 2 (corto USD) | Días |
|---|---|---|---|
| Europa | 08:00 Frankfurt → 14:15 Frankfurt (fixing BCE) | 16:00 Londres (fixing WM/R) → **16:55 ET** (paper: 17:00) | lunes-viernes, excluidos festivos TARGET |
| Tokio | **17:05 ET** del día anterior (paper: 17:00) → 09:55 Tokio | 09:55 Tokio → 08:00 Frankfurt | lunes-viernes de Tokio, excluidos festivos de Japón |

Las 4 h 55/17 h 05 evitan el rollover de las 17:00 ET (spread máximo y cargo de swap): sin
swap en ninguna posición. Sin filtros ni parámetros adicionales.

Ensayos: Europa × {EURUSD, GBPUSD, USDJPY} + Tokio × {EURUSD, GBPUSD, USDJPY} = 6.
**Principal: H71a = Europa en EURUSD.** Contador de selección múltiple: N = 79.

## 5. Evaluación

- Períodos: **REP** 2003-2019 (dentro de la muestra del paper: comprueba la fidelidad de la
  reproducción); **OOS** ene-2020 → oct-2026 (posterior a sus datos; la prueba que importa);
  se informa aparte 2024-2026 (posterior a la publicación), sin criterio por su tamaño.
- Métricas: media diaria en pb con t de Newey-West (5 rezagos), % días positivos, Sharpe
  anual, drawdown, desglose por año y por tramo.
- Control: misma estrategia con signo aleatorio por día (10.000 simulaciones).

## 6. Costes

Por tramo (una ida y vuelta): spread medido a la entrada/2 + spread medido a la salida/2 +
comisión ECN 0,35 pb por lado + 0,1 pb de deslizamiento por lado.
- **Escenario principal (ECN):** spread = mediana Dukascopy de la muestra para esa hora
  (redondeada a la media hora más próxima) y ese par.
- Estrés: 2 × spread medido + comisión + deslizamiento.
- Cuenta estándar sin comisión: spread fijo 1,0 pip EURUSD, 1,5 pip GBPUSD, 1,0 pip USDJPY.

## 7. Criterios de decisión (H71a)

1. REP: media bruta > 0 (si no, la reproducción no es fiel y se investiga antes de concluir).
2. OOS: media bruta > 0 con t ≥ 2.
3. OOS: media neta (escenario ECN principal) > 0 con t ≥ 2, y positiva en ≥ 4 de los 7 años.
4. DSR ≥ 0,95 sobre la serie neta OOS con N = 79.
5. Dos motores independientes idénticos.

Si se cumplen todos: congelar especificación, prueba de estrés de costes, cálculo de capital
y riesgo, EA para MT5 y propuesta de forward test en demo. Si no: se cierra.
