# PREREGISTRO E10b — Plata larga en víspera de festivo NYSE, 16:00 → 16:45 NY (salida adelantada por el cierre de las firmas de futuros) — 28-oct-2026

Base: E10 (certificada, 16:00 → 16:55; desactivada en FTMO porque el spread del CFD ~14,5 pb supera la ventaja). Las firmas de fondeo de
futuros obligan a cerrar antes de las 16:45-16:50 NY (TradeDay 16:50, Lucid 16:45): la salida se adelanta a 16:45, la hora la fija la
plataforma (igual que E8b con el oro).

**Transparencia:** antes de este preregistro calculé el tramo en el FUTURO SI (Databento 1 min): 16:00→16:45 n 131, +5,50 pb (t 3,95),
2018-26 +6,13 pb. Ese número ya visto no puede usarse como confirmación. La prueba que decide es la segunda fuente, aún no calculada:

## Prueba (HistData XAGUSD M1, contado BID; hora de NY con cambio de hora, ya corregida)
Vísperas de festivo NYSE (último día laborable antes de un festivo), 2010-06 → 2026-09. Largo del cierre del minuto 15:59 al cierre del
último minuto ≤ 16:44 NY.

## Criterio (como C49)
Media > 0 con t (Newey-West) ≥ 2,0; ≥ 60 % de años positivos; media 2018-2026 > 0 y > coste de futuros SI (2,3 pb). Pasa → E10b
utilizable en una cuenta de fondeo de futuros (no en FTMO). Falla → se cierra. Contador +1.
