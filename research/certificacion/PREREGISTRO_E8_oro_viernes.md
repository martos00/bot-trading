# Pre-registro E8 — Estrategia "oro del viernes" (B4 + C45) — 22-oct-2026
Congelada ANTES de calcular el backtest con tamaño y la cartera con E2.
## Regla de operación
- Cada viernes hábil (si el viernes es festivo de EE. UU. y el CME cierra antes, no se opera): compra de oro (CFD XAUUSD o futuro GC/MGC)
  a las 16:00:00 NY; cierre a las 16:55:00 NY. Nunca se mantiene el fin de semana.
- Tamaño: riesgo objetivo r % del capital por operación = r / (desviación de los últimos 52 viernes de la rentabilidad 16:00-16:55);
  stop de catástrofe a 4 desviaciones. r = 0,5 % (igual que E2).
- Coste: futuro 0,74 pb; CFD = el medido con Medir_Costes_Oro_Viernes_Gas_Jueves.mq5 (provisional 1,5 pb).
- Regla de noticias FTMO: no hay noticias programadas de alto impacto a las 16:00/16:55 NY del viernes (comprobar en el calendario de MT5;
  si las hubiera a ±2 min, no se opera ese viernes).
## Backtest (informativo; la certificación ya está hecha con B4 + C45)
GC.v.0 1 min (Databento), 2011-2026: rentabilidad anual, Sharpe, caída máxima, años positivos; correlación con E1; cartera E2 + E8 con
igual riesgo. Luego forward en demo junto con E2. Contador +0 (no es una prueba nueva).
