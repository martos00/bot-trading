# C95 — Resultados: ETF apalancados de energía y la media hora antes de la liquidación (14:00 → 14:30 NY) — 28-oct-2026
Preregistro `PREREGISTRO_C95_...` (commit 10e3f5a). Plantilla `c95_quantconnect_plantilla.py` (QuantConnect, 1 min). Salida `c95_resultados.txt`.

| Futuro | 2010-17 | 2018-26 (confirmación) | Años + (2018-26) | Coste | Veredicto |
|---|---|---|---|---|---|
| **NG gas natural** | +7,47 pb (t 5,26) | **+4,79 pb (t 2,75)** | 6/9 | 4 | **PASA (justo por encima del coste)** |
| CL crudo | +3,63 (t 3,03) | +0,41 (t 0,23) | 5/9 | 1,6 | no |
| HO gasóleo (control) | +3,84 (t 3,75) | −1,89 | 2/9 | — | — |
| RB gasolina (control) | +3,29 (t 2,90) | −1,25 | 4/9 | — | — |

- NG dosis-respuesta (terciles de |r|, todo el periodo): +0,4 / +6,5 / +11,2 pb. Placebo 13:30-14:00: +0,15 pb (t 0,19).
- NG por año 2018-26: −1,4, +0,7, +10,8, +2,1, **+22,1 (2022, BOIL/KOLD muy grandes)**, +0,8, +14,5, −1,3, **−8,7 (2026)**.
- Antes de 2018 la continuación aparecía en toda la energía (también en los controles); desde 2018 solo queda en el gas, que es donde
  están los ETF apalancados grandes: coherente con el mecanismo, pero no lo demuestra.

Lectura honesta:
- Pasa los criterios fijados, pero el margen neto es mínimo: +4,79 − 4 ≈ +0,8 pb por operación (Sharpe neto ~0,15). Con salida por
  orden TAS (sin cruzar el spread a la salida) el coste bajaría a ~3 pb → neto ~1,8 pb (Sharpe ~0,35).
- Sin segunda fuente a 1 minuto, y con 2025-2026 negativos. Estado: **candidata**, no ventaja. Pendiente: segunda fuente y coste real del
  NG/QG en la plataforma de la firma. El filtro por |r| grande (tercil alto) no se puede adoptar ahora: sería una regla elegida tras ver
  los datos; requeriría preregistro nuevo con datos nuevos (forward).
Contador +2.
