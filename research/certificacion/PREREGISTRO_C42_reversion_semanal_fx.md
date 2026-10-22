# Pre-registro C42 — Reversión semanal en sección cruzada de divisas — 22-oct-2026
Redactado y enviado a git ANTES de calcular nada.
## Motivo y fuente (de memoria, no texto completo verificado)
La reversión a corto plazo en sección cruzada es una anomalía documentada en acciones (Jegadeesh 1990, Lehmann 1990) y se ha
estudiado en divisas como compensación por proveer liquidez (p. ej. trabajos sobre "currency short-term reversal"). Mecanismo:
los flujos no informativos grandes (coberturas, rebalanceos) empujan una divisa durante la semana y se deshacen después. El
proyecto ha probado momentum, carry y value en divisas, nunca la reversión semanal.
## Regla
Divisas frente al USD: EUR, GBP, JPY, CHF, AUD, CAD, NZD (NZDUSD = EURUSD / EURNZD). FXCM M1, mid a las 16:00 NY del viernes
(o último día hábil de la semana). Cada viernes: rentabilidad de la semana de cada divisa frente al USD; largo de las 2 que más
cayeron, corto de las 2 que más subieron (igual peso, 1/4 cada una), mantenidas hasta el viernes siguiente.
Coste: 1,5 pb ida y vuelta por pata que cambia (2,5 pb para NZD, sintética), proporcional a la rotación.
## Tramos y criterios
Descubrimiento 2012-2018; **confirmación 2019 – 2026-09**: media semanal neta > 0 con t (NW, 4) ≥ 2,0 y ≥ 60 % de años
positivos. Informativo: Sharpe anual, versión con 1 divisa por lado, correlación con E1. Contador +1.
Aplicable en FTMO (CFD de divisas; cuenta Swing por mantener el fin de semana).
