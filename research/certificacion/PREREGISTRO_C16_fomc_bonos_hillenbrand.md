# Pre-registro C16 — Bonos largos en la ventana de 3 días del FOMC (Hillenbrand, RFS 2025) — 21-oct-2026

Redactado y enviado a git ANTES de calcular ningún resultado.

## Fuente (resumen leído vía búsqueda; no el texto completo)
Hillenbrand, "The Fed and the Secular Decline in Interest Rates" (working paper 2020; RFS 2025): casi toda la caída de los
tipos largos desde 1989 se produjo en ventanas de 3 días alrededor de las reuniones del FOMC (día anterior, día del anuncio
y día siguiente); fuera de ellas los movimientos tienden a compensarse. Mecanismo: la guía de la Fed sobre el tipo a largo plazo.

## Regla
Largo del futuro del bono a 10 años (ZN) del cierre del día −2 al cierre del día +1 respecto al anuncio programado
(3 sesiones). Fechas de `research/nuevas/fechas_fomc.py`.
- Réplica 1990-2019 con el rendimiento DGS10 de FRED convertido a precio (bono a la par, como en C8).
- Confirmación 2020-01 → 2026-09 con el futuro real (Yahoo `ZN=F`, días de cambio de contrato anulados).
- Coste 1,8 pb por operación. Informativo: ZB (30 años), ventanas de 3 días sin FOMC.

## Criterios
Réplica: media > 0. Confirmación (todos): (1) media neta > 0 con t ≥ 2,0; (2) bruta ≥ 3 × coste; (3) neta positiva en
≥ 60% de los años; (4) mayor que la media de las ventanas de 3 días sin FOMC (t ≥ 1,645).
Aviso: la confirmación coincide con el ciclo de subidas de tipos de 2022-2023. Contador +1 (N ≈ 1.171).
Nota (no es prueba): se anota como hipótesis para probar SOLO con datos futuros "semanas impares del ciclo FOMC > pares"
(observada a posteriori en C15, t 1,06).
