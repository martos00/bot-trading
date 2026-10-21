# Pre-registro G1 y G2 — Ideas propuestas por Google al usuario (21-oct-2026)

Redactado y enviado a git ANTES de calcular nada. Valores estándar de los indicadores; nada se ajusta después.
Datos HistData M1 (BID, hora de Nueva York con cambio de hora, verificada). Descubrimiento 2010-2017, confirmación
2018-2026-09. N acumulado del proyecto: +3.

## G1 — Reversión a la media en la sesión asiática (EURUSD y GBPUSD) — 2 pruebas
- Velas de 15 min construidas desde M1. Bandas de Bollinger (20, 2) sobre los cierres de 15 min (causales, continuas).
- Ventana de entrada: velas que cierran entre las 19:00 y la 01:00 NY (sesión asiática, después de la pausa de las 17:00).
- Señal al cierre de la vela: cierre < banda inferior → compra; cierre > banda superior → venta. Entrada a la apertura de
  la vela siguiente. Una sola posición a la vez.
- Salida: al cierre de la primera vela que cruce la media de 20 (SMA20), ejecutada a la apertura de la vela siguiente; o
  cierre forzoso a las 02:00 NY (antes de la apertura europea, como aconseja la propia idea). Sin stop.
- Coste por operación (ida y vuelta, spread asiático + comisión): EURUSD 0,8 pb, GBPUSD 1,2 pb. Estrés: ×2.
- Criterios (cada par): en confirmación, media neta por operación > 0 con t ≥ 2,24 (Bonferroni para 2 pares); media bruta
  ≥ 2 × coste; positiva en ≥ 6 de 9 años; y media neta del descubrimiento > 0 (misma dirección).

## G2 — Pares oro/plata (cointegración simple) — 1 prueba
- Cierres diarios (último minuto del día de NY) de XAUUSD y XAGUSD. L = ln(oro / plata) (relación fija 1:1 en valor,
  sin estimar coeficientes, para no mirar el futuro). z = (L − media de 60 días) / desviación de 60 días (días anteriores).
- Entrada al cierre del día con |z| > 2: si z > 2, venta de oro y compra de plata (mismo nominal); si z < −2, al revés.
- Salida: cuando z cruza 0, o a los 20 días hábiles como máximo.
- Costes: spreads de entrada y salida 1,5 pb por pata (3 pb por operación) + financiación nocturna neta del par
  (la pata larga paga y la corta cobra menos): 1,4 pb por día de posición sobre el nominal de una pata.
- Criterios: en confirmación, media neta por operación > 0 con t ≥ 2; positiva en ≥ 6 de 9 años; media neta del
  descubrimiento > 0.

Si alguna se confirma, pasa a certificación (otra fuente de datos con BID/ASK y costes medidos), como C1.
