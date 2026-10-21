# Resultados P3 — Yen en horario de Tokio con costes reales: SE CIERRA

Pre-registro: `PREREGISTRO_P3_yen_tokio_viabilidad.md` (commit 3cbc7b4). Script `p3_yen_tokio.py`, salida `p3_resultados.txt`.
FXCM M1 BID/ASK 2012-2026, 3.691 días.

| | Resultado | Criterio |
|---|---|---|
| Punto medio | +1,43 pb/día, t 3,17 | — |
| Ejecutable (venta al BID 08:00, recompra al ASK 15:00, comisión y deslizamiento) | **+0,26 pb/día, t 0,57** | ✗ (t ≥ 2) |
| Coste medio | 1,17 pb (ventaja/coste 1,2) | ✗ (≥ 3) |
| Años netos positivos | 6/15 | ✗ (≥ 60%) |
| Spread 08:00 Tokio | mediana 0,46 pb, p90 1,95 pb (cola por la cercanía del rollover) | informativo |
| Correlación con E1 | −0,06 (diversificaría, si fuera operable) | informativo |

Además, en punto medio el efecto se ha debilitado: negativo en 2021, 2023, 2024 y 2026. **No pasa a forward test.**
