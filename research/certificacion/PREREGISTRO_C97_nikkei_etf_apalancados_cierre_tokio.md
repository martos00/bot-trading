# PREREGISTRO C97 — Nikkei: rebalanceo de los ETF apalancados/inversos japoneses en la última media hora de Tokio — 28-oct-2026

Redactado y subido a git ANTES de calcular. Mecanismo de C95 en el mercado donde esos ETF pesan más: los ETF del Nikkei ×2 (1570) y
−1/−2 (1571, 1357, 1360) y los de TOPIX rebalancean al cierre de Tokio comprando si el día sube y vendiendo si baja (L(L−1) > 0).
Previsión: continuación en la última media hora de la sesión de contado.

## Regla (hora de Tokio, JST)
Cierre de la sesión: 15:00 JST hasta el 4-nov-2024; 15:30 JST desde el 5-nov-2024 (ampliación de la TSE). C = cierre; A = C − 30 min.
r = ln(P(A) hoy / P(C) sesión anterior). Posición en el sentido de r de A a C. Días laborables de Japón con datos en ambas horas.

## Datos
- Principal: HistData JPXJPY M1 (índice Nikkei, CFD sobre el futuro de Osaka; hora de NY con cambio de hora → convertida a JST),
  2010-06 → 2026-09.
- Confirmación: futuro NKD (CME) de Databento en barras de 1 h: barra 14:00-15:00 JST (05-06 UTC) con señal 15:00 JST anterior → 14:00 JST,
  toda la muestra (aproximación horaria; aviso: en NKD los precios nocturnos pueden estar rancios, ver B14/C60).
- Controles informativos sin ETF apalancados grandes: ASX 200 (AUXAUD; cierre 16:00 Sídney) y Hang Seng (HKXHKD; cierre 16:00 HK),
  misma regla con su cierre.

## Criterio (1 prueba)
HistData: descubrimiento 2010-06 → 2017 media > 0; confirmación 2018 → 2026-09 media > 0 con t (Newey-West) ≥ 2,0, ≥ 60 % de años
positivos y media > coste del NKD (2,5 pb: 1 tick ≈ 1,25 pb + spread nocturno). Y Databento NKD: media > 0 con t ≥ 2,0 en 2018-2026.
Contador +1.
