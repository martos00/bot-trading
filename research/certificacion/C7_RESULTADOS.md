# Resultados C7 — Cambio de mes y víspera de festivo (S&P 500 1990-2026): NINGUNA CERTIFICADA

Pre-registro: `PREREGISTRO_C7_cambio_mes_festivos.md` (commit e5a8347). Script `c7_cambio_mes_festivos.py`, salida
`c7_resultados.txt`. Costes CFD: spread 0,5 pb + financiación 2,0 pb por noche.

| S&P 500 | R1 cambio de mes | R2 víspera de festivo |
|---|---|---|
| Descubrimiento 1990-2007: diferencia diaria ventana − resto | +8,0 pb, t 2,28 ✓ | −0,7 pb, t −0,10 ✗ |
| Confirmación 2008-2026: neto por operación | +13,4 pb, t 0,85 ✗ | +12,8 pb, t 1,87 ✗ (exige 2,24) |
| Confirmación: diferencia diaria | +3,0 pb, t 0,72 ✗ | +12,4 pb, t 1,75 ✓ |
| Años netos positivos | 12/19 ✓ | 15/19 ✓ |
| Bruto / coste | 1,9 ✗ (la financiación de 7 noches cuesta 15 pb) | 5,9 ✓ |
| Peor operación / caída máx. (1× capital) | −9,9% / −18,9% | −3,0% / −5,3% |

- **R1:** el efecto existía en 1990-2007 y desde 2008 casi no se distingue de la subida normal de la bolsa; además la
  financiación del CFD se come la mitad y una sola operación puede perder un 10%. Descartada.
- **R2:** no existía en 1990-2007 y aparece en 2008-2026 (también en el Nasdaq 100: +15,4 pb neto, t 1,94), sin llegar al
  umbral. Patrón invertido respecto a la literatura; no se puede certificar con datos ya vistos. Solo podría confirmarse con
  datos futuros (≈ 9 operaciones al año: harían falta muchos años). Descartada como estrategia.
