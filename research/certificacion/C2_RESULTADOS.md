# Certificación C2 — cripto 21:00 → 23:00 UTC: RESULTADOS (20-oct-2026)

Pre-registro: `PREREGISTRO_C2_cripto_21_23utc.md` (commit d7e8058, antes de descargar ETH). Salida: `c2_resultados.txt`.
Datos: Binance ETHUSDT 1 h (2017-08 → 2026-09), motor `research/fase71/h78_motor.py` (el mismo de H78, sin cambios).

| Criterio | Resultado | |
|---|---|---|
| E1 ETH post-publicación (2022-02-04 → 2026-09-30) | n = 1.700, **+6,85 pb/día, t = 2,97** | Cumple (t ≥ 2) |
| E2 Control de hora aleatoria | p = 0,0031 (media simulada 0,49 pb) | Cumple |
| E3 Años positivos | 2022 −4,9 · 2023 +5,8 · 2024 +15,0 · 2025 +13,7 · 2026 +2,5 → **4/5** | Cumple |
| E4 Informativo | Correlación diaria ETH-BTC en la franja 0,83; ETH antes de 2022-02: +13,0 pb, t = 3,98; las 21 h son la mejor hora de inicio también en ETH post-publicación (siguiente: 20 h, +4,6 pb) | — |

## Veredicto: VENTAJA CERTIFICADA (bruta)
Junto con H78 (BTC: +5,2 pb, t = 3,0 en Binance y Coinbase, control p = 0,004), la subida de cripto entre las 21:00 y
las 23:00 UTC cumple todos los criterios de certificación: aparece antes y después de su publicación, en dos bolsas y en
un segundo activo no usado para descubrirla, frente a un control aleatorio y la mayoría de los años.
Límites: ETH y BTC no son independientes (correlación 0,83); el tamaño ha bajado tras la publicación (BTC 12 → 5 pb,
ETH 13 → 7 pb). **Certifica la ventaja, no una estrategia**: con los costes de un CFD de fondeo (FTMO, ≈ 6,5 pb solo de
comisión) no es operable; el siguiente paso es buscar la forma de operarla con un coste menor que la ventaja.
