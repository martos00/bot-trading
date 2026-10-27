# PREREGISTRO C81 — Deriva previa al FOMC en bolsas fuera de EE. UU. (FTSE, DAX, Nikkei, ASX) — 27-oct-2026

Redactado y subido a git ANTES de calcular. Idea: Lucca y Moench (2015) documentaron la subida de la bolsa en las 24 h previas al
FOMC; en EE. UU. desapareció tras 2015 (nuestras pruebas de la familia FOMC y N2). Nunca se ha medido en bolsas extranjeras con
nuestros datos. Mecanismo: prima por el riesgo del anuncio de la Fed, que afecta a la renta variable mundial.

## Regla
FOMC: reuniones programadas (`n/fomc.csv`), 2010-06 → 2026-09. Bolsa local (CFD de HistData, hora de NY corregida): FTSE UKXGBP
(cierre 16:30 Londres), DAX GRXEUR (cierre 17:30 Fráncfort), Nikkei JPXJPY (15:00 Tokio), ASX AUXAUD (16:00 Sídney). Las cuatro
sesiones del día D0 del FOMC terminan ANTES del anuncio (14:00 NY). **Largo del cierre local del día hábil anterior a D0 al cierre
local de D0.** Días hábiles = días con cierre del propio mercado; si D0 no tiene cierre, sin operación.

## Criterio (4 pruebas)
Signo previsto positivo. Pasa si: t (Newey-West) ≥ 2,24 (Bonferroni unilateral 0,05/4) en 2010-2026, media > 0 en 2010-2017 y en
2018-2026, ≥ 60 % de años positivos y media 2018-2026 > 3,5 pb (spread + 1 noche). Informativo: mismos índices en días sin FOMC.
Lo que pase necesita otra fuente (futuros/índice) antes de nada. Contador +4.
