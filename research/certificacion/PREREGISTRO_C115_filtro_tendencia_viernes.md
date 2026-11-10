# PREREGISTRO C115 — Filtro de tendencia en el oro y la plata del viernes — 10-nov-2026

Redactado y subido a git ANTES de calcular. Motivo: el usuario vio en Playback una compra del viernes con el mercado bajando y pregunta si
conviene operar solo con tendencia alcista. Aviso: la idea nace de ver una operación; por eso se fija la regla ahora y se exige mucho.

## Regla a evaluar (una sola definición, sin probar variantes)
Tendencia alcista = el precio del viernes a las 16:00 NY está por encima de la media de los precios de las 16:00 de los 20 días laborables
anteriores. Con filtro: E8 (oro 16:00 → 16:55) y plata viernes (16:30 → 16:57/17:00) solo operan con tendencia alcista.

## Datos
- Contado HistData 2010-06 → 2026-09: XAUUSD y XAGUSD 1 min (rentabilidad bruta; misma tendencia con su propio precio).
- Futuros 2018-2026: series del bot (`componentes_B.csv`: oro_vie_1655, plata_viernes, ya netas de coste) con la tendencia de GC/SI 1 h (Databento).

## Criterio para adoptarlo (todo a la vez)
1. Diferencia viernes alcistas − bajistas > 0 con t ≥ 2,0 en contado 2010-2026, en oro Y en plata por separado.
2. El Sharpe anual de la estrategia con filtro supera al de sin filtro en 2010-17 Y en 2018-26 (contado) y en futuros 2018-26.
3. Para la cartera: el Sharpe de la cartera de 150K con el filtro supera al actual en 2018-21 y en 2022-26.
Si no se cumple todo, el bot sigue comprando todos los viernes. Contador +2.
