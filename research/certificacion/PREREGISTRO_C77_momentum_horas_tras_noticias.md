# PREREGISTRO C77 — Momentum de horas tras el informe de inventarios de petróleo (EIA) y tras noticias en EURUSD — 27-oct-2026

Redactado y subido a git ANTES de calcular. Ideas propuestas por el usuario (vía ChatGPT): "momentum tras inventarios de petróleo"
y "difusión lenta de noticias económicas en EURUSD (minutos a horas)". Ya probado y negativo: petróleo corto el miércoles (C27,
sin condicionar a la reacción), continuación 5→30 min tras NFP y FOMC (C76). Aquí: horizonte de HORAS condicionado a la reacción.

## Pruebas (3)
1. **WTI tras el informe EIA**: miércoles 10:30 NY; si el lunes de esa semana o el propio miércoles es festivo NYSE, jueves 11:00
   (aproximación declarada del calendario de la EIA). Señal = signo de P(T+5) − P(T); posición de T+5 a 14:30 NY (liquidación
   del NYMEX). Datos: HistData WTIUSD M1 (2010-2026). Coste 8 pb (doble de un spread normal de CFD de crudo ~4 pb).
2. **EURUSD tras el NFP**: fechas NFP de C76 (identificadas con el ES). Señal 08:30→08:35; posición de 08:35 a 12:00 NY. Coste 1,1 pb.
3. **EURUSD tras el comunicado del FOMC**: reuniones programadas desde 2013-03. Señal 14:00→14:05; posición de 14:05 a 16:00 NY.
   Coste 1,1 pb.
Precios: cierre del último minuto anterior a cada hora (hasta 10 minutos atrás). Sin precio o señal 0 → sin operación.

## Criterio
Por prueba: media bruta > 0 con t (Newey-West) ≥ 2,39 (Bonferroni unilateral 0,05/3); media > 0 antes y desde 2020; media neta
de costes > 0 desde 2020. Pasa → candidata (necesita segunda fuente: CL horario de Databento para el crudo; Dukascopy/FXCM
para EURUSD). Falla → cerrado sin variantes. Informativo: reversión. Contador +3.
