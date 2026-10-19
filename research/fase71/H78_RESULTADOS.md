# H78 — BTC largo 21:00 → 23:00 UTC (Quantpedia, feb-2022): RESULTADOS

Pre-registro: `PREREGISTRO_H78_btc_21_23utc.md` (commit a54b39d, antes de los datos). Salida completa: `h78_resultados.txt`.
Datos: Binance BTCUSDT 1 h (2017-08 → 2026-09) y 1 min (OOS); comprobación con Coinbase BTC-USD 1 h (OOS).
4 días sin dato excluidos. Motores: `h78_motor.py` (1 h, vectorizado) y `h78_motor_independiente.py`
(1 min, Python puro): diferencia máxima 0 en los 1700 días OOS.

| Tramo | n | Bruto: media / t_NW | Neto base 8,5 pb | Neto estrés 16,5 pb | Control hora aleatoria (p) |
|---|---|---|---|---|---|
| Réplica 2017-08 → 2022-02 | 1628 | **+12,1 pb / 4,51** | +3,6 pb / 1,35 | −4,4 pb | 0,0008 |
| **OOS 2022-02 → 2026-09** | 1700 | **+5,2 pb / 3,01** | **−3,3 pb / −1,91** | −11,3 pb | 0,0042 |
| OOS en Coinbase | 1700 | +5,2 pb / 3,01 (corr. 0,999) | −3,3 pb / −1,90 | — | — |

OOS por año, bruto (pb): 2022 −1,1 · 2023 +6,5 · 2024 +10,9 · 2025 +8,4 · 2026 −0,7. Neto base: positivo solo en 2024.
21 h sigue siendo la mejor hora de inicio en el OOS (la siguiente, 20 h, con +4,2 pb).

## Veredicto: RECHAZADA como candidata (neto negativo), anomalía bruta CONFIRMADA
- Es la primera anomalía de este proyecto que **sobrevive en bruto tras su publicación** con t ≥ 3 en dos bolsas
  y frente a un control aleatorio. Decae a ~43% de su tamaño anterior (12,1 → 5,2 pb), en línea con McLean-Pontiff.
- **No es operable con costes de CFD de fondeo**: equilibrio 5,2 pb por ida y vuelta, frente a 8,5 pb estimados en FTMO
  (comisión 0,0325% por lado, dato de terceros, más spread). La puerta de costes exigiría ≤ 1,7 pb de coste total.
- Los futuros micro de CME no sirven: la ventana coincide con la pausa diaria de CME (17:00-18:00 ET = 21-22 UTC
  en verano, 22-23 UTC en invierno).
- Ninguna regla se ha cambiado; las variantes de la fuente (día, tendencia, volatilidad) no se han evaluado.
- **Seguimiento congelado**: solo volvería a estudiarse si se mide en una cuenta demo un coste total ≤ 1,7 pb
  (requiere autorización del usuario para abrir cualquier cuenta). N acumulado = 93.
